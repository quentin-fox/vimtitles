let g:vimtitles_skip_amount=5

if !get(g:, 'vimtitles_no_default_key_mappings', 0)
	nnoremap <silent> - :execute "PlayerSeekBackward"<Cr>
	nnoremap <silent> = :execute "PlayerSeekForward"<Cr>
	nnoremap <silent> <Cr> :execute "PlayerCyclePause"<Cr>
	nnoremap <silent> <Bar> :execute "SetTimestamp"<Cr>
	nnoremap <silent> _ :execute "PlayerSeekByTimestamp"<Cr>
	nnoremap <silent> ;rs :execute "w <Bar> PlayerReloadSubs"<Cr>
	nnoremap <silent> + :execute "FindCurrentSub"<Cr>
endif

