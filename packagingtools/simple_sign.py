import os
import sys
import subprocess

def sign_exe():
    """Simple script to sign EXE with PFX certificate"""
    
    # Get the correct paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Paths
    pfx_path = os.path.join(current_dir, "SupportHelperSelfSignCert.pfx")
    exe_path = os.path.join(current_dir, 'dist', 'SupportHelper.exe')
    
    print("🔐 Signing SupportHelper.exe")
    print("=" * 40)
    
    # Check files
    if not os.path.exists(pfx_path):
        print(f"❌ PFX not found: {pfx_path}")
        return False
    
    if not os.path.exists(exe_path):
        print(f"❌ EXE not found: {exe_path}")
        print("Run build_exe.py first!")
        return False
    
    print(f"✅ PFX: {os.path.basename(pfx_path)}")
    print(f"✅ EXE: {os.path.basename(exe_path)}")
    
    # Find signtool
    signtool = None
    possible_paths = [
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
        r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.19041.0\x64\signtool.exe",
        r"C:\Program Files\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            signtool = path
            break
    
    if not signtool:
        print("❌ Signtool not found!")
        return False
    
    print(f"✅ Signtool: {signtool}")
    
    # Get password
    password = input("\nEnter PFX password: ").strip()
    
    # Sign the EXE
    print("\n📝 Signing...")
    cmd = [
        signtool, 'sign',
        '/f', pfx_path,
        '/p', password,
        '/fd', 'sha256',
        '/tr', 'http://timestamp.digicert.com',
        '/td', 'sha256',
        exe_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Signed successfully!")
            
            # Verify
            print("\n🔍 Verifying...")
            verify_cmd = [signtool, 'verify', '/pa', exe_path]
            v_result = subprocess.run(verify_cmd, capture_output=True, text=True)
            
            if v_result.returncode == 0:
                print("✅ Signature verified!")
                
                # Create signed package
                create_package(current_dir)
                return True
            else:
                print("⚠️ Verification failed")
                print(v_result.stderr)
        else:
            print("❌ Signing failed!")
            print(result.stderr)
            
            if "password" in result.stderr.lower():
                print("\n💡 Check the PFX password")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return False

def create_package(current_dir):
    """Create signed package"""
    import shutil
    import zipfile
    
    print("\n📦 Creating package...")
    
    # Create folder
    folder = os.path.join(current_dir, 'dist', 'SupportHelper_Signed')
    if os.path.exists(folder):
        shutil.rmtree(folder)
    os.makedirs(folder)
    
    # Copy EXE
    shutil.copy2(os.path.join(current_dir, 'dist', 'SupportHelper.exe'), 
                os.path.join(folder, 'SupportHelper.exe'))
    
    # Create README
    readme = """SupportHelper - Signed Version
================================

This executable is digitally signed.

To verify:
1. Right-click → Properties
2. Digital Signatures tab
3. Should show "SupportHelper" as signer

If Windows shows warning:
- Click "More info"
- Click "Run anyway"

Support: https://github.com/rehanmansury/SupportHelper
"""
    
    with open(os.path.join(folder, 'README.txt'), 'w') as f:
        f.write(readme)
    
    # Create ZIP
    zip_path = os.path.join(current_dir, 'dist', 'SupportHelper_Signed.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, folder)
                zipf.write(file_path, arcname)
    
    print(f"✅ Package: {zip_path}")
    print(f"📊 Size: {os.path.getsize(zip_path) / (1024*1024):.1f} MB")

if __name__ == "__main__":
    if sign_exe():
        print("\n🎉 Ready to upload to GitHub!")
