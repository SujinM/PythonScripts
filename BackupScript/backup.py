#!/usr/bin/env python3
"""
Folder Backup Script
====================
A simple, configuration-based backup solution for Windows.

Features:
- Reads configuration from config.ini
- Incremental backup (only copies changed files)
- Preserves folder structure
- Smart comparison using modification timestamps
- Proper error handling and logging

Author: Sujin
Version: 1.0
"""

import os
import shutil
import configparser
from datetime import datetime
from pathlib import Path
import sys


class BackupManager:
    """
    Main class for managing folder backup operations.
    """
    
    def __init__(self, config_file='config.ini'):
        """
        Initialize the BackupManager with configuration file.
        
        Args:
            config_file (str): Path to the INI configuration file
        """
        self.config_file = config_file
        self.source_folder = None
        self.destination_folder = None
        self.backup_folder = None
        self.stats = {
            'copied': 0,
            'updated': 0,
            'skipped': 0,
            'errors': 0
        }
        
    def load_configuration(self):
        """
        Load and validate configuration from INI file.
        
        Returns:
            bool: True if configuration loaded successfully, False otherwise
        """
        try:
            if not os.path.exists(self.config_file):
                self.log_error(f"Configuration file not found: {self.config_file}")
                return False
            
            config = configparser.ConfigParser()
            config.read(self.config_file, encoding='utf-8')
            
            # Read backup configuration
            if 'Backup' not in config:
                self.log_error("'[Backup]' section not found in config.ini")
                return False
            
            self.source_folder = config['Backup'].get('source_folder', '').strip()
            self.destination_folder = config['Backup'].get('destination_folder', '').strip()
            
            # Validate paths
            if not self.source_folder:
                self.log_error("'source_folder' not specified in config.ini")
                return False
            
            if not self.destination_folder:
                self.log_error("'destination_folder' not specified in config.ini")
                return False
            
            # Check if source exists
            if not os.path.exists(self.source_folder):
                self.log_error(f"Source folder does not exist: {self.source_folder}")
                return False
            
            if not os.path.isdir(self.source_folder):
                self.log_error(f"Source path is not a directory: {self.source_folder}")
                return False
            
            # Extract source folder name for backup folder creation
            source_folder_name = os.path.basename(os.path.normpath(self.source_folder))
            self.backup_folder = os.path.join(self.destination_folder, source_folder_name)
            
            self.log_info("Configuration loaded successfully")
            self.log_info(f"Source: {self.source_folder}")
            self.log_info(f"Destination: {self.destination_folder}")
            self.log_info(f"Backup folder: {self.backup_folder}")
            
            return True
            
        except Exception as e:
            self.log_error(f"Error loading configuration: {str(e)}")
            return False
    
    def create_backup_folder(self):
        """
        Create backup folder if it doesn't exist.
        
        Returns:
            bool: True if folder exists or was created successfully
        """
        try:
            if not os.path.exists(self.backup_folder):
                os.makedirs(self.backup_folder)
                self.log_info(f"Created backup folder: {self.backup_folder}")
            else:
                self.log_info(f"Backup folder already exists: {self.backup_folder}")
            return True
        except Exception as e:
            self.log_error(f"Failed to create backup folder: {str(e)}")
            return False
    
    def compare_files(self, source_file, dest_file):
        """
        Compare two files based on modification timestamp.
        
        Args:
            source_file (str): Path to source file
            dest_file (str): Path to destination file
        
        Returns:
            str: 'copy' if file should be copied,
                 'update' if file should be updated,
                 'skip' if file is up to date
        """
        try:
            # If destination file doesn't exist, copy it
            if not os.path.exists(dest_file):
                return 'copy'
            
            # Get modification times
            source_mtime = os.path.getmtime(source_file)
            dest_mtime = os.path.getmtime(dest_file)
            
            # Compare timestamps (with small tolerance for floating point comparison)
            if source_mtime > dest_mtime + 1:  # 1 second tolerance
                return 'update'
            else:
                return 'skip'
                
        except Exception as e:
            self.log_error(f"Error comparing files: {str(e)}")
            return 'skip'
    
    def copy_file(self, source_file, dest_file):
        """
        Copy a single file from source to destination.
        
        Args:
            source_file (str): Path to source file
            dest_file (str): Path to destination file
        
        Returns:
            bool: True if copy was successful
        """
        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(dest_file)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            # Copy the file
            shutil.copy2(source_file, dest_file)  # copy2 preserves metadata
            return True
            
        except Exception as e:
            self.log_error(f"Failed to copy file: {source_file} -> {dest_file}: {str(e)}")
            self.stats['errors'] += 1
            return False
    
    def perform_backup(self):
        """
        Perform the backup operation by walking through source folder.
        """
        try:
            self.log_info("=" * 60)
            self.log_info("Starting backup operation...")
            self.log_info("=" * 60)
            
            # Walk through all files in source folder
            for root, dirs, files in os.walk(self.source_folder):
                # Calculate relative path from source
                rel_path = os.path.relpath(root, self.source_folder)
                
                # Create corresponding destination directory
                if rel_path == '.':
                    dest_dir = self.backup_folder
                else:
                    dest_dir = os.path.join(self.backup_folder, rel_path)
                
                # Ensure destination directory exists
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                
                # Process each file
                for file in files:
                    source_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    
                    # Determine action based on file comparison
                    action = self.compare_files(source_file, dest_file)
                    
                    if action == 'copy':
                        if self.copy_file(source_file, dest_file):
                            self.log_info(f"[COPIED] {source_file}")
                            self.stats['copied'] += 1
                    
                    elif action == 'update':
                        if self.copy_file(source_file, dest_file):
                            self.log_info(f"[UPDATED] {source_file}")
                            self.stats['updated'] += 1
                    
                    elif action == 'skip':
                        self.log_debug(f"[SKIPPED] {source_file}")
                        self.stats['skipped'] += 1
            
            self.log_info("=" * 60)
            self.log_info("Backup completed successfully!")
            self.print_statistics()
            
        except Exception as e:
            self.log_error(f"Backup operation failed: {str(e)}")
            self.stats['errors'] += 1
    
    def print_statistics(self):
        """
        Print backup statistics summary.
        """
        self.log_info("Backup Statistics:")
        self.log_info(f"  Files copied:  {self.stats['copied']}")
        self.log_info(f"  Files updated: {self.stats['updated']}")
        self.log_info(f"  Files skipped: {self.stats['skipped']}")
        self.log_info(f"  Errors:        {self.stats['errors']}")
        total = self.stats['copied'] + self.stats['updated'] + self.stats['skipped']
        self.log_info(f"  Total files:   {total}")
        self.log_info("=" * 60)
    
    def run(self):
        """
        Main method to execute the backup process.
        
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        self.log_info("?????????????????????????????????????????????????????????????")
        self.log_info("?                                                           ?")
        self.log_info("?              FOLDER BACKUP UTILITY v1.0                   ?")
        self.log_info("?              Configuration-Based Backup                   ?")
        self.log_info("?                                                           ?")
        self.log_info("?????????????????????????????????????????????????????????????")
        self.log_info("")
        
        # Step 1: Load configuration
        if not self.load_configuration():
            self.log_error("Failed to load configuration. Exiting.")
            return 1
        
        # Step 2: Create backup folder
        if not self.create_backup_folder():
            self.log_error("Failed to create backup folder. Exiting.")
            return 1
        
        # Step 3: Perform backup
        self.perform_backup()
        
        # Return exit code based on errors
        return 0 if self.stats['errors'] == 0 else 1
    
    @staticmethod
    def log_info(message):
        """Log informational message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[INFO] {timestamp} - {message}")
    
    @staticmethod
    def log_error(message):
        """Log error message."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[ERROR] {timestamp} - {message}", file=sys.stderr)
    
    @staticmethod
    def log_debug(message):
        """Log debug message (can be disabled for less verbose output)."""
        # Uncomment the next line for verbose output
        # timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # print(f"[DEBUG] {timestamp} - {message}")
        pass


def main():
    """
    Main entry point of the script.
    """
    try:
        backup_manager = BackupManager('config.ini')
        exit_code = backup_manager.run()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n[WARNING] Backup interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] Unexpected error: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
