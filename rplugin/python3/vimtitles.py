import pynvim
import datetime
import subprocess
import json
import re


@pynvim.plugin
class VimtitlesPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim
        self.running = False

    @pynvim.command('TestFunc', nargs='+', complete='file')
    def test_func(self, args):
        out = json.dumps(args)
        filename, *newargs = args
        newargs_out = json.dumps(newargs)
        buffer = self.nvim.current.buffer
        buffer[1] = out
        buffer[2] = newargs_out

    @pynvim.command('PlayerOpen', nargs='+', complete='file')
    def player_open(self, args):
        if not self.running:
            filename = args[0]
            try:
                timestart = args[1]

            except IndexError:
                timestart = '0:00'
            try:
                geometry = args[2]
            except IndexError:
                geometry = '50%x50%'
            self.player = Player(filename)
            self.player.play(timestart=timestart, geometry=geometry)
            self.running = True

    @pynvim.command('PlayerQuit')
    def player_quit(self):
        if self.running:
            self.player.quit()
            self.running = False

    @pynvim.command('PlayerCyclePause')
    def player_pause(self):
        self.player.cycle_pause()

    @pynvim.command('SetTimestamp')
    def set_timestamp(self):
        time = self.player.get_time()
        buffer = self.nvim.current.buffer
        # c flag will also accept the current cursor
        blank_line = self.get_line('^\\s*$', 'bnc')
        timestamp_line = self.get_line('^\\d\\d:\\d\\d:\\d\\d,\\d\\d\\d$', 'bnc')
        arrow_line = self.get_line('-->', 'bnc')
        if blank_line > timestamp_line and blank_line > arrow_line:
            time_srt = convert_time(time)
            buffer[blank_line] = time_srt
        elif timestamp_line > blank_line:
            # abort if there's a second timestamp
            old_time = buffer[timestamp_line]
            old_time = old_time.rstrip()
            time_srt = convert_time(time)
            full_time = old_time + " --> " + time_srt
            buffer[timestamp_line] = full_time

    def get_line(self, pattern, flags):
        row, col = self.nvim.funcs.searchpos(pattern, flags)
        return(row - 1)

    @pynvim.command('PlayerSeekForward')
    def player_seek_forward(self):
        try:
            seconds = float(self.nvim.eval('g:vimtitles_skip_amount'))
        except NameError:
            seconds = 5  # default time to skip if not set in init.vim
        self.player.seek(seconds)

    @pynvim.command('PlayerSeekBackward')
    def player_seek_backward(self):
        try:
            seconds = float(self.nvim.eval('g:vimtitles_skip_amount')) * -1
        except NameError:
            seconds = -5  # default time to skip if not set in init.vim
        self.player.seek(seconds)

    @pynvim.command('PlayerSeekByStartTimestamp')
    def player_seek_by_start_ts(self):
        """will seek to the timestamp at the beginning of the most recent line"""
        buffer = self.nvim.current.buffer
        ts_line = self.get_line('^\\d\\d:\\d\\d:\\d\\d', 'bnc')
        start_ts = buffer[ts_line].split(' ')[0]  # will work even if no spaces in line
        time_float = convert_time(start_ts)
        self.player.seek_abs(time_float)

    @pynvim.command('PlayerSeekByStopTimestamp')
    def player_seek_by_stop_ts(self):
        """will seek to the timestamp at the beginning of the most recent line"""
        buffer = self.nvim.current.buffer
        tsformat = '^\\d\\d:\\d\\d:\\d\\d,\\d\\d\\d --> \\d\\d:\\d\\d:\\d\\d,\\d\\d\\d\\s?$'
        ts_line = self.get_line(tsformat, 'bnc')
        stop_ts = buffer[ts_line].split(' ')[2]  # will work even if no spaces in line
        time_float = convert_time(stop_ts)
        self.player.seek_abs(time_float)

    @pynvim.command('PlayerSeekAbs', nargs=1)
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
    def player_loop(self):
        buffer = self.nvim.current.buffer
        ts_line = self.get_line('-->', 'bnc')
        blank_line = self.get_line('^\\s*$', 'bn')
        if blank_line > ts_line:
            return
        elif ts_line > blank_line:
            ts_a, _, ts_b = buffer[ts_line].split(' ')
            self.ts_a = ts_a.replace(',', '.')
            self.ts_b = ts_b.replace(',', '.')
            self.player.loop(self.ts_a, self.ts_b)

    @pynvim.command('PlayerStopLoop')
    def player_stop_loop(self):
        if self.ts_a and self.ts_b:
            self.player.stop_loop()
            self.ts_a = self.ts_b = None
        else:
            return("No loop found")

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
    def player_reload_subs(self):
        self.player.send_command('sub-reload')

    @pynvim.command('FindCurrentSub')
    def find_current_sub(self):
        buffer = self.nvim.current.buffer
        tsformat = '^\\d\\d:\\d\\d:\\d\\d,\\d\\d\\d --> \\d\\d:\\d\\d:\\d\\d,\\d\\d\\d\\s?$'
        ts_list = [(i, self.parse_ts(x)) for i, x in enumerate(buffer) if bool(re.match(tsformat, x))]
        current_time = self.player.get_time()
        cursor_pos = [(i + 2, 0) for i, x in ts_list if x <= current_time][-1]
        window = self.nvim.current.window
        window.cursor = (cursor_pos)

    @pynvim.command('ShiftSubs', nargs=1)
    def shift_subs(self, args):
        shift = float(args[0])
        buffer = self.nvim.current.buffer
        tsformat = '^\\d\\d:\\d\\d:\\d\\d,\\d\\d\\d --> \\d\\d:\\d\\d:\\d\\d,\\d\\d\\d\\s?$'
        ts_list = [(i, x.split(' ')[0], x.split(' ')[2]) for i, x in enumerate(buffer) if bool(re.match(tsformat, x))]
        ts_shift = [(i, self.shift_ts(x, shift), self.shift_ts(y, shift)) for i, x, y in ts_list]
        for i, ts1, ts2 in ts_shift:
            buffer[i] = ts1 + ' --> ' + ts2

    @pynvim.command('PlayerIncSpeed')
    def player_inc_speed(self):
        try:
            multiplier = float(self.nvim.eval('g:vimtitles_speed_shift_multiplier'))
            self.player.inc_speed(multiplier)
        except pynvim.api.nvim.NvimError:
            self.player.inc_speed()

    @pynvim.command('PlayerDecSpeed')
    def player_dec_speed(self):
        try:
            multiplier = float(self.nvim.eval('g:vimtitles_speed_shift_multiplier'))
            self.player.dec_speed(multiplier)
        except pynvim.api.nvim.NvimError:
            self.player.dec_speed()

    def parse_ts(self, ts):
        ts1 = ts.split(' ')[0]
        ts_float = convert_time(ts1)
        return(ts_float)

    def shift_ts(self, ts, shift):
        ts_float = convert_time(ts)
        new_ts = ts_float + shift
        if new_ts <= 0:
            return('00:00:00,000')
        else:
            new_ts_str = convert_time(float(new_ts))
            return(new_ts_str)


