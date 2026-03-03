import sys
import os
import json
import subprocess
from difflib import get_close_matches
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices


from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QTabWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QTextEdit,
    QDialog,
    QMessageBox,
    QGroupBox
)

from PySide6.QtWidgets import QCheckBox, QRadioButton, QButtonGroup
from PySide6.QtWidgets import QToolButton, QFileDialog
from PySide6.QtGui import QIcon


from PySide6.QtCore import Qt


# Determine base directory (AppImage or development)
if getattr(sys, '_MEIPASS', None):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

BUNDLED_PROFILES_DIR = os.path.join(BASE_DIR, "bundled_profiles")

CONFIG_DIR = os.path.expanduser("~/.config/project_daemon")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
PROFILES_DIR = os.path.join(CONFIG_DIR, "profiles")
DEFAULT_GIT_ENABLED = True
DEFAULT_GIT_VISIBILITY = "private"



def run_command(command, cwd, parent_widget, error_title):
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(
            parent_widget,
            error_title,
            f"Command failed:\n\n{' '.join(command)}\n\n{e.stderr}"
        )
        return False


import shutil

def detect_installed_editors():
    candidates = [
        ("VS Code", "code"),
        ("Zed", "zeditor"),
        ("Cursor", "cursor"),
        ("PyCharm", "pycharm"),
        ("Antigravity", "antigravity"),
    ]

    available = []

    for name, cmd in candidates:
        if shutil.which(cmd):
            available.append((name, cmd))

    return available

def show_loading_dialog(parent, message):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Please wait")
    dialog.setModal(True)
    dialog.setWindowFlags(
        Qt.Dialog |
        Qt.CustomizeWindowHint |
        Qt.WindowTitleHint
    )

    layout = QVBoxLayout(dialog)

    label = QLabel(message)
    label.setAlignment(Qt.AlignCenter)

    # 🔧 FIX: force readable text color
    label.setStyleSheet("""
        QLabel {
            color: white;
            font-size: 14px;
        }
    """)

    layout.addWidget(label)

    dialog.resize(380, 130)
    dialog.show()

    QApplication.processEvents()
    return dialog



def copy_bundled_profiles():
    """Copy bundled profiles to user config directory on first run."""
    os.makedirs(PROFILES_DIR, exist_ok=True)
    
    if not os.path.exists(BUNDLED_PROFILES_DIR):
        return
    
    for profile_file in os.listdir(BUNDLED_PROFILES_DIR):
        if profile_file.endswith(".sh"):
            src = os.path.join(BUNDLED_PROFILES_DIR, profile_file)
            dst = os.path.join(PROFILES_DIR, profile_file)
            
            # Only copy if it doesn't exist (don't overwrite user modifications)
            if not os.path.exists(dst):
                try:
                    with open(src, 'r') as f:
                        content = f.read()
                    with open(dst, 'w') as f:
                        f.write(content)
                    os.chmod(dst, 0o755)
                except Exception:
                    pass  # Silently fail if copy fails


def load_config():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    # Copy bundled profiles on first run or if profiles dir is empty
    copy_bundled_profiles()

    if not os.path.exists(CONFIG_FILE):
        default = {
            "last_parent_path": os.path.expanduser("~/Desktop"),
            "last_profile": None,
            "projects": {},
            "profile_git_prefs": {},
            "hide_profile_warning": False
        }

        with open(CONFIG_FILE, "w") as f:
            json.dump(default, f, indent=2)
        return default

    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    config.setdefault("profile_git_prefs", {})
    config.setdefault("preferred_editor", None)
    config.setdefault("hide_profile_warning", False)


    return config


def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_git_prefs_for_profile(config, profile):
    prefs = config.get("profile_git_prefs", {})
    if profile in prefs:
        return prefs[profile]

    return {
        "enabled": DEFAULT_GIT_ENABLED,
        "visibility": DEFAULT_GIT_VISIBILITY
    }

