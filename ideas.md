---
title: "Subtitles Vim Plugin Ideas"
author: "Quentin Fox"
mainfont: Times New Roman
mathfont: XITS Math
geometry:
- margin=1in
---

Features:

1. Can open up MPV in a small terminal window embedded in Vim.
2. Features only activated in a .srt or .sub filetype (so it's not a thing in .md files)
3. Play/pause/track bound to -/=/<Cr> in normal mode
4. Another binding which will track to the start of the transcription block using the timestamps at the top of the paragraph (in .srt format)
5. Syntax highlighting for the timestamps and for the arrows?
6. Maybe write the plugin in python so it's not in awful vimscript?
7. Another keybinding to insert the first and second timestamp
    i. If on a new line with nothing on it, pressing the button will insert the timestamp that the mpv player is currently onn
    ii. maybe using the ;ts binding will insert either the first or the second

example format:

```
00:00:00,000 --> 00:00:04,440
These are the captions that are being typed
During this time frame.

00:00:04,440 --> 00:00:010,000
Another set of captions for another time frame



```

Resources:
http://candidtim.github.io/vim/2017/08/11/write-vim-plugin-in-python.html
https://mpv.io/manual/stable/
(absolute seek, --start=<relative time>)
https://github.com/mpv-player/mpv/blob/master/DOCS/man/ipc.rst (how to control mpv with json)


