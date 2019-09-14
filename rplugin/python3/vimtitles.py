import pynvim
import pathlib
from player import Player
from convert_time import convert_time

@pynvim.plugin
class VimtitlesPlugin(object):

    def __init__(self, nvim):
        self.nvim = nvim

    @pynvim.command('PrevTime')
    def prevtime(self):
        buffer = self.nvim.current.buffer
        ts = self.nvim.funcs.searchpos('00:00', 'bn')
        ln = ts[0] - 1
        self.nvim.funcs.echo(buffer[ln])



