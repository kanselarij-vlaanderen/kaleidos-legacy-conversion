#!/bin/sh

fixEncoding ()
{
    input_enc="windows-1252"
    output_enc="UTF-8"
    new_file=$(dirname "$1")/$(basename "$1" .csv)_enc_fixes.csv
    cp "$1" "$1".old
    cp "$1" "$1".new

    echo "Changing encoding from $input_enc to $output_enc"
    iconv -f "$input_enc" -t "$output_enc" "$1".old > "$1".new
    # git --no-pager diff --unified=0 --word-diff=color --word-diff-regex=. "$1".old "$1".new
    cp "$1".new "$1".old

    echo "Fixing Dutch plural ’s apostrophe ..."
    sed -i -E "s/([a-zA-Z0-9.-])_(s|S)(\W)/\1’\2\3/g" "$1".new # Dutch plural: KMO_s -> KMO's
    echo "Diff for apostrophe fixes:"
    echo "####################################################################"
    git --no-pager diff --unified=0 --word-diff=porcelain --word-diff-regex="\w+(_|’)(s|S)|[^[:space:]]" "$1".old "$1".new
    cp "$1".new "$1".old

    echo "Fixing opening of quotation ('open aanhaling') ..."
    sed -i -E "s/(\W)(_|¿)([a-zA-Z0-9.-])/\1‘\3/g" "$1".new # Start of quotation
    # git --no-pager diff --unified=0 --word-diff=color --word-diff-regex=. "$1".old "$1".new
    # cp "$1".new "$1".old

    echo "Fixing closing of quotation ('sluit aanhaling') ..."
    sed -i -E "s/([a-zA-Z0-9.-\)])(_|¿)(\W)/\1’\3/g" "$1".new # End of quotation
    # git --no-pager diff --unified=0 --word-diff=color --word-diff-regex=. "$1".old "$1".new
    # cp "$1".new "$1".old

    echo "Fixing long dash ('gedachtestreepje') ..."
    sed -i -E "s/(\s)¿(\s)/\1—\2/g" "$1".new
    echo "Diff for opening- & closing quotation and long dash fixes:"
    echo "####################################################################"
    git --no-pager diff --unified=0 --word-diff=color --word-diff-regex=. "$1".old "$1".new
    cp "$1".new "$1".old

    mv -f "$1".new "$new_file"
    rm "$1".old
}

echo "Fixing encoding issues ..."
find "/data" -iname 'metadata.csv'
find "/data" -iname "metadata.csv" | while read f
do    echo "Fixing encoding issues for file $f"
    fixEncoding "$f"
done
