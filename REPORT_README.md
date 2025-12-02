# NVMe Stress Test Report

## 📊 Report Generated

The HTML report has been successfully created: **`nvme_stress_test_report.html`**

## 🚀 How to View the Report

### Option 1: Open in Browser
```bash
xdg-open nvme_stress_test_report.html
```

### Option 2: Direct File Path
Open your browser and navigate to:
```
file:///home/bizon/nvme_stress_test/nvme_stress_test_report.html
```

### Option 3: Python HTTP Server
```bash
python3 -m http.server 8000
```
Then open: `http://localhost:8000/nvme_stress_test_report.html`

## 📋 Report Contents

The report includes:

### Summary Section
- **Total drives tested**: 7 NVMe drives
- **Health status**: All drives PASSED
- **PCIe Interface**: PCIe 5.0 x4 (32.0 GT/s)
- **Test type**: AI Workload simulation
- **Duration**: 10 minutes per drive

### Per-Drive Information
For each drive, the report shows:

#### Drive Specifications
- Model number and serial number
- Total capacity (15.3 TB per drive)
- Firmware version
- NVMe version (2.0)
- Current health status
- Percentage used
- Error count (0 errors on all drives)

#### Performance Metrics
- **Read Bandwidth**: ~3.6-3.8 GB/s
- **Read IOPS**: ~29-30K IOPS
- **Write Bandwidth**: ~8.3-8.4 GB/s  
- **Write IOPS**: ~8.3-8.4K IOPS
- Total data read/written during test

#### Temperature Monitoring
- Temperature before test
- Temperature after test
- Individual sensor readings (4 sensors per drive)
- All temperatures remained within safe operating ranges

## ✅ Test Results Summary

**All 7 drives PASSED all tests successfully!**

- ✅ SMART health status: PASSED
- ✅ No errors reported
- ✅ Running at PCIe 5.0 x4 speeds
- ✅ Excellent read/write performance
- ✅ Temperatures within normal ranges
- ✅ AI workload stress test completed successfully

## 🔄 Regenerating the Report

To regenerate the report (e.g., after new tests):

```bash
python3 generate_report.py
```

The script will automatically:
1. Find all `nvme*.log` files in the directory
2. Parse SMART data and performance metrics
3. Extract PCIe generation information
4. Generate a new HTML report

## 📝 Notes

- The report is self-contained (no external dependencies)
- Can be shared via email or hosted on a web server
- Fully responsive design (works on mobile devices)
- Modern, professional appearance suitable for client presentations

## 🎨 Report Features

- **Modern gradient design** with clean typography
- **Color-coded status badges** for quick health assessment
- **Performance visualizations** with key metrics highlighted
- **Temperature monitoring** across multiple sensors
- **Comprehensive footer** explaining PCIe 5.0 performance benefits
