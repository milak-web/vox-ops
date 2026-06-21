# VOX OPS

VOX OPS is a Windows desktop voice assistant built for low-latency, local-first control. It turns spoken phrases into macros, hotkeys, system actions, app launches, and spoken feedback while keeping speech recognition on-device with Vosk.

The project is aimed at gamers, streamers, and power users who want fast voice control without cloud processing or subscription lock-in.

## What VOX OPS does

- Maps voice triggers to keyboard shortcuts, mouse actions, app launches, URLs, delays, and text input
- Supports separate profiles for different games, tools, and workflows
- Uses local speech recognition models with a first-run model picker
- Offers push-to-talk, tray mode, startup launch, and an optional on-screen HUD overlay
- Lets users browse, install, and publish community command profiles
- Packages the desktop app as a standalone Windows executable with PyInstaller

## Best use cases

- Game-specific command layouts
- Stream and recording shortcuts
- Repetitive desktop automation
- Accessibility-friendly hands-free control

## Quick start

1. Download the latest Windows build from [Releases](https://github.com/milak-web/vox-ops/releases/latest).
2. Launch `VOX_OPS.exe`.
3. Choose a speech model during the first-run setup.
4. Load a preset or create your own profile.
5. Start listening and trigger commands by voice.

## Run from source

VOX OPS is Windows-first and expects a desktop Python environment with microphone access.

```bash
pip install customtkinter vosk pyautogui pyaudio keyboard pystray pillow pygetwindow pyttsx3
python voxops.PY
```

To build a standalone executable:

```bash
python build_exe.py
```

You can also build from the provided PyInstaller spec:

```bash
pyinstaller VOX_OPS.spec
```

## Project entrypoints

- `voxops.PY` - main desktop application
- `build_exe.py` - packaging helper for Windows builds
- `VOX_OPS.spec` - PyInstaller configuration
- `user_profiles/` - local command profiles

## Notes

- Recognition models are downloaded on demand and stored locally.
- Some integrations are optional and depend on Windows-only libraries such as tray, TTS, or keyboard hooks.
- The current release focus is the desktop client and profile workflow.

## License

MIT