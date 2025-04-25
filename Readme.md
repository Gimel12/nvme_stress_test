# Make sure to install the tools and they work

```
# Install the cli tool to control nvmes on terminal 
sudo apt install nvme-cli


# List all your nvmes 
sudo nvme list

# Running a test 

sudo nvme device-self-test /dev/nvme1n1 -s 2 

sudo nvme device-self-test /dev/nvme2n1 -s 2 

sudo nvme device-self-test /dev/nvme3n1 -s 2 

sudo nvme device-self-test /dev/nvme4n1 -s 2 

sudo nvme device-self-test /dev/nvme5n1 -s 2 


# Check info including temps about nvmes 
sudo watch nvme smart-log /dev/nvme1n1  

sudo watch nvme smart-log /dev/nvme2n1 

sudo watch nvme smart-log /dev/nvme3n1

sudo watch nvme smart-log /dev/nvme4n1

sudo watch nvme smart-log /dev/nvme5n1



/dev/nvme1n1                    
/dev/nvme2n1                      
/dev/nvme3n1                     
/dev/nvme4n1                    
/dev/nvme5n1
```bash 

# Custom GUI nvme benchmark for Linux.

What need to have: 

- NVME selection
- Run the test until hard drive is full
- Temperature monitor
- Critical temperature treshold notification
- Speed


# NVMe AI Workload Stress Test

This script provides a comprehensive stress testing tool for NVMe drives, specifically optimized for evaluating performance under AI workloads. It helps you determine if your NVMe drive can handle the thermal and performance demands of AI training and inference tasks.

## Features

- **Drive Selection**: Automatically detects and lists all NVMe drives in your system
- **Safe Testing**: Checks if the selected drive is mounted and safely unmounts it before testing
- **Temperature Monitoring**: Logs drive temperature every 5 seconds during the test
- **SMART Data Collection**: Captures drive health metrics before and after testing
- **AI Workload Simulation**: Uses realistic I/O patterns that mimic AI training and inference

## Usage

```bash
sudo ./nvme.sh
```

The script requires root privileges to access the drives directly.

## Test Parameters

The stress test simulates AI workloads using the following parameters:

### Phase 1: AI Data Loading Simulation

This phase simulates the process of loading datasets and batches during AI training:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Read/Write Mix | 70% reads, 30% writes | Typical for data loading pipelines with caching |
| Block Size | 128KB | Optimized for large dataset files |
| Parallel Jobs | 8 | Simulates multiple worker processes loading data |
| Queue Depth | 32 | Stresses controller with many parallel requests |
| Test Size | 4GB | Large working set to stress cache and controller |
| I/O Mode | Direct | Bypasses OS cache for realistic drive stress |

### Phase 2: Model Checkpoint Simulation

This phase simulates the periodic saving of model weights during training:

| Parameter | Value | Description |
|-----------|-------|-------------|
| Operation | Write-only | Model checkpoints are primarily write operations |
| Block Size | 1MB | Larger blocks for efficient model file writing |
| Parallel Jobs | 4 | Simulates distributed training checkpoints |
| Queue Depth | 16 | High but realistic for checkpoint operations |
| Test Size | 2GB | Typical for model checkpoint files |
| I/O Mode | Direct | Bypasses OS cache for realistic drive stress |

## Why These Parameters Matter for AI Workloads

1. **High Queue Depths**: AI frameworks often use asynchronous I/O and prefetching, generating deep queues of I/O requests
2. **Mixed Read/Write Patterns**: Training involves both reading datasets and writing checkpoints
3. **Large Block Sizes**: AI datasets and models consist of large contiguous files
4. **High Parallelism**: Modern AI frameworks use multiple workers for data loading
5. **Direct I/O**: Bypasses the OS cache to stress the actual drive performance

## Interpreting Results

After running the test, check the log file for:

1. **Temperature Trends**: Look for thermal throttling or concerning temperature spikes
2. **IOPS and Throughput**: Higher values indicate better performance for AI workloads
3. **Latency**: Lower values, especially for p99 (99th percentile), are better for consistent performance

## Safety Notes

- The script will unmount the selected drive before testing
- Always ensure you don't have important unsaved data on the drive being tested
- For maximum stress, run the test for at least 30 minutes (1800 seconds)

