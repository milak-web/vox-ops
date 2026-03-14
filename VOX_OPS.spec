# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = []
binaries = [('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libgcc_s_seh-1.dll', '.'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libgcc_s_seh-1.dll', 'vosk'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libstdc++-6.dll', '.'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libstdc++-6.dll', 'vosk'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libvosk.dll', '.'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libvosk.dll', 'vosk'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libwinpthread-1.dll', '.'), ('C:\\Users\\MK2\\Desktop\\PRO\\.venv\\Lib\\site-packages\\vosk\\libwinpthread-1.dll', 'vosk')]
hiddenimports = ['pystray', 'PIL', 'pyautogui', 'keyboard', 'pygetwindow', 'engineio.async_drivers.threading']
tmp_ret = collect_all('vosk')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['voxops.PY'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VOX_OPS',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['vox_ops.ico'],
)
