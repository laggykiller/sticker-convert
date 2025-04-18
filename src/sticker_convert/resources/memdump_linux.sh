#!/bin/bash
# Reference: https://github.com/hajzer/bash-memory-dump

OS_PAGESIZE=`getconf PAGESIZE`

PID=$1
PID_MAPS=/proc/$PID/maps
PID_MEM=/proc/$PID/mem

grep rw-p $PID_MAPS |
while IFS='' read -r line || [[ -n "$line" ]]; do
    range=`echo $line | awk '{print $1;}'`

    vma_start=$(( 0x`echo $range | cut -d- -f1` ))
    vma_end=$(( 0x`echo $range | cut -d- -f2` ))
    vma_size=$(( $vma_end - $vma_start ))

    dd_start=$(( $vma_start / $OS_PAGESIZE ))
    dd_bs=$OS_PAGESIZE
    dd_count=$(( $vma_size / $OS_PAGESIZE ))

    set +e
    dd if="$PID_MEM" bs="$dd_bs" skip="$dd_start" count="$dd_count"
    set -e
done