#!/bin/bash
# Quick maximum performance test for all NVMe drives
# Tests sequential read and write speeds

echo "Starting quick peak performance tests..."
echo "This will take approximately 2-3 minutes for all drives"
echo ""

DRIVES=(nvme0n1 nvme1n1 nvme2n1 nvme3n1 nvme4n1 nvme5n1 nvme7n1)

for DRIVE in "${DRIVES[@]}"; do
    if [ ! -b "/dev/$DRIVE" ]; then
        echo "⚠️  Drive /dev/$DRIVE not found, skipping..."
        continue
    fi
    
    OUTPUT_FILE="${DRIVE}_peak.json"
    echo "📊 Testing $DRIVE..."
    
    # Quick sequential read test (20 seconds)
    echo "  - Sequential Read..."
    sudo fio --name=seq_read_$DRIVE \
        --filename=/dev/$DRIVE \
        --rw=read \
        --bs=1M \
        --iodepth=64 \
        --ioengine=libaio \
        --direct=1 \
        --numjobs=4 \
        --runtime=20 \
        --time_based \
        --group_reporting \
        --output-format=json \
        --output="${DRIVE}_read.json" 2>/dev/null
    
    # Quick sequential write test (20 seconds)
    echo "  - Sequential Write..."
    sudo fio --name=seq_write_$DRIVE \
        --filename=/dev/$DRIVE \
        --rw=write \
        --bs=1M \
        --iodepth=64 \
        --ioengine=libaio \
        --direct=1 \
        --numjobs=4 \
        --runtime=20 \
        --time_based \
        --group_reporting \
        --output-format=json \
        --output="${DRIVE}_write.json" 2>/dev/null
    
    echo "  ✅ $DRIVE complete"
    echo ""
done

echo "All peak performance tests completed!"
echo "Run 'python3 update_report_with_peak_perf.py' to update the HTML report"
