# NVMe AI Workload Stress Test

This script provides a comprehensive stress testing tool for NVMe drives, specifically optimized for evaluating performance under AI workloads. It helps you determine if your NVMe drive can handle the thermal and performance demands of AI training and inference tasks.

## Quick Start

### Installation

1. **Clone or download this repository**
2. **Run the installation script**:
   ```bash
   ./install.sh
   ```
   This will:
   - Install required dependencies (`fio`, `nvme-cli`, `python3-tkinter`)
   - Set proper permissions for all shell scripts
   - Verify the installation

3. **Start using the tool**:
   ```bash
   # GUI version (recommended)
   python3 nvme_stress_gui.py
   
   # Command line version
   sudo ./nvme.sh
   ```

### Manual Installation

If you prefer to install manually:
```bash
# Install dependencies
sudo apt update
sudo apt install fio nvme-cli python3-tkinter

# Make scripts executable
chmod +x *.sh
```

### Docker Installation (Recommended for Easy Deployment)

For the easiest deployment with all dependencies included:

1. **Install Docker** (if not already installed):
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Clone the repository**:
   ```bash
   git clone https://github.com/Gimel12/nvme_stress_test.git
   cd nvme_stress_test
   ```

3. **Run the containerized GUI**:
   ```bash
   ./run-docker.sh
   ```

**Docker Benefits:**
- ✅ All dependencies pre-installed
- ✅ No permission issues
- ✅ Consistent environment across systems
- ✅ Easy cleanup and removal
- ✅ Isolated from host system

**Requirements for Docker version:**
- Linux system with X11 (for GUI display)
- Docker with privileged container support (for direct NVMe access)
- NVMe drives must be accessible from the host system

## Features

- **Drive Selection**: Automatically detects and lists all NVMe drives in your system
- **Safe Testing**: Checks if the selected drive is mounted and safely unmounts it before testing
- **Temperature Monitoring**: Logs drive temperature every 5 seconds during the test
- **SMART Data Collection**: Captures drive health metrics before and after testing
- **AI Workload Simulation**: Uses realistic I/O patterns that mimic AI training and inference
- **🤖 AI Analysis**: Intelligent analysis of test results using OpenAI to identify issues, temperature problems, and provide recommendations

## Usage

```bash
sudo ./nvme.sh
```

The script requires root privileges to access the drives directly.

## AI Analysis Setup

To enable the AI analysis feature, you need to set up your OpenAI API key:

1. **Get an OpenAI API key** from [OpenAI Platform](https://platform.openai.com/api-keys)

2. **Create a `.env` file** in the project directory:
   ```bash
   cp .env.example .env
   ```

3. **Add your API key** to the `.env` file:
   ```
   OPENAI_API_KEY=your_api_key_here
   ```

4. **Install Python dependencies** (if not already done):
   ```bash
   pip3 install -r requirements.txt
   ```

Once configured, the 🤖 **AI Analyze** button will be enabled in the GUI after running a test. The AI will analyze your test logs and provide:

- Overall test result (PASS/FAIL)
- Temperature analysis and thermal concerns
- Performance issue identification
- Error analysis and patterns
- Drive health assessment
- Specific recommendations for any issues found

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

## Deploy to Bizon users 
```bash
curl -O https://raw.githubusercontent.com/Gimel12/nvme_stress_test/main/nvme.sh && sudo chmod +x nvme.sh && sudo ./nvme.sh
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


# Custom GUI nvme benchmark for Linux.

What need to have: 

- NVME selection
- Run the test until hard drive is full
- Temperature monitor
- Critical temperature treshold notification
- Speed
