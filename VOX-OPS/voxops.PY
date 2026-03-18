import customtkinter as ctk
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import socket
import threading
import pyautogui
import json
import time
import os
import sys
import pyaudio
import zipfile
import urllib.request
import urllib.error
import shutil
import webbrowser
import subprocess
import struct
import math
import random
import base64
import io
import re
import logging

# --- FIX: VOSK DLL Loading for PyInstaller ---
if getattr(sys, 'frozen', False):
    import ctypes
    import logging
    
    # Setup debug logging for startup
    logging.basicConfig(filename="voxops_debug.log", level=logging.DEBUG, 
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logging.info("Starting VOSK DLL fix...")
    
    base_dir = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.dirname(os.path.abspath(__file__))
    logging.info(f"Base dir: {base_dir}")
    
    # List files for debug
    try:
        logging.info(f"Files in base: {os.listdir(base_dir)}")
        vosk_sub = os.path.join(base_dir, 'vosk')
        if os.path.exists(vosk_sub):
            logging.info(f"Files in vosk subdir: {os.listdir(vosk_sub)}")
    except Exception as e:
        logging.error(f"Failed to list files: {e}")

    # Add paths
    paths_to_add = [base_dir, os.path.join(base_dir, 'vosk')]
    for p in paths_to_add:
        if os.path.exists(p):
            os.environ['PATH'] += os.pathsep + p
            if hasattr(os, 'add_dll_directory'):
                try:
                    os.add_dll_directory(p)
                    logging.info(f"Added DLL dir: {p}")
                except Exception as e:
                    logging.error(f"Failed to add DLL dir {p}: {e}")

    # Load dependencies explicitly
    dlls = ['libwinpthread-1.dll', 'libgcc_s_seh-1.dll', 'libstdc++-6.dll']
    for dll in dlls:
        # Try finding in root then vosk folder
        found = False
        for search_path in paths_to_add:
            full_path = os.path.join(search_path, dll)
            if os.path.exists(full_path):
                try:
                    ctypes.CDLL(full_path)
                    logging.info(f"Successfully loaded {dll} from {full_path}")
                    found = True
                    break
                except Exception as e:
                    logging.error(f"Failed to load {dll} from {full_path}: {e}")
        if not found:
            logging.warning(f"Could not find/load dependency: {dll}")

    # Monkeypatch
    if hasattr(os, 'add_dll_directory'):
        _original_add_dll = os.add_dll_directory
        def _safe_add_dll_directory(path):
            try:
                if os.path.exists(path):
                    return _original_add_dll(path)
            except Exception:
                pass
            return None
        os.add_dll_directory = _safe_add_dll_directory

try:
    from vosk import Model, KaldiRecognizer
except Exception as e:
    # Log full error to file for debugging
    import traceback
    with open("voxops_error.log", "w") as f:
        f.write(traceback.format_exc())
        
    # Fallback for build errors
    print(f"CRITICAL ERROR: Failed to import VOSK. {e}")
    try:
        import tkinter.messagebox
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        tkinter.messagebox.showerror("Critical Build Error", 
            f"Failed to load VOSK library.\n\nError: {e}\n\n"
            "A detailed error log has been written to 'voxops_error.log'.\n"
            "Please ensure 'vosk' folder is correctly bundled.")
    except:
        pass
    sys.exit(1)

# --- CONFIG ---
QR_CODE_BASE64 = "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" # Paste your base64 string here to embed the QR code permanently


# --- DEPENDENCIES ---
try:
    import keyboard
    PTT_AVAILABLE = True
except ImportError:
    PTT_AVAILABLE = False
    print("Warning: 'keyboard' module missing. PTT unavailable.")

try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

try:
    import pygetwindow as gw
    CONTEXT_AVAILABLE = True
except ImportError:
    CONTEXT_AVAILABLE = False

try:
    import winsound
    SFX_AVAILABLE = True
except ImportError:
    SFX_AVAILABLE = False

try:
    import pyttsx3
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

# Windows Registry for Startup
try:
    import winreg
    REGISTRY_AVAILABLE = True
except ImportError:
    REGISTRY_AVAILABLE = False

# --- Configuration ---
APP_TITLE = "VOX OPS // SYSTEM OVERRIDE"
APP_SIZE = "1150x780"
SETTINGS_FILE = "user_settings.json"
PROFILES_DIR = "user_profiles"

# --- Modern Theme Palette ---
COLOR_BG = "#1e1e1e"
COLOR_SIDEBAR = "#252526"
COLOR_CARD = "#2d2d30"
COLOR_ACCENT = "#007acc"
COLOR_ACCENT_HOVER = "#005f9e"
COLOR_SUCCESS = "#3fb950"
COLOR_SUCCESS_HOVER = "#2ea043"
COLOR_DANGER = "#f85149"
COLOR_TEXT_MAIN = "#ffffff"
COLOR_TEXT_SUB = "#8b949e"
COLOR_BORDER = "#30363d"
COLOR_TOOLTIP_BG = "#202020"
COLOR_TOOLTIP_BORDER = "#404040"

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Function to set process priority to High to prevent throttling
def _set_high_priority():
    if sys.platform == "win32":
        try:
            import ctypes
            # HIGH_PRIORITY_CLASS = 0x00000080
            # ABOVE_NORMAL_PRIORITY_CLASS = 0x00008000
            process = ctypes.windll.kernel32.GetCurrentProcess()
            if ctypes.windll.kernel32.SetPriorityClass(process, 0x00000080):
                logging.info("Process priority set to HIGH.")
            else:
                logging.warning("Failed to set process priority.")
        except Exception as e:
            logging.error(f"Error setting priority: {e}")

# Function to disable exclusive mode for microphone devices
def _disable_exclusive_mode():
    _set_high_priority() # Ensure high priority when doing this
    try:
        # PowerShell command to disable exclusive mode for all audio capture devices
        # It sets the value of the registry key "{b3f8fa53-0004-438e-9003-51a46e139bfc},3" to 0
        # for all audio capture device properties. This key controls "Allow applications to take exclusive control of this device".
        powershell_command = r"""
$ErrorActionPreference = "SilentlyContinue"
Get-ItemProperty -Path "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\MMDevices\Audio\Capture\*\*\Properties" -Name "{b3f8fa53-0004-438e-9003-51a46e139bfc},3" | ForEach-Object {
    Set-ItemProperty -LiteralPath $_.PSPath -Name "{b3f8fa53-0004-438e-9003-51a46e139bfc},3" -Value 0 -Force
}
"""
        # Execute the PowerShell command.
        # Requires administrative privileges to modify HKLM.
        # '-WindowStyle Hidden' prevents a PowerShell window from flashing.
        # '-EncodedCommand' is used to run complex commands more reliably.
        
        # Check if the script is running with administrative privileges
        if sys.platform == "win32":
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                # logging.warning("Disabling exclusive mode requires administrative privileges. Skipping.")
                # For now, we'll proceed and let the PowerShell command fail gracefully if not admin.
                # The user will need to run the app as admin for this to work.
                pass 

        logging.info("Attempting to disable exclusive mode for microphone devices...")
        
        process = subprocess.run(
            ["powershell.exe", "-Command", powershell_command],
            capture_output=True,
            text=True,
            check=True, # Raise an exception for non-zero exit codes
            encoding='utf8'
        )
        
        if process.stdout:
            logging.info(f"PowerShell output: {process.stdout.strip()}")
        if process.stderr:
            logging.error(f"PowerShell error: {process.stderr.strip()}")
        
        logging.info("Exclusive mode disable attempt completed.")

    except subprocess.CalledProcessError as e:
        logging.error(f"PowerShell command failed with error: {e}")
        logging.error(f"Stdout: {e.stdout}")
        logging.error(f"Stderr: {e.stderr}")
    except Exception as e:
        logging.error(f"An unexpected error occurred while trying to disable exclusive mode: {e}")

# --- GLOBAL MODEL DATABASE ---
VOSK_MODELS = {
    "English": {
        "Lightweight (Fast)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip",
            "folder": "vosk-model-small-en-us-0.15",
            "path": "model_en_light",
            "size": "40 MB",
            "ram": "~200 MB",
            "desc": "Best for: Gaming & Fast Commands.\nBehavior: Instant response, low CPU usage."
        },
        "Pro (High Accuracy)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.22.zip",
            "folder": "vosk-model-en-us-0.22",
            "path": "model_en_pro",
            "size": "1.8 GB",
            "ram": "~2-4 GB",
            "desc": "Best for: Dictation & Complex Macros.\nBehavior: Very high accuracy."
        },
        "Pro (Technical/Daanzu)": {
             "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-daanzu-20200905.zip",
             "folder": "vosk-model-en-us-daanzu-20200905",
             "path": "model_en_daanzu",
             "size": "1.0 GB",
             "ram": "~2 GB",
             "desc": "Best for: Technical/Medical Terms."
        },
        "Indian English (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-en-in-0.5.zip",
            "folder": "vosk-model-en-in-0.5",
            "path": "model_en_in",
            "size": "1 GB",
            "ram": "~1.5 GB",
            "desc": "Best for: Indian English Accents."
        },
        "Indian English (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-en-in-0.4.zip",
            "folder": "vosk-model-small-en-in-0.4",
            "path": "model_en_in_small",
            "size": "36 MB",
            "ram": "~200 MB",
            "desc": "Lightweight Indian English model."
        },
        "GigaSpeech (Ultra)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-en-us-0.42-gigaspeech.zip",
            "folder": "vosk-model-en-us-0.42-gigaspeech",
            "path": "model_en_giga",
            "size": "2.3 GB",
            "ram": "~3 GB",
            "desc": "Best for: Podcasts & varied audio."
        }
    },
    "Chinese": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-cn-0.22.zip",
            "folder": "vosk-model-small-cn-0.22",
            "path": "model_cn_light",
            "size": "42 MB",
            "ram": "~200 MB",
            "desc": "Lightweight model for Android and RPi"
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-cn-0.22.zip",
            "folder": "vosk-model-cn-0.22",
            "path": "model_cn_pro",
            "size": "1.3 GB",
            "ram": "~2 GB",
            "desc": "Big generic Chinese model for server processing"
        },
        "MultiCN (Kaldi)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-cn-kaldi-multicn-0.15.zip",
            "folder": "vosk-model-cn-kaldi-multicn-0.15",
            "path": "model_cn_multicn",
            "size": "1.5 GB",
            "ram": "~2 GB",
            "desc": "Original Wideband Kaldi multi-cn model"
        }
    },
    "Russian": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip",
            "folder": "vosk-model-small-ru-0.22",
            "path": "model_ru_light",
            "size": "45 MB",
            "ram": "~200 MB",
            "desc": "Lightweight wideband model"
        },
        "Pro (Big v0.42)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ru-0.42.zip",
            "folder": "vosk-model-ru-0.42",
            "path": "model_ru_pro_42",
            "size": "1.8 GB",
            "ram": "~2 GB",
            "desc": "Big mixed band Russian model (Newest)"
        },
        "Pro (Big v0.22)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ru-0.22.zip",
            "folder": "vosk-model-ru-0.22",
            "path": "model_ru_pro_22",
            "size": "1.5 GB",
            "ram": "~2 GB",
            "desc": "Big mixed band Russian model (Older)"
        },
        "Server (Big v0.10)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ru-0.10.zip",
            "folder": "vosk-model-ru-0.10",
            "path": "model_ru_server",
            "size": "2.5 GB",
            "ram": "~3 GB",
            "desc": "Big narrowband Russian model"
        }
    },
    "French": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-0.22.zip",
            "folder": "vosk-model-small-fr-0.22",
            "path": "model_fr_light",
            "size": "41 MB",
            "ram": "~200 MB",
            "desc": "Lightweight wideband model"
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-fr-0.22.zip",
            "folder": "vosk-model-fr-0.22",
            "path": "model_fr_pro",
            "size": "1.4 GB",
            "ram": "~2 GB",
            "desc": "Big accurate model for servers"
        },
        "Linto (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-fr-0.6-linto-2.2.0.zip",
            "folder": "vosk-model-fr-0.6-linto-2.2.0",
            "path": "model_fr_linto",
            "size": "1.5 GB",
            "ram": "~2 GB",
            "desc": "Model from LINTO project"
        },
        "Guyot (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-fr-pguyot-0.3.zip",
            "folder": "vosk-model-small-fr-pguyot-0.3",
            "path": "model_fr_guyot",
            "size": "39 MB",
            "ram": "~200 MB",
            "desc": "Alternative small model"
        }
    },
    "German": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-de-0.15.zip",
            "folder": "vosk-model-small-de-0.15",
            "path": "model_de_light",
            "size": "45 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast German Commands."
        },
        "Pro (Standard)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-de-0.21.zip",
            "folder": "vosk-model-de-0.21",
            "path": "model_de_pro",
            "size": "1.9 GB",
            "ram": "~2 GB",
            "desc": "Big German model for telephony and server"
        },
        "Tuda (Ultra)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-de-tuda-0.6-900k.zip",
            "folder": "vosk-model-de-tuda-0.6-900k",
            "path": "model_de_tuda",
            "size": "4.4 GB",
            "ram": "~4 GB",
            "desc": "Latest big wideband model from Tuda-DE project"
        }
    },
    "Spanish": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip",
            "folder": "vosk-model-small-es-0.42",
            "path": "model_es_light",
            "size": "39 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Spanish Commands."
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-es-0.42.zip",
            "folder": "vosk-model-es-0.42",
            "path": "model_es_pro",
            "size": "1.4 GB",
            "ram": "~2 GB",
            "desc": "Big model for Spanish"
        }
    },
    "Italian": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-it-0.22.zip",
            "folder": "vosk-model-small-it-0.22",
            "path": "model_it_light",
            "size": "48 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Italian Commands."
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-it-0.22.zip",
            "folder": "vosk-model-it-0.22",
            "path": "model_it_pro",
            "size": "1.2 GB",
            "ram": "~2 GB",
            "desc": "Big generic Italian model for servers"
        }
    },
    "Japanese": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-ja-0.22.zip",
            "folder": "vosk-model-small-ja-0.22",
            "path": "model_ja_light",
            "size": "49 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Japanese Commands."
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ja-0.22.zip",
            "folder": "vosk-model-ja-0.22",
            "path": "model_ja_pro",
            "size": "1 GB",
            "ram": "~1.5 GB",
            "desc": "Big model for Japanese"
        }
    },
    "Portuguese": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip",
            "folder": "vosk-model-small-pt-0.3",
            "path": "model_pt_light",
            "size": "31 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Portuguese Commands."
        },
        "FalaBrazil (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-pt-fb-v0.1.1-20220516_2113.zip",
            "folder": "vosk-model-pt-fb-v0.1.1-20220516_2113",
            "path": "model_pt_fb",
            "size": "1.6 GB",
            "ram": "~2 GB",
            "desc": "Big model from FalaBrazil"
        }
    },
    "Turkish": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-tr-0.3.zip",
            "folder": "vosk-model-small-tr-0.3",
            "path": "model_tr_light",
            "size": "35 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Turkish Commands."
        }
    },
    "Vietnamese": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-vn-0.4.zip",
            "folder": "vosk-model-small-vn-0.4",
            "path": "model_vn_light",
            "size": "32 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Vietnamese Commands."
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-vn-0.4.zip",
            "folder": "vosk-model-vn-0.4",
            "path": "model_vn_pro",
            "size": "78 MB",
            "ram": "~500 MB",
            "desc": "Bigger Vietnamese model for server"
        }
    },
    "Hindi": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-hi-0.22.zip",
            "folder": "vosk-model-small-hi-0.22",
            "path": "model_hi_light",
            "size": "42 MB",
            "ram": "~200 MB",
            "desc": "Best for: Fast Hindi Commands."
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-hi-0.22.zip",
            "folder": "vosk-model-hi-0.22",
            "path": "model_hi_pro",
            "size": "1.5 GB",
            "ram": "~2 GB",
            "desc": "Big accurate model for servers"
        }
    },
    "Ukrainian": {
        "Nano": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-uk-v3-nano.zip",
            "folder": "vosk-model-small-uk-v3-nano",
            "path": "model_uk_nano",
            "size": "73 MB",
            "ram": "~300 MB",
            "desc": "Nano model from Speech Recognition for Ukrainian"
        },
        "Small": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-uk-v3-small.zip",
            "folder": "vosk-model-small-uk-v3-small",
            "path": "model_uk_small",
            "size": "133 MB",
            "ram": "~400 MB",
            "desc": "Small model from Speech Recognition for Ukrainian"
        },
        "Big (v3)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-uk-v3.zip",
            "folder": "vosk-model-uk-v3",
            "path": "model_uk_big",
            "size": "343 MB",
            "ram": "~1 GB",
            "desc": "Bigger model from Speech Recognition for Ukrainian"
        },
        "Dynamic (LGraph)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-uk-v3-lgraph.zip",
            "folder": "vosk-model-uk-v3-lgraph",
            "path": "model_uk_lgraph",
            "size": "325 MB",
            "ram": "~1 GB",
            "desc": "Big dynamic model from Speech Recognition for Ukrainian"
        }
    },
    "Farsi": {
        "Pro (Big 0.42)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-fa-0.42.zip",
            "folder": "vosk-model-fa-0.42",
            "path": "model_fa_pro",
            "size": "1.6 GB",
            "ram": "~2 GB",
            "desc": "Model with large vocabulary"
        },
        "Lightweight (Small 0.42)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-fa-0.42.zip",
            "folder": "vosk-model-small-fa-0.42",
            "path": "model_fa_light",
            "size": "53 MB",
            "ram": "~300 MB",
            "desc": "Small model for desktop and mobile"
        }
    },
    "Arabic": {
        "Pro (MGB2)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ar-mgb2-0.4.zip",
            "folder": "vosk-model-ar-mgb2-0.4",
            "path": "model_ar_pro",
            "size": "318 MB",
            "ram": "~1 GB",
            "desc": "Best for: General Arabic Speech."
        },
        "Linto (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ar-0.22-linto-1.1.0.zip",
            "folder": "vosk-model-ar-0.22-linto-1.1.0",
            "path": "model_ar_linto",
            "size": "1.3 GB",
            "ram": "~2 GB",
            "desc": "Big model from LINTO project"
        },
        "Tunisian (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-ar-tn-0.1-linto.zip",
            "folder": "vosk-model-small-ar-tn-0.1-linto",
            "path": "model_ar_tn_small",
            "size": "158 MB",
            "ram": "~500 MB",
            "desc": "Small Arabic Tunisian model"
        },
        "Tunisian (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-ar-tn-0.1-linto.zip",
            "folder": "vosk-model-ar-tn-0.1-linto",
            "path": "model_ar_tn_big",
            "size": "517 MB",
            "ram": "~1 GB",
            "desc": "Arabic Tunisian model"
        }
    },
    "Dutch": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-nl-0.22.zip",
            "folder": "vosk-model-small-nl-0.22",
            "path": "model_nl_light",
            "size": "39 MB",
            "ram": "~200 MB",
            "desc": "Lightweight model for Dutch"
        },
        "Kaldi_NL (Medium)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-nl-spraakherkenning-0.6.zip",
            "folder": "vosk-model-nl-spraakherkenning-0.6",
            "path": "model_nl_kaldi",
            "size": "860 MB",
            "ram": "~1.5 GB",
            "desc": "Medium Dutch model from Kaldi_NL"
        }
    },
    "Kazakh": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-kz-0.42.zip",
            "folder": "vosk-model-small-kz-0.42",
            "path": "model_kz_light",
            "size": "58 MB",
            "ram": "~300 MB",
            "desc": "Small mobile model for Kazakh"
        },
        "Pro (Big)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-kz-0.42.zip",
            "folder": "vosk-model-kz-0.42",
            "path": "model_kz_pro",
            "size": "1.3 GB",
            "ram": "~2 GB",
            "desc": "Bigger model for Kazakh"
        }
    },
    "Korean": {
        "Lightweight (Small)": {
            "url": "https://alphacephei.com/vosk/models/vosk-model-small-ko-0.22.zip",
            "folder": "vosk-model-small-ko-0.22",
            "path": "model_ko_light",
            "size": "82 MB",
            "ram": "~300 MB",
            "desc": "Lightweight model for Korean"
        }
    }
}

