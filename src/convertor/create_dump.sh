#!/bin/ash

echo "Starting new dump, moving old files to /old"

cd /output
for f in ttl/*.ttl
do
    [ -f "$f" ] || continue
    mv "$f" "ttl/old"
done

for f in log/*.log
do
    [ -f "$f" ] || continue
    mv "$f" "log/old"
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

cd /output/log/
for f in *.log
do
    [ -f "$f" ] || continue
    mv "$f" "$TIMESTAMP$f"
done
