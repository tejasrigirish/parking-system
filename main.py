"""
Main Entry Point for the Smart Parking System.
Starts the Python REST backend and launches the interactive HTML/CSS/JS web UI in a separate window.
Also supports launching the Tkinter desktop GUI via '--gui' argument.
"""

import sys
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

def main():
    if "--gui" in sys.argv:
        from app_gui import run_app
        print("Launching Desktop Tkinter GUI in a separate window...")
        run_app()
    elif "--cli" in sys.argv:
        from main_cli import main as run_cli
        run_cli()
    else:
        # Default: Launch the modern interactive HTML/CSS/JS web UI
        from server import run_server
        print("Starting Park Wave Backend & Launching Interactive Web UI...")
        run_server(port=5000, open_browser=True)

if __name__ == "__main__":
    main()