# --- MOCK COMMUNITY DATA ---
COMMUNITY_PROFILES = [
    {
        "name": "Elite Dangerous Commander Pack",
        "author": "Cmdr Jameson",
        "desc": "Essential ship controls: landing gear, hardpoints, power distribution, and FSD jumps.",
        "commands": {
            "landing gear": "press:l",
            "deploy hardpoints": "press:u",
            "engage drive": "press:j",
            "full power engines": "press:up;press:up;press:up",
            "full power shields": "press:left;press:left;press:left"
        }
    },
    {
        "name": "Photoshop Workflow",
        "author": "CreativePro",
        "desc": "Speed up editing with voice layers. Create layers, merge, save for web, and undo.",
        "commands": {
            "new layer": "hotkey:ctrl+shift+n",
            "merge layers": "hotkey:ctrl+e",
            "save for web": "hotkey:ctrl+alt+shift+s",
            "undo that": "hotkey:ctrl+z"
        }
    },
    {
        "name": "Streamer Deck",
        "author": "TwitchMaster",
        "desc": "OBS Controls. Switch scenes, mute mic, start/stop recording hands-free.",
        "commands": {
            "scene chatting": "hotkey:f1",
            "scene game": "hotkey:f2",
            "mute stream": "hotkey:ctrl+m",
            "start recording": "hotkey:ctrl+f9"
        }
    },
    {
        "name": "Minecraft Survival",
        "author": "BlockBuilder",
        "desc": "Quick inventory management and chat commands for survival mode.",
        "commands": {
            "open inventory": "press:e",
            "drop item": "press:q",
            "chat list": "press:t",
            "screenshot": "press:f2"
        }
    },
    {
        "name": "Developer Essentials",
        "author": "CodeNinja",
        "desc": "VS Code and Terminal shortcuts. Git commit, run tests, format document.",
        "commands": {
            "git commit": "type:git commit -m ",
            "format code": "hotkey:shift+alt+f",
            "run tests": "type:npm test;press:enter",
            "quick fix": "hotkey:ctrl+."
        }
    }
]

# --- TEMPLATES FOR "ADD COMMAND" ---
MACRO_TEMPLATES = {
    "Manual Input (Custom)": {
        "Press Single Key...": "press:KEY_NAME",
        "Type Text...": "type:YOUR_TEXT_HERE",
        "Hotkey Combo...": "hotkey:CTRL+KEY",
        "Wait/Delay...": "wait:SECONDS"
    },
    "Power & System": {
        "Shutdown PC": "system:shutdown",
        "Restart PC": "system:restart",
        "Sleep PC": "system:sleep",
        "Lock PC": "system:lock",
        "Empty Recycle Bin": "system:empty_bin"
    },
    "General": {
        "Stop Listening (Sleep)": "internal:stop_listening",
        "Say Greeting": "say:Systems online commander|Welcome back, pilot|Interface ready",
        "Wait 1 Second": "wait:1.0"
    },
    "System Volume": {
        "Volume Mute": "press:volumemute",
        "Volume Up": "press:volumeup",
        "Volume Down": "press:volumedown"
    },
    "Windows Actions": {
        "Copy (Ctrl+C)": "hotkey:ctrl+c",
        "Paste (Ctrl+V)": "hotkey:ctrl+v",
        "Close Window (Alt+F4)": "hotkey:alt+f4",
        "Switch Window (Alt+Tab)": "hotkey:alt+tab",
        "Task Manager": "hotkey:ctrl+shift+esc",
        "Show Desktop": "hotkey:win+d",
        "Snap Left": "hotkey:win+left",
        "Snap Right": "hotkey:win+right"
    },
    "Internet": {
        "Open Google": "browser:google.com",
        "Open YouTube": "browser:youtube.com",
        "New Tab": "hotkey:ctrl+t",
        "Close Tab": "hotkey:ctrl+w"
    },
    "Apps": {
        "Open Notepad": "app:notepad",
        "Open Calculator": "app:calc"
    }
}

