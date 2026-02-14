# PowerShell Script to Create Certificate and Sign Exe
# Called by sign-quick.bat

try {
    # Create self-signed certificate
    Write-Host "[INFO] Creating self-signed certificate..." -ForegroundColor Yellow
    
    $cert = New-SelfSignedCertificate `
        -Type CodeSigningCert `
        -Subject "CN=Backup Utility by Sujin" `
        -CertStoreLocation "Cert:\CurrentUser\My" `
        -NotAfter (Get-Date).AddYears(2)
    
    if ($cert) {
        Write-Host "[SUCCESS] Certificate created" -ForegroundColor Green
        Write-Host ""
        Write-Host "Certificate Details:" -ForegroundColor Cyan
        Write-Host "  Subject: $($cert.Subject)"
        Write-Host "  Thumbprint: $($cert.Thumbprint)"
        Write-Host "  Valid Until: $($cert.NotAfter)"
        Write-Host ""
        
        # Add certificate to Trusted Root store (required for self-signed certs)
        Write-Host "[INFO] Adding certificate to Trusted Root store..." -ForegroundColor Yellow
        $store = New-Object System.Security.Cryptography.X509Certificates.X509Store("Root", "CurrentUser")
        $store.Open("ReadWrite")
        $store.Add($cert)
        $store.Close()
        Write-Host "[SUCCESS] Certificate is now trusted" -ForegroundColor Green
        Write-Host ""
        
        # Sign the exe
        Write-Host "[INFO] Signing backup.exe..." -ForegroundColor Yellow
        
        $signature = Set-AuthenticodeSignature -FilePath "dist\backup.exe" -Certificate $cert
        
        if ($signature.Status -eq "Valid") {
            Write-Host ""
            Write-Host "============================================" -ForegroundColor Green
            Write-Host "SUCCESS! Exe has been digitally signed!" -ForegroundColor Green
            Write-Host "============================================" -ForegroundColor Green
            Write-Host ""
            Write-Host "Verify by:"
            Write-Host "1. Right-click dist\backup.exe -> Properties -> Digital Signatures"
            Write-Host "2. You should see: Backup Utility by Sujin"
            Write-Host ""
            Write-Host "Signature Details:"
            Write-Host "  Status: $($signature.Status)"
            Write-Host "  Signer: $($signature.SignerCertificate.Subject)"
            Write-Host ""
            exit 0
        } else {
            Write-Host "[ERROR] Signing failed: $($signature.StatusMessage)" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "[ERROR] Failed to create certificate" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[ERROR] Exception occurred: $_" -ForegroundColor Red
    exit 1
}
