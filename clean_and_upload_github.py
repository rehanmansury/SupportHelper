import os
import sys
import subprocess

def clean_and_upload():
    """Clean up GitHub repository and upload new structure"""
    
    print("🧹 Cleaning up GitHub Repository")
    print("=" * 50)
    
    # Get current directory
    repo_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Check if we're in a git repo
    if not os.path.exists(os.path.join(repo_dir, '.git')):
        print("❌ Not in a git repository!")
        return
    
    print("\n📋 Current status:")
    os.system('git status')
    
    # Step 1: Add all changes (including deletions)
    print("\n[1/4] Adding all changes...")
    subprocess.run(['git', 'add', '-A'], cwd=repo_dir)
    
    # Step 2: Commit the reorganization
    print("\n[2/4] Committing reorganization...")
    result = subprocess.run([
        'git', 'commit', '-m', 
        'Restructure project for better organization\n\n'
        '- Move packaging tools to packagingtools/ folder\n'
        '- Move backup files to Extras/ folder\n'
        '- Keep only essential files in root\n'
        '- Update all paths in packaging scripts'
    ], cwd=repo_dir)
    
    if result.returncode != 0:
        print("⚠️ No changes to commit or commit failed")
    
    # Step 3: Push to GitHub
    print("\n[3/4] Pushing to GitHub...")
    result = subprocess.run(['git', 'push', 'origin', 'main'], cwd=repo_dir)
    
    if result.returncode != 0:
        print("❌ Failed to push to GitHub!")
        print("\nPossible solutions:")
        print("1. Check your internet connection")
        print("2. Verify you have push access to the repository")
        print("3. Check if you need to authenticate")
        return
    
    # Step 4: Show final structure
    print("\n[4/4] Repository structure uploaded:")
    print("\n📁 SupportHelper/")
    print("├── 📄 main.py")
    print("├── 📄 world_clock_tab_pyqt.py")
    print("├── 📄 database.py")
    print("├── 📄 ocr_utils.py")
    print("├── 📄 requirements.txt")
    print("├── 📄 README.md")
    print("├── 📁 assets/")
    print("├── 📁 logs/")
    print("├── 📁 clipboard_history/")
    print("├── 📁 .git/")
    print("├── 📁 packagingtools/")
    print("│   ├── 📄 build_exe.py")
    print("│   ├── 📄 simple_sign.py")
    print("│   ├── 📄 build_and_package.py")
    print("│   ├── 📄 *.ps1, *.bat (cert scripts)")
    print("│   ├── 📁 dist/ (build outputs)")
    print("│   └── 📄 README_USAGE.md")
    print("└── 📁 Extras/")
    print("    ├── 📄 backup files")
    print("    └── 📄 miscellaneous")
    
    print("\n✅ Repository successfully updated on GitHub!")
    print("\n🔗 Repository: https://github.com/rehanmansury/SupportHelper")
    
    # Ask if user wants to create a release
    create_release = input("\n🚀 Do you want to create a new release? (y/n): ").lower().strip()
    
    if create_release == 'y':
        print("\n📦 To create a release:")
        print("1. Go to: https://github.com/rehanmansury/SupportHelper/releases")
        print("2. Click 'Create a new release'")
        print("3. Tag version: v1.0.0")
        print("4. Title: SupportHelper v1.0.0 - Reorganized")
        print("5. Upload files from packagingtools/dist/")

if __name__ == "__main__":
    clean_and_upload()
