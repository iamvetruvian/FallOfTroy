#!/bin/bash
set -e

echo "======================================"
echo "FallOfTroy AppImage Build Script"
echo "======================================"
echo ""

# Configuration
APP_NAME="FallOfTroy"
APPDIR="AppDir"

# Check if running on x86_64
ARCH=$(uname -m)
if [ "$ARCH" != "x86_64" ]; then
    echo "Error: This script only supports x86_64 architecture"
    exit 1
fi

# Check for required tools
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is required but not installed"
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    echo "Error: pip3 is required but not installed"
    exit 1
fi

# Clean previous build
echo "Cleaning previous build..."
rm -rf "${APPDIR}/usr"
rm -f "${APP_NAME}-${ARCH}.AppImage"

# Create directory structure
echo "Creating AppDir structure..."
mkdir -p "${APPDIR}/usr/bin"
mkdir -p "${APPDIR}/usr/lib/python3/site-packages"
mkdir -p "${APPDIR}/usr/share/bundled_profiles"

# Copy application files
echo "Copying application files..."
cp FallOfTroy.py "${APPDIR}/usr/bin/"
cp -r bundled_profiles/* "${APPDIR}/usr/share/bundled_profiles/" 2>/dev/null || true

# Install dependencies to AppDir
echo "Installing Python dependencies..."
pip3 install -r requirements.txt --target="${APPDIR}/usr/lib/python3/site-packages" --upgrade

# Update the bundled profiles path in the copied script
echo "Updating bundled profiles path..."
sed -i 's|BUNDLED_PROFILES_DIR = os.path.join(BASE_DIR, "bundled_profiles")|BUNDLED_PROFILES_DIR = os.path.join(BASE_DIR, "usr/share/bundled_profiles")|g' "${APPDIR}/usr/bin/FallOfTroy.py"

# Create a wrapper script that uses system Python
echo "Creating Python wrapper..."
cat > "${APPDIR}/usr/bin/python3-wrapper" << 'WRAPPER_EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PYTHONPATH="${HERE}/../lib/python3/site-packages:${PYTHONPATH:-}"
exec python3 "$@"
WRAPPER_EOF
chmod +x "${APPDIR}/usr/bin/python3-wrapper"

# Update AppRun to use the wrapper
cat > "${APPDIR}/AppRun" << 'APPRUN_EOF'
#!/bin/bash
set -e

HERE="$(dirname "$(readlink -f "${0}")")"

# Export AppImage-specific environment variables
export APPDIR="${HERE}"
export APPIMAGE="${APPIMAGE:-}"

# Set Python path to include bundled libraries
export PYTHONPATH="${HERE}/usr/lib/python3/site-packages:${PYTHONPATH:-}"

# Disable PySide6 Qt platform plugin debug output
export QT_LOGGING_RULES="*.debug=false"

# Launch the application with system Python
exec python3 "${HERE}/usr/bin/FallOfTroy.py" "$@"
APPRUN_EOF
chmod +x "${APPDIR}/AppRun"

# Download appimagetool if not exists
APPIMAGETOOL="appimagetool-${ARCH}.AppImage"
if [ ! -f "$APPIMAGETOOL" ]; then
    echo "Downloading appimagetool..."
    wget --show-progress "https://github.com/AppImage/AppImageKit/releases/download/continuous/${APPIMAGETOOL}"
    
    if [ ! -s "$APPIMAGETOOL" ]; then
        echo "Error: Failed to download appimagetool"
        rm -f "$APPIMAGETOOL"
        exit 1
    fi
    
    chmod +x "$APPIMAGETOOL"
fi

# Build AppImage
echo "Building AppImage..."
ARCH="${ARCH}" ./"$APPIMAGETOOL" "${APPDIR}" "${APP_NAME}-${ARCH}.AppImage"

# Make it executable
chmod +x "${APP_NAME}-${ARCH}.AppImage"

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
echo "AppImage created: ${APP_NAME}-${ARCH}.AppImage"
echo ""
echo "NOTE: This AppImage requires Python 3 to be installed on the target system."
echo "To run: ./${APP_NAME}-${ARCH}.AppImage"
echo ""
