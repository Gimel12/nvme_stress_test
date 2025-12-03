// NVMe Stress Test Web App - JavaScript

let socket;
let selectedDevice = null;
let currentTestId = null;
let statusUpdateInterval = null;

// Initialize Socket.IO connection
function initSocket() {
    socket = io();
    
    socket.on('connect', () => {
        console.log('Connected to server');
        showNotification('Connected to server', 'success');
    });
    
    socket.on('disconnect', () => {
        console.log('Disconnected from server');
        showNotification('Disconnected from server', 'warning');
    });
    
    socket.on('test_output', (data) => {
        if (data.test_id === currentTestId) {
            appendConsoleOutput(data.line);
        }
    });
    
    socket.on('test_finished', (data) => {
        if (data.test_id === currentTestId) {
            testFinished(data.success, data.message);
        }
    });
    
    socket.on('test_error', (data) => {
        if (data.test_id === currentTestId) {
            showNotification('Test Error: ' + data.message, 'danger');
            testFinished(false, data.message);
        }
    });
}

// Load devices on page load
document.addEventListener('DOMContentLoaded', () => {
    initSocket();
    refreshDevices();
    refreshLogs();
});

// Refresh device list
function refreshDevices() {
    fetch('/api/devices')
        .then(response => response.json())
        .then(devices => {
            const deviceList = document.getElementById('deviceList');
            
            if (devices.length === 0) {
                deviceList.innerHTML = `
                    <div class="alert alert-warning">
                        <i class="fas fa-exclamation-triangle"></i>
                        No NVMe devices found
                    </div>
                `;
                return;
            }
            
            deviceList.innerHTML = '';
            devices.forEach(device => {
                const healthBadge = getHealthBadge(device.health);
                const mountedBadge = device.mounted ? 
                    '<span class="badge bg-warning">Mounted</span>' : 
                    '<span class="badge bg-success">Not Mounted</span>';
                
                const deviceCard = document.createElement('div');
                deviceCard.className = 'device-card';
                deviceCard.innerHTML = `
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <h5 class="mb-1">
                                <i class="fas fa-hard-drive text-primary"></i>
                                ${device.name}
                            </h5>
                            <div class="text-muted small">
                                <div><i class="fas fa-database"></i> ${device.size}</div>
                                <div><i class="fas fa-tag"></i> ${device.model}</div>
                                <div><i class="fas fa-map-marker-alt"></i> ${device.path}</div>
                            </div>
                        </div>
                        <div class="text-end">
                            ${healthBadge}
                            <br>
                            ${mountedBadge}
                            <br>
                            <button class="btn btn-sm btn-outline-primary mt-2" onclick="showSmartData('${device.name}')">
                                <i class="fas fa-heartbeat"></i> Health
                            </button>
                        </div>
                    </div>
                `;
                
                deviceCard.onclick = (e) => {
                    // Don't select if clicking the health button
                    if (e.target.closest('button')) return;
                    
                    selectDevice(device, deviceCard);
                };
                
                deviceList.appendChild(deviceCard);
            });
        })
        .catch(error => {
            console.error('Error fetching devices:', error);
            showNotification('Error loading devices', 'danger');
        });
}

// Get health badge HTML
function getHealthBadge(health) {
    const colorMap = {
        'success': 'bg-success',
        'warning': 'bg-warning',
        'danger': 'bg-danger'
    };
    const badgeClass = colorMap[health.color] || 'bg-secondary';
    return `<span class="badge ${badgeClass}">${health.status}</span>`;
}

// Select a device
function selectDevice(device, cardElement) {
    // Remove previous selection
    document.querySelectorAll('.device-card').forEach(card => {
        card.classList.remove('selected');
    });
    
    // Select this device
    cardElement.classList.add('selected');
    selectedDevice = device;
    
    // Show configuration card
    document.getElementById('testConfigCard').style.display = 'block';
}

