@echo off
echo ========================================
echo Creating Self-Signed Certificate
echo ========================================
echo.
echo NOTE: This requires Administrator privileges!
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Please run this as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo Creating certificate configuration file...

(
echo [NewRequest]
echo Subject = "CN=SupportHelper, OU=Software Development, O=Rehan Mansury, L=City, S=State, C=US"
echo Exportable = TRUE
echo KeyLength = 2048
echo KeySpec = 1
echo KeyUsage = 0xA0
echo MachineKeySet = TRUE
echo ProviderName = "Microsoft RSA SChannel Cryptographic Provider"
echo ProviderType = 12
echo RequestType = Cert
echo Silent = TRUE
echo.
echo [Extensions]
echo 2.5.29.37 = "{text}1.3.6.1.5.5.7.3.3"
echo.
echo [EnhancedKeyUsageExtension]
echo OID = 1.3.6.1.5.5.7.3.3
) > SupportHelper.inf

echo Generating private key and certificate...
certreq -new -q SupportHelper.inf SupportHelper.cer

echo Installing certificate to Personal store...
certreq -accept -q SupportHelper.cer

echo.
echo ========================================
echo Certificate created successfully!
echo ========================================
echo.
echo The certificate has been installed in:
echo Current User -^> Personal -^> Certificates
echo.
echo You can now run sign_exe.py to sign your executable.
echo.
pause