def show_profile_warning_if_needed(parent, config):
    if config.get("hide_profile_warning", False):
        return True

    dialog = QDialog(parent)
    dialog.setWindowTitle("Critical Warning!")
    dialog.setModal(True)
    dialog.resize(520, 260)

    layout = QVBoxLayout(dialog)

    warning_text = QLabel(
        "Profiles are shell scripts.\n\n"
        "Only install profiles from the official repo of this project.\n\n"
        "Third party profiles may execute malicious shell commands that "
        "could dangerously harm your system.\n\n"
        "Make sure you know what you are doing before installing arbitrary "
        "third-party profiles."
    )
    warning_text.setWordWrap(True)
    warning_text.setStyleSheet("font-size: 13px;")
    layout.addWidget(warning_text)

    dont_show_checkbox = QCheckBox("Don't show again")
    layout.addWidget(dont_show_checkbox)

    btn = QPushButton("I understand")
    btn.setDefault(True)
    layout.addWidget(btn)

    def accept_warning():
        if dont_show_checkbox.isChecked():
            config["hide_profile_warning"] = True
            save_config(config)
        dialog.accept()

    btn.clicked.connect(accept_warning)

    dialog.exec()
    return True


def save_git_prefs_for_profile(config, profile, enabled, visibility):
    config.setdefault("profile_git_prefs", {})
    config["profile_git_prefs"][profile] = {
        "enabled": enabled,
        "visibility": visibility
    }
    save_config(config)


def list_profiles():
    if not os.path.exists(PROFILES_DIR):
        return []

    profiles = []
    for f in os.listdir(PROFILES_DIR):
        if f.endswith(".sh"):
            profiles.append(f)

    profiles.sort()
    return profiles

def open_new_profile_dialog(parent, profile_dropdown, config):
    dialog = QDialog(parent)
    dialog.setWindowTitle("New Profile")
    dialog.resize(520, 420)

    main_layout = QVBoxLayout(dialog)

    tabs = QTabWidget()
    main_layout.addWidget(tabs)

    # ===============================
    # TAB 1: Create Profile
    # ===============================
    create_tab = QWidget()
    create_layout = QVBoxLayout(create_tab)

    create_layout.addWidget(QLabel("Profile Name"))
    name_input = QLineEdit()
    create_layout.addWidget(name_input)

    create_layout.addWidget(QLabel("Shell Script Content (Dangerous! Only enter trustified profile scripts)"))
    script_input = QTextEdit()
    script_input.setPlaceholderText(
        "#!/usr/bin/env bash\n"
        "set -e\n\n"
        "# Arguments:\n"
        "#   $1 = parent directory\n"
        "#   $2 = project name\n\n"
        "# This script is responsible for:\n"
        "# - creating the project folder\n"
        "# - setting up folder structure\n"
        "# - installing dependencies (npm/pip/etc)\n"
        "# - any language/runtime setup\n\n"
    )
    create_layout.addWidget(script_input)

    create_btn = QPushButton("Create Profile")
    create_layout.addWidget(create_btn)

    tabs.addTab(create_tab, "Create Profile")

    # ===============================
    # TAB 2: Download Profiles
    # ===============================
    download_tab = QWidget()
    download_layout = QVBoxLayout(download_tab)

    download_label = QLabel(
        'Coming Soon...<br><br>'
        'Till then you can check out profiles from the '
        '<a href="https://github.com/iamvetruvian/tryfall">GitHub</a> repo.'
    )
    download_label.setAlignment(Qt.AlignCenter)
    download_label.setOpenExternalLinks(True)
    download_label.setStyleSheet("""
        QLabel {
            font-size: 13px;
            color: gray;
        }
        QLabel a {
            color: #4ea1ff;
            text-decoration: none;
        }
        QLabel a:hover {
            text-decoration: underline;
        }
    """)

    download_layout.addWidget(download_label)

    tabs.addTab(download_tab, "Download Profiles")

    # ===============================
    # Create profile logic (unchanged)
    # ===============================
    def create_profile():
        name = name_input.text().strip()
        script = script_input.toPlainText().strip()

        if not name:
            QMessageBox.warning(dialog, "Error", "Profile name is required.")
            return

        filename = f"{name}.sh"
        path = os.path.join(PROFILES_DIR, filename)

        if os.path.exists(path):
            QMessageBox.warning(dialog, "Error", "Profile already exists.")
            return

        if not script:
            QMessageBox.warning(dialog, "Error", "Script content is required.")
            return

        if not script.startswith("#!"):
            script = "#!/usr/bin/env bash\nset -e\n\n" + script

        with open(path, "w") as f:
            f.write(script)

        os.chmod(path, 0o755)

        profile_dropdown.addItem(filename)
        profile_dropdown.setCurrentText(filename)

        config["last_profile"] = filename
        save_config(config)

        dialog.accept()

    create_btn.clicked.connect(create_profile)

    dialog.exec()


