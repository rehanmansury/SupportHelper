# Create Self-Signed Certificate for SupportHelper
# Run this script in PowerShell (may require admin)

Write-Host "SupportHelper Certificate Creator" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Check if running as admin
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Please run this script as Administrator!" -ForegroundColor Red
    Write-Host "Right-click PowerShell and 'Run as Administrator'" -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit
}

Write-Host "Creating self-signed certificate..." -ForegroundColor Yellow

# Create the certificate
$cert = New-SelfSignedCertificate `
    -DnsName "SupportHelper" `
    -CertStoreLocation "cert:\CurrentUser\My" `
    -KeyUsage DigitalSignature `
    -KeyUsageProperty All `
    -KeyAlgorithm RSA `
    -KeyLength 2048 `
    -NotAfter (Get-Date).AddYears(5) `
    -FriendlyName "SupportHelper Code Signing"

if ($cert) {
    Write-Host "✅ Certificate created successfully!" -ForegroundColor Green
    Write-Host "Thumbprint: $($cert.Thumbprint)" -ForegroundColor Cyan
    
    # Also copy to Trusted Publishers for this user
    Move-Item -Path "cert:\CurrentUser\My\$($cert.Thumbprint)" -Destination "cert:\CurrentUser\TrustedPublisher"
    
    Write-Host "✅ Certificate also added to Trusted Publishers" -ForegroundColor Green
    Write-Host ""
    Write-Host "Now you can run: python sign_with_cert.py" -ForegroundColor Yellow
} else {
    Write-Host "❌ Failed to create certificate!" -ForegroundColor Red
}

Read-Host "Press Enter to exit"
