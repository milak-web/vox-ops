
import PyInstaller.__main__
import os
import shutil
import vosk

# Clean previous builds
if os.path.exists("build"):
    shutil.rmtree("build")
if os.path.exists("dist"):
    shutil.rmtree("dist")

print("Building VOX OPS Executable...")

# Get VOSK path and DLLs
vosk_dir = os.path.dirname(vosk.__file__)
dlls = [f for f in os.listdir(vosk_dir) if f.endswith('.dll')]
binaries = []
for dll in dlls:
    src = os.path.join(vosk_dir, dll)
    # Add to root AND vosk folder to be safe
    binaries.append(f'{src};.')
    binaries.append(f'{src};vosk')

# PyInstaller arguments
args = [
    'voxops.PY',                  # Main script
    '--name=VOX_OPS',             # Name of the executable
    '--onefile',                  # Single EXE file
    '--windowed',                 # No console window (GUI only)
    '--icon=vox_ops.ico',         # Icon file
    '--clean',                    # Clean cache
    '--noconfirm',                # Overwrite existing
    
    # CRITICAL FIX: Collect all data/binaries for VOSK
    '--collect-all=vosk',
    
    # Explicitly add binaries
] + [f'--add-binary={b}' for b in binaries] + [
    
    # Ensure other dynamic libraries are found
    '--hidden-import=pystray',
    '--hidden-import=PIL',
    '--hidden-import=pyautogui',
    '--hidden-import=keyboard',
    '--hidden-import=pygetwindow',
    '--hidden-import=engineio.async_drivers.threading',
]

try:
    PyInstaller.__main__.run(args)
    print("\nSUCCESS! Executable created in 'dist' folder: dist/VOX_OPS.exe")
except Exception as e:
    print(f"\nERROR: Build failed - {e}")
