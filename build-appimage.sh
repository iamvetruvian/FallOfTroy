#!/bin/bash
set -e

echo "======================================"
echo "FallOfTroy AppImage Build Script"
echo "======================================"
echo ""

# Configuration
PYTHON_VERSION="3.11"
APP_NAME="FallOfTroy"
APPDIR="AppDir"

# Check if running on x86_64
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
    echo "Error: This script only supports x86_64 architecture"
    exit 1
fi

# Clean previous build
echo "Cleaning previous build..."
rm -rf "${APPDIR}/usr/lib" "${APPDIR}/usr/bin/python3"
rm -f "${APP_NAME}-${ARCH}.AppImage"

# Download python-appimage if not exists
PYTHON_APPIMAGE="python${PYTHON_VERSION}-${ARCH}.AppImage"
if [ ! -f "$PYTHON_APPIMAGE" ]; then
    echo "Downloading Python ${PYTHON_VERSION} AppImage..."
    wget -q --show-progress "https://github.com/niess/python-appimage/releases/download/python3.11/python${PYTHON_VERSION}.7-cp311-cp311-manylinux2014_${ARCH}.AppImage" -O "$PYTHON_APPIMAGE"
    chmod +x "$PYTHON_APPIMAGE"
fi

# Extract Python AppImage
echo "Extracting Python runtime..."
./"$PYTHON_APPIMAGE" --appimage-extract > /dev/null 2>&1

# Copy Python to AppDir
echo "Setting up Python in AppDir..."
cp -r squashfs-root/usr "${APPDIR}/"
rm -rf squashfs-root

# Install dependencies
echo "Installing Python dependencies..."
"${APPDIR}/usr/bin/python3" -m pip install --upgrade pip > /dev/null 2>&1
"${APPDIR}/usr/bin/python3" -m pip install -r requirements.txt --target="${APPDIR}/usr/lib/python3/site-packages" > /dev/null 2>&1

# Ensure bundled profiles are in place
echo "Copying bundled profiles..."
mkdir -p "${APPDIR}/usr/share/bundled_profiles"
cp -r bundled_profiles/* "${APPDIR}/usr/share/bundled_profiles/" 2>/dev/null || true

# Update the bundled profiles path in the copied script
echo "Updating bundled profiles path..."
sed -i 's|BUNDLED_PROFILES_DIR = os.path.join(BASE_DIR, "bundled_profiles")|BUNDLED_PROFILES_DIR = os.path.join(BASE_DIR, "usr/share/bundled_profiles")|g' "${APPDIR}/usr/bin/FallOfTroy.py"

# Download appimagetool if not exists
APPIMAGETOOL="appimagetool-${ARCH}.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget -q --show-progress "https://github.com/AppImage/AppImageKit/releases/download/continuous/${APPIMAGETOOL}"
    chmod +x "$APPIMAGETOOL"
fi

# Build AppImage
echo "Building AppImage..."
ARCH="${ARCH}" ./"$APPIMAGETOOL" "${APPDIR}" "${APP_NAME}-${ARCH}.AppImage" > /dev/null 2>&1

# Make it executable
chmod +x "${APP_NAME}-${ARCH}.AppImage"

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
echo "AppImage created: ${APP_NAME}-${ARCH}.AppImage"
echo ""
echo "To run: ./${APP_NAME}-${ARCH}.AppImage"
echo ""
