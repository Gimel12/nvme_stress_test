#!/bin/bash

# List all NVMe devices with size and model
echo "Detecting NVMe devices..."
nvme_list=$(lsblk -d -o NAME,SIZE,MODEL | grep nvme)

if [ -z "$nvme_list" ]; then
    echo "No NVMe devices found. Exiting."
    exit 1
fi

echo "Available NVMe devices:"
echo "$nvme_list"

# Prepare device selection menu with name, size, and model
mapfile -t nvme_menu < <(lsblk -d -o NAME,SIZE,MODEL | grep nvme | awk '{print $1 " (" $2 ", "$3,$4,$5,$6,$7,$8,$9,$10 ")"}')
mapfile -t nvme_devices < <(lsblk -d -o NAME | grep nvme)

echo ""
echo "Select the NVMe device to stress test:"
select nvme_info in "${nvme_menu[@]}"; do
    idx=$((REPLY-1))
    nvme=${nvme_devices[$idx]}
    if [[ -n "$nvme" ]]; then
        echo "You selected: /dev/$nvme"
        break
    else
        echo "Invalid selection. Try again."
    fi
done

# Function to install a package if missing
auto_install() {
    pkg="$1"
    cmd_check="$2"
    if ! command -v "$cmd_check" &> /dev/null; then
        echo "$cmd_check is not installed. Attempting to install..."
        if command -v apt &> /dev/null; then
            sudo apt update && sudo apt install -y "$pkg"
        elif command -v dnf &> /dev/null; then
            sudo dnf install -y "$pkg"
        elif command -v yum &> /dev/null; then
            sudo yum install -y "$pkg"
        elif command -v zypper &> /dev/null; then
            sudo zypper install -y "$pkg"
        else
            echo "No supported package manager found. Please install $pkg manually."
            exit 1
        fi
    else
        echo "$cmd_check is already installed."
    fi
}

# Function to check if a drive is mounted
is_mounted() {
    local device=$1
    if grep -q "/dev/$device" /proc/mounts; then
        return 0  # True, is mounted
    else
        return 1  # False, not mounted
    fi
}

# Ensure fio and smartmontools are installed
# fio (command: fio), smartmontools (command: smartctl)
auto_install fio fio
auto_install smartmontools smartctl

# Check if the selected drive is mounted and unmount if necessary
if is_mounted "$nvme"; then
    echo "WARNING: /dev/$nvme is currently mounted."
    echo "The drive needs to be unmounted before running the stress test."
    echo "This will make the drive temporarily unavailable to the system."
    echo -n "Do you want to continue and unmount the drive? (y/n): "
    read -r unmount_confirm
    
    if [[ "$unmount_confirm" =~ ^[Yy]$ ]]; then
        echo "Attempting to unmount all partitions on /dev/$nvme..."
        
        # Get all mounted partitions for this device
        mounted_parts=$(grep "/dev/$nvme" /proc/mounts | awk '{print $1}')
        
        for part in $mounted_parts; do
            echo "Unmounting $part..."
            sudo umount "$part"
            if [ $? -ne 0 ]; then
                echo "Failed to unmount $part. Please ensure no processes are using it."
                echo "You can try: sudo lsof $part"
                echo "Aborting test."
                exit 1
            fi
        done
        echo "Successfully unmounted /dev/$nvme"
    else
        echo "Test aborted by user."
        exit 0
    fi
else
    echo "/dev/$nvme is not mounted. Proceeding with the test."
fi

# Ask user for test duration
echo ""
echo "Enter stress test duration in seconds (default: 60):"
read -r duration
if [[ -z "$duration" || ! "$duration" =~ ^[0-9]+$ ]]; then
    duration=60
fi

# Ask user for log file name
echo ""
echo "Enter a name for the log file (leave blank for automatic name):"
read -r logname
if [[ -z "$logname" ]]; then
    device_log="nvme_stress_${nvme}_$(date +%Y%m%d_%H%M%S).log"
else
    # Clean up logname to avoid spaces and special chars
    safe_logname=$(echo "$logname" | tr -cs '[:alnum:]_-' '_')
    device_log="${safe_logname}_nvme_${nvme}_$(date +%Y%m%d_%H%M%S).log"
fi
echo "Log file: $device_log"

# Function to log temperature and SMART info
dump_smart() {
    echo "--- SMART info for /dev/$nvme at $(date) ---" >> "$device_log"
    sudo smartctl -a "/dev/$nvme" >> "$device_log" 2>&1
    echo "----------------------" >> "$device_log"
}

dump_smart  # Before test

# Start background temperature logging
temp_log_pid=""
log_temp_bg() {
    while true; do
        echo "[TEMP] $(date): $(sudo smartctl -a /dev/$nvme | grep -i temperature)" >> "$device_log"
        sleep 5
    done
}
log_temp_bg &
temp_log_pid=$!

# Run fio stress test with logging
echo "Running AI workload simulation stress test on /dev/$nvme for $duration seconds..." | tee -a "$device_log"
if [ "$EUID" -ne 0 ]; then
    echo "fio requires root permissions to access block devices. Re-running with sudo..." | tee -a "$device_log"
    sudo fio --name=ai_data_load --filename=/dev/$nvme --rw=randrw --rwmixread=70 --bs=128k --size=4G --numjobs=8 --iodepth=32 --direct=1 --time_based --runtime=$duration --group_reporting --name=ai_model_checkpoint --filename=/dev/$nvme --stonewall --rw=write --bs=1m --size=2G --numjobs=4 --iodepth=16 --direct=1 --time_based --runtime=$duration --group_reporting | tee -a "$device_log"
else
    fio --name=ai_data_load --filename=/dev/$nvme --rw=randrw --rwmixread=70 --bs=128k --size=4G --numjobs=8 --iodepth=32 --direct=1 --time_based --runtime=$duration --group_reporting --name=ai_model_checkpoint --filename=/dev/$nvme --stonewall --rw=write --bs=1m --size=2G --numjobs=4 --iodepth=16 --direct=1 --time_based --runtime=$duration --group_reporting | tee -a "$device_log"
fi

# Stop background temp logging
kill $temp_log_pid 2>/dev/null
wait $temp_log_pid 2>/dev/null

dump_smart  # After test

echo "Stress test completed. Log saved to $device_log."
