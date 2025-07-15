# NVMe Stress Test GUI - Docker Container
FROM ubuntu:22.04

# Avoid interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Set display environment for GUI
ENV DISPLAY=:0

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-tk \
    fio \
    nvme-cli \
    sudo \
    x11-apps \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user for running the application
RUN useradd -m -s /bin/bash nvmeuser && \
    echo "nvmeuser ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

# Set working directory
WORKDIR /app

# Copy application files
COPY . /app/

# Make shell scripts executable
RUN chmod +x /app/*.sh

# Change ownership to nvmeuser
RUN chown -R nvmeuser:nvmeuser /app

# Switch to non-root user
USER nvmeuser

# Expose any ports if needed (not required for this app)
# EXPOSE 8080

# Default command to run the GUI application
CMD ["python3", "nvme_stress_gui.py"]
