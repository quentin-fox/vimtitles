import pynvim
import datetime
import subprocess
import json
import time
import re


@pynvim.plugin
class VimtitlesPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.command('PlayerOpen', nargs=1, complete="file")
    def player_open(self, args):
        filename = args[0]
        self.player = Player(filename)
        self.player.play(geometry="50%x50%")

    @pynvim.command('PlayerQuit')
    def player_quit(self):
        self.player.quit()

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

    @pynvim.command('PlayerSeekByTimestamp')
    def player_seek_by_ts(self):
        """will seek to the timestamp at the beginning of the most recent line"""
        buffer = self.nvim.current.buffer
        ts_line = self.get_line('^\\d\\d:\\d\\d:\\d\\d', 'bnc')
        first_ts = buffer[ts_line].split(' ')[0]  # will work even if no spaces in line
        time_float = convert_time(first_ts)
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
        blank_lines = [bool(re.match('^\s*$', x)) for x in buffer]
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

    def play(self, geometry):
        """initiates the player the file, depending on the filetype"""
        mpvargs = ('mpv',
                   self.file,
                   '--input-ipc-server=/tmp/mpvsocket',
                   '--really-quiet',  # prevents text being sent via stdout
                   '--geometry=' + geometry,  # geometry can be 50%x50%, for example
                   '--sub-auto=fuzzy')
        subprocess.Popen(mpvargs, close_fds=True, shell=False, stdout=open('stdout.txt', 'w'))
        time.sleep(1)
        self.cycle_pause()

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

    def quit(self):
        self.send_command('quit')


def convert_time(input):
    """method for converting .srt time strings to number of seconds"""
    if isinstance(input, float):
        time = str(datetime.timedelta(seconds=input))
        time = time.replace(".", ",")  # second to milisecond separator is a comma in .srt
        time = time[:-3]  # converts from microseconds to miliseconds
        time = time.rjust(12, '0')  # will add extra zero if hours are missing them
        return(time)
    elif isinstance(input, str):
        time = input
        time_struct = datetime.datetime.strptime(input, "%H:%M:%S,%f")
        td = time_struct - datetime.datetime(1900, 1, 1)
        time_float = td.total_seconds()
        return(time_float)