def execute_profile(
    project_name,
    parent_dir,
    profile,
    parent_widget,
    config,
    create_repo,
    visibility
):
    if not project_name:
        QMessageBox.warning(parent_widget, "Error", "Project name is required.")
        return

    parent_dir = os.path.expanduser(parent_dir)
    if not os.path.isdir(parent_dir):
        QMessageBox.warning(parent_widget, "Error", "Parent directory does not exist.")
        return

    if not profile:
        QMessageBox.warning(parent_widget, "Error", "No profile selected.")
        return

    profile_path = os.path.join(PROFILES_DIR, profile)
    if not os.path.isfile(profile_path):
        QMessageBox.warning(parent_widget, "Error", "Profile script not found.")
        return

    project_path = os.path.join(parent_dir, project_name)

    if os.path.exists(project_path):
        QMessageBox.warning(
            parent_widget,
            "Error",
            "Project directory already exists."
        )
        return

    loading_dialog = show_loading_dialog(
            parent_widget,
            "Please wait.\nWe are cooking something good..."
    )


    # 1. Execute profile script (folder structure)
    try:
        subprocess.run(
            [profile_path, parent_dir, project_name],
            check=True
        )
    except subprocess.CalledProcessError as e:
        QMessageBox.critical(
            parent_widget,
            "Profile Failed",
            f"Profile execution failed.\n\n{e}"
        )
        loading_dialog.close()
        return

    if create_repo:
        # 4. git init
        if not run_command(
            ["git", "init"],
            cwd=project_path,
            parent_widget=parent_widget,
            error_title="git init failed"
        ):
            loading_dialog.close()
            return

        # 5. git add .
        if not run_command(
            ["git", "add", "."],
            cwd=project_path,
            parent_widget=parent_widget,
            error_title="git add failed"
        ):
            loading_dialog.close()
            return

        # 6. git commit
        if not run_command(
            ["git", "commit", "-m", "Initialised project"],
            cwd=project_path,
            parent_widget=parent_widget,
            error_title="git commit failed"
        ):
            loading_dialog.close()
            return

        # Defensive check: ensure .git exists before GitHub step
        if not os.path.isdir(os.path.join(project_path, ".git")):
            QMessageBox.critical(
                parent_widget,
                "Git Error",
                "Local git repository not found. Aborting GitHub creation."
            )
            loading_dialog.close()
            return

        # 7. Create GitHub repo and push
        if not run_command(
            [
                "gh", "repo", "create", project_name,
                "--private",
                "--source=.",
                "--remote=origin",
                "--push",
            ],
            cwd=project_path,
            parent_widget=parent_widget,
            error_title="GitHub repo creation failed"
        ):
            loading_dialog.close()
            return

    loading_dialog.close()
    # Save project in registry
    config.setdefault("projects", {})
    config["projects"][project_name] = project_path
    save_config(config)

    try:
        editor_cmd = config.get("preferred_editor")

        if editor_cmd:
            try:
                subprocess.Popen([editor_cmd, project_path])
            except Exception:
                pass
    except Exception:
        pass

    QApplication.quit()


def find_closest_project(name, projects):
    if not projects:
        return None
    matches = get_close_matches(name, projects.keys(), n=1, cutoff=0.3)
    return matches[0] if matches else None



