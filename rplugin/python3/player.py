import subprocess
import json
import datetime


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
                   '--geometry=' + geometry)  # geometry can be 50%x50%, for example
        subprocess.Popen(mpvargs, close_fds=True, shell=False, stdout=open('stdout.txt', 'w'))

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
        time.replace(".", ",")  # second to milisecond separator is a comma in .srt
        time = time[:-3]
        return(time)
    elif isinstance(input, str):
        time = input
        time_struct = datetime.datetime.strptime(input, "%H:%M:%S,%f")
        td = time_struct - datetime.datetime(1900, 1, 1)
        time_float = td.total_seconds()
        return(time_float)


