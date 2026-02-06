# SupportHelper Packaging Tools

This folder contains all tools and scripts for creating and signing SupportHelper executables.

## 📁 Folder Structure
```
SupportHelper/
├── main.py                 # Main application (run from here)
├── packagingtools/         # This folder - all build tools
│   ├── build_exe.py       # Build standalone EXE
│   ├── simple_sign.py     # Sign EXE with certificate
│   ├── build_and_package.py # Master build script
│   ├── dist/              # Output folder for built files
│   └── *.ps1, *.bat      # Certificate creation scripts
└── Extras/               # Backup and old files
```

## 🚀 Quick Start

### Option 1: Interactive Menu
```bash
cd packagingtools
python build_and_package.py
```
This shows a menu with all options.

### Option 2: Manual Steps

1. **Build the EXE:**
   ```bash
   cd packagingtools
   python build_exe.py
   ```

2. **Sign the EXE** (optional):
   ```bash
   python simple_sign.py
   ```
   - Enter password when prompted
   - Creates signed version in `dist/SupportHelper_Signed/`

3. **Create Installer Package:**
   ```bash
   python create_installer.py
   ```

4. **Create GitHub Release:**
   ```bash
   python create_release.py
   ```

## 🔐 Certificate Management

### Create New Certificate:
- **PowerShell**: `create_code_signing_cert.ps1` (Run as Admin)
- **makecert**: `create_cert_makecert.bat` (Run as Admin)
- **OpenSSL**: `create_cert_openssl.bat` (Requires OpenSSL)

### Using Existing Certificate:
- Place `.pfx` file in this folder
- Run `simple_sign.py` to sign EXE

## 📦 Output Files

All outputs go to the `dist/` folder:
- `SupportHelper.exe` - Main executable
- `SupportHelper_Portable/` - Portable version
- `SupportHelper_Signed/` - Signed version
- `SupportHelper_Installer/` - Installer package
- Various `.zip` files for distribution

## 🛠️ Requirements

- Python 3.7+
- PyInstaller (`pip install pyinstaller`)
- Windows SDK (for signtool)
- Administrator rights (for certificate creation)

## 📝 Notes

- Scripts automatically find paths to parent folder
- All relative paths work from `packagingtools/` folder
- Built executables are standalone - no Python needed
- Self-signed certificates still show security warnings

## 🔗 Links

- GitHub: https://github.com/rehanmansury/SupportHelper
- Issues: https://github.com/rehanmansury/SupportHelper/issues
