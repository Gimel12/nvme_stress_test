#!/bin/bash

# Script to run AI stress tests on all NVMe drives simultaneously
# Created: $(date)

# Set test duration to 1 hour (3600 seconds)
DURATION=3600

# Create a directory for test results
RESULTS_DIR="nvme_parallel_stress_results_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$RESULTS_DIR"

echo "===== NVMe AI Workload Parallel Stress Test ====="
echo "Starting tests on all NVMe drives simultaneously"
echo "Test duration: 1 hour"
echo "Results will be saved to: $RESULTS_DIR"
echo ""

# Get list of NVMe drives, excluding nvme0 (system drive)
NVME_DRIVES=$(lsblk -d -o NAME | grep nvme | grep -v nvme0)

# Check if any drives are mounted
for drive in $NVME_DRIVES; do
    if grep -q "/dev/$drive" /proc/mounts; then
        echo "WARNING: /dev/$drive is mounted. Attempting to unmount..."
        
        # Get all mounted partitions for this device
        mounted_parts=$(grep "/dev/$drive" /proc/mounts | awk '{print $1}')
        
        for part in $mounted_parts; do
            echo "Unmounting $part..."
            sudo umount "$part"
            if [ $? -ne 0 ]; then
                echo "Failed to unmount $part. Skipping this drive."
                # Remove this drive from the list
                NVME_DRIVES=$(echo "$NVME_DRIVES" | grep -v "$drive")
                continue 2
            fi
        done
        echo "Successfully unmounted /dev/$drive"
    fi
done

# Function to run test on a single drive in background
run_test_on_drive_bg() {
    local drive=$1
    local drive_name=$(echo $drive | tr -d '[:space:]')
    local log_file="$RESULTS_DIR/${drive_name}_stress_$(date +%Y%m%d_%H%M%S).log"
    
    echo "Starting test on $drive (Log: $log_file)"
    
    # Collect SMART data before test
    echo "--- SMART info for /dev/$drive before test ($(date)) ---" >> "$log_file"
    sudo smartctl -a "/dev/$drive" >> "$log_file" 2>&1
    echo "----------------------" >> "$log_file"
    
    # Start background temperature logging
    (
        while true; do
            echo "[TEMP] $(date): $(sudo nvme smart-log /dev/$drive | grep -i temperature)" >> "$log_file"
            sleep 5
        done
    ) &
    local temp_pid=$!
    
    # Run the AI workload stress test
    sudo fio --name=ai_data_load_${drive} --filename=/dev/$drive --rw=randrw --rwmixread=70 --bs=128k --size=4G --numjobs=8 --iodepth=32 --direct=1 --time_based --runtime=$DURATION --group_reporting --name=ai_model_checkpoint_${drive} --filename=/dev/$drive --stonewall --rw=write --bs=1m --size=2G --numjobs=4 --iodepth=16 --direct=1 --time_based --runtime=$DURATION --group_reporting >> "$log_file" 2>&1
    
    # Stop temperature monitoring
    kill $temp_pid 2>/dev/null
    wait $temp_pid 2>/dev/null
    
    # Collect SMART data after test
    echo "--- SMART info for /dev/$drive after test ($(date)) ---" >> "$log_file"
    sudo smartctl -a "/dev/$drive" >> "$log_file" 2>&1
    echo "----------------------" >> "$log_file"
    
    echo "Test completed for $drive"
}

# Array to store background process IDs
pids=()

# Start tests on all drives in parallel
echo "Starting parallel tests on drives: $NVME_DRIVES"
for drive in $NVME_DRIVES; do
    run_test_on_drive_bg "$drive" &
    pids+=($!)
    echo "Started test on $drive (PID: $!)"
done

echo "All tests started in parallel. Waiting for completion..."
echo "This will take approximately 1 hour."
echo ""

# Monitor system temperature during the test
echo "Monitoring overall system temperatures every 30 seconds..."
(
    while true; do
        echo "===== System Temperature at $(date) =====" >> "$RESULTS_DIR/system_temps.log"
        echo "CPU Temperatures:" >> "$RESULTS_DIR/system_temps.log"
        sensors | grep -i "core\|package" >> "$RESULTS_DIR/system_temps.log" 2>&1
        echo "" >> "$RESULTS_DIR/system_temps.log"
        echo "Drive Temperatures:" >> "$RESULTS_DIR/system_temps.log"
        for drive in $NVME_DRIVES; do
            echo "$drive: $(sudo nvme smart-log /dev/$drive | grep -i temperature)" >> "$RESULTS_DIR/system_temps.log"
        done
        echo "-------------------" >> "$RESULTS_DIR/system_temps.log"
        sleep 30
    done
) &
monitor_pid=$!

# Wait for all tests to complete
for pid in ${pids[@]}; do
    wait $pid
done

# Stop the temperature monitoring
kill $monitor_pid 2>/dev/null
wait $monitor_pid 2>/dev/null

echo "All tests completed!"
echo "Results are saved in: $RESULTS_DIR"

# Create a summary report
SUMMARY_FILE="$RESULTS_DIR/summary_report.txt"
echo "===== NVMe Parallel Stress Test Summary =====" > "$SUMMARY_FILE"
echo "Test date: $(date)" >> "$SUMMARY_FILE"
echo "Test duration: 1 hour" >> "$SUMMARY_FILE"
echo "Drives tested simultaneously: $NVME_DRIVES" >> "$SUMMARY_FILE"
echo "" >> "$SUMMARY_FILE"

for drive in $NVME_DRIVES; do
    drive_name=$(echo $drive | tr -d '[:space:]')
    log_file=$(ls -1 "$RESULTS_DIR/${drive_name}_stress_"*.log | head -1)
    
    if [ -f "$log_file" ]; then
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
    else
        echo "=== Drive: $drive ===" >> "$SUMMARY_FILE"
        echo "No log file found or test failed" >> "$SUMMARY_FILE"
        echo "" >> "$SUMMARY_FILE"
    fi
done

echo "Summary report created: $SUMMARY_FILE"
echo ""
echo "IMPORTANT: Check system_temps.log for overall system temperature during the test."
