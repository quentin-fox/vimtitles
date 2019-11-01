let g:vimtitles_skip_amount=5
let g:vimtitles_speed_shift_multiplier=1.1

if !get(g:, 'vimtitles_no_default_key_mappings', 0)
	nnoremap <silent> - :execute "PlayerSeekBackward"<Cr>
	nnoremap <silent> = :execute "PlayerSeekForward"<Cr>
	nnoremap <silent> <Cr> :execute "PlayerCyclePause"<Cr>
	nnoremap <silent> <Bar> :execute "SetTimestamp"<Cr>
	nnoremap <silent> _ :execute "PlayerSeekByStartTimestamp"<Cr>
	nnoremap <silent> + :execute "PlayerSeekByStopTimestamp"<Cr>
	nnoremap <silent> ;rs :execute "w <Bar> PlayerReloadSubs"<Cr>
	nnoremap <silent> \\ :execute "FindCurrentSub"<Cr>zz
	nnoremap <silent> [ :execute "PlayerDecSpeed"<Cr>
	nnoremap <silent> ] :execute "PlayerIncSpeed"<Cr>
endif

