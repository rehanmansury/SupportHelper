# Create Code Signing Certificate for SupportHelper
# Run as Administrator

Write-Host "SupportHelper Code Signing Certificate Creator" -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Check if running as admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

# Certificate details
$certName = "SupportHelper"
$subject = "CN=SupportHelper Code Signing, OU=Software Development, O=Rehan Mansury, L=Dubai, S=Dubai, C=AE"
$validYears = 5

Write-Host "Creating code signing certificate..." -ForegroundColor Yellow
Write-Host "Subject: $subject" -ForegroundColor Cyan
Write-Host "Valid for: $validYears years" -ForegroundColor Cyan

try {
    # Create the certificate with code signing EKU
    $cert = New-SelfSignedCertificate `
        -DnsName $certName `
        -Subject $subject `
        -CertStoreLocation "cert:\CurrentUser\My" `
        -KeyUsage DigitalSignature `
        -KeyUsageProperty All `
        -KeyAlgorithm RSA `
        -KeyLength 2048 `
        -NotAfter (Get-Date).AddYears($validYears) `
        -FriendlyName "SupportHelper Code Signing" `
        -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3") `
        -HashAlgorithm SHA256

    if ($cert) {
        Write-Host "`n✅ Certificate created successfully!" -ForegroundColor Green
        Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
        Write-Host "Subject: $($cert.Subject)" -ForegroundColor Cyan
        Write-Host "Issuer: $($cert.Issuer)" -ForegroundColor Cyan
        Write-Host "Valid from: $($cert.NotBefore)" -ForegroundColor Cyan
        Write-Host "Valid to: $($cert.NotAfter)" -ForegroundColor Cyan
        
        # Also add to Trusted Publishers
        $pubKey = $cert | Select-Object -ExpandProperty PublicKey
        $pubKeyBytes = $pubKey.EncodedKeyValue
        $pubKeyBase64 = [System.Convert]::ToBase64String($pubKeyBytes)
        
        # Copy to Trusted Publishers
        $certStore = New-Object System.Security.Cryptography.X509Certificates.X509Store("TrustedPublisher", "CurrentUser")
        $certStore.Open([System.Security.Cryptography.X509Certificates.OpenFlags]::ReadWrite)
        $certStore.Add($cert)
        $certStore.Close()
        
        Write-Host "`n✅ Certificate also added to Trusted Publishers" -ForegroundColor Green
        
        # Export to PFX
        $pfxPath = "$ScriptDir\SupportHelperCodeSigning.pfx"
        $password = ConvertTo-SecureString -String "Nexthink.123" -Force -AsPlainText
        
        Export-PfxCertificate `
            -Cert $cert `
            -FilePath $pfxPath `
            -Password $password `
            -ChainOption BuildChain | Out-Null
        
        Write-Host "`n✅ Certificate exported to PFX:" -ForegroundColor Green
        Write-Host "Path: $pfxPath" -ForegroundColor Cyan
        Write-Host "Password: Nexthink.123" -ForegroundColor Yellow
        
        # Export public key as CER
        $cerPath = "$ScriptDir\SupportHelperCodeSigning.cer"
        Export-Certificate -Cert $cert -FilePath $cerPath | Out-Null
        Write-Host "✅ Public key exported to: $cerPath" -ForegroundColor Green
        
        Write-Host "`n" + "="*50
        Write-Host "NEXT STEPS:" -ForegroundColor Yellow
        Write-Host "1. Run: python sign_with_pfx.py" -ForegroundColor White
        Write-Host "2. Use password: Nexthink.123" -ForegroundColor White
        Write-Host "3. Upload the signed EXE to GitHub" -ForegroundColor White
        Write-Host "="*50
        
    } else {
        Write-Host "❌ Failed to create certificate!" -ForegroundColor Red
    }
}
catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "`nPossible solutions:" -ForegroundColor Yellow
    Write-Host "1. Make sure you're running as Administrator" -ForegroundColor White
    Write-Host "2. Check if Windows SDK is installed" -ForegroundColor White
    Write-Host "3. Try Method 2 (makecert.exe) below" -ForegroundColor White
}

Read-Host "`nPress Enter to exit"
