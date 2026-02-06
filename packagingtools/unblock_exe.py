import os
import sys

def unblock_exe():
    """Add unblock metadata to the EXE to reduce security warnings"""
    exe_path = os.path.join('dist', 'SupportHelper.exe')
    
    if not os.path.exists(exe_path):
        print(f"❌ Error: {exe_path} not found!")
        return
    
    print(f"🔓 Processing {exe_path}...")
    
    try:
        # Read the EXE
        with open(exe_path, 'rb') as f:
            data = f.read()
        
        # The Zone.Identifier stream is what causes Windows to block downloads
        # We'll create a PowerShell script to remove it
        ps_script = f"""
# Unblock SupportHelper.exe
 Unblock-File -Path "{exe_path}"
 Write-Host "SupportHelper.exe has been unblocked"
"""
        
        with open('unblock.ps1', 'w') as f:
            f.write(ps_script)
        
        print("✅ Created unblock.ps1")
        print("\n📋 To unblock the EXE:")
        print("1. Right-click unblock.ps1 → 'Run with PowerShell'")
        print("2. Or run as administrator: powershell -ExecutionPolicy Bypass -File unblock.ps1")
        
        # Also create instructions for users
        user_instructions = """
HOW TO RUN SupportHelper ON OTHER COMPUTERS
==========================================

If Windows blocks SupportHelper.exe with a security warning:

METHOD 1 - Quick Fix:
1. Right-click on SupportHelper.exe
2. Select "Properties"
3. If you see "This file came from another computer" checkbox
4. Check "Unblock" and click OK
5. Run the file normally

METHOD 2 - Windows Defender Warning:
1. When you see the Windows Defender warning
2. Click "More info"
3. Click "Run anyway"
4. Check "Always run" if available

METHOD 3 - PowerShell (Admin):
1. Open PowerShell as Administrator
2. Navigate to the folder with SupportHelper.exe
3. Run: Unblock-File SupportHelper.exe
4. Run the application

WHY THIS HAPPENS:
- Windows protects against unknown applications
- The EXE is not digitally signed (certificates cost $300+/year)
- This is normal for independent developers

FOR ORGANIZATIONS:
- Ask IT to add SupportHelper.exe to the whitelist
- Or host on a trusted internal network location

The application is SAFE - it's just Windows being protective!
"""
        
        with open('HOW_TO_RUN.txt', 'w') as f:
            f.write(user_instructions)
        
        print("\n✅ Created HOW_TO_RUN.txt with user instructions")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    unblock_exe()
