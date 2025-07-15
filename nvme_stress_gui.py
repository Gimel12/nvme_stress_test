#!/usr/bin/env python3
import sys
import os
import subprocess
import time
import threading
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QPushButton, QComboBox, QSpinBox, QLineEdit, 
                            QTextEdit, QGroupBox, QFormLayout, QMessageBox, QTabWidget,
                            QProgressBar, QCheckBox, QRadioButton, QButtonGroup, QDialog)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QIcon, QTextCursor

# AI Analysis imports
try:
    import openai
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env file
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

class WorkerThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, command, log_file):
        super().__init__()
        self.command = command
        self.log_file = log_file
        self.process = None
        self.killed = False
        
    def run(self):
        try:
            self.process = subprocess.Popen(
                self.command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                shell=True,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line
            for line in iter(self.process.stdout.readline, ""):
                if line:
                    self.update_signal.emit(line.strip())
            
            return_code = self.process.wait()
            
            if self.killed:
                self.finished_signal.emit(False, "Test was cancelled")
            elif return_code == 0:
                self.finished_signal.emit(True, f"Test completed successfully. Log saved to {self.log_file}")
            else:
                self.finished_signal.emit(False, f"Test failed with return code {return_code}")
                
        except Exception as e:
            self.finished_signal.emit(False, f"Error: {str(e)}")
    
    def kill(self):
        if self.process:
            self.killed = True
            self.process.terminate()
            # Give it a moment to terminate gracefully
            time.sleep(0.5)
            # If still running, kill it
            if self.process.poll() is None:
                self.process.kill()


class NVMeStressTestGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("NVMe AI Workload Stress Test")
        self.setMinimumSize(800, 600)
        
        self.nvme_devices = []
        self.worker_thread = None
        self.log_file = None
        
        self.init_ui()
        self.detect_nvme_devices()
        
    def init_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Create tabs
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # Test tab
        test_tab = QWidget()
        test_layout = QVBoxLayout()
        test_tab.setLayout(test_layout)
        
        # Results tab
        results_tab = QWidget()
        results_layout = QVBoxLayout()
        results_tab.setLayout(results_layout)
        
        # Add tabs
        tab_widget.addTab(test_tab, "Run Test")
        tab_widget.addTab(results_tab, "Results & Logs")
        
        # ===== TEST TAB =====
        # Device selection
        device_group = QGroupBox("NVMe Device Selection")
        device_layout = QVBoxLayout()
        device_group.setLayout(device_layout)
        
        # Refresh button and device dropdown in one row
        refresh_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh Devices")
        self.refresh_button.clicked.connect(self.detect_nvme_devices)
        refresh_layout.addWidget(self.refresh_button)

        self.health_check_button = QPushButton("Check Device Health")
        self.health_check_button.clicked.connect(self.show_health_report)
        self.health_check_button.setEnabled(False)
        refresh_layout.addWidget(self.health_check_button)
        
        self.device_combo = QComboBox()
        self.device_combo.setMinimumWidth(400)
        refresh_layout.addWidget(self.device_combo)
        device_layout.addLayout(refresh_layout)
        
        # Device info
        self.device_info = QLabel("No device selected")
        self.device_info.setTextFormat(Qt.RichText)
        device_layout.addWidget(self.device_info)
        test_layout.addWidget(device_group)
        
        # Test configuration
        config_group = QGroupBox("Test Configuration")
        config_layout = QFormLayout()
        config_group.setLayout(config_layout)
        
        # Duration
        duration_layout = QHBoxLayout()
        self.duration_spin = QSpinBox()
        self.duration_spin.setRange(10, 86400)  # 10 seconds to 24 hours
        self.duration_spin.setValue(600)  # Default 10 minutes
        self.duration_spin.setSuffix(" seconds")
        self.duration_spin.setMinimumWidth(150)
        duration_layout.addWidget(self.duration_spin)
        
        # Add some preset buttons
        duration_presets = QHBoxLayout()
        preset_5min = QPushButton("5 min")
        preset_5min.clicked.connect(lambda: self.duration_spin.setValue(300))
        preset_10min = QPushButton("10 min")
        preset_10min.clicked.connect(lambda: self.duration_spin.setValue(600))
        preset_30min = QPushButton("30 min")
        preset_30min.clicked.connect(lambda: self.duration_spin.setValue(1800))
        preset_1hour = QPushButton("1 hour")
        preset_1hour.clicked.connect(lambda: self.duration_spin.setValue(3600))
        
        duration_presets.addWidget(preset_5min)
        duration_presets.addWidget(preset_10min)
        duration_presets.addWidget(preset_30min)
        duration_presets.addWidget(preset_1hour)
        duration_layout.addLayout(duration_presets)
        
        config_layout.addRow("Test Duration:", duration_layout)
        
        # Log file name
        self.log_name_edit = QLineEdit()
        self.log_name_edit.setPlaceholderText("Leave blank for automatic name")
        config_layout.addRow("Log File Name:", self.log_name_edit)
        
        # Workload selection
        workload_layout = QVBoxLayout()
        self.workload_ai = QRadioButton("AI Workload Simulation")
        self.workload_ai.setChecked(True)
        self.workload_standard = QRadioButton("Standard Stress Test")
        
        workload_layout.addWidget(self.workload_ai)
        workload_layout.addWidget(self.workload_standard)
        
        # AI workload description
        ai_description = QLabel("Simulates AI training with data loading (70% read, 30% write) and model checkpointing phases")
        ai_description.setWordWrap(True)
        workload_layout.addWidget(ai_description)
        
        # Standard workload description
        std_description = QLabel("Basic random read/write test with 4K blocks")
        std_description.setWordWrap(True)
        workload_layout.addWidget(std_description)
        
        config_layout.addRow("Workload Type:", workload_layout)
        
        # Auto unmount option
        self.auto_unmount = QCheckBox("Automatically unmount drive (recommended)")
        self.auto_unmount.setChecked(True)
        config_layout.addRow("", self.auto_unmount)
        
        test_layout.addWidget(config_group)
        
        # Control buttons
        control_layout = QHBoxLayout()
        self.start_button = QPushButton("Start Test")
        self.start_button.clicked.connect(self.start_test)
        self.start_button.setMinimumHeight(50)
        font = self.start_button.font()
        font.setBold(True)
        font.setPointSize(12)
        self.start_button.setFont(font)
        
        self.stop_button = QPushButton("Stop Test")
        self.stop_button.clicked.connect(self.stop_test)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(50)
        
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        test_layout.addLayout(control_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        test_layout.addWidget(self.progress_bar)
        
        # Status
        self.status_label = QLabel("Ready")
        test_layout.addWidget(self.status_label)
        
        # ===== RESULTS TAB =====
        # Output console
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Monospace", 9))
        self.console_output.setStyleSheet("background-color: #f0f0f0;")
        results_layout.addWidget(QLabel("Test Output:"))
        results_layout.addWidget(self.console_output)
        
        # Temperature chart placeholder (we'll just use text for now)
        self.temp_output = QTextEdit()
        self.temp_output.setReadOnly(True)
        self.temp_output.setFont(QFont("Monospace", 9))
        self.temp_output.setStyleSheet("background-color: #f0f0f0;")
        results_layout.addWidget(QLabel("Temperature Log:"))
        results_layout.addWidget(self.temp_output)
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Open log button
        self.open_log_button = QPushButton("Open Log File")
        self.open_log_button.clicked.connect(self.open_log_file)
        self.open_log_button.setEnabled(False)
        buttons_layout.addWidget(self.open_log_button)
        
        # AI Analyze button
        self.ai_analyze_button = QPushButton("🤖 AI Analyze")
        self.ai_analyze_button.clicked.connect(self.ai_analyze_log)
        self.ai_analyze_button.setEnabled(False)
        if not AI_AVAILABLE:
            self.ai_analyze_button.setToolTip("Install openai and python-dotenv packages to enable AI analysis")
        else:
            self.ai_analyze_button.setToolTip("Analyze test results using AI to identify issues and provide recommendations")
        buttons_layout.addWidget(self.ai_analyze_button)
        
        results_layout.addLayout(buttons_layout)
        
        # Setup timer for progress updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.start_time = 0
        self.test_duration = 0
    
    def detect_nvme_devices(self):
        try:
            # Clear previous devices
            self.nvme_devices = []
            self.device_combo.clear()
            
            # Run lsblk to get NVMe devices
            result = subprocess.run(
                ["lsblk", "-d", "-o", "NAME,SIZE,MODEL"],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                QMessageBox.critical(self, "Error", "Failed to detect NVMe devices")
                return
            
            # Parse output
            lines = result.stdout.strip().split('\n')
            for line in lines:
                if 'nvme' in line:
                    parts = line.split()
                    name = parts[0]
                    size = parts[1]
                    model = ' '.join(parts[2:]) if len(parts) > 2 else "Unknown"
                    
                    self.nvme_devices.append({
                        'name': name,
                        'size': size,
                        'model': model,
                        'path': f"/dev/{name}"
                    })
                    
                    self.device_combo.addItem(f"{name} ({size}, {model})")
            
            if not self.nvme_devices:
                self.device_info.setText("No NVMe devices found")
                self.health_check_button.setEnabled(False)
            else:
                self.device_combo.setCurrentIndex(0)
                self.update_device_info()
                
            # Connect signal after populating to avoid triggering during setup
            self.device_combo.currentIndexChanged.connect(self.update_device_info)
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error detecting NVMe devices: {str(e)}")
    
    def update_device_info(self):
        idx = self.device_combo.currentIndex()
        if idx >= 0 and idx < len(self.nvme_devices):
            device = self.nvme_devices[idx]
            self.health_check_button.setEnabled(True)
            
            # Check if mounted
            is_mounted = self.check_if_mounted(device['name'])
            mount_status = "Currently mounted" if is_mounted else "Not mounted"
            
            # Get health summary
            health_summary, health_color = self.get_health_summary(device['path'])

            self.device_info.setText(
                f"Device: {device['path']}\n"
                f"Size: {device['size']}\n"
                f"Model: {device['model']}\n"
                f"Status: {mount_status}\n"
                f"<b>Health: <font color='{health_color}'>{health_summary}</font></b>"
            )

    def get_health_summary(self, device_path):
        try:
            if not self.is_tool("smartctl"):
                return "smartctl not found", "orange"

            result = subprocess.run(
                ["sudo", "smartctl", "-H", device_path],
                capture_output=True, text=True, timeout=5
            )
            
            output = result.stdout.lower() + result.stderr.lower()
            if "overall-health self-assessment test result: passed" in output or "health status: ok" in output:
                return "Healthy", "green"
            elif "overall-health self-assessment test result: failed" in output:
                return "Failed", "red"
            else:
                return "Unknown", "orange"
        except subprocess.TimeoutExpired:
            return "Timeout", "orange"
        except Exception:
            return "Error fetching status", "red"

    def show_health_report(self):
        idx = self.device_combo.currentIndex()
        if idx < 0:
            return
            
        device = self.nvme_devices[idx]
        device_path = device['path']

        if not self.is_tool("smartctl"):
            QMessageBox.critical(self, "Error", "smartctl command not found. Please install 'smartmontools'.")
            return

        try:
            self.status_label.setText(f"Running health check on {device_path}...")
            QApplication.processEvents()

            result = subprocess.run(
                ["sudo", "smartctl", "-a", device_path],
                capture_output=True, text=True, timeout=10
            )
            
            self.status_label.setText("Ready")

            dialog = QDialog(self)
            dialog.setWindowTitle(f"SMART Health Report for {device_path}")
            dialog.setMinimumSize(700, 500)
            
            layout = QVBoxLayout()
            text_edit = QTextEdit()
            text_edit.setReadOnly(True)
            text_edit.setFont(QFont("Monospace", 9))
            text_edit.setText(result.stdout if result.stdout else result.stderr)
            layout.addWidget(text_edit)
            
            close_button = QPushButton("Close")
            close_button.clicked.connect(dialog.close)
            layout.addWidget(close_button)
            
            dialog.setLayout(layout)
            dialog.exec_()

        except subprocess.TimeoutExpired:
            self.status_label.setText("Ready")
            QMessageBox.critical(self, "Error", "Health check timed out.")
        except Exception as e:
            self.status_label.setText("Ready")
            QMessageBox.critical(self, "Error", f"Failed to run health check: {str(e)}")

    def is_tool(self, name):
        """Check whether `name` is on PATH."""
        try:
            subprocess.run([name, "--version"], capture_output=True, text=True, check=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
    
    def check_if_mounted(self, device_name):
        try:
            with open('/proc/mounts', 'r') as f:
                mounts = f.read()
                return f"/dev/{device_name}" in mounts
        except Exception:
            return False
    
    def start_test(self):
        idx = self.device_combo.currentIndex()
        if idx < 0 or idx >= len(self.nvme_devices):
            QMessageBox.warning(self, "Warning", "Please select an NVMe device")
            return

        device = self.nvme_devices[idx]
        device_path = device['path']

        # Check if mounted and unmount if necessary
        is_mounted = self.check_if_mounted(device['name'])
        if is_mounted and self.auto_unmount.isChecked():
            try:
                result = subprocess.run(
                    f"grep '{device_path}' /proc/mounts | awk '{{print $1}}'",
                    shell=True, capture_output=True, text=True
                )
                mounted_parts = result.stdout.strip().split('\n')
                for part in mounted_parts:
                    if part:
                        # Use pkexec for graphical sudo prompt
                        unmount_cmd = f"pkexec umount {part}"
                        unmount_proc = subprocess.run(unmount_cmd, shell=True, capture_output=True, text=True)
                        if unmount_proc.returncode != 0:
                            QMessageBox.critical(self, "Error", f"Failed to unmount {part}:\n{unmount_proc.stderr}")
                            return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to get mount info: {str(e)}")
                return
        elif is_mounted and not self.auto_unmount.isChecked():
            QMessageBox.critical(self, "Error", f"Device {device_path} is mounted. Please enable auto-unmount or unmount it manually.")
            return

        # Get test parameters
        duration = self.duration_spin.value()
        log_name = self.log_name_edit.text().strip()

        # Generate log file name
        if not log_name:
            log_name = f"nvme_stress_{device['name']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        else:
            log_name = ''.join(c if c.isalnum() or c in '_-' else '_' for c in log_name)
        self.log_file = os.path.abspath(f"{log_name}.log")

        # Prepare to call the external script
        workload_type = "ai" if self.workload_ai.isChecked() else "standard"
        script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "run_single_drive_test.sh")

        if not os.path.exists(script_path):
            QMessageBox.critical(self, "Error", f"Test script not found at {script_path}")
            return

        # The command is now a simple call to our robust shell script
        full_command = f'"{script_path}" "{device_path}" {duration} "{self.log_file}" "{workload_type}"'

        # Start worker thread
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.status_label.setText(f"Starting test on {device_path}...")
        self.console_output.clear()
        self.temp_output.clear()

        self.test_duration = duration
        self.start_time = time.time()
        self.timer.start(1000)  # Update every second

        self.worker_thread = WorkerThread(full_command, self.log_file)
        self.worker_thread.update_signal.connect(self.update_output)
        self.worker_thread.finished_signal.connect(self.test_finished)
        self.worker_thread.start()
    
    def stop_test(self):
        if self.worker_thread and self.worker_thread.isRunning():
            reply = QMessageBox.question(
                self, 
                "Confirm Stop", 
                "Are you sure you want to stop the test?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker_thread.kill()
                self.status_label.setText("Stopping test...")
    
    def update_output(self, line):
        # Update console output
        self.console_output.append(line)
        self.console_output.moveCursor(QTextCursor.End)
        
        # If it's a temperature line, add it to the temperature output
        if "[TEMP]" in line:
            self.temp_output.append(line)
            self.temp_output.moveCursor(QTextCursor.End)
    
    def test_finished(self, success, message):
        self.timer.stop()
        self.progress_bar.setValue(100 if success else 0)
        self.status_label.setText(message)
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.open_log_button.setEnabled(True)
        
        # Enable AI analyze button if AI is available and we have a log file
        if AI_AVAILABLE and self.log_file and os.path.exists(self.log_file):
            self.ai_analyze_button.setEnabled(True)
        
        if success:
            QMessageBox.information(self, "Test Complete", message)
        else:
            QMessageBox.warning(self, "Test Failed", message)
    
    def update_progress(self):
        if self.test_duration <= 0:
            return
            
        elapsed = time.time() - self.start_time
        progress = min(int((elapsed / self.test_duration) * 100), 100)
        self.progress_bar.setValue(progress)
        
        # Update remaining time
        remaining = max(0, self.test_duration - elapsed)
        minutes, seconds = divmod(int(remaining), 60)
        hours, minutes = divmod(minutes, 60)
        
        if hours > 0:
            time_str = f"{hours}h {minutes}m {seconds}s remaining"
        elif minutes > 0:
            time_str = f"{minutes}m {seconds}s remaining"
        else:
            time_str = f"{seconds}s remaining"
            
        self.status_label.setText(f"Running test... {time_str}")
    
    def open_log_file(self):
        if not self.log_file or not os.path.exists(self.log_file):
            QMessageBox.warning(self, "Warning", "Log file not found")
            return
            
        try:
            # Try to open with xdg-open (Linux)
            subprocess.Popen(["xdg-open", self.log_file])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open log file: {str(e)}")
    
    def ai_analyze_log(self):
        """Analyze the test log using OpenAI API"""
        if not AI_AVAILABLE:
            QMessageBox.warning(self, "AI Analysis Unavailable", 
                              "Please install required packages:\n\n"
                              "pip install openai python-dotenv")
            return
        
        if not self.log_file or not os.path.exists(self.log_file):
            QMessageBox.warning(self, "Warning", "Log file not found")
            return
        
        # Check for OpenAI API key
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            QMessageBox.warning(self, "API Key Missing", 
                              "Please set your OpenAI API key:\n\n"
                              "1. Create a .env file in the project directory\n"
                              "2. Add: OPENAI_API_KEY=your_api_key_here\n\n"
                              "Or set the environment variable OPENAI_API_KEY")
            return
        
        try:
            # Show progress dialog
            progress_dialog = QMessageBox(self)
            progress_dialog.setWindowTitle("AI Analysis")
            progress_dialog.setText("Analyzing test results with AI...\nThis may take a few moments.")
            progress_dialog.setStandardButtons(QMessageBox.NoButton)
            progress_dialog.show()
            QApplication.processEvents()
            
            # Read the log file
            with open(self.log_file, 'r') as f:
                log_content = f.read()
            
            # Prepare the prompt for AI analysis
            prompt = self._create_analysis_prompt(log_content)
            
            # Call OpenAI API
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert NVMe storage analyst. Analyze test logs and provide concise, actionable insights about drive health, performance, and any issues found."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            progress_dialog.close()
            
            # Display the analysis result
            analysis = response.choices[0].message.content
            self._show_analysis_result(analysis)
            
        except Exception as e:
            progress_dialog.close()
            QMessageBox.critical(self, "AI Analysis Error", 
                               f"Failed to analyze log file:\n{str(e)}")
    
    def _create_analysis_prompt(self, log_content):
        """Create a structured prompt for AI analysis"""
        return f"""Please analyze this NVMe stress test log and provide a concise report with the following:

1. **Overall Test Result**: PASS/FAIL with brief explanation
2. **Temperature Analysis**: Any thermal issues or concerns
3. **Performance Issues**: Any performance degradation or anomalies
4. **Error Analysis**: Any errors, warnings, or concerning patterns
5. **Drive Health**: Assessment of drive condition
6. **Recommendations**: Specific actions if issues found

Keep the analysis concise but thorough. Focus on actionable insights.

--- TEST LOG ---
{log_content[:8000]}  # Limit to first 8000 chars to stay within token limits
--- END LOG ---"""
    
    def _show_analysis_result(self, analysis):
        """Display the AI analysis result in a dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("🤖 AI Analysis Results")
        dialog.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Analysis text
        text_edit = QTextEdit()
        text_edit.setPlainText(analysis)
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Arial", 10))
        layout.addWidget(text_edit)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.clicked.connect(dialog.close)
        layout.addWidget(close_button)
        
        dialog.setLayout(layout)
        dialog.exec_()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = NVMeStressTestGUI()
    window.show()
    sys.exit(app.exec_())
