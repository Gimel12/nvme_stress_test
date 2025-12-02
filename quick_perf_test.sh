#!/bin/bash
# Quick peak performance test for NVMe drives

DRIVE=$1
OUTPUT_FILE="${DRIVE}_peak_perf.txt"

echo "Testing peak performance for $DRIVE..." > "$OUTPUT_FILE"
echo "===========================================" >> "$OUTPUT_FILE"

# Sequential Read Test (maximum performance)
echo "" >> "$OUTPUT_FILE"
echo "Sequential Read Test (128KB blocks, 32 queue depth):" >> "$OUTPUT_FILE"
sudo fio --name=seq_read \
    --filename=/dev/$DRIVE \
    --rw=read \
    --bs=128k \
    --iodepth=32 \
    --ioengine=libaio \
    --direct=1 \
    --numjobs=4 \
    --runtime=30 \
    --time_based \
    --group_reporting 2>&1 | tee -a "$OUTPUT_FILE"

# Sequential Write Test (maximum performance)
echo "" >> "$OUTPUT_FILE"
echo "Sequential Write Test (128KB blocks, 32 queue depth):" >> "$OUTPUT_FILE"
sudo fio --name=seq_write \
    --filename=/dev/$DRIVE \
    --rw=write \
    --bs=128k \
    --iodepth=32 \
    --ioengine=libaio \
    --direct=1 \
    --numjobs=4 \
    --runtime=30 \
    --time_based \
    --group_reporting 2>&1 | tee -a "$OUTPUT_FILE"

echo "" >> "$OUTPUT_FILE"
echo "Test completed for $DRIVE" >> "$OUTPUT_FILE"
