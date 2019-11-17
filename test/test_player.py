import pytest
import sys
import socket

sys.path.append('rplugin/python3/')

from vimtitles import Player


def test_open():
    p = Player('oscr_auto_backup')
    assert p
    p.quit()


def test_play():
    p = Player('oscr_auto_backup')
    p.play()
    assert p.get_time() == 0

