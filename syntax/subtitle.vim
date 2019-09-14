if exists('b:current_syntax')
	finish
endif

" highlighting groups
syntax match subtitleArrow ' --> '
syntax match subtitleNumber '^\d\+\s\?$'
syntax match subtitleTimestamp '\d\d:\d\d:\d\d,\d\d\d'
syntax match subtitleComment '#.*'

" srt errors
" period instead of comma in timestamp
syntax match subtitleError '\d\d:\d\d:\d\d\.\d\d\d'

highlight link subtitleArrow Special
highlight link subtitleNumber Special
highlight link subtitleTimestamp Special
highlight link subtitleComment Special
highlight link subtitleError Special

let b:current_syntax = 'subtitle'
