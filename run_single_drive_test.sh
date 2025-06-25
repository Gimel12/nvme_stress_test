#!/bin/bash

# Script to run an AI stress test on a single specified NVMe drive.
# This script is designed to be called from the NVMe Stress Test GUI.

# Arguments:
# $1: Device path (e.g., /dev/nvme0n1)
# $2: Test duration in seconds
# $3: Full path to the log file
# $4: Workload type ('ai' or 'standard')

if [ "$#" -ne 4 ]; then
    echo "Usage: $0 <device_path> <duration_seconds> <log_file_path> <workload_type>"
    exit 1
fi

DEVICE_PATH=$1
DURATION=$2
LOG_FILE=$3
WORKLOAD=$4

DRIVE_NAME=$(basename "$DEVICE_PATH")

echo "Starting test on $DEVICE_PATH (Log: $LOG_FILE) with workload '$WORKLOAD'" >> "$LOG_FILE"

# This block runs in a subshell to ensure cleanup happens.
(
    # Collect SMART data before test
    echo "--- SMART info for $DEVICE_PATH before test ($(date)) ---" >> "$LOG_FILE"
    sudo smartctl -a "$DEVICE_PATH" >> "$LOG_FILE" 2>&1
    echo "----------------------" >> "$LOG_FILE"
    
    # Start background temperature logging
    (
        while true; do
            echo "[TEMP] $(date): $(sudo smartctl -a $DEVICE_PATH | grep -i temperature)" >> "$LOG_FILE"
            sleep 5
        done
    ) &
    temp_pid=$!
    # Ensure the temp logger is killed on exit
    trap "kill $temp_pid 2>/dev/null || true" EXIT

    # Define the FIO command based on workload type
    if [ "$WORKLOAD" == "ai" ]; then
        fio_cmd="sudo fio --name=ai_data_load_${DRIVE_NAME} --filename=${DEVICE_PATH} --rw=randrw --rwmixread=70 --bs=128k --size=4G --numjobs=8 --iodepth=32 --direct=1 --time_based --runtime=${DURATION} --group_reporting --name=ai_model_checkpoint_${DRIVE_NAME} --filename=${DEVICE_PATH} --stonewall --rw=write --bs=1m --size=2G --numjobs=4 --iodepth=16 --direct=1 --time_based --runtime=${DURATION} --group_reporting"
    else
        fio_cmd="sudo fio --name=nvme_stress_test_${DRIVE_NAME} --filename=${DEVICE_PATH} --rw=randrw --bs=4k --size=1G --numjobs=4 --time_based --runtime=${DURATION} --group_reporting"
    fi

    # Run the FIO test and redirect output
    $fio_cmd >> "$LOG_FILE" 2>&1
    fio_exit_code=$?

    # Collect SMART data after test
    echo "--- SMART info for $DEVICE_PATH after test ($(date)) ---" >> "$LOG_FILE"
    sudo smartctl -a "$DEVICE_PATH" >> "$LOG_FILE" 2>&1
    echo "----------------------" >> "$LOG_FILE"
    
    echo "Test completed for $DEVICE_PATH with exit code $fio_exit_code" >> "$LOG_FILE"
    exit $fio_exit_code
)

exit $?
