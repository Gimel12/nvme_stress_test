#!/bin/bash

# Script to run AI stress tests on all NVMe drives (except system drive)
# Created: $(date)

# Set test duration to 1 hour (3600 seconds)
DURATION=3600

# Create a directory for test results
RESULTS_DIR="nvme_stress_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "===== NVMe AI Workload Stress Test ====="
echo "Starting tests on all NVMe drives (except system drive)"
echo "Test duration: 1 hour per drive"
echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Get list of NVMe drives, excluding nvme0 (system drive)
NVME_DRIVES=$(lsblk -d -o NAME | grep nvme | grep -v nvme0)

# Function to run test on a single drive
run_test_on_drive() {
    local drive=$1
    local drive_name=$(echo $drive | tr -d '[:space:]')
    local log_file="$RESULTS_DIR/${drive_name}_stress_$(date +%Y%m%d_%H%M%S).log"
    
    echo "===== Testing $drive ====="
    echo "Start time: $(date)"
    echo "Log file: $log_file"
    
    # Check if drive is mounted
    if grep -q "/dev/$drive" /proc/mounts; then
        echo "WARNING: /dev/$drive is mounted. Attempting to unmount..."
        
        # Get all mounted partitions for this device
        mounted_parts=$(grep "/dev/$drive" /proc/mounts | awk '{print $1}')
        
        for part in $mounted_parts; do
            echo "Unmounting $part..."
            sudo umount "$part"
            if [ $? -ne 0 ]; then
                echo "Failed to unmount $part. Skipping this drive."
                return 1
            fi
        done
        echo "Successfully unmounted /dev/$drive"
    fi
    
    # Collect SMART data before test
    echo "--- SMART info for /dev/$drive before test ($(date)) ---" >> "$log_file"
    sudo smartctl -a "/dev/$drive" >> "$log_file" 2>&1
    echo "----------------------" >> "$log_file"
    
    # Start background temperature logging
    echo "Starting temperature monitoring..."
    (
        while true; do
            echo "[TEMP] $(date): $(sudo nvme smart-log /dev/$drive | grep -i temperature)" >> "$log_file"
            sleep 5
        done
    ) &
    temp_pid=$!
    
    # Run the AI workload stress test
    echo "Running AI workload stress test for 1 hour..."
    sudo fio --name=ai_data_load --filename=/dev/$drive --rw=randrw --rwmixread=70 --bs=128k --size=4G --numjobs=8 --iodepth=32 --direct=1 --time_based --runtime=$DURATION --group_reporting --name=ai_model_checkpoint --filename=/dev/$drive --stonewall --rw=write --bs=1m --size=2G --numjobs=4 --iodepth=16 --direct=1 --time_based --runtime=$DURATION --group_reporting | tee -a "$log_file"
    
    # Stop temperature monitoring
    kill $temp_pid 2>/dev/null
    wait $temp_pid 2>/dev/null
    
    # Collect SMART data after test
    echo "--- SMART info for /dev/$drive after test ($(date)) ---" >> "$log_file"
    sudo smartctl -a "/dev/$drive" >> "$log_file" 2>&1
    echo "----------------------" >> "$log_file"
    
    echo "Test completed for $drive"
    echo "End time: $(date)"
    echo ""
}

# Run tests on each drive
for drive in $NVME_DRIVES; do
    run_test_on_drive "$drive"
done

echo "All tests completed!"
echo "Results are saved in: $RESULTS_DIR"

# Create a summary report
SUMMARY_FILE="$RESULTS_DIR/summary_report.txt"
echo "===== NVMe Stress Test Summary =====" > "$SUMMARY_FILE"
echo "Test date: $(date)" >> "$SUMMARY_FILE"
echo "Test duration: 1 hour per drive" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

for drive in $NVME_DRIVES; do
    drive_name=$(echo $drive | tr -d '[:space:]')
    log_file=$(ls -1 "$RESULTS_DIR/${drive_name}_stress_"*.log | head -1)
    
    echo "=== Drive: $drive ===" >> "$SUMMARY_FILE"
    
    # Extract max temperature
    max_temp=$(grep "\[TEMP\]" "$log_file" | grep -o "temperature.*" | sort -r | head -1)
    echo "Max temperature: $max_temp" >> "$SUMMARY_FILE"
    
    # Extract IOPS and throughput from fio results
    read_iops=$(grep "read: IOPS" "$log_file" | head -1 | grep -o "IOPS=.*," | cut -d'=' -f2 | cut -d',' -f1)
    write_iops=$(grep "write: IOPS" "$log_file" | head -1 | grep -o "IOPS=.*," | cut -d'=' -f2 | cut -d',' -f1)
    read_bw=$(grep "read: IOPS" "$log_file" | head -1 | grep -o "BW=.*(" | cut -d'=' -f2 | cut -d'(' -f1)
    write_bw=$(grep "write: IOPS" "$log_file" | head -1 | grep -o "BW=.*(" | cut -d'=' -f2 | cut -d'(' -f1)
    
    echo "Read IOPS: $read_iops" >> "$SUMMARY_FILE"
    echo "Write IOPS: $write_iops" >> "$SUMMARY_FILE"
    echo "Read Bandwidth: $read_bw" >> "$SUMMARY_FILE"
    echo "Write Bandwidth: $write_bw" >> "$SUMMARY_FILE"
    echo "" >> "$SUMMARY_FILE"
done

echo "Summary report created: $SUMMARY_FILE"
