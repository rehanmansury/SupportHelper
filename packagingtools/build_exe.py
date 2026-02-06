import os
import sys
import shutil
import subprocess

def build_exe():
    """Build the SupportHelper executable"""
    print("Building SupportHelper executable...")
    
    # Get the correct paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    
    # Clean previous builds
    for folder in ['build', 'dist']:
        folder_path = os.path.join(current_dir, folder)
        if os.path.exists(folder_path):
            print(f"Cleaning {folder} folder...")
            try:
                shutil.rmtree(folder_path)
            except PermissionError:
                print(f"Permission denied for {folder}, trying to remove contents...")
                import stat
                def remove_readonly(func, path, _):
                    os.chmod(path, stat.S_IWRITE)
                    func(path)
                shutil.rmtree(folder_path, onerror=remove_readonly)
    
    # Build the executable using simple PyInstaller command
    print("Running PyInstaller...")
    subprocess.run([
        sys.executable, 
        '-m', 
        'PyInstaller',
        '--name=SupportHelper',
        '--onefile',
        '--windowed',  # No console window for GUI app
        '--clean',
        '--noconfirm',
        '--add-data=' + os.path.join(parent_dir, 'database.py') + ';.',
        '--add-data=' + os.path.join(parent_dir, 'world_clock_tab_pyqt.py') + ';.',
        '--hidden-import=pytz',
        '--hidden-import=sqlite3',
        '--hidden-import=urllib.parse',
        '--hidden-import=webbrowser',
        '--hidden-import=subprocess',
        os.path.join(parent_dir, 'main.py')
    ])
    
    # Check if build was successful
    exe_path = os.path.join(current_dir, 'dist', 'SupportHelper.exe')
    if os.path.exists(exe_path):
        print(f"\n✅ Build successful!")
        print(f"📦 Executable created at: {exe_path}")
        print(f"📊 File size: {os.path.getsize(exe_path) / (1024*1024):.2f} MB")
        
        # Create a portable folder with database
        portable_dir = os.path.join(current_dir, 'dist', 'SupportHelper_Portable')
        if not os.path.exists(portable_dir):
            os.makedirs(portable_dir)
        
        # Copy executable
        shutil.copy2(exe_path, portable_dir)
        
        # Create a README for the portable version
        readme_content = """SupportHelper - Portable Version
=====================================

This is the portable version of SupportHelper.

To run:
1. Double-click SupportHelper.exe
2. The application will create a database file automatically

Features:
- World Clock with multiple time zones
- Meeting scheduling with Teams/Outlook integration
- Custom URL integrations
- And much more!

For updates and support, visit:
https://github.com/rehanmansury/SupportHelper

Database file:
- The app will create 'clip_snippet_manager.db' automatically
- This file stores your settings and data
- Keep this file in the same folder as the exe
"""
        
        with open(os.path.join(portable_dir, 'README.txt'), 'w') as f:
            f.write(readme_content)
        
        print(f"\n📁 Portable package created at: {portable_dir}")
        
    else:
        print("\n❌ Build failed! Check the error messages above.")
    
    print("\nBuild process completed!")

if __name__ == "__main__":
    build_exe()
