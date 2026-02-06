import os
import sys
import subprocess
import json
from datetime import datetime

def create_github_release():
    """Create a GitHub release with the executable"""
    
    # Get the correct paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Configuration
    EXE_PATH = os.path.join(current_dir, 'dist', 'SupportHelper.exe')
    PORTABLE_PATH = os.path.join(current_dir, 'dist', 'SupportHelper_Portable')
    REPO_NAME = "rehanmansury/SupportHelper"
    
    print("🚀 Creating GitHub Release for SupportHelper")
    print("=" * 50)
    
    # Check if executable exists
    if not os.path.exists(EXE_PATH):
        print(f"❌ Error: Executable not found at {EXE_PATH}")
        print("Please run build_exe.py first!")
        return
    
    # Get file info
    exe_size = os.path.getsize(EXE_PATH) / (1024*1024)
    print(f"📦 Found executable: {EXE_PATH}")
    print(f"📊 Size: {exe_size:.2f} MB")
    
    # Get version (you can modify this)
    version = input("\nEnter version number (e.g., 1.0.0): ").strip()
    if not version:
        version = "1.0.0"
    
    # Create release notes
    release_notes = f"""# SupportHelper v{version}

## Features
- World Clock with multiple time zones
- Time zone conversion
- Meeting scheduling with Teams/Outlook integration
- Custom URL integrations
- Pinned cities for quick access
- DST support
- Parameter guide with examples
- Popup confirmations for all actions

## Installation
1. Download `SupportHelper.exe` below
2. Double-click to run (no installation required)
3. The application will create a database automatically

## Portable Version
- Download `SupportHelper_Portable.zip` for the full package
- Includes README.txt with instructions

## System Requirements
- Windows 10 or later
- No additional dependencies required

## Changes in v{version}
- Initial release with all features
- Fixed integration type saving
- Added comprehensive parameter guide
- Improved popup messages
- Enhanced email integration
"""
    
    # Save release notes to file
    with open('release_notes.md', 'w') as f:
        f.write(release_notes)
    
    print("\n📝 Release notes saved to release_notes.md")
    
    # Instructions for manual release
    print("\n" + "=" * 50)
    print("📋 Next Steps - Manual Release Creation:")
    print("=" * 50)
    print(f"\n1. Go to: https://github.com/{REPO_NAME}/releases")
    print("2. Click 'Create a new release'")
    print(f"3. Tag version: v{version}")
    print(f"4. Title: SupportHelper v{version}")
    print("5. Copy/paste contents from release_notes.md")
    print("6. Attach files:")
    print(f"   - {EXE_PATH}")
    print(f"   - {PORTABLE_PATH} (as a zip file)")
    print("\n7. Click 'Publish release'")
    
    # Create zip for portable version
    import zipfile
    zip_path = os.path.join('dist', 'SupportHelper_Portable.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(PORTABLE_PATH):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, PORTABLE_PATH)
                zipf.write(file_path, arcname)
    
    print(f"\n✅ Portable zip created: {zip_path}")
    print(f"📊 Zip size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")
    
    print("\n🎉 Ready to upload to GitHub!")

if __name__ == "__main__":
    create_github_release()
