import subprocess
import json

def update_github_info():
    """Script to help update GitHub repository information"""
    
    print("🔄 GitHub Repository Update Guide")
    print("=" * 50)
    
    print("\n✅ Local updates completed:")
    print("  - README.md already updated to SupportHelper")
    print("  - start_SupportHelper.bat updated")
    print("  - clipboard_history.json updated")
    print("  - All code references updated")
    
    print("\n📋 To update GitHub repository information:")
    print("\n1. Update Repository Description:")
    print("   - Go to: https://github.com/rehanmansury/SupportHelper")
    print("   - Click the gear icon ⚙️ or 'About' section")
    print("   - Update description to:")
    print("     'A comprehensive support helper tool with World Clock features, meeting scheduling, and custom integrations.'")
    print("   - Update website to: https://github.com/rehanmansury/SupportHelper")
    
    print("\n2. Update Topics/Tags:")
    print("   - In the About section, add topics:")
    print("     - python")
    print("     - pyqt5")
    print("     - world-clock")
    print("     - meeting-scheduler")
    print("     - clipboard-manager")
    print("     - ocr")
    print("     - support-tools")
    
    print("\n3. Update Releases (if any):")
    print("   - Go to: https://github.com/rehanmansury/SupportHelper/releases")
    print("   - Edit any releases mentioning 'Project Custom'")
    print("   - Update titles and descriptions")
    
    print("\n4. Update Wiki (if exists):")
    print("   - Go to: https://github.com/rehanmansury/SupportHelper/wiki")
    print("   - Update any wiki pages mentioning 'Project'")
    
    print("\n5. Update Issues (if any):")
    print("   - Go to: https://github.com/rehanmansury/SupportHelper/issues")
    print("   - Update any issue titles or descriptions")
    
    print("\n6. Check GitHub Pages (if enabled):")
    print("   - Go to: https://github.com/rehanmansury/SupportHelper/pages")
    print("   - Update any content mentioning 'Project'")
    
    print("\n" + "=" * 50)
    print("✅ Current Repository Status:")
    
    # Check current git status
    result = subprocess.run(['git', 'status'], capture_output=True, text=True)
    print(result.stdout)
    
    # Get remote info
    result = subprocess.run(['git', 'remote', '-v'], capture_output=True, text=True)
    print("\n📡 Remote Repository:")
    print(result.stdout)
    
    print("\n🚀 To push changes:")
    print("  git add .")
    print("  git commit -m 'Remove Project references'")
    print("  git push origin main")
    
    print("\n" + "=" * 50)
    print("💡 Note: Some updates need to be done manually on GitHub website!")

if __name__ == "__main__":
    update_github_info()