// Show SMART data
function showSmartData(deviceName) {
    fetch(`/api/device/${deviceName}/health`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('smartData').textContent = data.smart_data;
            const modal = new bootstrap.Modal(document.getElementById('smartModal'));
            modal.show();
        })
        .catch(error => {
            showNotification('Error fetching SMART data', 'danger');
        });
}

// Set duration preset
function setDuration(seconds) {
    document.getElementById('durationInput').value = seconds;
}

// Start test
function startTest() {
    if (!selectedDevice) {
        showNotification('Please select a device first', 'warning');
        return;
    }
    
    const duration = parseInt(document.getElementById('durationInput').value);
    const workloadType = document.querySelector('input[name="workloadType"]:checked').value;
    const autoUnmount = document.getElementById('autoUnmount').checked;
    const logName = document.getElementById('logNameInput').value.trim();
    
    if (duration < 10 || duration > 86400) {
        showNotification('Duration must be between 10 and 86400 seconds', 'warning');
        return;
    }
    
    // Disable start button
    document.getElementById('startTestBtn').disabled = true;
    document.getElementById('startTestBtn').innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
    
    // Clear console
    clearConsole();
    
    // Start test
    fetch('/api/test/start', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            device_path: selectedDevice.path,
            duration: duration,
            workload_type: workloadType,
            auto_unmount: autoUnmount,
            log_name: logName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showNotification('Error: ' + data.error, 'danger');
            document.getElementById('startTestBtn').disabled = false;
            document.getElementById('startTestBtn').innerHTML = '<i class="fas fa-play"></i> Start Test';
            return;
        }
        
        currentTestId = data.test_id;
        showTestRunning();
        startStatusUpdates();
        showNotification('Test started successfully', 'success');
    })
    .catch(error => {
        console.error('Error starting test:', error);
        showNotification('Error starting test', 'danger');
        document.getElementById('startTestBtn').disabled = false;
        document.getElementById('startTestBtn').innerHTML = '<i class="fas fa-play"></i> Start Test';
    });
}

// Stop test
function stopTest() {
    if (!currentTestId) return;
    
    if (!confirm('Are you sure you want to stop the test?')) {
        return;
    }
    
    fetch(`/api/test/${currentTestId}/stop`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        showNotification('Test stopped', 'warning');
    })
    .catch(error => {
        showNotification('Error stopping test', 'danger');
    });
}

// Show test running UI
function showTestRunning() {
    document.getElementById('testConfigCard').style.display = 'none';
    document.getElementById('testControls').style.display = 'block';
    document.getElementById('runningDevice').textContent = selectedDevice.name;
}

// Hide test running UI
function hideTestRunning() {
    document.getElementById('testControls').style.display = 'none';
    document.getElementById('testConfigCard').style.display = 'block';
    document.getElementById('startTestBtn').disabled = false;
    document.getElementById('startTestBtn').innerHTML = '<i class="fas fa-play"></i> Start Test';
}

// Start status updates
function startStatusUpdates() {
    if (statusUpdateInterval) {
        clearInterval(statusUpdateInterval);
    }
    
    statusUpdateInterval = setInterval(() => {
        if (!currentTestId) {
            clearInterval(statusUpdateInterval);
            return;
        }
        
        fetch(`/api/test/${currentTestId}/status`)
            .then(response => response.json())
            .then(data => {
                if (!data.running) {
                    clearInterval(statusUpdateInterval);
                    return;
                }
                
                updateProgress(data.progress, data.remaining);
            });
    }, 1000);
}

// Update progress bar
function updateProgress(progress, remaining) {
    const progressBar = document.getElementById('progressBar');
    const progressPercent = document.getElementById('progressPercent');
    const timeRemaining = document.getElementById('timeRemaining');
    
    progressBar.style.width = progress + '%';
    progressPercent.textContent = progress + '%';
    
    const minutes = Math.floor(remaining / 60);
    const seconds = Math.floor(remaining % 60);
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    
    let timeStr = '';
    if (hours > 0) {
        timeStr = `${hours}h ${mins}m ${seconds}s remaining`;
    } else if (minutes > 0) {
        timeStr = `${minutes}m ${seconds}s remaining`;
    } else {
        timeStr = `${seconds}s remaining`;
    }
    
    timeRemaining.innerHTML = `<i class="fas fa-clock"></i> ${timeStr}`;
}

