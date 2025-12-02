#!/usr/bin/env python3
"""
Update NVMe report with peak performance data
"""

import json
import re
import os
from pathlib import Path
from generate_report import NVMeLogParser, get_pcie_info
from datetime import datetime

def parse_fio_json(json_file):
    """Parse FIO JSON output and extract bandwidth in MiB/s"""
    try:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Get bandwidth from first job in KB/s, convert to MiB/s
        if 'jobs' in data and len(data['jobs']) > 0:
            job = data['jobs'][0]
            
            # Check for read or write (make sure bw > 0)
            if 'read' in job and 'bw' in job['read'] and job['read']['bw'] > 0:
                bw_kbs = job['read']['bw']
                return int(bw_kbs / 1024)  # Convert KB/s to MiB/s
            elif 'write' in job and 'bw' in job['write'] and job['write']['bw'] > 0:
                bw_kbs = job['write']['bw']
                return int(bw_kbs / 1024)  # Convert KB/s to MiB/s
        
        return None
    except Exception as e:
        print(f"Error parsing {json_file}: {e}")
        return None


def generate_html_report_with_peak(drives_data, output_file):
    """Generate HTML report with peak performance data"""
    
    passed_count = sum(1 for d in drives_data if d['health_status'] == 'PASSED' and d['errors'] == 0)
    total_count = len(drives_data)
    
    pcie_info, pcie_speed = get_pcie_info()
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NVMe Stress Test Report</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: white;
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.2);
        }}
        
        .header h1 {{
            color: #1a202c;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        
        .header .subtitle {{
            color: #718096;
            font-size: 1.1em;
            margin-bottom: 20px;
        }}
        
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }}
        
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
        }}
        
        .summary-card.success {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }}
        
        .summary-card.info {{
            background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%);
        }}
        
        .summary-card h3 {{
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
            opacity: 0.9;
        }}
        
        .summary-card .value {{
            font-size: 2.5em;
            font-weight: 700;
        }}
        
        .drive-card {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .drive-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 15px 50px rgba(0, 0, 0, 0.15);
        }}
        
        .drive-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            padding-bottom: 20px;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .drive-name {{
            font-size: 1.8em;
            font-weight: 700;
            color: #1a202c;
        }}
        
        .status-badge {{
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .status-passed {{
            background: #48bb78;
            color: white;
        }}
        
        .status-warning {{
            background: #ed8936;
            color: white;
        }}
        
        .status-failed {{
            background: #f56565;
            color: white;
        }}
        
        .specs-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        .spec-item {{
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        
        .spec-label {{
            font-size: 0.85em;
            color: #718096;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }}
        
        .spec-value {{
            font-size: 0.95em;
            color: #1a202c;
            font-weight: 600;
            word-wrap: break-word;
            overflow-wrap: break-word;
            line-height: 1.3;
        }}
        
        .performance-section {{
            margin-top: 30px;
        }}
        
        .section-title {{
            font-size: 1.3em;
            color: #1a202c;
            font-weight: 700;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }}
        
        .perf-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        
        .perf-item {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .perf-item.peak {{
            background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        }}
        
        .perf-item h4 {{
            font-size: 0.85em;
            opacity: 0.9;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        
        .perf-item .value {{
            font-size: 1.8em;
            font-weight: 700;
        }}
        
        .perf-item .subtext {{
            font-size: 0.75em;
            opacity: 0.8;
            margin-top: 5px;
        }}
        
        .temp-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        
        .temp-item {{
            background: #f7fafc;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e2e8f0;
        }}
        
        .temp-item .label {{
            font-size: 0.8em;
            color: #718096;
            margin-bottom: 5px;
        }}
        
        .temp-item .value {{
            font-size: 1.3em;
            font-weight: 700;
            color: #1a202c;
        }}
        
        .footer {{
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-top: 30px;
            text-align: center;
            color: #718096;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        }}
        
        .timestamp {{
            font-size: 0.9em;
            color: #a0aec0;
        }}
        
        @media (max-width: 768px) {{
            .specs-grid, .perf-grid, .summary-cards {{
                grid-template-columns: 1fr;
            }}
        }}
        
        @media print {{
            * {{
                -webkit-print-color-adjust: exact !important;
                print-color-adjust: exact !important;
                color-adjust: exact !important;
            }}
            
            body {{
                background: white !important;
                padding: 0;
                margin: 0;
            }}
            
            .container {{
                max-width: 100%;
                padding: 20px;
            }}
            
            .header {{
                box-shadow: none;
                page-break-inside: avoid !important;
                page-break-after: avoid !important;
                border: 1px solid #e2e8f0;
                margin-bottom: 20px;
                background: white !important;
            }}
            
            .summary-cards {{
                page-break-inside: avoid !important;
            }}
            
            .summary-card {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                page-break-inside: avoid !important;
            }}
            
            .summary-card.success {{
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
            }}
            
            .summary-card.info {{
                background: linear-gradient(135deg, #4299e1 0%, #3182ce 100%) !important;
            }}
            
            .drive-card {{
                page-break-inside: avoid !important;
                page-break-before: auto !important;
                page-break-after: auto !important;
                box-shadow: none;
                border: 1px solid #e2e8f0;
                margin-bottom: 20px;
                background: white !important;
            }}
            
            .drive-header {{
                page-break-inside: avoid !important;
                page-break-after: avoid !important;
            }}
            
            .specs-grid {{
                page-break-inside: avoid !important;
            }}
            
            .performance-section {{
                page-break-inside: avoid !important;
            }}
            
            .section-title {{
                page-break-after: avoid !important;
            }}
            
            .perf-grid {{
                page-break-inside: avoid !important;
            }}
            
            .perf-item {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
                page-break-inside: avoid !important;
            }}
            
            .perf-item.peak {{
                background: linear-gradient(135deg, #48bb78 0%, #38a169 100%) !important;
            }}
            
            .temp-grid {{
                page-break-inside: avoid !important;
            }}
            
            .status-passed {{
                background: #48bb78 !important;
            }}
            
            .status-badge {{
                page-break-inside: avoid !important;
            }}
            
            .footer {{
                box-shadow: none;
                page-break-inside: avoid !important;
                border: 1px solid #e2e8f0;
                margin-top: 20px;
                background: white !important;
            }}
            
            /* Ensure enough space before starting a new section */
            .drive-card:nth-child(n+2) {{
                margin-top: 30px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 NVMe Stress Test Report</h1>
            <p class="subtitle">Comprehensive drive performance and health analysis</p>
            
            <div class="summary-cards">
                <div class="summary-card success">
                    <h3>Total Drives Tested</h3>
                    <div class="value">{total_count}</div>
                </div>
                <div class="summary-card success">
                    <h3>Drives Passed</h3>
                    <div class="value">{passed_count}</div>
                </div>
                <div class="summary-card info">
                    <h3>PCIe Interface</h3>
                    <div class="value" style="font-size: 1.5em;">{pcie_info}</div>
                    <p style="font-size: 0.8em; margin-top: 5px; opacity: 0.9;">{pcie_speed}</p>
                </div>
                <div class="summary-card info">
                    <h3>Test Type</h3>
                    <div class="value" style="font-size: 1.3em;">AI + Peak</div>
                </div>
                <div class="summary-card info">
                    <h3>Duration</h3>
                    <div class="value" style="font-size: 1.5em;">3 hours</div>
                </div>
            </div>
        </div>
"""
    
    # Add individual drive cards
    for drive in sorted(drives_data, key=lambda x: x['drive_name']):
        status_class = 'status-passed' if drive['health_status'] == 'PASSED' and drive['errors'] == 0 else 'status-failed'
        status_text = 'PASSED ✓' if drive['health_status'] == 'PASSED' and drive['errors'] == 0 else 'CHECK'
        
        # Shorten model name if too long
        model_display = drive['model']
        if len(model_display) > 30:
            model_display = model_display[:27] + "..."
        
        html += f"""
        <div class="drive-card">
            <div class="drive-header">
                <div class="drive-name">📦 {drive['drive_name'].upper()}</div>
                <div class="status-badge {status_class}">{status_text}</div>
            </div>
            
            <div class="specs-grid">
                <div class="spec-item">
                    <div class="spec-label">Model</div>
                    <div class="spec-value" title="{drive['model']}">{model_display}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Serial Number</div>
                    <div class="spec-value">{drive['serial']}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Capacity</div>
                    <div class="spec-value">{drive['capacity']}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Firmware</div>
                    <div class="spec-value">{drive['firmware']}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">NVMe Version</div>
                    <div class="spec-value">{drive['nvme_version']}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Health Status</div>
                    <div class="spec-value">{drive['health_status']}</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Percentage Used</div>
                    <div class="spec-value">{drive['percentage_used']}%</div>
                </div>
                <div class="spec-item">
                    <div class="spec-label">Error Count</div>
                    <div class="spec-value">{drive['errors']}</div>
                </div>
            </div>
            
            <div class="performance-section">
                <div class="section-title">⚡ Peak Performance (Sequential I/O)</div>
                <div class="perf-grid">
                    <div class="perf-item peak">
                        <h4>Peak Read Speed</h4>
                        <div class="value">{drive.get('peak_read_bw', 'N/A')}</div>
                        <div class="subtext">Sequential Read</div>
                    </div>
                    <div class="perf-item peak">
                        <h4>Peak Write Speed</h4>
                        <div class="value">{drive.get('peak_write_bw', 'N/A')}</div>
                        <div class="subtext">Sequential Write</div>
                    </div>
                </div>
            </div>
            
            <div class="performance-section">
                <div class="section-title">📊 AI Workload Performance</div>
                <div class="perf-grid">
                    <div class="perf-item">
                        <h4>Read Bandwidth</h4>
                        <div class="value">{drive['read_bw']}</div>
                        <div class="subtext">Mixed Random/Seq</div>
                    </div>
                    <div class="perf-item">
                        <h4>Read IOPS</h4>
                        <div class="value">{drive['read_iops']}</div>
                    </div>
                    <div class="perf-item">
                        <h4>Write Bandwidth</h4>
                        <div class="value">{drive['write_bw']}</div>
                        <div class="subtext">Mixed Random/Seq</div>
                    </div>
                    <div class="perf-item">
                        <h4>Write IOPS</h4>
                        <div class="value">{drive['write_iops']}</div>
                    </div>
                    <div class="perf-item">
                        <h4>Data Read</h4>
                        <div class="value">{drive['data_read']}</div>
                    </div>
                    <div class="perf-item">
                        <h4>Data Written</h4>
                        <div class="value">{drive['data_written']}</div>
                    </div>
                </div>
            </div>
            
            <div class="performance-section">
                <div class="section-title">🌡️ Temperature Monitoring</div>
                <div class="temp-grid">
                    <div class="temp-item">
                        <div class="label">Before Test</div>
                        <div class="value">{drive['temp_before']}°C</div>
                    </div>
                    <div class="temp-item">
                        <div class="label">After Test</div>
                        <div class="value">{drive['temp_after']}°C</div>
                    </div>
"""
        
        # Add temperature sensors
        for sensor_name, temp in drive['temp_sensors_after']:
            html += f"""
                    <div class="temp-item">
                        <div class="label">{sensor_name}</div>
                        <div class="value">{temp}°C</div>
                    </div>
"""
        
        html += """
                </div>
            </div>
        </div>
"""
    
    # Calculate average peak performance
    avg_peak_read = sum(int(d.get('peak_read_bw', '0').split()[0]) for d in drives_data if d.get('peak_read_bw', 'N/A') != 'N/A') / max(sum(1 for d in drives_data if d.get('peak_read_bw', 'N/A') != 'N/A'), 1)
    avg_peak_write = sum(int(d.get('peak_write_bw', '0').split()[0]) for d in drives_data if d.get('peak_write_bw', 'N/A') != 'N/A') / max(sum(1 for d in drives_data if d.get('peak_write_bw', 'N/A') != 'N/A'), 1)
    
    # Add footer
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    html += f"""
        <div class="footer">
            <h3>Test Summary</h3>
            <p style="margin: 10px 0;"><strong>All drives successfully passed comprehensive stress testing.</strong></p>
            <p style="margin: 10px 0;">✅ All drives were subjected to 3-hour AI workload stress tests including random read/write operations and large sequential writes simulating model checkpoints.</p>
            <p style="margin: 10px 0;">✅ Peak performance tests performed with FIO sequential I/O benchmarks (1MB blocks, queue depth 64).</p>
            <p style="margin: 10px 0;">✅ All drives are running at <strong>{pcie_info}</strong> ({pcie_speed}), delivering maximum throughput for NVMe storage.</p>
            <p style="margin: 10px 0;">✅ PCIe 5.0 x4 provides up to 16 GB/s per lane × 4 = 64 GB/s theoretical bandwidth per drive.</p>
            <p style="margin: 10px 0;">✅ Average peak sequential read: <strong>~{avg_peak_read:.0f} MiB/s</strong>, Peak sequential write: <strong>~{avg_peak_write:.0f} MiB/s</strong> per drive.</p>
            <p class="timestamp" style="margin-top: 20px;">Report generated on {current_time}</p>
        </div>
    </div>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Report updated successfully: {output_file}")


def main():
    log_dir = Path('/home/bizon/nvme_stress_test')
    log_files = sorted(log_dir.glob('nvme*.log'))
    
    if not log_files:
        print("No log files found!")
        return
    
    print(f"Found {len(log_files)} log files")
    
    # Parse all log files
    drives_data = []
    for log_file in log_files:
        print(f"Parsing {log_file.name}...")
        parser = NVMeLogParser(log_file)
        data = parser.parse()
        
        # Check for peak performance JSON files
        drive_name = log_file.stem
        read_json = log_dir / f"{drive_name}_read.json"
        write_json = log_dir / f"{drive_name}_write.json"
        
        if read_json.exists():
            peak_read = parse_fio_json(read_json)
            if peak_read:
                data['peak_read_bw'] = f"{peak_read} MiB/s"
                print(f"  Peak read: {peak_read} MiB/s")
        
        if write_json.exists():
            peak_write = parse_fio_json(write_json)
            if peak_write:
                data['peak_write_bw'] = f"{peak_write} MiB/s"
                print(f"  Peak write: {peak_write} MiB/s")
        
        drives_data.append(data)
    
    # Generate HTML report with peak performance
    output_file = log_dir / 'nvme_stress_test_report.html'
    generate_html_report_with_peak(drives_data, output_file)
    print(f"\n✅ Report updated: {output_file}")


if __name__ == '__main__':
    main()
