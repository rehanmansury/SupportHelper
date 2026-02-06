@echo off
echo ========================================
echo Create Code Signing Certificate
echo Using OpenSSL
echo ========================================
echo.

REM Check if OpenSSL is available
openssl version >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: OpenSSL not found!
    echo.
    echo Install OpenSSL:
    echo 1. Download from: https://slproweb.com/products/Win32OpenSSL.html
    echo 2. Install and add to PATH
    echo 3. Run this script again
    pause
    exit /b 1
)

echo OpenSSL found, creating certificate...
echo.

REM Create private key
echo [1/4] Creating private key...
openssl genrsa -out SupportHelper.key 2048

if %errorLevel% neq 0 (
    echo ERROR: Failed to create private key!
    pause
    exit /b 1
)

REM Create certificate signing request
echo [2/4] Creating CSR...
openssl req -new -key SupportHelper.key -out SupportHelper.csr -subj "/C=AE/ST=Dubai/L=Dubai/O=Rehan Mansury/OU=Software Development/CN=SupportHelper Code Signing"

if %errorLevel% neq 0 (
    echo ERROR: Failed to create CSR!
    pause
    exit /b 1
)

REM Create self-signed certificate
echo [3/4] Creating self-signed certificate...
openssl x509 -req -days 1825 -in SupportHelper.csr -signkey SupportHelper.key -out SupportHelper.crt -extensions v3_req -extfile <(
echo [v3_req]
echo basicConstraints = CA:FALSE
echo keyUsage = digitalSignature, keyEncipherment
echo extendedKeyUsage = codeSigning
)

if %errorLevel% neq 0 (
    echo ERROR: Failed to create certificate!
    pause
    exit /b 1
)

REM Convert to PFX
echo [4/4] Converting to PFX...
openssl pkcs12 -export -out SupportHelperSelfSignCert.pfx -inkey SupportHelper.key -in SupportHelper.crt -password pass:Nexthink.123

if %errorLevel% neq 0 (
    echo ERROR: Failed to create PFX!
    pause
    exit /b 1
)

echo.
echo ✅ Certificate created successfully!
echo.
echo Files created:
echo - SupportHelper.key (private key)
echo - SupportHelper.crt (public certificate)
echo - SupportSelfSignCert.pfx (PKCS#12 bundle)
echo.
echo PFX Password: Nexthink.123
echo.
echo You can now sign your EXE with this PFX!
echo.
pause
