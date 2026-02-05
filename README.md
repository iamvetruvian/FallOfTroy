# FallOfTroy - Project Daemon

A powerful project initialization and management tool for developers. FallOfTroy helps you quickly bootstrap new projects using customizable shell script profiles and optionally create GitHub repositories with a single click.

## Features

- 🚀 **Quick Project Setup**: Initialize projects with pre-configured templates (profiles)
- 📦 **Profile System**: Use shell scripts to define custom project structures and dependencies
- 🔧 **GitHub Integration**: Automatically create and push to GitHub repositories (public or private)
- 💾 **Project Registry**: Keep track of all your projects for easy reopening
- 🎨 **Modern GUI**: Clean PySide6-based interface

## System Requirements

### Required
- **Linux** (x86_64)
- **Python 3.11+** (bundled in AppImage)
- **Git** - for version control features
- **GitHub CLI (`gh`)** - for GitHub repository creation
  ```bash
  # Install GitHub CLI
  # Debian/Ubuntu:
  sudo apt install gh
  # Arch:
  sudo pacman -S github-cli
  # Fedora:
  sudo dnf install gh
  ```

### Optional
- **Text Editor** - The app tries to open `zeditor` by default. You can modify `FallOfTroy.py` to use your preferred editor (VS Code, Sublime, etc.)
- **File Manager** - For the "Open profiles folder" feature (thunar, nautilus, dolphin, etc.)

## Installation & Usage

### Option 1: Download AppImage (Recommended)

1. Download the latest `FallOfTroy-x86_64.AppImage` from releases
2. Make it executable:
   ```bash
   chmod +x FallOfTroy-x86_64.AppImage
   ```
3. Run it:
   ```bash
   ./FallOfTroy-x86_64.AppImage
   ```

### Option 2: Build from Source

1. Clone this repository:
   ```bash
   git clone https://github.com/iamvetruvian/FallOfTroy.git
   cd FallOfTroy
   ```

2. Run the build script:
   ```bash
   bash build-appimage.sh
   ```
   This will:
   - Download Python 3.11 AppImage
   - Install dependencies
   - Create `FallOfTroy-x86_64.AppImage`

3. Run the AppImage:
   ```bash
   ./FallOfTroy-x86_64.AppImage
   ```

### Option 3: Run Directly (Development)

```bash
pip install -r requirements.txt
python FallOfTroy.py
```

## How It Works

### Profiles

Profiles are shell scripts that define how to set up a project. They receive two arguments:
- `$1` - Parent directory path
- `$2` - Project name

Example profile (`ExpressDefault.sh`):
```bash
#!/usr/bin/env bash
set -e

PARENT_DIR="$1"
PROJECT_NAME="$2"
PROJECT_PATH="${PARENT_DIR}/${PROJECT_NAME}"

# Create project structure
mkdir -p "${PROJECT_PATH}"
cd "${PROJECT_PATH}"

# Initialize npm project
npm init -y
npm install express

# Create basic files
echo "const express = require('express');" > index.js
echo "node_modules/" > .gitignore
```

### Configuration

FallOfTroy stores its configuration in:
```
~/.config/project_daemon/
├── config.json          # App settings and project registry
└── profiles/            # Your custom profiles
    └── *.sh
```

Bundled profiles are automatically copied to this directory on first run.

## Creating Custom Profiles

1. Click the "+" button next to the profile dropdown
2. Enter a profile name
3. Write your shell script (or paste from the [official profiles repo](https://github.com/iamvetruvian/tryfall))
4. Click "Create Profile"

**⚠️ Security Warning**: Profiles are executable shell scripts. Only use profiles from trusted sources!

## GitHub Integration

To use GitHub features:

1. Install and authenticate GitHub CLI:
   ```bash
   gh auth login
   ```

2. Check the "Create a GitHub repository" option when creating a project
3. Choose visibility (Public/Private)
4. FallOfTroy will automatically:
   - Initialize git
   - Create initial commit
   - Create GitHub repo
   - Push code

## Troubleshooting

**AppImage won't run:**
- Ensure it's executable: `chmod +x FallOfTroy-x86_64.AppImage`
- Try running with `--appimage-extract-and-run` flag

**GitHub creation fails:**
- Verify `gh` is installed: `gh --version`
- Check authentication: `gh auth status`

**Profile execution fails:**
- Check profile script syntax
- Ensure required tools (npm, pip, etc.) are installed
- View profile script: `cat ~/.config/project_daemon/profiles/YourProfile.sh`

## Development

Project structure:
```
FallOfTroy/
├── FallOfTroy.py              # Main application
├── bundled_profiles/          # Default profiles
├── requirements.txt           # Python dependencies
├── build-appimage.sh         # AppImage build script
└── AppDir/                   # AppImage structure
    ├── AppRun                # Launcher script
    ├── FallOfTroy.desktop    # Desktop entry
    ├── FallOfTroy.png        # App icon
    └── usr/
        ├── bin/
        └── share/
```

## License

MIT License - See LICENSE file for details

## Credits

Made with ❤️ by [iamvetruvian](https://github.com/iamvetruvian)

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
