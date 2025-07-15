# Docker Deployment Guide

This guide explains how to run the NVMe Stress Test GUI using Docker containers.

## Quick Start

1. **Install Docker** (if not already installed):
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   ```

2. **Clone and run**:
   ```bash
   git clone https://github.com/Gimel12/nvme_stress_test.git
   cd nvme_stress_test
   ./run-docker.sh
   ```

## Manual Docker Commands

### Build the Image
```bash
docker build -t nvme-stress-test .
```

### Run with Docker Compose (Recommended)
```bash
docker-compose up --build
```

### Run with Docker Command
```bash
# Allow X11 forwarding for GUI
xhost +local:docker

# Run the container
docker run -it --rm \
  --privileged \
  --name nvme-stress-gui \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  -v /dev:/dev:rw \
  -v /sys:/sys:ro \
  -v $(pwd)/results:/app/results \
  nvme-stress-test

# Clean up X11 permissions
xhost -local:docker
```

## Important Notes

### Security Considerations
- **Privileged Mode**: The container runs in privileged mode to access NVMe devices directly
- **Device Access**: The container has access to `/dev` and `/sys` for hardware interaction
- **X11 Forwarding**: GUI display requires X11 socket mounting

### Requirements
- **Linux Host**: Must be running on a Linux system with X11
- **NVMe Drives**: NVMe devices must be present and accessible on the host
- **Docker Version**: Docker 20.10+ recommended
- **Display**: X11 display server for GUI functionality

### Limitations
- **GUI Only on Linux**: X11 forwarding works best on Linux hosts
- **Hardware Access**: Requires privileged containers for direct NVMe access
- **Root Privileges**: Some NVMe operations require elevated privileges

## Troubleshooting

### GUI Not Displaying
```bash
# Check X11 forwarding
echo $DISPLAY
xhost +local:docker

# Test X11 with simple app
docker run --rm -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix:rw ubuntu:22.04 apt update && apt install -y x11-apps && xclock
```

### Permission Issues
```bash
# Ensure Docker daemon is running
sudo systemctl start docker

# Add user to docker group (logout/login required)
sudo usermod -aG docker $USER
```

### NVMe Access Issues
```bash
# Check if NVMe devices are visible
ls -la /dev/nvme*

# Verify container can see devices
docker run --rm --privileged -v /dev:/dev:rw nvme-stress-test ls -la /dev/nvme*
```

## File Structure

```
nvme_stress_test/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Compose configuration
├── run-docker.sh          # Easy runner script
├── .dockerignore          # Files to exclude from build
└── results/               # Test results (mounted volume)
```

## Benefits of Docker Deployment

✅ **Consistent Environment**: Same dependencies across all systems  
✅ **Easy Installation**: No manual dependency management  
✅ **Isolation**: Doesn't affect host system packages  
✅ **Portability**: Works on any Docker-enabled Linux system  
✅ **Clean Removal**: Easy to remove without traces  
✅ **Version Control**: Container images can be versioned and distributed  

## Advanced Usage

### Custom Build Arguments
```bash
# Build with specific Ubuntu version
docker build --build-arg UBUNTU_VERSION=20.04 -t nvme-stress-test .
```

### Persistent Results
```bash
# Create dedicated volume for results
docker volume create nvme-results
docker run -v nvme-results:/app/results nvme-stress-test
```

### Remote Display (SSH X11 Forwarding)
```bash
# On remote server
ssh -X user@remote-server
cd nvme_stress_test
./run-docker.sh
```
