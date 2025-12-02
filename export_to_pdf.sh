#!/bin/bash
# Export HTML report to PDF with proper colors and formatting

REPORT_FILE="nvme_stress_test_report.html"
OUTPUT_PDF="nvme_stress_test_report.pdf"

echo "📄 Exporting HTML report to PDF..."

# Method 1: Try using Chrome/Chromium headless (best quality)
if command -v google-chrome &> /dev/null; then
    echo "Using Google Chrome for PDF export..."
    google-chrome --headless --disable-gpu --print-to-pdf="$OUTPUT_PDF" \
        --print-to-pdf-no-header \
        --no-margins \
        "$REPORT_FILE"
    echo "✅ PDF created: $OUTPUT_PDF"
    exit 0
elif command -v chromium-browser &> /dev/null; then
    echo "Using Chromium for PDF export..."
    chromium-browser --headless --disable-gpu --print-to-pdf="$OUTPUT_PDF" \
        --print-to-pdf-no-header \
        --no-margins \
        "$REPORT_FILE"
    echo "✅ PDF created: $OUTPUT_PDF"
    exit 0
elif command -v chromium &> /dev/null; then
    echo "Using Chromium for PDF export..."
    chromium --headless --disable-gpu --print-to-pdf="$OUTPUT_PDF" \
        --print-to-pdf-no-header \
        --no-margins \
        "$REPORT_FILE"
    echo "✅ PDF created: $OUTPUT_PDF"
    exit 0
# Method 2: Try wkhtmltopdf
elif command -v wkhtmltopdf &> /dev/null; then
    echo "Using wkhtmltopdf for PDF export..."
    wkhtmltopdf --enable-local-file-access \
        --print-media-type \
        --enable-javascript \
        --no-stop-slow-scripts \
        "$REPORT_FILE" "$OUTPUT_PDF"
    echo "✅ PDF created: $OUTPUT_PDF"
    exit 0
else
    echo "❌ No PDF converter found!"
    echo ""
    echo "Please install one of the following:"
    echo "  1. Google Chrome/Chromium:"
    echo "     sudo apt install chromium-browser"
    echo ""
    echo "  2. wkhtmltopdf:"
    echo "     sudo apt install wkhtmltopdf"
    echo ""
    echo "Alternative: Open the HTML in your browser and use:"
    echo "  - Chrome/Edge: Press Ctrl+P → 'Save as PDF' → Enable 'Background graphics'"
    echo "  - Firefox: Press Ctrl+P → 'Print to PDF' → Enable 'Print backgrounds'"
    exit 1
fi
