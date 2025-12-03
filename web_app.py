#!/usr/bin/env python3
"""
NVMe Stress Test Web Application
A web-based interface for running NVMe stress tests accessible from any browser
"""

from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import subprocess
import os
import time
import json
import threading
from datetime import datetime
from pathlib import Path
import signal

app = Flask(__name__)
app.config['SECRET_KEY'] = 'nvme-stress-test-secret-2024'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
active_tests = {}
log_directory = Path(__file__).parent


def detect_nvme_devices():
    """Detect all NVMe devices on the system"""
    try:
        result = subprocess.run(
            ["lsblk", "-d", "-o", "NAME,SIZE,MODEL", "-J"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return []
        
        devices = []
        data = json.loads(result.stdout)
        
        for device in data.get('blockdevices', []):
            name = device.get('name', '')
            if 'nvme' in name:
                devices.append({
                    'name': name,
                    'size': device.get('size', 'Unknown'),
                    'model': device.get('model', 'Unknown'),
                    'path': f"/dev/{name}"
                })
        
        return devices
    except Exception as e:
        print(f"Error detecting NVMe devices: {e}")
        return []


def get_device_health(device_path):
    """Get SMART health status for a device"""
    try:
        result = subprocess.run(
            ["sudo", "smartctl", "-H", device_path],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        output = result.stdout.lower() + result.stderr.lower()
        if "overall-health self-assessment test result: passed" in output or "health status: ok" in output:
            return {"status": "Healthy", "color": "success"}
        elif "overall-health self-assessment test result: failed" in output:
            return {"status": "Failed", "color": "danger"}
        else:
            return {"status": "Unknown", "color": "warning"}
    except Exception as e:
        return {"status": "Error", "color": "danger"}


def get_device_smart_data(device_path):
    """Get full SMART data for a device"""
    try:
        result = subprocess.run(
            ["sudo", "smartctl", "-a", device_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        return result.stdout if result.stdout else result.stderr
    except Exception as e:
        return f"Error getting SMART data: {str(e)}"


def check_if_mounted(device_name):
    """Check if device is mounted"""
    try:
        with open('/proc/mounts', 'r') as f:
            mounts = f.read()
            return f"/dev/{device_name}" in mounts
    except Exception:
        return False


def run_stress_test(test_id, device_path, duration, workload_type, log_file):
    """Run the stress test in a background thread"""
    script_path = log_directory / "run_single_drive_test.sh"
    
    if not script_path.exists():
        socketio.emit('test_error', {
            'test_id': test_id,
            'message': f"Test script not found at {script_path}"
        })
        return
    
    command = f'"{script_path}" "{device_path}" {duration} "{log_file}" "{workload_type}"'
    
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        active_tests[test_id]['process'] = process
        active_tests[test_id]['start_time'] = time.time()
        
        # Stream output line by line
        for line in iter(process.stdout.readline, ""):
            if line:
                socketio.emit('test_output', {
                    'test_id': test_id,
                    'line': line.strip()
                })
        
        return_code = process.wait()
        
        # Test finished
        socketio.emit('test_finished', {
            'test_id': test_id,
            'success': return_code == 0,
            'message': f"Test completed {'successfully' if return_code == 0 else 'with errors'}"
        })
        
        if test_id in active_tests:
            del active_tests[test_id]
            
    except Exception as e:
        socketio.emit('test_error', {
            'test_id': test_id,
            'message': str(e)
        })
        if test_id in active_tests:
            del active_tests[test_id]


@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')


@app.route('/api/devices')
def api_devices():
    """Get list of NVMe devices"""
    devices = detect_nvme_devices()
    
    # Add health and mount status
    for device in devices:
        device['health'] = get_device_health(device['path'])
        device['mounted'] = check_if_mounted(device['name'])
    
    return jsonify(devices)


@app.route('/api/device/<device_name>/health')
def api_device_health(device_name):
    """Get detailed health information for a device"""
    device_path = f"/dev/{device_name}"
    smart_data = get_device_smart_data(device_path)
    return jsonify({'smart_data': smart_data})


@app.route('/api/test/start', methods=['POST'])
def api_test_start():
    """Start a stress test"""
    data = request.json
    
    device_path = data.get('device_path')
    duration = int(data.get('duration', 600))
    workload_type = data.get('workload_type', 'ai')
    auto_unmount = data.get('auto_unmount', True)
    log_name = data.get('log_name', '').strip()
    
    if not device_path:
        return jsonify({'error': 'Device path required'}), 400
    
    # Check if device is mounted
    device_name = device_path.split('/')[-1]
    if check_if_mounted(device_name):
        if auto_unmount:
            try:
                # Unmount all partitions
                result = subprocess.run(
                    f"grep '{device_path}' /proc/mounts | awk '{{print $1}}'",
                    shell=True, capture_output=True, text=True
                )
                mounted_parts = result.stdout.strip().split('\n')
                for part in mounted_parts:
                    if part:
                        subprocess.run(['sudo', 'umount', part], check=True)
            except subprocess.CalledProcessError:
                return jsonify({'error': 'Failed to unmount device'}), 500
        else:
            return jsonify({'error': 'Device is mounted. Enable auto-unmount or unmount manually.'}), 400
    
    # Generate log file name
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    if log_name:
        # Sanitize log name - keep only alphanumeric, underscores, and dashes
        log_name = ''.join(c if c.isalnum() or c in '_-' else '_' for c in log_name)
        log_file = log_directory / f"{log_name}.log"
    else:
        log_file = log_directory / f"nvme_stress_{device_name}_{timestamp}.log"
    
    # Create test ID
    test_id = f"test_{timestamp}_{device_name}"
    
    # Store test info
    active_tests[test_id] = {
        'device': device_path,
        'duration': duration,
        'log_file': str(log_file),
        'start_time': time.time(),
        'workload_type': workload_type
    }
    
    # Start test in background thread
    thread = threading.Thread(
        target=run_stress_test,
        args=(test_id, device_path, duration, workload_type, str(log_file))
    )
    thread.daemon = True
    thread.start()
    
    return jsonify({
        'test_id': test_id,
        'log_file': str(log_file)
    })


@app.route('/api/test/<test_id>/stop', methods=['POST'])
def api_test_stop(test_id):
    """Stop a running test"""
    if test_id not in active_tests:
        return jsonify({'error': 'Test not found'}), 404
    
    process = active_tests[test_id].get('process')
    if process:
        try:
            process.terminate()
            time.sleep(0.5)
            if process.poll() is None:
                process.kill()
            
            socketio.emit('test_finished', {
                'test_id': test_id,
                'success': False,
                'message': 'Test was stopped by user'
            })
            
            del active_tests[test_id]
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'Process not found'}), 404


@app.route('/api/test/<test_id>/status')
def api_test_status(test_id):
    """Get status of a running test"""
    if test_id not in active_tests:
        return jsonify({'running': False})
    
    test_info = active_tests[test_id]
    elapsed = time.time() - test_info['start_time']
    duration = test_info['duration']
    progress = min(int((elapsed / duration) * 100), 100)
    remaining = max(0, duration - elapsed)
    
    return jsonify({
        'running': True,
        'progress': progress,
        'elapsed': elapsed,
        'remaining': remaining,
        'device': test_info['device']
    })


@app.route('/api/logs')
def api_logs():
    """Get list of log files"""
    logs = []
    for log_file in log_directory.glob('*.log'):
        stat = log_file.stat()
        logs.append({
            'name': log_file.name,
            'size': stat.st_size,
            'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        })
    
    logs.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(logs)


@app.route('/api/log/<log_name>')
def api_log_content(log_name):
    """Get content of a log file"""
    log_file = log_directory / log_name
    
    if not log_file.exists() or not log_file.is_file():
        return jsonify({'error': 'Log file not found'}), 404
    
    try:
        with open(log_file, 'r') as f:
            content = f.read()
        return jsonify({'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/log/<log_name>/download')
def api_log_download(log_name):
    """Download a log file"""
    log_file = log_directory / log_name
    
    if not log_file.exists() or not log_file.is_file():
        return jsonify({'error': 'Log file not found'}), 404
    
    return send_file(log_file, as_attachment=True)


@app.route('/api/report/generate', methods=['POST'])
def api_report_generate():
    """Generate HTML report"""
    try:
        script_path = log_directory / "update_report_with_peak_perf.py"
        
        if not script_path.exists():
            script_path = log_directory / "generate_report.py"
        
        if not script_path.exists():
            return jsonify({'error': 'Report generator not found'}), 404
        
        result = subprocess.run(
            ['python3', str(script_path)],
            cwd=str(log_directory),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        report_file = log_directory / "nvme_stress_test_report.html"
        
        if report_file.exists():
            return jsonify({
                'success': True,
                'report_url': '/report',
                'message': 'Report generated successfully'
            })
        else:
            return jsonify({
                'error': 'Report file was not created',
                'output': result.stdout,
                'errors': result.stderr
            }), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/report')
def view_report():
    """View the generated HTML report"""
    report_file = log_directory / "nvme_stress_test_report.html"
    
    if not report_file.exists():
        return "Report not found. Please generate a report first.", 404
    
    return send_file(report_file)


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to NVMe Stress Test Server'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')


def get_local_ip():
    """Get the local IP address"""
    try:
        result = subprocess.run(
            ["hostname", "-I"],
            capture_output=True,
            text=True
        )
        return result.stdout.split()[0]
    except:
        return "localhost"


if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 NVMe Stress Test Web Application")
    print("="*60)
    
    local_ip = get_local_ip()
    port = 5000
    
    print(f"\n✅ Server starting...")
    print(f"\n📡 Access the application from:")
    print(f"   - This computer: http://localhost:{port}")
    print(f"   - Local network:  http://{local_ip}:{port}")
    print(f"\n💡 Open the URL in any web browser on your network")
    print(f"\n⚠️  Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
