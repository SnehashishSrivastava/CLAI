#!/usr/bin/env python3
# file: run_gui.py
# Launch the CLAI GUI
# Usage: python run_gui.py

import sys
from pathlib import Path

# Add CLAI to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from gui.app import main

if __name__ == "__main__":
    main()

