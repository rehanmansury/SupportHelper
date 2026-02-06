# Packaging Tools

This folder contains all tools and scripts for creating and signing SupportHelper executables.

## Scripts:
- `build_exe.py` - Build standalone executable
- `simple_sign.py` - Sign EXE with PFX certificate
- `create_*.ps1/.bat` - Certificate creation scripts
- `create_release.py` - Create GitHub release
- `create_installer.py` - Create installer package

## Certificates:
- `.pfx` files - Certificate bundles (keep secure!)
- `.cer` files - Public certificates
- `.key/.crt` - OpenSSL certificate files

## Build Artifacts:
- `build/` - Temporary build files
- `dist/` - Final executables and packages

## Usage:
1. Run build scripts from here
2. Certificates are stored here
3. All output goes to `dist/` folder
