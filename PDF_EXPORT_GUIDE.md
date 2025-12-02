# 📄 How to Export Perfect PDF from HTML Report

The HTML report now has optimized print CSS to prevent page breaks inside elements and preserve all colors.

## ✨ Best Method: Chrome/Edge Browser

1. **Open the report** in Chrome or Edge browser:
   - Navigate to: `http://192.168.1.67:8000/nvme_stress_test_report.html`
   - Or open the local file: `file:///home/bizon/nvme_stress_test/nvme_stress_test_report.html`

2. **Print to PDF**:
   - Press `Ctrl + P` (or `Cmd + P` on Mac)
   - In the print dialog:
     - **Destination**: Select "Save as PDF"
     - **Layout**: Portrait (recommended) or Landscape
     - **Pages**: All
     - **Color**: Color (not Black and white)
     - ⚠️ **IMPORTANT**: Enable "Background graphics" checkbox ✓
     - **Margins**: Default or Minimum
     - **Scale**: 100%

3. **Click "Save"** and choose your filename

## 🎨 Settings to Enable Beautiful Colors

### Chrome/Edge:
- ✅ **"Background graphics"** - MUST be enabled to show colored boxes and gradients

### Firefox:
- Press `Ctrl + P`
- ✅ Enable **"Print backgrounds"** in the print settings
- Choose "Save to PDF"

## 📝 What the Print CSS Does

The updated report now includes:
- ✅ Prevents page breaks inside drive cards
- ✅ Prevents page breaks inside performance metrics
- ✅ Prevents page breaks inside temperature grids
- ✅ Keeps section titles with their content
- ✅ Preserves all gradient backgrounds and colors
- ✅ Maintains proper spacing between sections
- ✅ Removes shadows for clean PDF output

## 🚀 Alternative: Command-Line PDF Export

If you have Chromium installed, you can use the script:

```bash
# Make sure chromium-browser is installed
sudo apt install chromium-browser

# Use the export script
./export_to_pdf.sh
```

## 💡 Tips for Best Results

1. **Use Chrome or Edge** - They have the best CSS gradient and print support
2. **Always enable "Background graphics"** - This is critical for colors
3. **Use Portrait orientation** - The report is designed for portrait layout
4. **Set margins to Minimum or None** - For maximum content space
5. **Check print preview first** - Make sure everything looks good before saving

## 📊 Expected Result

Your PDF should have:
- Beautiful colored gradient cards (green, blue, purple)
- All performance metrics clearly visible
- No content cut across pages
- Professional appearance matching the HTML version
- All 8 drives on separate logical sections

Enjoy your beautiful NVMe stress test report! 🎉
