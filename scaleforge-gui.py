

#!/usr/bin/env python3
"""ScaleForge GUI entry point."""
import os
import sys
from pathlib import Path

# Add project root to PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from scaleforge.gui.core import ScaleForgeApp

if __name__ == '__main__':
    # Set environment variables for Kivy
    os.environ['KIVY_NO_ARGS'] = '1'
    os.environ['KIVY_NO_CONSOLELOG'] = '1'
    
    ScaleForgeApp().run()

