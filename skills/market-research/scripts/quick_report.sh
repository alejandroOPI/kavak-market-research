#!/bin/bash
# Quick Report Generation
# Generates reports from existing collected data
#
# Usage:
#   ./quick_report.sh
#   ./quick_report.sh --text-only

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

cd "$PROJECT_ROOT"

# Activate virtual environment if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

echo "==================================="
echo "KAVAK Market Research - Quick Report"
echo "==================================="
echo ""

if [ "$1" == "--text-only" ]; then
    echo "Generating text report only..."
    python -m src.analyzers.new_cars
else
    echo "Generating all reports..."
    python -m src.analyzers.new_cars
    python -m src.reporters.excel
fi

echo ""
echo "Reports saved to: data/outputs/"
ls -la data/outputs/*.{txt,xlsx,csv} 2>/dev/null || echo "No reports found"
