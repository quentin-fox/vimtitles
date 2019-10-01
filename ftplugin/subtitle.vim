let g:vimtitles_skip_amount=3
let g:vimtitles_speed_shift_multiplier=1.1
let g:vimtitles_no_subnumbers_on_save=1

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

function! RefreshSubNumbers()
	execute 'RemoveSubNumbers'
	execute 'AddSubNumbers'
endfunction

if !get(g:, 'vimtitles_no_subnumbers_on_save', 0)
	autocmd BufWritePre *.srt :call RefreshSubNumbers()
endif
