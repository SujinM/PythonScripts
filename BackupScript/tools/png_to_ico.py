#!/usr/bin/env python3
"""
Convert PNG image to ICO format.
Provides multiple resolution support for Windows icons.
"""

from PIL import Image
import os
import sys

def convert_png_to_ico(png_path=None, ico_path=None):
    """
    Convert PNG image to ICO format with multiple resolutions.
    
    Args:
        png_path (str): Path to the PNG file
        ico_path (str): Output ICO file path
    
    Returns:
        bool: True if successful, False otherwise
    """
    # Auto-detect paths based on working directory
    if png_path is None:
        # Check if we're in project root or tools folder
        if os.path.exists('assets/backup_icon.png'):
            # Called from project root
            png_path = 'assets/backup_icon.png'
            ico_path = 'assets/backup_icon.ico'
        elif os.path.exists('../assets/backup_icon.png'):
            # Called from tools folder
            png_path = '../assets/backup_icon.png'
            ico_path = '../assets/backup_icon.ico'
        else:
            print(f"✗ PNG file not found in assets/ or ../assets/")
            return False
    
    try:
        # Check if PNG exists
        if not os.path.exists(png_path):
            print(f"✗ PNG file not found: {png_path}")
            print(f"  Current directory: {os.getcwd()}")
            return False
        
        # Open the PNG image
        img = Image.open(png_path)
        print(f"✓ Loaded PNG image: {png_path}")
        print(f"  Size: {img.size[0]}x{img.size[1]}, Mode: {img.mode}")
        
        # Convert to RGB if necessary
        if img.mode in ('RGBA', 'LA', 'P'):
            # For RGBA, preserve transparency
            if img.mode == 'RGBA':
                img_converted = img
            else:
                # For other modes, convert to RGBA first
                if img.mode == 'P':
                    img = img.convert('RGBA')
                img_converted = img
        else:
            img_converted = img
        
        # Save with multiple resolutions for better quality
        img_converted.save(
            ico_path, 
            'ICO', 
            sizes=[(256, 256), (128, 128), (64, 64), (32, 32), (16, 16)]
        )
        print(f"✓ Icon created: {ico_path}")
        print(f"  Resolutions: 256x256, 128x128, 64x64, 32x32, 16x16")
        return True
        
    except Exception as e:
        print(f"✗ Failed to convert PNG to ICO: {str(e)}")
        return False

if __name__ == '__main__':
    convert_png_to_ico()
