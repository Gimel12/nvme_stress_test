# 🌐 NVMe Stress Test - Web Application

A modern, web-based interface for NVMe stress testing that can be accessed from any computer on your local network.

## ✨ Features

- **🖥️ Web-Based Interface** - Access from any device with a web browser
- **📱 Responsive Design** - Works on desktop, tablet, and mobile
- **🔄 Real-Time Updates** - Live test output via WebSocket
- **📊 Device Management** - Easy device selection and health monitoring
- **⚙️ Configurable Tests** - AI workload or standard stress tests
- **📈 Progress Tracking** - Real-time progress bar and time remaining
- **📄 Log Management** - View, download, and manage test logs
- **📋 Report Generation** - Generate HTML reports with one click
- **🎨 Modern UI** - Beautiful gradient design with smooth animations

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd /home/bizon/nvme_stress_test
./start_web_app.sh
```

The script will automatically:
- Create a Python virtual environment
- Install all required dependencies
- Start the web server

### 2. Access the Web Interface

Once the server starts, you'll see:
```
🚀 NVMe Stress Test Web Application
================================================================
✅ Server starting...

📡 Access the application from:
   - This computer: http://localhost:5000
   - Local network:  http://192.168.1.67:5000

💡 Open the URL in any web browser on your network
================================================================
```

### 3. Open in Browser

On **any computer** on your local network:
1. Open a web browser (Chrome, Firefox, Edge, Safari)
2. Navigate to: `http://YOUR_SERVER_IP:5000`
3. Start testing!

## 📖 How to Use

### Running a Test

1. **Select Device**
   - Click on any NVMe device from the list
   - View health status and device information
   - Click "Health" button for detailed SMART data

2. **Configure Test**
   - Set test duration (presets: 5min, 10min, 30min, 1hr, 3hrs)
   - Choose workload type:
     - **AI Workload**: Simulates ML training workloads
     - **Standard**: Basic random read/write test
   - Enable/disable auto-unmount

3. **Start Test**
   - Click "Start Test" button
   - Monitor real-time output in the console
   - Track progress with the progress bar
   - View time remaining

4. **Stop Test** (Optional)
   - Click "Stop Test" to abort the test early
   - Confirm the action

### Viewing Results

1. **Console Output**
   - Real-time test output displayed in the console
   - Temperature readings highlighted in orange
   - Auto-scrolls to latest output

2. **Logs & Reports**
   - View all completed test logs
   - Click "View" to see log content in modal
   - Click "Download" to save log file locally
   - Click "Generate HTML Report" to create visual report

### SMART Health Data

- Click "Health" button on any device
- View complete SMART data in a modal
- Check drive health, temperature, and statistics

## 🔧 Configuration

### Port Configuration

To change the default port (5000), edit `web_app.py`:

```python
if __name__ == '__main__':
    port = 5000  # Change this to your desired port
    socketio.run(app, host='0.0.0.0', port=port, debug=False)
```

### Firewall Configuration

If you can't access from other computers, allow the port through firewall:

```bash
# Ubuntu/Debian
sudo ufw allow 5000/tcp

# CentOS/RHEL
sudo firewall-cmd --permanent --add-port=5000/tcp
sudo firewall-cmd --reload
```

## 📋 Requirements

- **Python 3.7+**
- **Flask** - Web framework
- **Flask-SocketIO** - Real-time communication
- **Sudo access** - For device operations
- **smartmontools** - For SMART data (optional)

All Python dependencies are automatically installed by `start_web_app.sh`

## 🛠️ Manual Installation

If you prefer manual installation:

```bash
# Create virtual environment
python3 -m venv venv_web

# Activate virtual environment
source venv_web/bin/activate

# Install dependencies
pip install -r web_requirements.txt

# Start server
python3 web_app.py
```

## 🔐 Security Notes

⚠️ **Important Security Considerations:**

1. **Local Network Only** - The server binds to `0.0.0.0` which means it's accessible from any device on your network. Do NOT expose this to the internet.

2. **Sudo Access** - Tests require sudo privileges. Make sure only trusted users can access the web interface.

3. **No Authentication** - This version doesn't include user authentication. Anyone who can reach the server can run tests.

4. **Recommended Setup**:
   - Run on trusted local networks only
   - Use firewall rules to restrict access
   - Consider adding nginx reverse proxy with authentication for production use

## 🐛 Troubleshooting

### Server won't start

```bash
# Check if port is already in use
sudo lsof -i :5000

# Kill existing process if needed
sudo kill -9 <PID>

# Try starting again
./start_web_app.sh
```

### Can't access from other computers

1. **Check firewall**:
   ```bash
   sudo ufw status
   ```

2. **Verify server is listening**:
   ```bash
   netstat -tuln | grep 5000
   ```

3. **Test connection**:
   ```bash
   # From another computer
   curl http://SERVER_IP:5000
   ```

### Device unmount fails

- Ensure you have sudo permissions configured
- Check if device is in use by another process
- Try manually unmounting first

## 🎯 Features Comparison

| Feature | PyQt GUI | Web App |
|---------|----------|---------|
| Access from other computers | ❌ | ✅ |
| Cross-platform | Linux only | Any device with browser |
| Installation | Requires PyQt5 | Just Python + pip |
| Real-time updates | ✅ | ✅ |
| Device health check | ✅ | ✅ |
| Log management | Basic | Advanced |
| Report generation | ❌ | ✅ |
| Mobile support | ❌ | ✅ |

## 📱 Browser Compatibility

Tested and working on:
- ✅ Google Chrome/Chromium (Recommended)
- ✅ Mozilla Firefox
- ✅ Microsoft Edge
- ✅ Safari
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## 🚦 Status Indicators

- **Green indicator** - Connected to server
- **Grey indicator** - Disconnected from server
- **Progress bar** - Test progress and time remaining
- **Console colors** - Temperature lines in orange

## 💡 Tips

1. **Keep browser tab open** - Closing the tab won't stop the test, but you won't see real-time updates
2. **Multiple users** - Multiple people can view the interface, but only one test can run at a time
3. **Logs persist** - All logs are saved even if you close the browser
4. **Auto-refresh** - Device list and logs don't auto-refresh; click refresh button manually
5. **Background operation** - Tests continue running even if you close the browser

## 📞 Support

For issues or questions:
1. Check this README
2. Review the troubleshooting section
3. Check server console output for errors
4. Review browser console (F12) for JavaScript errors

## 🔄 Updating

To update the web app:

```bash
cd /home/bizon/nvme_stress_test
git pull origin main
./start_web_app.sh
```

---

**Happy Testing! 🎉**
