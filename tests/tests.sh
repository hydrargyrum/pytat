#!/bin/sh -e

cd $(dirname $0)

ret=0

for f in *.tat.py
do
    f=${f%.tat.py}
    out=$(mktemp tat.out.XXXXXX)
    ./$f.tat.py > "$out"

    if ! diff -u expected_$f.py "$out"
    then
        echo "[-] difference on $f"
        ret=1
        rm "$out"
    else
        echo "[+] ok for $f"
        rm "$out"
    fi
done

exit $ret