class Player:
    """class for the mpv player, has controls and can get info about the player"""

    def __init__(self, file):
        """requires an absolute path to the file?"""
        self.file = file
        self.pause = True

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

    def play(self, geometry='50%x50%', timestart='0:00'):
        """initiates the player the file, depending on the filetype"""
        mpvargs = ('mpv',
                   self.file,
                   '--input-ipc-server=/tmp/mpvsocket',
                   '--really-quiet',  # prevents text being sent via stdout
                   '--geometry=' + geometry,  # geometry can be 50%x50%, for example
                   '--sub-auto=fuzzy',
                   '--start=' + timestart,
                   '--pause')  # starts the video paused
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
        timestamps = []
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
        self.send_command('quit')


def convert_time(input):
    """method for converting .srt time strings to number of seconds"""
    if isinstance(input, float) or isinstance(input, int):
        if input == 0:
            return('00:00:00,000')
        else:
            time = str(datetime.timedelta(seconds=input))
            time = time.replace(".", ",")  # second to milisecond separator is a comma in .srt
            if len(time) in (6, 7):
                time = time + ',000000'  # sometimes the microseconds are not added
            time = time[:-3]  # converts from microseconds to miliseconds
            time = time.rjust(12, '0')  # will add extra zero if hours are missing them
            return(time)
    elif isinstance(input, str):
        time = input
        if time == '00:00:00,000':
            return(float(0))
        else:
            time_struct = datetime.datetime.strptime(input, "%H:%M:%S,%f")
            td = time_struct - datetime.datetime(1900, 1, 1)
            time_float = float(td.total_seconds())
            return(time_float)

