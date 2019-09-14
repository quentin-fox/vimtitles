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
highlight link subtitleNumber Constant
highlight link subtitleTimestamp Statement
highlight link subtitleComment Comment
highlight link subtitleError Error

let b:current_syntax = 'subtitle'