// Test finished
function testFinished(success, message) {
    clearInterval(statusUpdateInterval);
    currentTestId = null;
    hideTestRunning();
    refreshLogs();
    
    if (success) {
        showNotification(message, 'success');
        appendConsoleOutput('\n✅ Test completed successfully!\n');
    } else {
        showNotification(message, 'warning');
        appendConsoleOutput('\n⚠️ Test stopped or failed\n');
    }
}

// Append to console output
function appendConsoleOutput(line) {
    const console = document.getElementById('consoleOutput');
    
    // If this is the first line, clear the placeholder
    if (console.querySelector('.text-muted')) {
        console.innerHTML = '';
    }
    
    const lineDiv = document.createElement('div');
    lineDiv.className = 'line';
    
    // Highlight temperature lines
    if (line.includes('[TEMP]')) {
        lineDiv.className += ' temp-line';
    }
    
    lineDiv.textContent = line;
    console.appendChild(lineDiv);
    
    // Auto-scroll to bottom
    console.scrollTop = console.scrollHeight;
}

// Clear console
function clearConsole() {
    document.getElementById('consoleOutput').innerHTML = '<div class="text-muted text-center p-4">Waiting for test to start...</div>';
}

// Refresh logs list
function refreshLogs() {
    fetch('/api/logs')
        .then(response => response.json())
        .then(logs => {
            const logsList = document.getElementById('logsList');
            
            if (logs.length === 0) {
                logsList.innerHTML = '<div class="text-muted text-center p-3">No logs available</div>';
                return;
            }
            
            logsList.innerHTML = '';
            logs.forEach(log => {
                const logItem = document.createElement('div');
                logItem.className = 'log-item';
                logItem.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <i class="fas fa-file-alt text-primary"></i>
                            <strong>${log.name}</strong>
                            <br>
                            <small class="text-muted">
                                <i class="fas fa-clock"></i> ${log.modified} • 
                                <i class="fas fa-database"></i> ${formatBytes(log.size)}
                            </small>
                        </div>
                        <div>
                            <button class="btn btn-sm btn-outline-primary" onclick="viewLog('${log.name}')">
                                <i class="fas fa-eye"></i> View
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="downloadLog('${log.name}')">
                                <i class="fas fa-download"></i>
                            </button>
                        </div>
                    </div>
                `;
                logsList.appendChild(logItem);
            });
        })
        .catch(error => {
            console.error('Error fetching logs:', error);
        });
}

// View log content
function viewLog(logName) {
    fetch(`/api/log/${logName}`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('logModalTitle').textContent = logName;
            document.getElementById('logContent').textContent = data.content;
            document.getElementById('downloadLogBtn').onclick = () => downloadLog(logName);
            
            const modal = new bootstrap.Modal(document.getElementById('logModal'));
            modal.show();
        })
        .catch(error => {
            showNotification('Error loading log file', 'danger');
        });
}

// Download log
function downloadLog(logName) {
    window.location.href = `/api/log/${logName}/download`;
}

// Generate HTML report
function generateReport() {
    const btn = event.target.closest('button');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Generating...';
    
    fetch('/api/report/generate', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        
        if (data.success) {
            showNotification('Report generated successfully!', 'success');
            // Open report in new window
            window.open('/report', '_blank');
        } else {
            showNotification('Error generating report: ' + (data.error || 'Unknown error'), 'danger');
        }
    })
    .catch(error => {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
        showNotification('Error generating report', 'danger');
    });
}

// Show notification (Toast)
function showNotification(message, type = 'info') {
    const bgColors = {
        'success': 'bg-success',
        'danger': 'bg-danger',
        'warning': 'bg-warning',
        'info': 'bg-info'
    };
    
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white ${bgColors[type]} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove after hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Create toast container if not exists
function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

// Format bytes to human readable
function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}
