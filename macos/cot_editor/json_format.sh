#! /bin/bash

# %%%{CotEditorXInput=Selection}%%%
# %%%{CotEditorXOutput=ReplaceSelection}%%%

# brew install jq
cat - | jq .
# INPUT=`cat -`
# echo $INPUT | jq .