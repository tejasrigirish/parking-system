"""
Park Wave - Smart Parking System (Separate Desktop Window)
Double-clicking this .pyw file opens the application purely in a dedicated graphical window
with zero terminal / console window attached.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from app_gui import run_app

if __name__ == "__main__":
    run_app()
