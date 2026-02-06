import os
import sys
import subprocess
import json

def find_certificate_thumbprint():
    """Find the thumbprint of our self-signed certificate"""
    try:
        # PowerShell command to get certificate thumbprint
        ps_command = '''Get-ChildItem Cert:\\CurrentUser\\My | 
                      Where-Object {$_.Subject -like "*SupportHelper*"} | 
                      Select-Object -ExpandProperty Thumbprint'''
        
        result = subprocess.run(
            ['powershell', '-Command', ps_command],
            capture_output=True, text=True
        )
        
        if result.returncode == 0 and result.stdout.strip():
            thumbprint = result.stdout.strip()
            print(f"✅ Found certificate with thumbprint: {thumbprint}")
            return thumbprint
        else:
            print("❌ SupportHelper certificate not found!")
            print("\nPlease run create_cert.bat first (as Administrator)")
            return None
    except Exception as e:
        print(f"❌ Error finding certificate: {e}")
        return None

def sign_executable(thumbprint):
    """Sign the executable with the certificate"""
    exe_path = os.path.join('dist', 'SupportHelper.exe')
    
    if not os.path.exists(exe_path):
        print(f"❌ Error: {exe_path} not found!")
        print("Please run build_exe.py first!")
        return False
    
    print(f"\n📝 Signing {exe_path}...")
    
    try:
        # Sign with timestamp
        sign_command = [
            'signtool', 'sign',
            '/sha1', thumbprint,
            '/fd', 'sha256',
            '/tr', 'http://timestamp.digicert.com',
            '/td', 'sha256',
            exe_path
        ]
        
        print("Running: " + " ".join(sign_command))
        result = subprocess.run(sign_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ EXE signed successfully!")
            
            # Verify the signature
            print("\n🔍 Verifying signature...")
            verify_result = subprocess.run(
                ['signtool', 'verify', '/pa', exe_path],
                capture_output=True, text=True
            )
            
            if verify_result.returncode == 0:
                print("✅ Signature verified successfully!")
                return True
            else:
                print("⚠️ Warning: Signature verification failed")
                print(verify_result.stdout)
                return False
        else:
            print("❌ Failed to sign EXE!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except FileNotFoundError:
        print("❌ Signtool not found!")
        print("\nPlease install Windows SDK:")
        print("1. Download Windows 10 SDK")
        print("2. Or install Visual Studio with Windows SDK components")
        return False
    except Exception as e:
        print(f"❌ Error signing EXE: {e}")
        return False

def create_distribution_package():
    """Create a distribution package with the signed EXE"""
    print("\n📦 Creating distribution package...")
    
    # Create signed version folder
    signed_dir = os.path.join('dist', 'SupportHelper_Signed')
    if os.path.exists(signed_dir):
        import shutil
        shutil.rmtree(signed_dir)
    os.makedirs(signed_dir)
    
    # Copy signed EXE
    import shutil
    shutil.copy2(
        os.path.join('dist', 'SupportHelper.exe'),
        os.path.join(signed_dir, 'SupportHelper.exe')
    )
    
    # Create README for signed version
    readme_content = """SupportHelper - Signed Version
================================

This version of SupportHelper is signed with a self-signed certificate.

INSTALLATION:
--------------
1. Right-click SupportHelper.exe
2. Select "Properties"
3. You should see "Digital Signature" tab with SupportHelper certificate
4. Click "Install Certificate" if needed
5. Run the application

TRUSTING THE CERTIFICATE:
-------------------------
The first time you run this, Windows may still show a warning because
this is a self-signed certificate (not from a commercial CA).

To trust the certificate permanently:
1. Right-click SupportHelper.exe → Properties
2. Click "Digital Signatures" tab
3. Select "SupportHelper" certificate
4. Click "Details"
5. Click "View Certificate"
6. Click "Install Certificate"
7. Select "Current User" → "Trusted Publishers"
8. Click "OK" on all dialogs

After this, Windows will trust all applications signed with this certificate.

FOR ORGANIZATIONS:
------------------
For enterprise deployment, your IT administrator can:
1. Install the certificate in "Trusted Publishers" for all users
2. Add the certificate to the domain trust store
3. Deploy via Group Policy

Support: https://github.com/rehanmansury/SupportHelper
"""
    
    with open(os.path.join(signed_dir, "README.txt"), "w") as f:
        f.write(readme_content)
    
    # Create ZIP
    import zipfile
    zip_path = os.path.join('dist', 'SupportHelper_Signed.zip')
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(signed_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, signed_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Signed package created: {zip_path}")
    print(f"📊 Size: {os.path.getsize(zip_path) / (1024*1024):.2f} MB")

def main():
    """Main signing process"""
    print("🔐 SupportHelper EXE Signing Tool")
    print("=" * 50)
    
    # Step 1: Find certificate
    thumbprint = find_certificate_thumbprint()
    if not thumbprint:
        return
    
    # Step 2: Sign the EXE
    if sign_executable(thumbprint):
        # Step 3: Create distribution package
        create_distribution_package()
        
        print("\n🎉 Success!")
        print("\nNext steps:")
        print("1. Upload SupportHelper_Signed.zip to GitHub Releases")
        print("2. Users should install the certificate as shown in README.txt")
        print("3. Future updates will be trusted if certificate is installed")

if __name__ == "__main__":
    main()
