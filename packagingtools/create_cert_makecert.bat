@echo off
echo ========================================
echo Create Code Signing Certificate
echo Using makecert.exe
echo ========================================
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run this as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

REM Find makecert.exe
set MAKECERT=
for %%i in (
    "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\makecert.exe"
    "C:\Program Files\Windows Kits\10\bin\*\x64\makecert.exe"
    "C:\Program Files (x86)\Microsoft SDKs\Windows\v*\bin\makecert.exe"
) do (
    if exist %%i (
        set MAKECERT=%%i
        goto :found
    )
)

:found
if "%MAKECERT%"=="" (
    echo ERROR: makecert.exe not found!
    echo Please install Windows SDK or Visual Studio
    pause
    exit /b 1
)

echo Found makecert at: %MAKECERT%
echo.

REM Create certificate
echo Creating code signing certificate...
"%MAKECERT%" ^
    -r ^
    -n "CN=SupportHelper Code Signing, OU=Software Development, O=Rehan Mansury, C=AE" ^
    -b 01/01/2025 ^
    -e 01/01/2030 ^
    -eku 1.3.6.1.5.5.7.3.3 ^
    -ss My ^
    -sr CurrentUser ^
    -sky signature ^
    -sy 24 ^
    -sp "Microsoft RSA SChannel Cryptographic Provider" ^
    -a sha256 ^
    SupportHelper

if %errorLevel% neq 0 (
    echo ERROR: Failed to create certificate!
    pause
    exit /b 1
)

echo.
echo ✅ Certificate created successfully!
echo.
echo Now you can sign your EXE with:
echo python simple_sign.py
echo.
pause
