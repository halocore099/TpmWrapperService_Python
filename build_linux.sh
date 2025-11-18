#!/bin/bash
# Build script for Linux - Extracts .so files and builds wheel
# This script should be run on Linux (Ubuntu/Debian/Arch/etc.)

set -e

echo "========================================"
echo "TPM Wrapper Service - Linux Build"
echo "========================================"
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "ERROR: This script must be run on Linux"
    exit 1
fi

# Check if TSS2 libraries are installed
if ! pkg-config --exists tss2-esys 2>/dev/null; then
    echo "ERROR: TSS2 libraries not found"
    echo "Please install them first:"
    echo "  Ubuntu/Debian: sudo apt-get install libtss2-dev tpm2-tools pkg-config"
    echo "  Arch: sudo pacman -S tpm2-tss tpm2-tools"
    echo "  Fedora: sudo dnf install tpm2-tss-devel tpm2-tools"
    exit 1
fi

echo "TSS2 libraries found" 
echo ""

# Check if .so directory exists
SO_DIR="tpm_wrapper_service/libs/linux/$(uname -m)"
mkdir -p "$SO_DIR"
echo "Using directory: $SO_DIR"
echo ""

echo "Step 1: Building tpm2-pytss..."
if ! python3 -c "import tpm2_pytss" 2>/dev/null; then
    echo "Installing tpm2-pytss..."
    python3 -m pip install tpm2-pytss
else
    echo "tpm2-pytss already installed"
fi

echo ""
echo "Step 2: Finding TSS2 libraries..."

# Find TSS2 libraries
LIB_PATHS=(
    "/usr/lib/$(uname -m)-linux-gnu"
    "/usr/lib"
    "/usr/local/lib"
)

FOUND_LIBS=()

for lib_path in "${LIB_PATHS[@]}"; do
    if [ -d "$lib_path" ]; then
        for lib in libtss2-esys.so libtss2-mu.so libtss2-rcdecode.so libtss2-tctildr.so libtss2-tcti-device.so; do
            lib_file=$(find "$lib_path" -name "${lib}*" -type f 2>/dev/null | head -1)
            if [ -n "$lib_file" ]; then
                FOUND_LIBS+=("$lib_file")
            fi
        done
    fi
done

if [ ${#FOUND_LIBS[@]} -eq 0 ]; then
    echo "ERROR: Could not find TSS2 libraries"
    echo "Please ensure libtss2-dev (or equivalent) is installed"
    exit 1
fi

echo "Found ${#FOUND_LIBS[@]} library file(s)"
echo ""

echo "Step 3: Copying libraries and dependencies..."

# Copy libraries
COPIED_COUNT=0
for lib_file in "${FOUND_LIBS[@]}"; do
    lib_name=$(basename "$lib_file")
    dest="$SO_DIR/$lib_name"
    
    # Copy the actual file (not symlink)
    if [ -L "$lib_file" ]; then
        # Resolve symlink
        real_file=$(readlink -f "$lib_file")
        cp "$real_file" "$dest"
    else
        cp "$lib_file" "$dest"
    fi
    
    echo "  Copied: $lib_name"
    COPIED_COUNT=$((COPIED_COUNT + 1))
    
    # Copy dependencies using ldd
    if command -v ldd &> /dev/null; then
        deps=$(ldd "$lib_file" 2>/dev/null | grep -oP '/[^\s]+\.so[^\s]*' || true)
        for dep in $deps; do
            if [ -f "$dep" ] && [[ "$dep" == *"tss2"* ]] || [[ "$dep" == *"ssl"* ]] || [[ "$dep" == *"crypto"* ]]; then
                dep_name=$(basename "$dep")
                if [ ! -f "$SO_DIR/$dep_name" ]; then
                    cp "$dep" "$SO_DIR/$dep_name" 2>/dev/null || true
                    echo "    Dependency: $dep_name"
                fi
            fi
        done
    fi
done

if [ $COPIED_COUNT -eq 0 ]; then
    echo "ERROR: No libraries were copied"
    exit 1
fi

echo ""
echo "Copied $COPIED_COUNT library file(s) to $SO_DIR"
echo ""

echo "Step 4: Building wheel..."

# Clean previous builds
echo "Cleaning previous builds..."
python3 setup.py clean --all > /dev/null 2>&1 || true

# Build wheel
echo "Building wheel..."
python3 setup.py bdist_wheel

if [ $? -ne 0 ]; then
    echo "ERROR: Wheel build failed"
    exit 1
fi

echo ""
echo "Step 5: Verifying wheel contents..."

WHEEL_FILE=$(ls -t dist/*.whl 2>/dev/null | head -1)
if [ -n "$WHEEL_FILE" ]; then
    echo "Wheel created: $(basename "$WHEEL_FILE")"
    
    # Check if .so files are in the wheel
    echo "Verifying libraries are included..."
    SO_COUNT=$(unzip -l "$WHEEL_FILE" 2>/dev/null | grep -c "libs/linux.*\.so" || echo "0")
    
    if [ "$SO_COUNT" -gt 0 ]; then
        echo "Found $SO_COUNT library file(s) in wheel"
        unzip -l "$WHEEL_FILE" 2>/dev/null | grep "libs/linux.*\.so" | awk '{print "  - " $4}'
    else
        echo "WARNING: No libraries found in wheel. Check MANIFEST.in and setup.py"
    fi
else
    echo "ERROR: Wheel file not found in dist/"
    exit 1
fi

echo ""
echo "========================================"
echo "Build completed successfully!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Test installation: pip3 install $WHEEL_FILE"
echo "2. Test import: python3 -c 'from tpm_wrapper_service import service'"
echo ""

