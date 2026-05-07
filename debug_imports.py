#!/usr/bin/env python3
"""
Auto-install openpyxl if missing, then check installation
"""

import subprocess
import sys

print("=" * 70)
print("AUTO-INSTALLING openpyxl...")
print("=" * 70)

try:
    import openpyxl
    print(f"✅ openpyxl already installed: version {openpyxl.__version__}")
except ImportError:
    print("📦 Installing openpyxl (this may take a moment)...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl", "-q"])
        print("✅ openpyxl installed successfully!")
    except Exception as e:
        print(f"❌ Failed to install openpyxl: {e}")
        sys.exit(1)

print()
print("=" * 70)
print("VERIFYING INSTALLATION")
print("=" * 70)

EXCEL_AVAILABLE = False

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    
    print(f"✅ openpyxl version: {openpyxl.__version__}")
    print("✅ All imports successful")
    EXCEL_AVAILABLE = True
    print(f"✅ EXCEL_AVAILABLE = {EXCEL_AVAILABLE}")

except Exception as e:
    print(f"❌ Error: {e}")
    EXCEL_AVAILABLE = False
    print(f"❌ EXCEL_AVAILABLE = {EXCEL_AVAILABLE}")

print()
print("=" * 70)
if EXCEL_AVAILABLE:
    print("✅ Ready to run your main script!")
else:
    print("❌ openpyxl is still not available")
print("=" * 70)