def main():
    app = QApplication(sys.argv)

    config = load_config()

    window = QWidget()
    window.setWindowTitle("Project Daemon")
    window.resize(600, 300)

    layout = QVBoxLayout(window)

    tabs = QTabWidget()

    new_tab = QWidget()
    existing_tab = QWidget()

    new_tab_layout = QVBoxLayout(new_tab)
    existing_tab_layout = QVBoxLayout(existing_tab)


    # Project name
    row1 = QHBoxLayout()
    row1.addWidget(QLabel("Project Name"))
    project_name_input = QLineEdit()
    row1.addWidget(project_name_input)
    new_tab_layout.addLayout(row1)

    # Parent directory
    row2 = QHBoxLayout()
    row2.addWidget(QLabel("Parent Directory"))
    parent_dir_input = QLineEdit(config["last_parent_path"])
    row2.addWidget(parent_dir_input)
    browse_btn = QToolButton()
    browse_btn.setIcon(QIcon.fromTheme("folder"))
    browse_btn.setToolTip("Select parent directory")
    row2.addWidget(browse_btn)
    new_tab_layout.addLayout(row2)

    def browse_parent_directory():
        directory = QFileDialog.getExistingDirectory(
            window,
            "Select Parent Directory",
            parent_dir_input.text() or os.path.expanduser("~")
        )

        if directory:
            parent_dir_input.setText(directory)
            config["last_parent_path"] = directory
            save_config(config)

    browse_btn.clicked.connect(browse_parent_directory)

    # Profile selection
    row3 = QHBoxLayout()
    row3.addWidget(QLabel("Profile"))
    open_profiles_btn = QToolButton()
    open_profiles_btn.setIcon(QIcon.fromTheme("folder"))
    open_profiles_btn.setToolTip("Open profiles folder")
    row3.addWidget(open_profiles_btn)
    profile_dropdown = QComboBox()

    profiles = list_profiles()
    profile_dropdown.addItems(profiles)

    if profiles:
        if config.get("last_profile") in profiles:
            profile_dropdown.setCurrentText(config["last_profile"])
        else:
            # Force-select first profile and persist it
            profile_dropdown.setCurrentIndex(0)
            config["last_profile"] = profiles[0]
            save_config(config)
    new_profile_btn = QToolButton()
    new_profile_btn.setIcon(QIcon.fromTheme("list-add"))
    new_profile_btn.setToolTip("Create new profile")

    row3.addWidget(new_profile_btn)

    row3.addWidget(profile_dropdown)
    new_tab_layout.addLayout(row3)
    def open_profiles_folder():
        file_managers = [
            ["thunar", PROFILES_DIR],
            ["nautilus", PROFILES_DIR],
            ["dolphin", PROFILES_DIR],
            ["pcmanfm", PROFILES_DIR],
            ["gio", "open", PROFILES_DIR],
            ["nemo", PROFILES_DIR]
        ]

        for cmd in file_managers:
            try:
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                return
            except FileNotFoundError:
                continue
            except subprocess.CalledProcessError:
                continue

        QMessageBox.critical(
            window,
            "Error",
            "No graphical file manager found on this system."
        )

    open_profiles_btn.clicked.connect(open_profiles_folder)
    # def open_profiles_folder():
    #     QMessageBox.information(
    #         window,
    #         "Debug",
    #         f"Profiles dir:\n{PROFILES_DIR}"
    #     )

    # Display options to choose IDE (or select an IDE by default):
    editor_group_box = QGroupBox("Choose Editor")
    editor_layout = QVBoxLayout(editor_group_box)

    editor_button_group = QButtonGroup()
    editor_buttons = {}

    available_editors = detect_installed_editors()

    for name, cmd in available_editors:
        radio = QRadioButton(name)
        editor_layout.addWidget(radio)
        editor_button_group.addButton(radio)
        editor_buttons[cmd] = radio

    new_tab_layout.addWidget(editor_group_box)

    preferred = config.get("preferred_editor")

    # 1. If previously selected exists → use it
    if preferred in editor_buttons:
        editor_buttons[preferred].setChecked(True)

    # 2. Else if VS Code exists → default to it
    elif "code" in editor_buttons:
        editor_buttons["code"].setChecked(True)

    # 3. Else pick first available
    elif available_editors:
        first_cmd = available_editors[0][1]
        editor_buttons[first_cmd].setChecked(True)
    
    def on_editor_selected():
        for cmd, btn in editor_buttons.items():
            if btn.isChecked():
                config["preferred_editor"] = cmd
                save_config(config)
                break

    editor_button_group.buttonClicked.connect(on_editor_selected)

    # GitHub options
    git_checkbox = QCheckBox("Create a GitHub repository")
    def on_git_checkbox_toggle(state):
        visibility_container.setVisible(state)

        profile = profile_dropdown.currentText()
        if not profile:
            return

        save_git_prefs_for_profile(
            config,
            profile,
            state,
            "public" if public_radio.isChecked() else "private"
        )

    git_checkbox.stateChanged.connect(on_git_checkbox_toggle)

    new_tab_layout.addWidget(git_checkbox)

    visibility_container = QWidget()
    visibility_layout = QHBoxLayout(visibility_container)

    private_radio = QRadioButton("Private")
    public_radio = QRadioButton("Public")

    private_radio.setChecked(True)
    def on_visibility_change():
        profile = profile_dropdown.currentText()
        if not profile:
            return

        save_git_prefs_for_profile(
            config,
            profile,
            git_checkbox.isChecked(),
            "public" if public_radio.isChecked() else "private"
        )

    private_radio.toggled.connect(on_visibility_change)
    public_radio.toggled.connect(on_visibility_change)

    visibility_group = QButtonGroup()
    visibility_group.addButton(private_radio)
    visibility_group.addButton(public_radio)

    visibility_layout.addWidget(QLabel("Visibility"))
    visibility_layout.addWidget(private_radio)
    visibility_layout.addWidget(public_radio)

    visibility_container.setVisible(False)
    new_tab_layout.addWidget(visibility_container)

    def toggle_visibility_options(state):
        visibility_container.setVisible(state)

    git_checkbox.stateChanged.connect(toggle_visibility_options)


    # New Profile button
    # new_profile_btn = QPushButton("New Profile")
    # new_tab_layout.addWidget(new_profile_btn)

    def on_new_profile_clicked():
        show_profile_warning_if_needed(window, config)
        open_new_profile_dialog(window, profile_dropdown, config)

    new_profile_btn.clicked.connect(on_new_profile_clicked)


    # Create Project button
    create_project_btn = QPushButton("Create Project")
    new_tab_layout.addWidget(create_project_btn)

    def on_create_project():
        execute_profile(
            project_name_input.text().strip(),
            parent_dir_input.text().strip(),
            profile_dropdown.currentText(),
            window,
            config,
            git_checkbox.isChecked(),
            "private" if private_radio.isChecked() else "public"
        )



    create_project_btn.clicked.connect(on_create_project)


    def on_profile_change(profile):
        config["last_profile"] = profile

        prefs = get_git_prefs_for_profile(config, profile)

        git_checkbox.setChecked(prefs["enabled"])
        visibility_container.setVisible(prefs["enabled"])

        if prefs["visibility"] == "public":
            public_radio.setChecked(True)
        else:
            private_radio.setChecked(True)

        save_config(config)


    profile_dropdown.currentTextChanged.connect(on_profile_change)

    from PySide6.QtCore import QSignalBlocker

    def update_existing_suggestions(text):
        if not text:
            return

        projects = config.get("projects", {})
        if not projects:
            return

        matches = get_close_matches(
            text,
            projects.keys(),
            n=5,
            cutoff=0.2
        )

        line_edit = existing_project_input.lineEdit()

        blocker = QSignalBlocker(line_edit)

        # Save cursor position
        cursor_pos = line_edit.cursorPosition()

        existing_project_input.clear()
        existing_project_input.addItems(matches)
        existing_project_input.setEditText(text)

        # Restore cursor + focus
        line_edit.setCursorPosition(cursor_pos)
        line_edit.setFocus()




    def open_existing_project():
        name = existing_project_input.currentText().strip()
        if not name:
            QMessageBox.warning(window, "Error", "Project name is required.")
            return

        projects = config.get("projects", {})
        match = find_closest_project(name, projects)

        if not match:
            QMessageBox.warning(window, "Not Found", "No matching project found.")
            return

        path = projects[match]

        try:
            editor_cmd = config.get("preferred_editor")

            if editor_cmd:
                try:
                    subprocess.Popen([editor_cmd, project_path])
                except Exception:
                    pass
            QApplication.quit()
        except Exception:
            QMessageBox.warning(window, "Error", "Failed to open editor.")



    # Existing project input
    existing_row = QHBoxLayout()
    existing_row.addWidget(QLabel("Project Name"))
    existing_project_input = QComboBox()
    existing_project_input.setEditable(True)
    existing_project_input.setInsertPolicy(QComboBox.NoInsert)

    existing_project_input.lineEdit().textChanged.connect(
        update_existing_suggestions
    )

    existing_project_input.activated.connect(
        lambda _: open_existing_project()
    )

    existing_row.addWidget(existing_project_input)
    existing_tab_layout.addLayout(existing_row)

    # Open button
    open_project_btn = QPushButton("Open Project")
    open_project_btn.clicked.connect(open_existing_project)
    existing_tab_layout.addWidget(open_project_btn)


    tabs.addTab(new_tab, "New")
    tabs.addTab(existing_tab, "Existing")

    tabs.setCurrentIndex(0)

    footer = QLabel(
        'Made with ❤️ by <a href="https://github.com/iamvetruvian">iamvetruvian</a>'
    )
    footer.setAlignment(Qt.AlignCenter)
    footer.setOpenExternalLinks(True)
    footer.setStyleSheet("""
        QLabel {
            font-size: 11px;
            color: gray;
        }
        QLabel a {
            color: #4ea1ff;
            text-decoration: none;
        }
        QLabel a:hover {
            text-decoration: underline;
        }
    """)

    layout.addWidget(footer)


    layout.addWidget(tabs)

    window.setLayout(layout)
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
