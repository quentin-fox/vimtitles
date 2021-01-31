import pynvim
import datetime
import subprocess
import json
import re
import mimetypes
import pathlib
import time
from functools import wraps

SINGLE_TS_FORMAT = r'^\d\d:\d\d:\d\d,\d\d\d$'
# leaving off '\s\?' and '$', not always needed
FULL_TS_FORMAT = r'^\d\d:\d\d:\d\d,\d\d\d --> \d\d:\d\d:\d\d,\d\d\d'


@pynvim.plugin
class VimtitlesPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim
        self.running = False
        self.playspeed = 1
        self.player = None

    def requires_player(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not self.player or not self.running:
                self.write_err("Player must be running")
            else:
                func(self, *args, **kwargs)
        return wrapper

    def write_err(self, err: str):
        self.nvim.err_write(err + '\n')

    def write_msg(self, msg: str):
        self.nvim.out_write(msg + '\n')

    def parse_filetype(self, filename):
        mime_guess = mimetypes.guess_type(filename)[0]
        if mime_guess is None:
            raise ValueError(f'{filename} is not a known audio or video type')
            return
        if "audio" in mime_guess:
            return("a")
        elif "video" in mime_guess:
            return("v")
        else:
            raise ValueError(f'{mime_guess} is not a known audio or video type')

    def user_prompt(self, prompt: str) -> str:
        self.nvim.command('call inputsave()')
        self.nvim.command("let user_input = input('" + prompt + "')")
        self.nvim.command('call inputrestore()')
        return self.nvim.eval('user_input')

    @pynvim.command('PlayerOpen', nargs='+', complete='file')
    def player_open(self, args):
        if self.running:
            self.running = self.player_quit()

        filename = args[0]
        timestart = args[1] if len(args) > 1 else '0:00'
        geometry = args[2] if len(args) > 2 else '50%x50%'

        try:
            self.player = Player(filename=filename)
        except FileNotFoundError as err:
            self.write_err(str(err))

        try:
            filetype = self.parse_filetype(filename)
        except ValueError as err:
            msg = str(err) + '. Open anyways as a/v? (Enter to cancel.) '
            output = self.user_prompt(msg)
            if output.lower() not in {'a', 'v'}:
                return
            else:
                filetype = output.lower()

        self.player.play(av=filetype, timestart=timestart, geometry=geometry)

        # just used to see if the player opened - won't have any effects
        time.sleep(0.50)
        if self.player.test_open() != 1:
            msg = f'mpv encountered an error opening {filename}'
            self.write_err(msg)
            self.running = False
        else:
            self.running = True

    @pynvim.command('PlayerQuit')
    @requires_player
    def player_quit(self):
        if self.running:
            self.running = self.player.quit()
            self.write_msg('Quitting Player...')

    @pynvim.command('PlayerCyclePause')
    @requires_player
    def player_pause(self):
        self.player.cycle_pause()

    @pynvim.command('SetTimestamp')
    @requires_player
    def set_timestamp(self):
        ts = Timestamp(self.player.get_time())
        buffer = self.nvim.current.buffer

        # c flag will also accept the current cursor line
        blank_line = self.get_line('^\\s*$', 'bnc')
        timestamp_line = self.get_line(SINGLE_TS_FORMAT, 'bnc')
        arrow_line = self.get_line('-->', 'bnc')
        if blank_line > timestamp_line and blank_line > arrow_line:
            buffer[blank_line] = str(ts)
        elif timestamp_line > blank_line:
            # abort if there's a second timestamp
            old_ts = buffer[timestamp_line]
            ts_pair = TimestampPair(old_ts + ' --> ' + str(ts))
            buffer[timestamp_line] = str(ts_pair)

    def get_line(self, pattern, flags):
        row, col = self.nvim.funcs.searchpos(pattern, flags)
        return(row - 1)

    @pynvim.command('PlayerSeekForward')
    @requires_player
    def player_seek_forward(self):
        try:
            seconds = float(self.nvim.eval('g:vimtitles_skip_amount'))
        except NameError:
            seconds = 5  # default time to skip if not set in init.vim
        self.player.seek(seconds)

    @pynvim.command('PlayerSeekBackward')
    @requires_player
    def player_seek_backward(self):
        try:
            seconds = float(self.nvim.eval('g:vimtitles_skip_amount')) * -1
        except NameError:
            seconds = -5  # default time to skip if not set in init.vim
        self.player.seek(seconds)

    @pynvim.command('PlayerSeekByStartTimestamp')
    @requires_player
    def player_seek_by_start_ts(self):
        """will seek to the timestamp at the beginning of the most recent line"""
        buffer = self.nvim.current.buffer
        ts_line = self.get_line(SINGLE_TS_FORMAT[:-1], 'bnc')  # don't want EOL regex $
        start_ts_str = buffer[ts_line].split(' ')[0]
        start_ts = Timestamp.from_string(start_ts_str)
        self.player.seek_abs(start_ts.seconds)

    @pynvim.command('PlayerSeekByStopTimestamp')
    @requires_player
    def player_seek_by_stop_ts(self):
        """will seek to the timestamp at the beginning of the most recent line"""
        buffer = self.nvim.current.buffer
        ts_line = self.get_line(FULL_TS_FORMAT, 'bnc')
        ts_pair = TimestampPair(buffer[ts_line])
        self.player.seek_abs(ts_pair.ts2.seconds)

    @pynvim.command('PlayerSeekAbs', nargs=1)
    @requires_player
    def player_seek_abs(self, args):
        time_input = args[0]
        try:
            if ":" in time_input:
                time_switch = {
                    4: "%M:%S",  # 0:00
                    5: "%M:%S",  # 00:00
                    12: "%H:%M:%S,%f"  # 00:00:00,000
                }
                time_format = time_switch.get(len(time_input))
                time_struct = datetime.datetime.strptime(time_input, time_format)
                td = time_struct - datetime.datetime(1900, 1, 1)
                time_float = td.total_seconds()
            if ":" not in time_input:
                time_float = float(time_input)
        except ValueError:
            time_float = self.player.get_time()
        finally:
            self.player.seek_abs(time_float)

    @pynvim.command('PlayerLoop')
    @requires_player
    def player_loop(self):
        buffer = self.nvim.current.buffer
        ts_line = self.get_line(FULL_TS_FORMAT, 'bnc')
        blank_line = self.get_line('^\\s*$', 'bn')
        if blank_line > ts_line:
            return
        elif ts_line > blank_line:
            self.ts_loop = TimestampPair(buffer[ts_line])
            self.player.loop(self.ts_loop.ts1.seconds, self.ts_loop.ts2.seconds)
            self.write_msg(f"Looping between {self.ts_a} and {self.ts_b}")

    @pynvim.command('PlayerStopLoop')
    @requires_player
    def player_stop_loop(self):
        if self.ts_loop:
            self.player.stop_loop()
            self.write_msg("Stopping loop")
            del self.ts_loop
        else:
            self.write_msg("No loop found")

    @pynvim.command('RemoveSubNumbers')
    def remove_sub_numbers(self):
        buffer = self.nvim.current.buffer
        subnums = [bool(re.match('^\\d+$', x)) for x in buffer]
        subindex = [i for i, x in enumerate(subnums) if x]
        subindex.reverse()
        for i in subindex:
            del buffer[i]

    @pynvim.command('AddSubNumbers')
    def add_sub_numbers(self):
        buffer = self.nvim.current.buffer
        blank_lines = [bool(re.match('^\\s*$', x)) for x in buffer]
        arrow_lines = ['-->' in x for x in buffer]
        # compensates for the missing blank line at the top
        blank_lines[0:0] = [True]
        arrow_lines[0:0] = [False]
        arrow_lines_rot = arrow_lines[1:] + arrow_lines[:1]  # rotate so matches blank_lines
        sub_lines = [b & a for b, a in zip(blank_lines, arrow_lines_rot)]
        subindex = [i for i, x in enumerate(sub_lines) if x]
        sub_rep = [(i + 1, x) for i, x in enumerate(subindex)]
        sub_rep.reverse()
        for i, x in sub_rep:
            buffer[x:x] = [str(i)]

    @pynvim.command('PlayerReloadSubs')
    @requires_player
    def player_reload_subs(self):
        self.player.send_command('sub-reload')

    @pynvim.command('FindCurrentSub')
    @requires_player
    def find_current_sub(self):

        buffer = self.nvim.current.buffer
        window = self.nvim.current.window

        ts_list = [(line_num, TimestampPair(ts_pair))
                   for line_num, ts_pair in enumerate(buffer)
                   if re.match(FULL_TS_FORMAT, ts_pair)]

        current_time = self.player.get_time()

        cursor_pos_gen = ((line_num + 2, 0)
                          for line_num, ts_pair in ts_list
                          if current_time in ts_pair)
        try:
            cursor_pos = next(cursor_pos_gen)
        except StopIteration:  # no current sub
            self.write_msg("No subtitle found for current timepoint.")
        else:
            window.cursor = (cursor_pos)
            self.nvim.feedkeys('zz')

    @pynvim.command('ShiftSubs', nargs=1)
    def shift_subs(self, args):
        buffer = self.nvim.current.buffer
        shift_amount = float(args[0])

        ts_list = [(line_num, TimestampPair(ts_pair))
                   for line_num, ts_pair in enumerate(buffer)
                   if re.match(FULL_TS_FORMAT, ts_pair)]

        for line_num, ts in ts_list:
            buffer[line_num] = str(ts.shift(shift_amount))

    @pynvim.command('PlayerIncSpeed')
    @requires_player
    def player_inc_speed(self):
        try:
            multiplier = float(self.nvim.eval('g:vimtitles_speed_shift_multiplier'))
        except pynvim.api.nvim.NvimError:
            multiplier = 1.1
        finally:
            self.playspeed = self.playspeed * multiplier
            self.player.inc_speed(multiplier)
            self.write_msg(msg="Playback speed: " + format(self.playspeed, ".2f") + 'x')

    @pynvim.command('PlayerDecSpeed')
    @requires_player
    def player_dec_speed(self):
        try:
            multiplier = float(self.nvim.eval('g:vimtitles_speed_shift_multiplier'))
        except pynvim.api.nvim.NvimError:
            multiplier = 1.1
        finally:
            self.player.dec_speed(multiplier)
            self.playspeed = self.playspeed / multiplier
            self.write_msg(msg="Playback speed: " + format(self.playspeed, ".2f") + 'x')


class Player:
    """class for the mpv player, has controls and can get info about the player"""

    def __init__(self, filename):
        """requires an absolute path to the file?"""
        file = pathlib.Path(filename)
        if file.exists():
            self.file = file
            self.pause = True
        else:
            raise FileNotFoundError(f'{filename} could not be found')

    def send_command(self, command):
        """generic method for sending a command to the player"""
        if isinstance(command, dict):
            inputstr = json.dumps(command)
        elif isinstance(command, str):
            inputstr = command
        ps = subprocess.Popen(('echo', inputstr), stdout=subprocess.PIPE)
        output = subprocess.check_output(('socat', '-', '/tmp/mpvsocket'), stdin=ps.stdout)
        ps.wait()
        return(output)

    def test_open(self):
        test_dict = {"command": "client_name"}
        try:
            test_status = self.send_command(test_dict)
        except subprocess.CalledProcessError:
            return 0
        else:
            return 1

    def play(self, av="v", timestart="0:00", geometry="50%x50%"):
        """initiates the player the file, depending on the filetype"""
        # the order of mpvargs is really picky... very prone to breaking everything
        mpvargs = ('mpv',
                   str(self.file),
                   '--input-ipc-server=/tmp/mpvsocket')
        if av == "v":
            mpvargs += ('--geometry=' + geometry,)
        mpvargs += ('--really-quiet',  # prevents text being sent via stdout
                    '--sub-auto=fuzzy',  # subs loaded if they fuzzy match the av filename
                    '--start=' + timestart,
                    '--pause',  # don't quit mpv after file has finished
                    '--keep-open=always')  # starts the video paused
        subprocess.Popen(mpvargs, close_fds=True, shell=False, stdout=subprocess.DEVNULL)

    def cycle_pause(self):
        """cycles between play and pause"""
        self.send_command('cycle pause')
        self.pause = not self.pause  # used to toggle the pause state

    def seek(self, seconds):
        """scans the player by a number of seconds"""
        sec_str = str(seconds)
        seek_dict = {"command": ["seek", sec_str, "relative"]}
        self.send_command(seek_dict)

    def get_time(self):
        """returns the current timestamp of the player in decimal seconds"""
        get_time = {"command": ["get_property", "playback-time"]}
        time_dict = json.loads(self.send_command(get_time))
        return(time_dict['data'])

    def seek_abs(self, seconds):
        """goes to a specific timepoint of the player, in decimal seconds"""
        sec_str = str(seconds)
        seek_dict_abs = {"command": ["seek", sec_str, "absolute"]}
        self.send_command(seek_dict_abs)

    def loop(self, a, b):
        """loops between two timestamps, where timestamps are in the 00:00:00.000 format"""
        loop_a = {"command": ["set_property", "ab-loop-a", a]}
        loop_b = {"command": ["set_property", "ab-loop-b", b]}
        self.send_command(loop_a)
        self.send_command(loop_b)

    def stop_loop(self):
        self.send_command('ab-loop')

    def inc_speed(self, multiplier=1.1):
        cmd = {"command": ["multiply", "speed", multiplier]}
        self.send_command(cmd)

    def dec_speed(self, multiplier=1.1):
        cmd = {"command": ["multiply", "speed", 1 / multiplier]}
        self.send_command(cmd)

    def quit(self):
        """exits the mpv player"""
        try:
            self.send_command('quit')
        except subprocess.CalledProcessError:
            print("Player was not running")
        finally:
            return False


class Timestamp:
    def __init__(self, seconds):
        if seconds < 0:
            raise Exception('Number of seconds in timestamp must be greater than zero')
        self.seconds = seconds

    @classmethod
    def from_string(cls, ts_string):
        """initialize Timestamp class using string representation"""
        if not re.match(SINGLE_TS_FORMAT, ts_string):
            raise Exception(f'{ts_string} is not a valid srt timestamp.')

        # easily split all components by same character
        ts_string = ts_string.replace(',', ':')
        h, m, s, ms = ts_string.split(':')
        if int(m) >= 60:
            raise Exception('Minutes cannot be greater than 59')
        if int(s) >= 60:
            raise Exception('Seconds cannot be greater than 59')
        s_final = (int(h) * 3600) + (int(m) * 60) + (int(s)) + (int(ms) / 1000)
        return cls(float(s_final))

    def __str__(self):
        if self.seconds == 0:
            return '00:00:00,000'
        else:
            ts = str(datetime.timedelta(seconds=self.seconds))
            ts = ts.replace('.', ',')
            if len(ts) in (6, 7):  # sometimes mili/microseconds are left out
                ts = ts + ',000000'
            ts = ts[:-3]  # remove microseconds
            ts = ts.rjust(12, '0')  # pads zero for hours
            assert re.match(SINGLE_TS_FORMAT, ts)
            return ts

    def shift(self, seconds):
        newseconds = self.seconds + seconds
        if newseconds <= 0:
            self.seconds = 0
        else:
            self.seconds = newseconds


class TimestampPair:

    def __init__(self, ts_pair: str):
        ts_pair.rstrip()
        if not re.match(FULL_TS_FORMAT + r'\w?$', ts_pair):
            raise Exception(f'{ts_pair} is not a valid srt timestamp')
        self.ts_pair = ts_pair
        ts1, _, ts2 = ts_pair.split(' ')
        try:
            self.ts1 = Timestamp.from_string(ts1)
            self.ts2 = Timestamp.from_string(ts2)
        except Exception:
            raise Exception(f'{ts_pair} is not a valid srt timestamp')
        if self.ts1.seconds > self.ts2.seconds:
            raise Exception('First timestamp must come before second timestamp')

    def shift(self, seconds):
        self.ts1.shift(seconds)
        self.ts2.shift(seconds)
        return self  # allows chaining with to_string

    def __str__(self):
        ts_pair = str(self.ts1) + ' --> ' + str(self.ts2)
        return ts_pair

    def __contains__(self, seconds):
        return (self.ts1.seconds <= seconds <= self.ts2.seconds)


# for debugging purposes only
if __name__ == '__main__':
    from pynvim import attach
    nvim = attach('socket', path='/tmp/nvim')
    vt = VimtitlesPlugin(nvim)