# Pre-defined Profiles
PRESETS = {
    "Windows System": {
        "volume up": "press:volumeup",
        "volume down": "press:volumedown",
        "mute audio": "press:volumemute",
        "minimize window": "hotkey:win+down",
        "maximize window": "hotkey:win+up",
        "copy selection": "hotkey:ctrl+c",
        "paste selection": "hotkey:ctrl+v",
        "show desktop": "hotkey:win+d",
        "stop listening": "internal:stop_listening"
    },
    "Browser Control": {
        "new tab": "hotkey:ctrl+t",
        "close tab": "hotkey:ctrl+w",
        "refresh page": "press:f5",
        "open google": "browser:google.com"
    },
    "Media Control": {
        "play music": "press:playpause",
        "next track": "press:nexttrack",
        "previous track": "press:prevtrack",
        "stop music": "press:stop"
    }
}

# Helper for About Text
ABOUT_TEXT = """VOX OPS Control Suite v6.4
The Next-Gen Voice Engine for Gamers

Website: https://milak-web.github.io/vox-ops/
GitHub: https://github.com/milak-web/vox-ops

POWERED BY:
• Vosk API (Alpha Cephei) - Offline Speech Recognition
• PyAutoGUI - Input Simulation
• CustomTkinter - Modern UI Framework

LICENSE:
This software uses open source components.
Vosk Models are Apache 2.0 / CC-BY licensed.

Designed for low-latency, privacy-focused control."""

class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                       background=COLOR_TOOLTIP_BG, foreground="#e1e1e1",
                       relief=tk.SOLID, borderwidth=1,
                       font=("Segoe UI", 9, "normal"))
        label.pack(ipadx=5, ipady=3)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def create_tooltip(widget, text_func):
    toolTip = ToolTip(widget)
    def enter(event):
        widget.after(500, lambda: toolTip.showtip(text_func()))
    def leave(event):
        toolTip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)

class ModelBrowserDialog(ctk.CTkToplevel):
    def __init__(self, parent, current_lang, current_model, on_confirm):
        super().__init__(parent)
        self.title("Select Voice Model")
        self.geometry("750x550")
        self.attributes("-topmost", True)
        self.on_confirm = on_confirm
        self.selected_lang = current_lang
        self.selected_model_name = current_model
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Header
        ctk.CTkLabel(self, text="Model Browser", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0, column=0, columnspan=2, pady=(15, 5))

        # --- Left Side: Selection ---
        left_frame = ctk.CTkFrame(self, fg_color="transparent")
        left_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        
        ctk.CTkLabel(left_frame, text="1. Select Language:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.lang_combo = ctk.CTkComboBox(left_frame, values=list(VOSK_MODELS.keys()), command=self.on_lang_change, width=250)
        self.lang_combo.set(self.selected_lang)
        self.lang_combo.pack(anchor="w", pady=(5, 20))

        ctk.CTkLabel(left_frame, text="2. Select Model Version:", font=ctk.CTkFont(weight="bold")).pack(anchor="w")
        self.model_scroll = ctk.CTkScrollableFrame(left_frame, width=250)
        self.model_scroll.pack(fill="both", expand=True, pady=(5, 0))
        
        self.model_buttons = []
        
        # --- Right Side: Details ---
        right_frame = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=10)
        right_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=10)
        
        ctk.CTkLabel(right_frame, text="MODEL DETAILS", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SUB).pack(pady=(20, 10))
        
        self.lbl_desc = ctk.CTkLabel(right_frame, text="Hover over a model to see details.", justify="left", wraplength=220, text_color="#ccc")
        self.lbl_desc.pack(padx=20, pady=10)
        
        self.lbl_stats = ctk.CTkLabel(right_frame, text="", font=ctk.CTkFont(family="Consolas", size=12), justify="left", text_color=COLOR_ACCENT)
        self.lbl_stats.pack(padx=20, pady=10)

        # Footer Button
        self.btn_action = ctk.CTkButton(self, text="Download & Apply", command=self.confirm_selection, fg_color=COLOR_SUCCESS, height=40)
        self.btn_action.grid(row=2, column=0, columnspan=2, padx=50, pady=20, sticky="ew")

        # Refresh list AFTER UI init
        self.refresh_model_list()

    def refresh_model_list(self):
        for btn in self.model_buttons:
            btn.destroy()
        self.model_buttons = []
        
        models = VOSK_MODELS[self.selected_lang]
        for model_name in models.keys():
            is_active = (model_name == self.selected_model_name)
            color = COLOR_ACCENT if is_active else COLOR_SIDEBAR
            
            btn = ctk.CTkButton(self.model_scroll, text=model_name, fg_color=color, hover_color=COLOR_ACCENT_HOVER, anchor="w", command=lambda m=model_name: self.select_model(m))
            btn.pack(fill="x", pady=2)
            btn.bind("<Enter>", lambda e, m=model_name: self.show_info(m))
            
            self.model_buttons.append(btn)
            
        if self.selected_model_name in models:
            self.show_info(self.selected_model_name)
        
        self.update_action_button()

    def on_lang_change(self, choice):
        self.selected_lang = choice
        self.selected_model_name = list(VOSK_MODELS[choice].keys())[0]
        self.refresh_model_list()

    def select_model(self, model_name):
        self.selected_model_name = model_name
        self.refresh_model_list()

    def show_info(self, model_name):
        if not hasattr(self, 'lbl_desc'): return # Safety check
        data = VOSK_MODELS[self.selected_lang][model_name]
        desc = data.get("desc", "No description available.")
        stats = f"Download Size: {data.get('size', '?')}\nEst. RAM Usage: {data.get('ram', '?')}"
        self.lbl_desc.configure(text=desc)
        self.lbl_stats.configure(text=stats)

    def update_action_button(self):
        # Check availability
        model_data = VOSK_MODELS[self.selected_lang][self.selected_model_name]
        path = model_data["path"]
        folder = model_data["folder"]
        
        # Check if path exists or folder exists
        exists = False
        if os.path.exists(path): exists = True
        elif os.path.exists(folder): exists = True
        
        if exists:
            self.btn_action.configure(text="Use Selected Model", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER)
        else:
            self.btn_action.configure(text="Download & Install", fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER)

    def confirm_selection(self):
        self.on_confirm(self.selected_lang, self.selected_model_name)
        self.destroy()

class SimulatedServer:
    def __init__(self):
        self.filename = "community_data.json"
        self.local_profiles = []
        self.load_profiles()

    def load_profiles(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.local_profiles = json.load(f)
            except:
                self.local_profiles = []

    def get_profiles(self):
        # Combine hardcoded + local user profiles
        return COMMUNITY_PROFILES + self.local_profiles

    def publish(self, profile):
        self.local_profiles.append(profile)
        self.save_profiles()
        return True

    def save_profiles(self):
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.local_profiles, f, indent=4)
        except: pass

class NetworkClient:
    def __init__(self, server_url):
        self.server_url = server_url.rstrip("/")
        self.fallback = SimulatedServer()

    def get_profiles(self):
        # Try network first
        try:
            with urllib.request.urlopen(f"{self.server_url}/profiles", timeout=2) as response:
                if response.getcode() == 200:
                    data = json.loads(response.read().decode())
                    # The server returns summaries, but for now let's assume it returns what we need
                    # Or we need to fetch details. Let's keep it simple: 
                    # If the server returns a list of profiles with 'name', 'desc', that's enough for the list.
                    # However, to install, we need commands. 
                    # The server implementation returns summaries without commands.
                    # We should fetch details when installing.
                    return data
        except Exception as e:
            # Fallback to local simulation if offline
            print(f"Network error: {e}. Using local cache.")
            return self.fallback.get_profiles()
        return []

    def get_profile_details(self, name):
        try:
            # URL encode the name
            safe_name = urllib.parse.quote(name)
            with urllib.request.urlopen(f"{self.server_url}/profiles/{safe_name}", timeout=3) as response:
                if response.getcode() == 200:
                    return json.loads(response.read().decode())
        except:
            pass
        return None

    def publish(self, profile):
        try:
            req = urllib.request.Request(f"{self.server_url}/upload")
            req.add_header('Content-Type', 'application/json; charset=utf-8')
            jsondata = json.dumps(profile).encode('utf-8')
            req.add_header('Content-Length', len(jsondata))
            
            with urllib.request.urlopen(req, jsondata, timeout=5) as response:
                if response.getcode() == 200:
                    return True
        except Exception as e:
            print(f"Publish error: {e}")
            # Fallback to local
            return self.fallback.publish(profile)
        return False

class VoiceApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        _disable_exclusive_mode()
        socket.setdefaulttimeout(30)
        # Load settings to get URL
        # DEFAULT TO RENDER (Production)
        self.community_server_url = "https://pyvoice-community.onrender.com"
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                    # If setting exists, use it, otherwise fallback to render
                    self.community_server_url = data.get("server_url", "https://pyvoice-community.onrender.com")
            except: pass

        self.client = NetworkClient(self.community_server_url)
        # self.server = SimulatedServer() # Replaced by client
        self.title(APP_TITLE)
        self.geometry(APP_SIZE)
        
        # Set Icon
        try:
            icon_path = os.path.abspath("vox_ops.ico")
            if os.path.exists(icon_path):
                self.iconbitmap(icon_path)
            else:
                print(f"Warning: Icon not found at {icon_path}")
        except Exception as e:
            print(f"Warning: Failed to set icon: {e}")

        if not os.path.exists(PROFILES_DIR):
            os.makedirs(PROFILES_DIR)
        self.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
        # Engine State
        self.is_listening = False
        self.model = None
        self.rec = None
        self.p = None
        self.stream = None
        self.last_heard_phrase = ""
        self.tray_icon = None
        
        # Overlay State
        self.overlay_window = None
        self.overlay_label = None
        
        # Settings Defaults
        self.active_profile_name = "Untitled"
        self.active_profile_path = None
        self.commands = {} 
        self.confidence_threshold = 0.7
        self.appearance_mode = "Dark"
        
        # Globals
        self.current_language = "English"
        self.current_model_name = "Lightweight (Fast)"
        self.input_mode = "Voice Activation"
        self.ptt_key = "ctrl"
        self.enable_sfx = True
        self.start_minimized = False
        self.run_on_startup = False
        
        self.dictation_mode = tk.BooleanVar(value=False)
        self.enable_overlay = False
        self.target_window = ""
        
        # Search Var for Community
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_community_list)
        self.selected_community_profile = None

        # Init TTS
        self.tts_engine = None
        if TTS_AVAILABLE:
            try:
                self.tts_engine = pyttsx3.init()
            except:
                pass

        if TRAY_AVAILABLE:
            self.setup_tray_icon()

        # CHECK FIRST RUN
        settings_exist = os.path.exists(SETTINGS_FILE)
        self.load_settings()
        
        self.create_menu()
        self.create_layout()
        
        # HUD Initialization
        if self.enable_overlay:
            self.setup_overlay()
        
        if not settings_exist:
            self.after(200, self.open_first_run_wizard)
        else:
            self.log("Initializing System v6.4...")
            threading.Thread(target=self.trigger_model_load, daemon=True).start()
            
            # Start Minimized Check
            if self.start_minimized and TRAY_AVAILABLE:
                self.after(500, self.minimize_to_tray)

    def open_first_run_wizard(self):
        def on_complete(lang, model):
            self.current_language = lang
            self.current_model_name = model
            self.save_settings()
            self.log("First Run Configuration Applied.")
            threading.Thread(target=self.trigger_model_load, daemon=True).start()

        ModelBrowserDialog(self, self.current_language, self.current_model_name, on_complete)

    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, 'r') as f:
                    data = json.load(f)
                
                lang = data.get("language", "English")
                if lang in VOSK_MODELS:
                    self.current_language = lang
                
                mod = data.get("model", "Lightweight (Fast)")
                if mod in VOSK_MODELS[self.current_language]:
                    self.current_model_name = mod
                else:
                    self.current_model_name = list(VOSK_MODELS[self.current_language].keys())[0]

                self.confidence_threshold = data.get("threshold", 0.7)
                self.input_mode = data.get("input_mode", "Voice Activation")
                self.ptt_key = data.get("ptt_key", "ctrl")
                self.enable_sfx = data.get("sfx", True)
                self.enable_overlay = data.get("overlay", False)
                self.target_window = data.get("target_window", "")
                self.start_minimized = data.get("start_minimized", False)
                self.run_on_startup = data.get("run_on_startup", False)
                theme = data.get("theme", "Dark")
                ctk.set_appearance_mode(theme)
            except: pass

    def save_settings(self):
        data = {
            "language": self.current_language,
            "model": self.current_model_name,
            "theme": ctk.get_appearance_mode(),
            "threshold": self.confidence_threshold,
            "input_mode": self.input_mode,
            "ptt_key": self.ptt_key,
            "sfx": self.enable_sfx,
            "overlay": self.enable_overlay,
            "target_window": self.target_window,
            "start_minimized": self.start_minimized,
            "run_on_startup": self.run_on_startup,
            "server_url": self.community_server_url
        }
        try:
            with open(SETTINGS_FILE, 'w') as f:
                json.dump(data, f, indent=4)
        except: pass

    def set_startup(self, enable):
        if not REGISTRY_AVAILABLE: return
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_ALL_ACCESS)
            if enable:
                exe_path = sys.executable
                if getattr(sys, 'frozen', False):
                    winreg.SetValueEx(key, "VOX OPS", 0, winreg.REG_SZ, f'"{exe_path}"')
                else:
                    # Running as script
                    script_path = os.path.abspath(__file__)
                    py_exe = sys.executable.replace("python.exe", "pythonw.exe")
                    winreg.SetValueEx(key, "VOX OPS", 0, winreg.REG_SZ, f'"{py_exe}" "{script_path}"')
            else:
                try:
                    winreg.DeleteValue(key, "VOX OPS")
                except FileNotFoundError:
                    pass
            winreg.CloseKey(key)
        except Exception as e:
            print(f"Startup Registry Error: {e}")

    # --- GAME HUD OVERLAY ---
    def setup_overlay(self):
        if self.overlay_window is not None: return
        self.overlay_window = tk.Toplevel(self)
        self.overlay_window.overrideredirect(True)
        self.overlay_window.attributes("-topmost", True)
        self.overlay_window.attributes("-alpha", 0.8)
        self.overlay_window.geometry("+20+20")
        self.overlay_window.configure(bg="black")
        
        self.overlay_label = tk.Label(self.overlay_window, text="[VOX OPS] Standing By", fg="#00ff00", bg="black", font=("Consolas", 12, "bold"))
        self.overlay_label.pack(padx=10, pady=5)

    def close_overlay(self):
        if self.overlay_window:
            self.overlay_window.destroy()
            self.overlay_window = None

    def update_overlay(self, text, color="#00ff00"):
        if self.enable_overlay and self.overlay_label:
            self.overlay_label.config(text=f"[VOX OPS] {text}", fg=color)

    # --- SFX & TRAY ---
    def play_sfx(self, event_type):
        if not self.enable_sfx or not SFX_AVAILABLE: return
        def _sound():
            try:
                if event_type == "engage":
                    winsound.Beep(600, 100); winsound.Beep(800, 100); winsound.Beep(1200, 150)
                elif event_type == "disengage":
                    winsound.Beep(1000, 100); winsound.Beep(600, 150)
                elif event_type == "success":
                    winsound.Beep(1500, 50); winsound.Beep(2000, 50)
            except: pass
        threading.Thread(target=_sound, daemon=True).start()

    def setup_tray_icon(self):
        image = Image.new('RGB', (64, 64), color=(0, 122, 204))
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill=(255, 255, 255))
        
        def show_window(icon, item):
            self.deiconify()
            self.tray_icon.stop()

        def quit_app(icon, item):
            self.tray_icon.stop()
            self.quit()

        menu = pystray.Menu(pystray.MenuItem('Show Control Center', show_window, default=True), pystray.MenuItem('Exit', quit_app))
        self.tray_icon = pystray.Icon("VOX OPS", image, "VOX OPS Control", menu)

    def minimize_to_tray(self):
        if TRAY_AVAILABLE:
            self.withdraw()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            try: self.tray_icon.notify("Running in background.", "VOX OPS")
            except: pass
        else: self.quit()

    # --- UI CREATION ---
    def create_menu(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0, bg=COLOR_SIDEBAR, fg="black")
        file_menu.add_command(label="New Profile", command=self.new_profile)
        file_menu.add_command(label="Open Profile...", command=self.open_profile)
        file_menu.add_command(label="Save Profile", command=self.save_profile)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        preset_menu = tk.Menu(menubar, tearoff=0)
        for name in PRESETS.keys():
            preset_menu.add_command(label=f"Load {name}", command=lambda n=name: self.load_preset(n))
        menubar.add_cascade(label="Presets", menu=preset_menu)
        
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About VOX OPS", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

    def create_layout(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(5, weight=1)

        ctk.CTkLabel(self.sidebar, text="VOX OPS", font=ctk.CTkFont(family="Arial", size=22, weight="bold")).grid(row=0, column=0, padx=20, pady=(20, 0), sticky="w")
        ctk.CTkLabel(self.sidebar, text="GLOBAL CONTROL", text_color=COLOR_TEXT_SUB, font=ctk.CTkFont(size=11, weight="bold")).grid(row=1, column=0, padx=20, pady=(0, 20), sticky="w")

        self.create_nav_btn("Command Center", "Home", 2, "🎛️")
        self.create_nav_btn("My Profiles", "Profiles", 3, "📂")
        self.create_nav_btn("Community", "Community", 4, "🌐")
        self.create_nav_btn("Settings", "Settings", 5, "⚙️")

        self.status_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.status_frame.grid(row=6, column=0, padx=15, pady=20, sticky="ew")
        
        ctk.CTkLabel(self.status_frame, text="ENGINE STATUS", text_color=COLOR_TEXT_SUB, font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w")
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="BOOTING...", text_color="orange", font=ctk.CTkFont(size=12, weight="bold"))
        self.lbl_status.pack(anchor="w")
        self.audio_bar = ctk.CTkProgressBar(self.status_frame, height=6, progress_color=COLOR_SUCCESS)
        self.audio_bar.set(0)
        self.audio_bar.pack(fill="x", pady=(8,0))

        self.tabview = ctk.CTkTabview(self, corner_radius=0, segmented_button_fg_color=COLOR_SIDEBAR, segmented_button_selected_color=COLOR_ACCENT)
        self.tabview.grid(row=0, column=1, padx=0, pady=0, sticky="nsew")
        
        self.tabview.add("Home")
        self.tabview.add("Profiles")
        self.tabview.add("Community")
        self.tabview.add("Settings")

        # Hide the top bar (Segmented Button) so only Sidebar is used
        self.tabview._segmented_button.grid_forget()

        self.build_home()
        self.build_profiles()
        self.build_community()
        self.build_settings()

    def create_nav_btn(self, text, tab_name, row, icon):
        btn = ctk.CTkButton(self.sidebar, text=f"{icon}  {text}", command=lambda: self.tabview.set(tab_name),
                            fg_color="transparent", text_color="#aaaaaa", hover_color=COLOR_CARD,
                            anchor="w", font=ctk.CTkFont(size=13), height=40)
        btn.grid(row=row, column=0, padx=10, pady=2, sticky="ew")

    def build_home(self):
        tab = self.tabview.tab("Home")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=0)
        tab.grid_rowconfigure(1, weight=1)

        top_bar = ctk.CTkFrame(tab, fg_color="transparent")
        top_bar.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(10, 10))
        
        self.btn_listen = ctk.CTkButton(top_bar, text="ENGAGE SYSTEM", font=ctk.CTkFont(size=16, weight="bold"), 
                                        height=45, width=200, corner_radius=6, fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER,
                                        state="disabled", command=self.toggle_listening)
        self.btn_listen.pack(side="left")

        self.dict_switch = ctk.CTkSwitch(top_bar, text="Dictation Mode", variable=self.dictation_mode, progress_color=COLOR_ACCENT)
        self.dict_switch.pack(side="left", padx=20)

        self.lbl_active_profile = ctk.CTkLabel(top_bar, text=f"Profile: {self.active_profile_name}", font=ctk.CTkFont(size=14))
        self.lbl_active_profile.pack(side="right", padx=20)

        list_frame = ctk.CTkFrame(tab, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        list_frame.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        list_frame.grid_columnconfigure(0, weight=1)
        list_frame.grid_rowconfigure(1, weight=1)

        list_toolbar = ctk.CTkFrame(list_frame, fg_color="transparent", height=40)
        list_toolbar.grid(row=0, column=0, sticky="ew", padx=10, pady=5)
        ctk.CTkLabel(list_toolbar, text="ACTIVE COMMANDS", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SUB).pack(side="left", pady=5)
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2d2d30", foreground="#e1e1e1", fieldbackground="#2d2d30", borderwidth=0, rowheight=30, font=("Segoe UI", 10))
        style.configure("Treeview.Heading", background="#252526", foreground="#cccccc", relief="flat", font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[('selected', COLOR_ACCENT)])

        self.tree = ttk.Treeview(list_frame, columns=("phrase", "action"), show="headings", selectmode="extended")
        self.tree.heading("phrase", text="TRIGGERS", anchor="w")
        self.tree.heading("action", text="MACRO CHAIN", anchor="w")
        self.tree.column("phrase", width=250, anchor="w")
        self.tree.column("action", width=450, anchor="w")
        self.tree.grid(row=1, column=0, sticky="nsew", padx=1, pady=1)

        sb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        sb.grid(row=1, column=1, sticky="ns")
        self.tree.configure(yscrollcommand=sb.set)

        action_row = ctk.CTkFrame(list_frame, fg_color="transparent")
        action_row.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        ctk.CTkButton(action_row, text="+ Add Command", fg_color=COLOR_ACCENT, hover_color=COLOR_ACCENT_HOVER, width=120, command=self.add_command_dialog).pack(side="left")
        ctk.CTkButton(action_row, text="Edit Selected", fg_color=COLOR_SIDEBAR, hover_color=COLOR_ACCENT, width=120, command=self.edit_command).pack(side="left", padx=10)
        ctk.CTkButton(action_row, text="Remove Selected", fg_color=COLOR_SIDEBAR, hover_color=COLOR_DANGER, width=120, command=self.remove_command).pack(side="left")

        # Double click to edit
        self.tree.bind("<Double-1>", lambda e: self.edit_command())

        # Context Menu
        self.context_menu = tk.Menu(self, tearoff=0, bg=COLOR_SIDEBAR, fg="white", activebackground=COLOR_ACCENT)
        self.context_menu.add_command(label="Edit Command", command=self.edit_command)
        self.context_menu.add_command(label="Delete Command", command=self.remove_command)
        
        def show_context_menu(event):
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)
                self.context_menu.post(event.x_root, event.y_root)
        
        self.tree.bind("<Button-3>", show_context_menu)

        right_panel = ctk.CTkFrame(tab, fg_color="transparent", width=300)
        right_panel.grid(row=1, column=1, sticky="nsew", padx=(0, 20), pady=10)
        right_panel.grid_rowconfigure(1, weight=1)

        capture_frame = ctk.CTkFrame(right_panel, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        capture_frame.pack(fill="x", pady=(0, 10))
        
        ctk.CTkLabel(capture_frame, text="QUICK CAPTURE", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_TEXT_SUB).pack(anchor="w", padx=10, pady=(10,5))
        self.lbl_last_heard = ctk.CTkLabel(capture_frame, text="Listening...", font=ctk.CTkFont(size=14), wraplength=260)
        self.lbl_last_heard.pack(pady=5, padx=10)
        self.btn_quick_add = ctk.CTkButton(capture_frame, text="Create Command from Heard", state="disabled", fg_color=COLOR_SIDEBAR, command=self.quick_add_command)
        self.btn_quick_add.pack(fill="x", padx=10, pady=(5,10))

        ctk.CTkLabel(right_panel, text="LIVE LOG", font=ctk.CTkFont(size=12, weight="bold"), text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(0,5))
        self.log_box = ctk.CTkTextbox(right_panel, font=("Consolas", 11), text_color="#ddd", corner_radius=6, width=280)
        self.log_box.pack(fill="both", expand=True)

    def build_profiles(self):
        tab = self.tabview.tab("Profiles")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2)
        tab.grid_rowconfigure(1, weight=1)

        # --- Left Column: List ---
        left_panel = ctk.CTkFrame(tab, fg_color="transparent")
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(20, 10), pady=20)
        left_panel.grid_rowconfigure(1, weight=1)
        
        ctk.CTkLabel(left_panel, text="MY LIBRARY", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_TEXT_SUB).pack(anchor="w", pady=(0, 10))

        self.profile_list_frame = ctk.CTkScrollableFrame(left_panel, fg_color=COLOR_CARD)
        self.profile_list_frame.pack(fill="both", expand=True)

        ctk.CTkButton(left_panel, text="+ Create New Profile", command=self.create_new_local_profile, fg_color=COLOR_ACCENT).pack(fill="x", pady=(10, 0))

        # --- Right Column: Details ---
        right_panel = ctk.CTkFrame(tab, fg_color=COLOR_CARD, corner_radius=10)
        right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(10, 20), pady=20)
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(1, weight=1)

        self.lbl_prof_name = ctk.CTkLabel(right_panel, text="Select a Profile", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_prof_name.pack(pady=(30, 5))
        
        self.lbl_prof_path = ctk.CTkLabel(right_panel, text="", text_color=COLOR_TEXT_SUB, font=ctk.CTkFont(size=10))
        self.lbl_prof_path.pack(pady=(0, 15))

        # Preview
        ctk.CTkLabel(right_panel, text="COMMANDS IN THIS PROFILE", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(20, 5))
        self.prof_preview = ctk.CTkTextbox(right_panel, fg_color=COLOR_BG, font=("Consolas", 11), state="disabled")
        self.prof_preview.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Action Buttons
        actions = ctk.CTkFrame(right_panel, fg_color="transparent")
        actions.pack(fill="x", padx=20, pady=20)
        
        self.btn_load_prof = ctk.CTkButton(actions, text="Load Profile", state="disabled", fg_color=COLOR_SUCCESS, command=self.load_selected_local_profile)
        self.btn_load_prof.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_del_prof = ctk.CTkButton(actions, text="Delete", state="disabled", fg_color=COLOR_DANGER, width=80, command=self.delete_selected_local_profile)
        self.btn_del_prof.pack(side="right", padx=5)

        self.selected_local_profile = None
        self.refresh_profile_list()

    def refresh_profile_list(self):
        for w in self.profile_list_frame.winfo_children(): w.destroy()
        
        files = [f for f in os.listdir(PROFILES_DIR) if f.endswith(".json")]
        if not files:
            ctk.CTkLabel(self.profile_list_frame, text="No profiles found.").pack(pady=20)
            return

        for f in files:
            btn = ctk.CTkButton(self.profile_list_frame, text=f.replace(".json", ""), anchor="w", fg_color=COLOR_BG, hover_color=COLOR_SIDEBAR, height=40,
                                command=lambda n=f: self.show_local_profile(n))
            btn.pack(fill="x", pady=2)

    def show_local_profile(self, filename):
        path = os.path.join(PROFILES_DIR, filename)
        self.selected_local_profile = path
        self.lbl_prof_name.configure(text=filename.replace(".json", ""))
        self.lbl_prof_path.configure(text=path)
        
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            
            # Preview
            preview = ""
            cmds = data if isinstance(data, dict) else {} # Basic check
            for k, v in list(cmds.items())[:15]:
                preview += f"{k} -> {v}\n"
            if len(cmds) > 15: preview += f"... +{len(cmds)-15} more"
            
            self.prof_preview.configure(state="normal")
            self.prof_preview.delete("0.0", "end")
            self.prof_preview.insert("0.0", preview)
            self.prof_preview.configure(state="disabled")
            
            self.btn_load_prof.configure(state="normal", text=f"Load '{filename.replace('.json','')}'")
            self.btn_del_prof.configure(state="normal")
            
        except Exception as e:
            self.prof_preview.configure(state="normal")
            self.prof_preview.delete("0.0", "end")
            self.prof_preview.insert("0.0", f"Error reading file:\n{e}")
            self.prof_preview.configure(state="disabled")

    def create_new_local_profile(self):
        dialog = ctk.CTkInputDialog(text="Enter name for new profile:", title="New Profile")
        name = dialog.get_input()
        if name:
            filename = f"{name.strip().replace(' ', '_')}.json"
            path = os.path.join(PROFILES_DIR, filename)
            if os.path.exists(path):
                messagebox.showerror("Error", "Profile already exists!")
                return
            
            with open(path, 'w') as f:
                json.dump({}, f) # Empty profile
            
            self.refresh_profile_list()
            self.show_local_profile(filename)
            
            # Ask to load?
            if messagebox.askyesno("Load Profile", "Load this new empty profile now?"):
                self.load_local_profile_file(path)

    def load_selected_local_profile(self):
        if self.selected_local_profile:
            self.load_local_profile_file(self.selected_local_profile)

    def load_local_profile_file(self, path):
        try:
            with open(path, 'r') as f:
                self.commands = json.load(f)
            self.active_profile_name = os.path.basename(path)
            self.active_profile_path = path
            self.lbl_active_profile.configure(text=f"Profile: {self.active_profile_name}")
            self.refresh_ui()
            self.log(f"Loaded profile: {self.active_profile_name}")
            self.tabview.set("Home")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load profile: {e}")

    def delete_selected_local_profile(self):
        if not self.selected_local_profile: return
        if messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this profile?\nThis cannot be undone."):
            try:
                os.remove(self.selected_local_profile)
                self.selected_local_profile = None
                self.lbl_prof_name.configure(text="Select a Profile")
                self.prof_preview.configure(state="normal")
                self.prof_preview.delete("0.0", "end")
                self.prof_preview.configure(state="disabled")
                self.btn_load_prof.configure(state="disabled")
                self.btn_del_prof.configure(state="disabled")
                self.refresh_profile_list()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete: {e}")

    def build_community(self):
        tab = self.tabview.tab("Community")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_columnconfigure(1, weight=2) # Right side wider for details
        tab.grid_rowconfigure(1, weight=1)

        # --- Left Column: Search & List ---
        left_panel = ctk.CTkFrame(tab, fg_color="transparent")
        left_panel.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(20, 10), pady=20)
        left_panel.grid_rowconfigure(1, weight=1)
        
        # Search Bar
        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.filter_community_list)
        search_entry = ctk.CTkEntry(left_panel, textvariable=self.search_var, placeholder_text="🔍 Search Profiles...")
        search_entry.pack(fill="x", pady=(0, 10))

        # Profile List
        self.comm_list_frame = ctk.CTkScrollableFrame(left_panel, fg_color=COLOR_CARD)
        self.comm_list_frame.pack(fill="both", expand=True)
        
        # Share Button
        ctk.CTkButton(left_panel, text="☁️  Share Your Profile", command=self.upload_dialog, fg_color=COLOR_ACCENT).pack(fill="x", pady=(10, 0))

        # --- Right Column: Details & Preview ---
        right_panel = ctk.CTkFrame(tab, fg_color=COLOR_CARD, corner_radius=10)
        right_panel.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(10, 20), pady=20)
        right_panel.grid_columnconfigure(0, weight=1)
        right_panel.grid_rowconfigure(2, weight=1) # Content expands

        # Placeholder / Initial State
        self.details_frame = right_panel
        self.lbl_det_title = ctk.CTkLabel(right_panel, text="Select a Profile", font=ctk.CTkFont(size=20, weight="bold"))
        self.lbl_det_title.pack(pady=(30, 5))
        
        self.lbl_det_author = ctk.CTkLabel(right_panel, text="", text_color=COLOR_TEXT_SUB)
        self.lbl_det_author.pack(pady=(0, 15))
        
        self.lbl_det_desc = ctk.CTkLabel(right_panel, text="", wraplength=400, justify="left")
        self.lbl_det_desc.pack(padx=20, fill="x")
        
        # Command Preview Box
        ctk.CTkLabel(right_panel, text="COMMAND PREVIEW", font=ctk.CTkFont(size=11, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(20, 5))
        self.preview_box = ctk.CTkTextbox(right_panel, fg_color=COLOR_BG, font=("Consolas", 11), state="disabled")
        self.preview_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Install Button
        self.btn_install = ctk.CTkButton(right_panel, text="⬇  Install Profile", state="disabled", fg_color=COLOR_SUCCESS, height=45, command=self.install_selected_profile)
        self.btn_install.pack(fill="x", padx=40, pady=30)
        
        # Populate initial list
        self.selected_community_profile = None
        self.populate_community_list()

    def populate_community_list(self, query=""):
        # Clear existing
        for widget in self.comm_list_frame.winfo_children():
            widget.destroy()
            
        profiles = self.client.get_profiles()
        
        for profile in profiles:
            if query.lower() in profile["name"].lower() or query.lower() in profile["desc"].lower():
                self.create_community_item(profile)

    def create_community_item(self, profile):
        btn = ctk.CTkButton(self.comm_list_frame, text=profile["name"], anchor="w", fg_color=COLOR_BG, hover_color=COLOR_SIDEBAR, height=40,
                            command=lambda p=profile: self.show_community_details(p))
        btn.pack(fill="x", pady=2)
        
    def show_community_details(self, profile):
        self.selected_community_profile = profile
        self.lbl_det_title.configure(text=profile["name"])
        self.lbl_det_author.configure(text=f"By {profile['author']}")
        self.lbl_det_desc.configure(text=profile["desc"])
        
        # Check if full details (commands) are available, if not, fetch them
        cmds = profile.get("commands")
        if not cmds:
             # Fetch details
             full_profile = self.client.get_profile_details(profile["name"])
             if full_profile:
                 self.selected_community_profile = full_profile
                 cmds = full_profile.get("commands", {})
             else:
                 cmds = {}

        # Preview commands
        preview_text = ""
        for cmd, action in list(cmds.items())[:10]: # Show first 10
            preview_text += f"{cmd} -> {action}\n"
        if len(cmds) > 10:
            preview_text += f"... and {len(cmds) - 10} more."
            
        self.preview_box.configure(state="normal")
        self.preview_box.delete("0.0", "end")
        self.preview_box.insert("0.0", preview_text)
        self.preview_box.configure(state="disabled")
        
        self.btn_install.configure(state="normal", text=f"⬇  Install '{profile['name']}'")

    def filter_community_list(self, *args):
        self.populate_community_list(self.search_var.get())

    def install_selected_profile(self):
        if not self.selected_community_profile: return
        
        profile = self.selected_community_profile
        
        # SAFETY CHECK
        dangerous_keywords = ["os.system", "subprocess", "shutdown", "format", "del", "remove", "rmdir"]
        warnings = []
        cmds = profile.get("commands", {})
        for cmd, action in cmds.items():
            for k in dangerous_keywords:
                if k in action.lower():
                    warnings.append(f"Command '{cmd}' contains dangerous code: '{k}'")
        
        if warnings:
            warn_text = "WARNING: This profile contains potentially unsafe commands:\n\n" + "\n".join(warnings[:5])
            if len(warnings) > 5: warn_text += "\n...and more."
            warn_text += "\n\nDo you still want to install it?"
            if not messagebox.askyesno("Safety Warning", warn_text, icon="warning"):
                return

        confirm = messagebox.askyesno("Install", f"Import '{profile['name']}' into your local library?")
        if confirm:
            # Save as new file in PROFILES_DIR
            filename = f"{profile['name'].replace(' ', '_').lower()}.json"
            path = os.path.join(PROFILES_DIR, filename)
            
            # Check overwrite
            if os.path.exists(path):
                if not messagebox.askyesno("Overwrite", f"Profile '{filename}' already exists. Overwrite?"):
                    return

            with open(path, 'w') as f:
                json.dump(profile["commands"], f, indent=4)
            
            # Load it
            self.load_local_profile_file(path)
            self.refresh_profile_list() # Update the list
            self.tabview.set("Home")
            messagebox.showinfo("Success", f"Profile installed: {profile['name']}")

    def upload_dialog(self):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Share Profile")
        dialog.geometry("400x400")
        dialog.attributes("-topmost", True)
        
        ctk.CTkLabel(dialog, text="Publish to Community", font=ctk.CTkFont(weight="bold")).pack(pady=10)
        
        entry_name = ctk.CTkEntry(dialog, placeholder_text="Profile Name")
        entry_name.pack(fill="x", padx=20, pady=5)
        if self.active_profile_name != "Untitled":
            entry_name.insert(0, self.active_profile_name.replace(".json", ""))

        entry_author = ctk.CTkEntry(dialog, placeholder_text="Author Name")
        entry_author.pack(fill="x", padx=20, pady=5)
        
        entry_desc = ctk.CTkEntry(dialog, placeholder_text="Description")
        entry_desc.pack(fill="x", padx=20, pady=5)
        
        def perform_upload():
            name = entry_name.get().strip()
            author = entry_author.get().strip()
            desc = entry_desc.get().strip()
            
            if not name or not author:
                messagebox.showerror("Error", "Name and Author are required!")
                return
                
            self.log("Uploading profile to community server...")
            
            # Create profile object
            new_profile = {
                "name": name,
                "author": author,
                "desc": desc,
                "commands": self.commands.copy()
            }
            
            # Publish
            success = self.client.publish(new_profile)
            
            dialog.destroy()
            if success:
                messagebox.showinfo("Success", "Profile published to community!")
            else:
                messagebox.showerror("Error", "Failed to publish. Using local backup.")
            
            self.populate_community_list() # Refresh list
            
        ctk.CTkButton(dialog, text="Upload", command=perform_upload, fg_color=COLOR_SUCCESS).pack(pady=20)

    def build_settings(self):
        tab = self.tabview.tab("Settings")
        
        # --- SCROLLABLE CONTAINER ---
        settings_scroll = ctk.CTkScrollableFrame(tab, fg_color="transparent")
        settings_scroll.pack(fill="both", expand=True)



        ctk.CTkLabel(settings_scroll, text="AI & LANGUAGE ENGINE", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=40, pady=(20, 10))
        card_ai = ctk.CTkFrame(settings_scroll, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        card_ai.pack(fill="x", padx=40)

        # Replaced Dropdowns with a single "Browse" Button for Model Selection
        r_model = ctk.CTkFrame(card_ai, fg_color="transparent")
        r_model.pack(fill="x", padx=20, pady=15)
        
        # Display Current Selection
        self.lbl_current_model = ctk.CTkLabel(r_model, text=f"{self.current_language} - {self.current_model_name}", font=ctk.CTkFont(weight="bold"))
        self.lbl_current_model.pack(side="left")
        
        def open_browser():
            def on_selected(lang, model):
                self.current_language = lang
                self.current_model_name = model
                self.lbl_current_model.configure(text=f"{lang} - {model}")
                self.save_settings()
                if self.is_listening: self.stop_listening()
                self.btn_listen.configure(state="disabled", text="LOADING...")
                threading.Thread(target=self.trigger_model_load, daemon=True).start()
                
            ModelBrowserDialog(self, self.current_language, self.current_model_name, on_selected)

        ctk.CTkButton(r_model, text="Browse Models...", command=open_browser, width=150, fg_color=COLOR_SIDEBAR).pack(side="right")

        # Threshold
        r_thresh = ctk.CTkFrame(card_ai, fg_color="transparent")
        r_thresh.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(r_thresh, text="Confidence:").pack(side="left")
        def update_thresh(val):
            self.confidence_threshold = float(val)
            self.save_settings()
        s = ctk.CTkSlider(r_thresh, from_=0, to=1, number_of_steps=10, width=250, command=update_thresh)
        s.set(self.confidence_threshold)
        s.pack(side="right")

        # Visuals & Input
        ctk.CTkLabel(settings_scroll, text="VISUALS & INPUT", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=40, pady=(20, 10))
        card_vis = ctk.CTkFrame(settings_scroll, corner_radius=6, border_width=1, border_color=COLOR_BORDER)
        card_vis.pack(fill="x", padx=40)
        
        # Target Window (Context Awareness)
        r_target = ctk.CTkFrame(card_vis, fg_color="transparent")
        r_target.pack(fill="x", padx=20, pady=(15, 0))
        ctk.CTkLabel(r_target, text="Target Window (Title):").pack(side="left")
        
        self.entry_target = ctk.CTkEntry(r_target, width=200, placeholder_text="e.g. Elite Dangerous")
        self.entry_target.pack(side="right")
        self.entry_target.insert(0, self.target_window)
        
        def save_target(event=None):
            self.target_window = self.entry_target.get().strip()
            self.save_settings()
            
        self.entry_target.bind("<FocusOut>", save_target)
        self.entry_target.bind("<Return>", save_target)

        # Overlay
        r5 = ctk.CTkFrame(card_vis, fg_color="transparent")
        r5.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(r5, text="Game Overlay:").pack(side="left")
        self.hud_var = tk.IntVar(value=1 if self.enable_overlay else 0)
        def toggle_hud():
            self.enable_overlay = bool(self.hud_var.get())
            if self.enable_overlay: self.setup_overlay()
            else: self.close_overlay()
            self.save_settings()
        ctk.CTkSwitch(r5, text="Enabled", variable=self.hud_var, command=toggle_hud, progress_color=COLOR_SUCCESS).pack(side="right")

        # Start Minimized
        r6 = ctk.CTkFrame(card_vis, fg_color="transparent")
        r6.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(r6, text="Start Minimized:").pack(side="left")
        self.min_var = tk.IntVar(value=1 if self.start_minimized else 0)
        def toggle_min():
            self.start_minimized = bool(self.min_var.get())
            self.save_settings()
        ctk.CTkSwitch(r6, text="To Tray", variable=self.min_var, command=toggle_min, progress_color=COLOR_SUCCESS).pack(side="right")

        # Run on Startup
        r7 = ctk.CTkFrame(card_vis, fg_color="transparent")
        r7.pack(fill="x", padx=20, pady=(0, 15))
        ctk.CTkLabel(r7, text="Run on Windows Startup:").pack(side="left")
        self.start_var = tk.IntVar(value=1 if self.run_on_startup else 0)
        def toggle_startup_switch():
            self.run_on_startup = bool(self.start_var.get())
            self.save_settings()
            self.set_startup(self.run_on_startup)
        
        state_startup = "normal" if REGISTRY_AVAILABLE else "disabled"
        ctk.CTkSwitch(r7, text="Enabled", variable=self.start_var, command=toggle_startup_switch, progress_color=COLOR_SUCCESS, state=state_startup).pack(side="right")

        # --- SERVER SETTINGS (Minimized) ---
        r_serv = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        r_serv.pack(fill="x", padx=40, pady=20)
        
        ctk.CTkLabel(r_serv, text="Server:", text_color="gray").pack(side="left")
        self.entry_server = ctk.CTkEntry(r_serv, width=200)
        self.entry_server.pack(side="left", padx=10)
        self.entry_server.insert(0, self.community_server_url)
        
        def save_server_url():
            url = self.entry_server.get().strip()
            self.community_server_url = url
            self.client.server_url = url
            self.save_settings()
            self.populate_community_list() # Refresh
            messagebox.showinfo("Saved", "Server URL updated.")
            
        ctk.CTkButton(r_serv, text="Update", command=save_server_url, width=60, fg_color=COLOR_SIDEBAR, height=24).pack(side="left")

        # --- SUPPORT & DONATION (Static) ---
        
        # Divider
        ctk.CTkFrame(settings_scroll, height=2, fg_color=COLOR_BORDER).pack(fill="x", padx=40, pady=20)

        # Container
        content_frame = ctk.CTkFrame(settings_scroll, fg_color="transparent")
        content_frame.pack(fill="x", pady=(0, 40), padx=40)
        
        # Title
        ctk.CTkLabel(content_frame, text="Buy Me a Coffee ☕", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(10, 5))
        
        # QR Code Area (Locked)
        qr_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        qr_frame.pack(pady=10)

        def load_qr():
            try:
                from PIL import Image
                pil_img = None
                
                # Check Internal Base64 FIRST
                if QR_CODE_BASE64:
                    try:
                        img_data = base64.b64decode(QR_CODE_BASE64)
                        pil_img = Image.open(io.BytesIO(img_data))
                    except: pass
                
                # Check File (Fallback)
                if not pil_img and os.path.exists("qrcode.png"):
                    try: pil_img = Image.open("qrcode.png")
                    except: pass
                
                # Clear frame
                for widget in qr_frame.winfo_children(): widget.destroy()

                if pil_img:
                    pil_img = pil_img.resize((200, 200))
                    qr_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(200, 200))
                    ctk.CTkLabel(qr_frame, image=qr_img, text="").pack()
                    return True
                else:
                    ctk.CTkLabel(qr_frame, text="[ Project Support ]", text_color="gray").pack(pady=80)
                    return False
            except Exception as e:
                print("QR Error:", e)
            return False

        load_qr()
        
        # Info
        ctk.CTkLabel(content_frame, text="Network: TRON (TRC20)", font=ctk.CTkFont(weight="bold", size=12)).pack(pady=(5, 0))
        ctk.CTkLabel(content_frame, text="Currency: USDT", text_color=COLOR_TEXT_SUB, font=ctk.CTkFont(size=12)).pack(pady=(0, 10))

        # Wallet Address (Read-Only)
        my_wallet = "TXVkihrVZq2X9Zwm2WeZc46uXJ4MfsiowM" 
        
        addr_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        addr_frame.pack(pady=5, fill="x")
        
        addr_box = ctk.CTkEntry(addr_frame, justify="center", font=ctk.CTkFont(family="Consolas", size=11), width=280, fg_color="transparent", border_width=0)
        addr_box.pack(pady=(0, 5))
        addr_box.insert(0, my_wallet)
        addr_box.configure(state="readonly")
        
        def copy_addr():
            self.clipboard_clear()
            self.clipboard_append(my_wallet)
            btn_copy.configure(text="Copied!", fg_color=COLOR_SUCCESS)
            self.after(2000, lambda: btn_copy.configure(text="Copy Address", fg_color=COLOR_ACCENT))
            
        btn_copy = ctk.CTkButton(addr_frame, text="Copy Address", command=copy_addr, fg_color=COLOR_ACCENT, width=150)
        btn_copy.pack()
        
        ctk.CTkLabel(content_frame, text="Thank you for using VOX OPS!", font=ctk.CTkFont(size=11), text_color=COLOR_TEXT_SUB).pack(pady=(15, 0))

    # --- MODEL & LANGUAGE LOGIC ---

    def trigger_model_load(self):
        # Lookup model in nested dict
        try:
            model_data = VOSK_MODELS[self.current_language][self.current_model_name]
        except KeyError:
            # Fallback if config is invalid
            self.current_language = "English"
            self.current_model_name = "Lightweight (Fast)"
            model_data = VOSK_MODELS[self.current_language][self.current_model_name]

        target_path = model_data["path"]
        url = model_data["url"]
        folder_name = model_data["folder"]
        
        # 1. Smart Check (Rename extracted folders if found)
        if not os.path.exists(target_path):
            if os.path.exists(folder_name):
                try: os.rename(folder_name, target_path)
                except: pass
            elif os.path.exists("model"): # Check generic 'model' folder
                 try: os.rename("model", target_path)
                 except: pass

        # 2. Download Required?
        if not os.path.exists(target_path):
            # SHOW WARNING DIALOG
            msg = f"Download Required: {self.current_language} - {self.current_model_name}\n\n" \
                  f"File Size: {model_data['size']}\n" \
                  f"RAM Usage: {model_data['ram']}\n\n" \
                  "This will download the AI model to your device.\n" \
                  "Proceed?"
            
            confirm = messagebox.askyesno("Download Model", msg)
            if not confirm:
                self.log_safe("[SYSTEM] Model load cancelled by user.")
                self.after(0, lambda: self.btn_listen.configure(state="normal", text="ENGAGE SYSTEM"))
                return

            try:
                self.download_model(url, target_path, folder_name)
            except Exception as e:
                self.log_safe(f"[ERROR] Init failed: {e}")
                # Manual Fallback
                if messagebox.askyesno("Download Error", "Could not download model (Network Error).\n\nWould you like to select a local model folder manually?"):
                    from tkinter import filedialog
                    local_path = filedialog.askdirectory(title="Select VOSK Model Folder")
                    if local_path and os.path.exists(local_path):
                         # Verify it's a model?
                        if os.path.exists(os.path.join(local_path, "conf/mfcc.conf")):
                             target_path = local_path
                             self.log_safe(f"Using local model: {local_path}")
                        else:
                             messagebox.showerror("Invalid Model", "The selected folder does not appear to be a valid VOSK model.")
                             self.after(0, lambda: self.btn_listen.configure(state="normal", text="ENGAGE SYSTEM"))
                             return
                    else:
                        self.log_safe("[ERROR] No model selected.")
                        self.after(0, lambda: self.btn_listen.configure(state="normal", text="ENGAGE SYSTEM"))
                        return
                else:
                    self.after(0, lambda: self.btn_listen.configure(state="normal", text="ENGAGE SYSTEM"))
                    return

        # 3. Load
        try:
            self.log_safe(f"[SYSTEM] Loading: {self.current_language} ({self.current_model_name})...")
            self.model = Model(target_path)
            self.rec = KaldiRecognizer(self.model, 16000)
            self.log_safe(f"[SYSTEM] Engine Online.")
            self.after(0, lambda: self.lbl_status.configure(text="ONLINE", text_color=COLOR_SUCCESS))

            # --- STARTUP COMMAND ---
            if "startup" in self.commands:
                self.log_safe("[SYSTEM] Running 'startup' macro...")
                threading.Thread(target=self.execute_macro, args=(self.commands["startup"],)).start()
            self.after(0, lambda: self.btn_listen.configure(state="normal", text="ENGAGE SYSTEM"))
        except Exception as e:
            self.log_safe(f"[CRITICAL] Load Error: {e}")
            messagebox.showerror("Load Error", f"Failed to load model from '{target_path}'.\n\nError: {e}\n\nPlease check if the model folder is corrupted.")

    def download_model(self, url, final_path, extract_name):
        zip_name = "model_temp.zip"
        self._last_reported_percent = -1
        
        self.log_safe(f"[DOWNLOAD] Downloading {self.current_language} model...")
        
        try:
            # Custom download loop with timeout and progress
            with urllib.request.urlopen(url, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', -1))
                downloaded = 0
                block_size = 8192
                
                with open(zip_name, 'wb') as f:
                    while True:
                        try:
                            buffer = response.read(block_size)
                        except socket.timeout:
                            raise Exception("Download timed out (Read)")
                            
                        if not buffer:
                            break
                        downloaded += len(buffer)
                        f.write(buffer)
                        
                        if total_size > 0:
                            percent = int(downloaded * 100 / total_size)
                            if percent != self._last_reported_percent:
                                self._last_reported_percent = percent
                                self.after(0, lambda p=percent: self.lbl_status.configure(text=f"DL: {p}%", text_color="orange"))
                                if percent % 10 == 0:
                                    print(f"Downloading: {percent}%")
                        else:
                             # Indeterminate progress - update every ~1MB
                             if downloaded % (1024*1024) < block_size:
                                 mb = downloaded // (1024*1024)
                                 self.after(0, lambda m=mb: self.lbl_status.configure(text=f"DL: {m}MB", text_color="orange"))

        except Exception as e:
            if os.path.exists(zip_name): os.remove(zip_name)
            raise e
        
        self.log_safe("[DOWNLOAD] Extracting...")
        try:
            with zipfile.ZipFile(zip_name, 'r') as z:
                z.extractall(".")
        except zipfile.BadZipFile:
            if os.path.exists(zip_name): os.remove(zip_name)
            raise Exception("Downloaded file is corrupted (Bad Zip)")
            
        if os.path.exists(extract_name):
            if os.path.exists(final_path): shutil.rmtree(final_path)
            os.rename(extract_name, final_path)
            
        if os.path.exists(zip_name): os.remove(zip_name)
        self.log_safe("[DOWNLOAD] Installed.")

    # --- MACRO BUILDER ---
    def add_command_dialog(self, initial_phrase="", initial_macro=""):
        dialog = ctk.CTkToplevel(self)
        dialog.title("Macro Builder" if not initial_macro else "Edit Command")
        dialog.geometry("700x600")
        dialog.attributes("-topmost", True)
        
        # Track old phrase if editing
        self._editing_phrase = initial_phrase
        
        # 1. Triggers
        ctk.CTkLabel(dialog, text="1. Trigger Phrases", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(15, 5))
        ctk.CTkLabel(dialog, text="One trigger per command recommended. Use commas ONLY for multiple triggers.", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w", padx=20)
        
        e_phrase = ctk.CTkEntry(dialog, placeholder_text="e.g. go, move, run")
        e_phrase.pack(fill="x", padx=20, pady=5)
        if initial_phrase: e_phrase.insert(0, initial_phrase)

        ctk.CTkLabel(dialog, text="2. Action / Macro", font=ctk.CTkFont(size=14, weight="bold"), text_color=COLOR_ACCENT).pack(anchor="w", padx=20, pady=(20, 5))
        builder_frame = ctk.CTkFrame(dialog)
        builder_frame.pack(fill="x", padx=20, pady=5)

        controls_row = ctk.CTkFrame(builder_frame, fg_color="transparent")
        controls_row.pack(fill="x", padx=10, pady=10)

        action_type = ctk.CTkOptionMenu(controls_row, values=["Press Key", "Type Text", "Wait (Delay)", "Open App/File", "Open Website", "System Command", "Webhook (API)", "Python Code", "Say (TTS)"], width=140)
        action_type.pack(side="left", padx=5)

        input_container = ctk.CTkFrame(controls_row, fg_color="transparent")
        input_container.pack(side="left", fill="x", expand=True, padx=5)
        self.current_input_widget = None

        def clear_input_container():
            for w in input_container.winfo_children(): w.destroy()

        def record_key_event(event):
            key = event.keysym.lower()
            mapping = {'return': 'enter', 'prior': 'pageup', 'next': 'pagedown', 'control_l': 'ctrl', 'control_r': 'ctrl', 'alt_l': 'alt', 'shift_l': 'shift'}
            final_key = mapping.get(key, key)
            dialog.unbind('<Key>')
            if isinstance(self.current_input_widget, ctk.CTkButton):
                 self.current_input_widget.configure(text=f"Key: {final_key}", fg_color=COLOR_SUCCESS)
                 self.current_input_widget.recorded_key = final_key 

        def start_recording():
            if isinstance(self.current_input_widget, ctk.CTkButton):
                self.current_input_widget.configure(text="Listening...", fg_color=COLOR_ACCENT)
                dialog.bind('<Key>', record_key_event)
                dialog.focus_set()

        def browse_file():
            path = filedialog.askopenfilename()
            if path and isinstance(self.current_input_widget, ctk.CTkEntry):
                self.current_input_widget.delete(0, 'end')
                self.current_input_widget.insert(0, path)

        def on_type_change(choice):
            clear_input_container()
            if choice == "Press Key":
                self.current_input_widget = ctk.CTkButton(input_container, text="Record Key", fg_color=COLOR_SIDEBAR, command=start_recording)
                self.current_input_widget.recorded_key = "" 
                self.current_input_widget.pack(fill="x")
            elif choice == "System Command":
                cmds = ["shutdown", "restart", "sleep", "hibernate", "lock", "empty_bin", 
                        "volume_up", "volume_down", "mute", "play_pause", "next_track", "prev_track",
                        "minimize_all", "screenshot", "task_manager"]
                self.current_input_widget = ctk.CTkComboBox(input_container, values=cmds)
                self.current_input_widget.set("shutdown")
                self.current_input_widget.pack(fill="x")
            elif choice == "Webhook (API)":
                self.current_input_widget = ctk.CTkEntry(input_container, placeholder_text="http://...")
                self.current_input_widget.pack(fill="x")
            elif choice == "Python Code":
                self.current_input_widget = ctk.CTkEntry(input_container, placeholder_text="e.g. print('Hello World')")
                self.current_input_widget.pack(fill="x")
            elif choice == "Open App/File":
                self.current_input_widget = ctk.CTkEntry(input_container, placeholder_text="C:/Path/To/App.exe")
                self.current_input_widget.pack(side="left", fill="x", expand=True)
                ctk.CTkButton(input_container, text="📂", width=40, command=browse_file, fg_color=COLOR_SIDEBAR).pack(side="right", padx=5)
            elif choice == "Open Website":
                sites = [
                    "google.com", "youtube.com", "reddit.com", "github.com", "chatgpt.com", "wikipedia.org",
                    "twitter.com", "facebook.com", "instagram.com", "linkedin.com", "tiktok.com", "twitch.tv", "discord.com", "pinterest.com",
                    "amazon.com", "ebay.com", "walmart.com", "aliexpress.com", "etsy.com",
                    "cnn.com", "bbc.com", "nytimes.com", "foxnews.com",
                    "stackoverflow.com", "medium.com", "dev.to", "kaggle.com", "huggingface.co",
                    "netflix.com", "spotify.com", "hulu.com", "disneyplus.com",
                    "gmail.com", "outlook.live.com", "canva.com", "zoom.us", "notion.so", "trello.com", "slack.com"
                ]
                self.current_input_widget = ctk.CTkComboBox(input_container, values=sites)
                self.current_input_widget.set("")
                self.current_input_widget.pack(fill="x")
            else:
                self.current_input_widget = ctk.CTkEntry(input_container, placeholder_text="Value...")
                self.current_input_widget.pack(fill="x")
        
        action_type.configure(command=on_type_change)
        on_type_change("Press Key")

        chain_list = tk.Listbox(builder_frame, height=6, bg="#252526", fg="white", borderwidth=0, font=("Segoe UI", 10))
        chain_list.pack(fill="x", padx=10, pady=(0, 10))
        
        # Pre-populate chain if editing
        if initial_macro:
            for step in initial_macro.split(";"):
                if step.strip():
                    chain_list.insert('end', step.strip())

        def add_step():
            kind = action_type.get()
            val = ""
            if isinstance(self.current_input_widget, ctk.CTkEntry): val = self.current_input_widget.get()
            elif isinstance(self.current_input_widget, ctk.CTkComboBox): val = self.current_input_widget.get()
            elif isinstance(self.current_input_widget, ctk.CTkButton):
                val = getattr(self.current_input_widget, "recorded_key", "")
            
            if not val: return
            
            code = ""
            if kind == "Press Key": code = f"press:{val}"
            elif kind == "Type Text": code = f"type:{val}"
            elif kind == "Wait (Delay)": code = f"wait:{val}"
            elif kind == "Open Website": code = f"browser:{val}"
            elif kind == "Open App/File": code = f"app:{val}"
            elif kind == "System Command": code = f"system:{val}"
            elif kind == "Say (TTS)": code = f"say:{val}"
            elif kind == "Webhook (API)": code = f"webhook:{val}"
            elif kind == "Python Code": code = f"python:{val}"
            
            if code: chain_list.insert('end', code)

        ctk.CTkButton(controls_row, text="Add Step", width=80, command=add_step, fg_color=COLOR_SIDEBAR).pack(side="right", padx=5)
        ctk.CTkButton(builder_frame, text="Clear List", width=100, fg_color=COLOR_DANGER, height=24, command=lambda: chain_list.delete(0, 'end')).pack(anchor="e", padx=10, pady=(0, 10))

        def save():
            raw_phrases = e_phrase.get().lower()
            steps = list(chain_list.get(0, 'end'))
            final_macro = "; ".join(steps)
            if raw_phrases and final_macro:
                # If we were editing, remove the old phrase first if it changed
                if hasattr(self, '_editing_phrase') and self._editing_phrase and self._editing_phrase in self.commands:
                    del self.commands[self._editing_phrase]
                
                for p in [p.strip() for p in raw_phrases.replace('|', ',').split(',') if p.strip()]:
                    self.commands[p] = final_macro
                self.refresh_ui()
                self.auto_save_profile()
                dialog.destroy()
        
        ctk.CTkButton(dialog, text="SAVE COMMAND", command=save, fg_color=COLOR_SUCCESS, height=45, font=ctk.CTkFont(size=14, weight="bold")).pack(side="bottom", pady=20, padx=20, fill="x")

    def quick_add_command(self):
        if self.last_heard_phrase: self.add_command_dialog(initial_phrase=self.last_heard_phrase)

    # --- Core Logic ---
    def log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_box.insert("end", f"[{timestamp}] {msg}\n")
        self.log_box.see("end")
        print(f"[{timestamp}] {msg}")

    def log_safe(self, msg):
        self.after(0, lambda: self.log(msg))

    def on_model_switch(self, choice):
        if choice == self.current_model_name: return
        self.current_model_name = choice
        self.save_settings()
        if self.is_listening: self.stop_listening()
        self.btn_listen.configure(state="disabled", text="SWITCHING...")
        threading.Thread(target=self.trigger_model_load, daemon=True).start()

    def toggle_listening(self):
        if not self.is_listening: self.start_listening()
        else: self.stop_listening()

    def start_listening(self):
        # Admin privilege check for game interaction
        if sys.platform == "win32":
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logging.warning("NOT RUNNING AS ADMIN - Game interaction may be blocked.")
                # self.log_safe("!!! WARNING: NOT RUNNING AS ADMIN - Games may block inputs !!!")

        if not self.model or not self.rec:
            messagebox.showerror("Error", "Speech Engine not initialized.\nPlease check your model settings or internet connection.")
            self.stop_listening() # Reset UI
            return

        self.is_listening = True
        self.play_sfx("engage")
        self.btn_listen.configure(text="STOP SYSTEM", fg_color=COLOR_DANGER, hover_color=COLOR_DANGER)
        self.lbl_status.configure(text="LISTENING", text_color=COLOR_SUCCESS)
        self.update_overlay("Listening...", "#00aaff")
        
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2048)
        self.stream.start_stream()
        threading.Thread(target=self.listen_loop, daemon=True).start()

    def stop_listening(self):
        self.is_listening = False
        self.play_sfx("disengage")
        self.btn_listen.configure(text="ENGAGE SYSTEM", fg_color=COLOR_SUCCESS, hover_color=COLOR_SUCCESS_HOVER)
        self.lbl_status.configure(text="STANDBY", text_color="orange")
        self.update_overlay("Standby.", "#ffaa00")
        self.audio_bar.set(0)
        
        if self.stream: self.stream.stop_stream(); self.stream.close()
        if self.p: self.p.terminate()

    def listen_loop(self):
        last_heartbeat = time.time()
        while self.is_listening:
            if time.time() - last_heartbeat > 30:
                logging.debug("Heartbeat: Listening loop active.")
                last_heartbeat = time.time()

            if self.input_mode == "Push-to-Talk" and PTT_AVAILABLE:
                if not keyboard.is_pressed(self.ptt_key):
                    self.after(0, lambda: self.audio_bar.set(0))
                    self.update_overlay("PTT: Waiting for Input", "#888888")
                    time.sleep(0.05)
                    continue

            try:
                if not self.stream or not self.stream.is_active():
                    logging.warning("Audio stream inactive. Attempting restart...")
                    self.stream.stop_stream()
                    self.stream.close()
                    self.stream = self.p.open(format=pyaudio.paInt16, channels=1, rate=16000, input=True, frames_per_buffer=2048)
                    self.stream.start_stream()

                data = self.stream.read(2048, exception_on_overflow=False)
                # Visualizer
                if len(data) > 0:
                    shorts = struct.unpack(f"{len(data)//2}h", data)
                    sum_squares = sum(s**2 for s in shorts[::10]) 
                    rms = (sum_squares / (len(shorts)/10)) ** 0.5
                    level = min(max(rms / 3000, 0.0), 1.0)
                    self.after(0, lambda l=level: self.audio_bar.set(l))
                
                if self.rec.AcceptWaveform(data):
                    text = json.loads(self.rec.Result()).get("text", "")
                    if text:
                        self.log_safe(f"Heard: '{text}'")
                        self.update_last_heard(text)
                        
                        if self.dictation_mode.get() and self.check_context():
                            pyautogui.write(text + " ")
                            self.update_overlay(f"Dictated: {text}", "#ffffff")
                        else:
                            self.process_command(text)
            except Exception as e:
                logging.error(f"Error in listen loop: {e}")
                time.sleep(0.1) # Avoid tight loop on failure

    def update_last_heard(self, text):
        self.last_heard_phrase = text
        self.after(0, lambda: self.lbl_last_heard.configure(text=f"'{text}'"))
        if not self.dictation_mode.get():
            self.update_overlay(f"Heard: {text}", "#00aaff")
        self.after(0, lambda: self.btn_quick_add.configure(state="normal" if not any(p in text for p in self.commands) else "disabled"))

    def check_match(self, text, is_partial=False):
        for phrase, action in self.commands.items():
            if phrase in text:
                prefix = "FAST MATCH" if is_partial else "MATCH"
                self.log_safe(f">> {prefix}: '{phrase}'")
                # self.play_sfx("success") # User requested removal
                threading.Thread(target=self.execute_macro, args=(action,)).start()
                if is_partial: self.rec.Reset()
                break

    def check_context(self):
        # OPTIMIZATION: If target_window is empty, return immediately (fast path)
        if not self.target_window: return True
        
        # If no window context logic is set up, always return True
        if not CONTEXT_AVAILABLE: return True
        
        try:
            active = gw.getActiveWindow()
            if active and self.target_window.lower() in active.title.lower():
                return True
        except: pass
        return False

    def process_command(self, text):
        if not self.check_context(): return
        self.check_match(text, is_partial=False)

    def execute_macro(self, macro_str):
        steps = macro_str.split(";")
        for step in steps:
            step = step.strip()
            if not step: continue
            try:
                if ":" in step:
                    cmd, arg = step.split(":", 1)
                    cmd = cmd.lower().strip()
                    arg = arg.strip()
                    
                    # --- RANDOMIZATION FEATURE ---
                    # If arg contains '|', pick one randomly
                    if "|" in arg:
                        arg = random.choice(arg.split("|"))
                    
                    if cmd == "browser":
                        if not arg.startswith("http"): arg = "https://" + arg
                        webbrowser.open(arg)
                        self.log_safe(f"   [ACT] Browser: {arg}")
                    elif cmd == "app":
                        self.log_safe(f"   [ACT] App: {arg}")
                        try: subprocess.Popen(arg)
                        except: os.startfile(arg)
                    elif cmd == "say":
                        self.log_safe(f"   [TTS] {arg}")
                        if self.tts_engine:
                            self.tts_engine.say(arg)
                            self.tts_engine.runAndWait()
                    elif cmd == "wait":
                        time.sleep(float(arg))
                    elif cmd == "type":
                        pyautogui.write(arg)
                    elif cmd == "press":
                        if "+" in arg: pyautogui.hotkey(*arg.split("+"))
                        else: pyautogui.press(arg)
                    elif cmd == "hotkey":
                        pyautogui.hotkey(*arg.split("+"))
                    elif cmd == "internal":
                        if arg == "stop_listening":
                            self.stop_listening()
                    elif cmd == "system":
                        if arg == "shutdown": os.system("shutdown /s /t 0")
                        elif arg == "restart": os.system("shutdown /r /t 0")
                        elif arg == "sleep": os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
                        elif arg == "hibernate": os.system("shutdown /h")
                        elif arg == "lock": os.system("rundll32.exe user32.dll,LockWorkStation")
                        elif arg == "empty_bin": 
                             try:
                                 import ctypes
                                 # SHERB_NOCONFIRMATION = 0x00000001
                                 # SHERB_NOPROGRESSUI = 0x00000002
                                 # SHERB_NOSOUND = 0x00000004
                                 ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 7)
                                 self.log_safe("   [INFO] Recycle Bin Emptied")
                             except Exception as e:
                                 self.log_safe(f"   [ERROR] Bin Empty Failed: {e}")
                        elif arg == "volume_up": pyautogui.press("volumeup")
                        elif arg == "volume_down": pyautogui.press("volumedown")
                        elif arg == "mute": pyautogui.press("volumemute")
                        elif arg == "play_pause": pyautogui.press("playpause")
                        elif arg == "next_track": pyautogui.press("nexttrack")
                        elif arg == "prev_track": pyautogui.press("prevtrack")
                        elif arg == "minimize_all": pyautogui.hotkey('win', 'd')
                        elif arg == "screenshot": 
                            fname = f"screenshot_{int(time.time())}.png"
                            pyautogui.screenshot(fname)
                            self.log_safe(f"   [INFO] Saved: {fname}")
                        elif arg == "task_manager": pyautogui.hotkey('ctrl', 'shift', 'esc')
                    elif cmd == "sound" or cmd == "play":
                        self.log_safe(f"   [SFX] Playing: {arg}")
                        if SFX_AVAILABLE and os.path.exists(arg):
                            winsound.PlaySound(arg, winsound.SND_FILENAME | winsound.SND_ASYNC)
                    elif cmd == "focus":
                        self.log_safe(f"   [FOCUS] Switching to: {arg}")
                        if CONTEXT_AVAILABLE:
                            try:
                                wins = gw.getWindowsWithTitle(arg)
                                if wins: wins[0].activate()
                            except: pass
                    else:
                        pyautogui.press(step)
                else:
                    pyautogui.press(step)
            except Exception as e:
                self.log_safe(f"   [ERROR] Macro fail: {e}")

    # --- Profile Mgmt ---
    def load_preset(self, preset_name):
        if preset_name in PRESETS:
            self.commands = PRESETS[preset_name].copy()
            self.active_profile_name = preset_name
            self.active_profile_path = None
            self.refresh_ui()

    def new_profile(self):
        self.commands = {}
        self.active_profile_name = "Untitled"
        self.active_profile_path = None
        self.refresh_ui()

    def save_profile(self):
        path = filedialog.asksaveasfilename(initialdir=PROFILES_DIR, defaultextension=".json", filetypes=[("JSON", "*.json")])
        if path:
            with open(path, 'w') as f:
                json.dump(self.commands, f, indent=4)
            self.active_profile_name = os.path.basename(path)
            self.active_profile_path = path
            self.lbl_active_profile.configure(text=f"Profile: {self.active_profile_name}")
            self.log(f"Saved: {self.active_profile_name}")
            self.refresh_ui()
            try: self.refresh_profile_list()
            except: pass

    def open_profile(self):
        path = filedialog.askopenfilename(initialdir=PROFILES_DIR, filetypes=[("JSON", "*.json")])
        if path:
            self.load_profile(path)

    def load_profile(self, path):
        if os.path.exists(path):
            with open(path, 'r') as f:
                self.commands = json.load(f)
            self.active_profile_name = os.path.basename(path)
            self.active_profile_path = path
            self.lbl_active_profile.configure(text=f"Profile: {self.active_profile_name}")
            self.log(f"Loaded: {self.active_profile_name}")
            self.refresh_ui()
        else:
            self.refresh_ui()

    def refresh_ui(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        for p, a in self.commands.items():
            self.tree.insert("", tk.END, values=(p, a))

    def edit_command(self):
        sel = self.tree.selection()
        if sel:
            item = sel[0]
            phrase = self.tree.item(item)['values'][0]
            macro = self.tree.item(item)['values'][1]
            self.add_command_dialog(initial_phrase=phrase, initial_macro=macro)

    def remove_command(self):
        sel = self.tree.selection()
        if sel:
            for item in sel:
                phrase = self.tree.item(item)['values'][0]
                if phrase in self.commands:
                    del self.commands[phrase]
            self.refresh_ui()
            self.auto_save_profile()

    def auto_save_profile(self):
        if self.active_profile_path and os.path.exists(self.active_profile_path):
            try:
                with open(self.active_profile_path, 'w') as f:
                    json.dump(self.commands, f, indent=4)
                self.log(f"Auto-saved: {self.active_profile_name}")
            except Exception as e:
                self.log(f"Auto-save failed: {e}")

    def show_about(self):
        messagebox.showinfo("About VOX OPS", ABOUT_TEXT)

if __name__ == "__main__":
    app = VoiceApp()
    app.mainloop()
