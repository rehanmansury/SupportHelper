import os
import sys
import subprocess
import zipfile
import shutil

def create_installer():
    """Create an installer package with proper configuration"""
    print("📦 Creating SupportHelper installer package...")
    
    # Get the correct paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths
    source_exe = os.path.join(current_dir, 'dist', 'SupportHelper.exe')
    output_dir = os.path.join(current_dir, 'dist', 'SupportHelper_Installer')
    
    if not os.path.exists(source_exe):
        print(f"❌ Error: {source_exe} not found!")
        return
    
    # Clean output directory
    if os.path.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)
    
    # Copy EXE
    shutil.copy2(source_exe, output_dir)
    
    # Create installation instructions
    install_instructions = """SupportHelper Installation Instructions
============================================

IMPORTANT: Windows Security Warning
----------------------------------
When you run SupportHelper.exe for the first time, Windows may show a security warning.
This is normal for applications that are not from the Microsoft Store.

TO RUN THE APPLICATION:
------------------------

Method 1: Recommended
1. Right-click on SupportHelper.exe
2. Select "Properties"
3. Check "Unblock" at the bottom (if present)
4. Click "OK"
5. Double-click to run

Method 2: If blocked by Windows Defender
1. Click on "More info" in the security warning
2. Click "Run anyway"
3. Check the box to remember your choice

Method 3: Add to Windows Defender exclusions
1. Open Windows Security
2. Go to Virus & threat protection
3. Click "Manage settings"
4. Add an exclusion for the SupportHelper folder

ABOUT THE WARNING:
------------------
SupportHelper is a safe application built with PyInstaller.
The warning appears because it's not digitally signed.
Digital signing certificates are expensive ($300+/year).

For professional use, consider:
1. Running from a trusted network location
2. Adding to your organization's software whitelist
3. Contacting your IT administrator

Features:
- World Clock with time zones
- Meeting scheduling
- Custom integrations
- No installation required - just run the exe!

Support: https://github.com/rehanmansury/SupportHelper
"""
    
    with open(os.path.join(output_dir, "INSTALL.txt"), "w") as f:
        f.write(install_instructions)
    
    # Create a batch file to run with admin rights if needed
    batch_content = """@echo off
echo SupportHelper Launcher
echo ====================
echo.
echo If Windows blocks the application, this will help.
echo.
pause
cd /d "%~dp0"
if exist SupportHelper.exe (
    echo Launching SupportHelper...
    start SupportHelper.exe
) else (
    echo Error: SupportHelper.exe not found!
    pause
)
"""
    
    with open(os.path.join(output_dir, "Run_SupportHelper.bat"), "w") as f:
        f.write(batch_content)
    
    # Create ZIP
    zip_path = os.path.join('dist', 'SupportHelper_Installer.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(output_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, output_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n✅ Installer package created!")
    print(f"📁 Location: {output_dir}")
    print(f"📦 ZIP file: {zip_path}")
    print(f"📊 Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")
    
    print("\n📋 Distribution Instructions:")
    print("1. Upload SupportHelper_Installer.zip to GitHub Releases")
    print("2. Users should:")
    print("   - Download and extract the ZIP")
    print("   - Read INSTALL.txt")
    print("   - Right-click SupportHelper.exe → Properties → Unblock")
    print("   - Run the application")

if __name__ == "__main__":
    create_installer()
