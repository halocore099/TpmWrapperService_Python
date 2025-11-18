#!/bin/bash
# Build script for both Windows and Linux platforms
# This script is designed to run in WSL2 where you can build both platforms

set -e

echo "========================================"
echo "TPM Wrapper Service - Build All Platforms"
echo "========================================"
echo ""

# Detect if running in WSL
if grep -qEi "(Microsoft|WSL)" /proc/version &> /dev/null ; then
    IS_WSL=true
    echo "Detected WSL environment"
else
    IS_WSL=false
    echo "Running on native Linux"
fi

echo ""

# Build Linux wheel
echo "========================================"
echo "Building Linux wheel..."
echo "========================================"
chmod +x build_linux.sh
./build_linux.sh

if [ $? -ne 0 ]; then
    echo "ERROR: Linux build failed"
    exit 1
fi

echo ""
echo "========================================"
echo "Linux build completed"
echo "========================================"
echo ""

# Instructions for Windows build
echo "========================================"
echo "Windows Build Instructions"
echo "========================================"
echo ""
echo "To build the Windows wheel:"
echo "1. Open PowerShell on Windows (not WSL)"
echo "2. Navigate to the project directory"
echo "3. Run: .\build_windows.ps1"
echo ""
echo "Or manually:"
echo "1. Build tpm2-pytss in MSYS2 UCRT64"
echo "2. Extract DLLs from C:\\msys64\\ucrt64\\bin\\"
echo "3. Copy to tpm_wrapper_service\\libs\\windows\\"
echo "4. Run: python setup.py bdist_wheel"
echo ""

if [ "$IS_WSL" = true ]; then
    echo "Note: You can access Windows files from WSL at:"
    echo "  /mnt/c/Users/$(whoami)/..."
    echo ""
    echo "To build Windows wheel from WSL (if MSYS2 is accessible):"
    echo "  You may need to use Windows Python and MSYS2 tools"
    echo "  It's recommended to build Windows wheel on native Windows"
fi

echo ""
echo "========================================"
echo "Build process complete!"
echo "========================================"
echo ""
echo "Wheels are in the dist/ directory:"
ls -lh dist/*.whl 2>/dev/null || echo "  (No wheels found yet - build Windows wheel separately)"
echo ""

