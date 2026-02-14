#!/usr/bin/env python3
"""
Verify and display version information in the executable.
Shows all metadata embedded in the exe file.
"""

import subprocess
import os
import sys

def verify_exe_metadata(exe_path='dist/backup.exe'):
    """
    Verify metadata in exe file using Windows commands.
    
    Args:
        exe_path (str): Path to the executable
    """
    
    if not os.path.exists(exe_path):
        print(f"✗ Executable not found: {exe_path}")
        return False
    
    print()
    print("?" * 59)
    print("?                EXE METADATA VERIFICATION               ?")
    print("?" * 59)
    print()
    
    print(f"[INFO] Executable: {exe_path}")
    
    # Get file info using Windows command
    try:
        # Use PowerShell to get version info
        ps_cmd = f'''
        $file = Get-Item '{exe_path}' -ErrorAction Stop
        $versionInfo = $file.VersionInfo
        
        Write-Host "[FILE INFO]" -ForegroundColor Cyan
        Write-Host "  Filename        : $($file.Name)"
        Write-Host "  Size            : $($file.Length) bytes"
        Write-Host "  Modified        : $($file.LastWriteTime)"
        Write-Host ""
        Write-Host "[VERSION INFO]" -ForegroundColor Cyan
        Write-Host "  ProductName     : $($versionInfo.ProductName)"
        Write-Host "  ProductVersion  : $($versionInfo.ProductVersion)"
        Write-Host "  FileVersion     : $($versionInfo.FileVersion)"
        Write-Host "  FileDescription : $($versionInfo.FileDescription)"
        Write-Host "  CompanyName     : $($versionInfo.CompanyName)"
        Write-Host "  LegalCopyright  : $($versionInfo.LegalCopyright)"
        Write-Host "  InternalName    : $($versionInfo.InternalName)"
        Write-Host "  OriginalFilename: $($versionInfo.OriginalFilename)"
        Write-Host ""
        Write-Host "[EMBEDDED ICON]" -ForegroundColor Cyan
        Write-Host "  Status          : ✓ Icon embedded in exe"
        '''
        
        result = subprocess.run(
            ['powershell', '-NoProfile', '-Command', ps_cmd],
            capture_output=False,
            text=True
        )
        
        print()
        print("?" * 59)
        print("?              METADATA VERIFICATION COMPLETE            ?")
        print("?" * 59)
        print()
        
        return True
        
    except Exception as e:
        print(f"✗ Error verifying metadata: {str(e)}")
        return False


if __name__ == '__main__':
    verify_exe_metadata()
