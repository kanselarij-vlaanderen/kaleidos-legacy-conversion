#!/bin/ash

echo "Starting new dump, moving old files to /old"

cd /output/ttl/
for f in *.ttl
do
    [ -f "$f" ] || continue
    mv "$f" "old/"
done

TIMESTAMP=`date +"%Y-%m-%d_%H-%m-%S_"`

cd  /app
python $1

cd /output/ttl/
for f in *.ttl
do
    [ -f "$f" ] || continue
    mv "$f" "$TIMESTAMP$f"
done

