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
import platform
import time


class ProgressBar:
    """
    Professional progress bar with percentage, time estimation, and file display.
    Shows all files being processed with their status.
    """
    
    def __init__(self, total, prefix='Progress', bar_length=40):
        """
        Initialize progress bar.
        
        Args:
            total (int): Total number of items to process
            prefix (str): Prefix text for progress bar
            bar_length (int): Length of progress bar in characters
        """
        self.total = total
        self.prefix = prefix
        self.bar_length = bar_length
        self.current = 0
        self.start_time = time.time()
        self.progress_lines = 0  # Track how many lines progress bar uses
        
    def update(self, current_file="", status="", increment=1):
        """
        Update progress bar and show file status.
        
        Args:
            current_file (str): Current file being processed
            status (str): Status of the file (COPIED, UPDATED, SKIPPED)
            increment (int): Number to increment current count by
        """
        self.current += increment
        
        # Clear the current progress bar if it exists
        if self.progress_lines > 0:
            # Move cursor up to start of progress bar and clear it
            sys.stdout.write(f'\033[{self.progress_lines}A\033[J')
            sys.stdout.flush()
        
        # Show file status above progress bar (if provided)
        if current_file and status:
            self._display_file_status(current_file, status)
        
        # Draw the progress bar
        self._draw()
    
    def _display_file_status(self, file_path, status):
        """
        Display file status with color coding.
        
        Args:
            file_path (str): Path to the file
            status (str): Status (COPIED, UPDATED, SKIPPED, ERROR)
        """
        # Truncate long paths
        display_path = file_path
        if len(display_path) > 90:
            display_path = "..." + display_path[-87:]
        
        # Color code based on status
        if status == "COPIED":
            color = "\033[32m"  # Green
            icon = "✓"
        elif status == "UPDATED":
            color = "\033[33m"  # Yellow
            icon = "↻"
        elif status == "SKIPPED":
            color = "\033[90m"  # Gray
            icon = "○"
        elif status == "ERROR":
            color = "\033[31m"  # Red
            icon = "✗"
        else:
            color = "\033[37m"  # White
            icon = "•"
        
        # Print the file status
        print(f"{color}[{status:7}] {icon} {display_path}\033[0m")
        sys.stdout.flush()
    
    def _draw(self):
        """Draw the progress bar at the bottom."""
        if self.total == 0:
            return
        
        # Calculate percentage
        percent = (self.current / self.total) * 100
        
        # Calculate elapsed time and estimate remaining time
        elapsed_time = time.time() - self.start_time
        if self.current > 0:
            avg_time_per_file = elapsed_time / self.current
            remaining_files = self.total - self.current
            remaining_time = avg_time_per_file * remaining_files
        else:
            remaining_time = 0
        
        # Format time
        elapsed_str = self._format_time(elapsed_time)
        remaining_str = self._format_time(remaining_time)
        
        # Calculate bar fill
        filled_length = int(self.bar_length * self.current // self.total)
        bar = '█' * filled_length + '░' * (self.bar_length - filled_length)
        
        # Calculate speed
        speed = self.current / elapsed_time if elapsed_time > 0 else 0
        
        # Draw separator line
        print("\033[36m" + "─" * 100 + "\033[0m")
        
        # Display progress bar
        print(f"\033[1m{self.prefix}: |{bar}| {percent:.1f}% ({self.current}/{self.total})\033[0m")
        
        # Display stats (elapsed, remaining, speed)
        stats = f"⏱  Elapsed: {elapsed_str} | ⏳ Remaining: ~{remaining_str} | 🚀 Speed: {speed:.1f} files/s"
        print(f"\033[36m{stats}\033[0m")
        
        # Remember we used 3 lines for progress bar
        self.progress_lines = 3
        
        sys.stdout.flush()
    
    def _format_time(self, seconds):
        """
        Format time in seconds to readable format.
        
        Args:
            seconds (float): Time in seconds
            
        Returns:
            str: Formatted time string
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def finish(self):
        """Mark progress as complete."""
        self.current = self.total
        
        # Clear progress bar lines
        if self.progress_lines > 0:
            sys.stdout.write(f'\033[{self.progress_lines}A\033[J')
        
        # Draw final progress bar
        self._draw()
        print()  # New line after completion
    
    def show_copy_animation(self, file_path, spinner, file_percent):
        """
        Show animated copying progress for large files.
        
        Args:
            file_path (str): Path being copied
            spinner (str): Spinner character/frame
            file_percent (float): Percentage of file copied
        """
        # Clear the progress bar
        if self.progress_lines > 0:
            sys.stdout.write(f'\033[{self.progress_lines}A\033[J')
        
        # Truncate long paths
        display_path = file_path
        if len(display_path) > 75:
            display_path = "..." + display_path[-72:]
        
        # Show animated copying status
        print(f"\033[36m[COPYING] {spinner} {display_path} ({file_percent:.0f}%)\033[0m")
        sys.stdout.flush()
        
        # Redraw progress bar
        self._draw()


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
        self.error_files = []  # Track files that had errors
        
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
    
    def copy_file(self, source_file, dest_file, progress_callback=None):
        """
        Copy a single file from source to destination.
        
        Args:
            source_file (str): Path to source file
            dest_file (str): Path to destination file
            progress_callback (callable): Optional callback for progress updates
        
        Returns:
            bool: True if copy was successful
        """
        try:
            # Create destination directory if it doesn't exist
            dest_dir = os.path.dirname(dest_file)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            # Get file size
            file_size = os.path.getsize(source_file)
            
            # For files larger than 1MB, use animated copy
            if file_size > 1024 * 1024 and progress_callback:
                self._copy_with_animation(source_file, dest_file, file_size, progress_callback)
            else:
                # For small files, use fast copy
                shutil.copy2(source_file, dest_file)
            
            return True
            
        except Exception as e:
            # Track error silently and show in final report
            self.stats['errors'] += 1
            self.error_files.append((source_file, str(e)))  # Track error
            return False
    
    def _copy_with_animation(self, source_file, dest_file, file_size, progress_callback):
        """
        Copy file with progress animation for large files.
        
        Args:
            source_file (str): Source file path
            dest_file (str): Destination file path
            file_size (int): Size of file in bytes
            progress_callback (callable): Callback for animation updates
        """
        # Animation frames
        spinner_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        frame_index = 0
        
        # Copy in chunks with animation
        chunk_size = 1024 * 1024  # 1MB chunks
        bytes_copied = 0
        
        with open(source_file, 'rb') as fsrc:
            with open(dest_file, 'wb') as fdst:
                while True:
                    chunk = fsrc.read(chunk_size)
                    if not chunk:
                        break
                    
                    fdst.write(chunk)
                    bytes_copied += len(chunk)
                    
                    # Show animation
                    frame = spinner_frames[frame_index % len(spinner_frames)]
                    percent = (bytes_copied / file_size) * 100
                    progress_callback(frame, percent)
                    frame_index += 1
        
        # Copy metadata (timestamps, permissions)
        shutil.copystat(source_file, dest_file)
    
    def scan_files(self):
        """
        Scan all files and collect statistics without performing actual backup.
        
        Returns:
            dict: Dictionary containing file lists and statistics
        """
        scan_results = {
            'to_copy': [],      # New files to copy
            'to_update': [],    # Existing files to update
            'to_skip': [],      # Files that are up to date
            'total': 0
        }
        
        # Animation frames (Braille spinner)
        animation_frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        frame_index = 0
        files_scanned = 0
        
        try:
            print("\n\033[33m Scanning files and analyzing changes...\033[0m")
            
            for root, dirs, files in os.walk(self.source_folder):
                # Calculate relative path from source
                rel_path = os.path.relpath(root, self.source_folder)
                
                # Calculate corresponding destination directory
                if rel_path == '.':
                    dest_dir = self.backup_folder
                else:
                    dest_dir = os.path.join(self.backup_folder, rel_path)
                
                # Analyze each file
                for file in files:
                    source_file = os.path.join(root, file)
                    dest_file = os.path.join(dest_dir, file)
                    
                    # Display scanning animation
                    files_scanned += 1
                    frame = animation_frames[frame_index % len(animation_frames)]
                    sys.stdout.write(f'\r\033[36m{frame} Scanning... {files_scanned} files analyzed\033[0m')
                    sys.stdout.flush()
                    frame_index += 1
                    
                    # Determine action based on file comparison
                    action = self.compare_files(source_file, dest_file)
                    
                    # Categorize the file
                    if action == 'copy':
                        scan_results['to_copy'].append((source_file, dest_file))
                    elif action == 'update':
                        scan_results['to_update'].append((source_file, dest_file))
                    elif action == 'skip':
                        scan_results['to_skip'].append((source_file, dest_file))
                    
                    scan_results['total'] += 1
            
            # Clear animation line
            sys.stdout.write('\r\033[K')
            print(f"\033[32m Scan complete! {files_scanned} files analyzed\033[0m")
            
            return scan_results
            
        except Exception as e:
            self.log_error(f"File scanning failed: {str(e)}")
            return scan_results
    
    def display_scan_summary(self, scan_results):
        """
        Display a summary of the scan results with paths.
        
        Args:
            scan_results (dict): Results from scan_files()
        """
        print("\n" + "=" * 100)
        print("\033[1m\033[36m                          BACKUP ANALYSIS SUMMARY\033[0m")
        print("=" * 100)
        
        # Display paths
        print("\n\033[1m SOURCE PATH:\033[0m")
        print(f"   \033[32m{self.source_folder}\033[0m")
        
        print("\n\033[1m DESTINATION PATH:\033[0m")
        print(f"   \033[32m{self.backup_folder}\033[0m")
        
        # Display statistics
        print("\n\033[1m FILE STATISTICS:\033[0m")
        print(f"   \033[32m✓ Files to COPY (new files):     {len(scan_results['to_copy']):>6}\033[0m")
        print(f"   \033[33m↻ Files to UPDATE (modified):    {len(scan_results['to_update']):>6}\033[0m")
        print(f"   \033[90m○ Files to SKIP (up-to-date):    {len(scan_results['to_skip']):>6}\033[0m")
        print(f"   \033[1m─────────────────────────────────────────\033[0m")
        print(f"   \033[1mTotal files:                     {scan_results['total']:>6}\033[0m")
        
        print("\n" + "=" * 100 + "\n")
    
    def get_user_confirmation(self):
        """
        Get user confirmation to proceed with backup.
        
        Returns:
            bool: True if user confirms, False otherwise
        """
        while True:
            response = input("\033[1m Do you want to proceed with the backup? (yes/no): \033[0m").strip().lower()
            
            if response in ['yes', 'y']:
                print("\033[32m✓ Proceeding with backup...\033[0m\n")
                return True
            elif response in ['no', 'n']:
                print("\033[33m✗ Backup cancelled by user.\033[0m\n")
                return False
            else:
                print("\033[31m⚠ Invalid input. Please enter 'yes' or 'no'.\033[0m")
    
    def perform_backup(self, scan_results):
        """
        Perform the backup operation using pre-scanned file information.
        
        Args:
            scan_results (dict): Results from scan_files()
        """
        try:
            self.log_info("=" * 60)
            self.log_info("Starting backup operation...")
            self.log_info("=" * 60)
                        # Calculate total files to process (copy + update)
            files_to_process = scan_results['to_copy'] + scan_results['to_update']
            total_to_process = len(files_to_process)
            
            # Set skipped count immediately (no need to process them)
            self.stats['skipped'] = len(scan_results['to_skip'])
            
            if total_to_process == 0:
                self.log_info("No files need to be copied or updated.")
                return
            
            # Initialize progress bar (reserve 3 lines)
            print("\n\n")  # Reserve space for progress bar
            progress = ProgressBar(total_to_process, prefix='Backup Progress')
            
            # Create animation callback for large files
            def copy_animation_callback(spinner, file_percent):
                progress.show_copy_animation(current_source_file, spinner, file_percent)
            
            # Process files that need to be copied
            for source_file, dest_file in scan_results['to_copy']:
                current_source_file = source_file  # For callback closure
                if self.copy_file(source_file, dest_file, copy_animation_callback):
                    self.stats['copied'] += 1
                    progress.update(current_file=source_file, status="COPIED")
                else:
                    progress.update(current_file=source_file, status="ERROR")
            
            # Process files that need to be updated
            for source_file, dest_file in scan_results['to_update']:
                current_source_file = source_file  # For callback closure
                if self.copy_file(source_file, dest_file, copy_animation_callback):
                    self.stats['updated'] += 1
                    progress.update(current_file=source_file, status="UPDATED")
                else:
                    progress.update(current_file=source_file, status="ERROR")
            '''
            # Process files that are skipped (just update progress)
            for source_file, dest_file in scan_results['to_skip']:
                self.stats['skipped'] += 1
                progress.update(current_file=source_file, status="SKIPPED")
            
            '''
            # Finish progress bar
            progress.finish()
            
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
        
        # Display error details if any
        if self.error_files:
            print("\n\033[31m ERROR REPORT:\033[0m")
            print("\033[31m" + "=" * 100 + "\033[0m")
            for idx, (file_path, error_msg) in enumerate(self.error_files, 1):
                print(f"\033[31m{idx}. {file_path}\033[0m")
                print(f"\033[90m   Error: {error_msg}\033[0m")
            print("\033[31m" + "=" * 100 + "\033[0m\n")
    
    def run(self):
        """
        Main method to execute the backup process.
        
        Returns:
            int: Exit code (0 for success, 1 for failure)
        """
        # Step 1: Load configuration
        if not self.load_configuration():
            self.log_error("Failed to load configuration. Exiting.")
            return 1
        
        # Step 2: Create backup folder
        if not self.create_backup_folder():
            self.log_error("Failed to create backup folder. Exiting.")
            return 1
        
        # Step 3: Scan files and collect statistics
        scan_results = self.scan_files()
        
        # Step 4: Display summary
        self.display_scan_summary(scan_results)
        
        # Step 5: Get user confirmation
        if not self.get_user_confirmation():
            self.log_info("Backup cancelled by user.")
            return 0  # Exit gracefully, not an error
        
        # Step 6: Perform backup
        self.perform_backup(scan_results)
        
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


def create_default_config():
    """
    Create a default config.ini template if it doesn't exist.
    
    Returns:
        str: Path to config file
    """
    config_content = """# Backup Configuration File
# ==========================
# This file contains settings for the folder backup utility.
# 
# Instructions:
# 1. Edit the paths below to match your needs
# 2. Use full paths (e.g., C:\\Users\\YourName\\Documents)
# 3. Paths can contain spaces
# 4. Do not use quotes around paths
#
# Example:
# source_folder = C:\\Data\\TestFolder
# destination_folder = D:\\Backup
# This will create: D:\\Backup\\TestFolder

[Backup]
# Source folder to backup
# This is the folder you want to backup
source_folder = C:\\Temp\\New folder

# Destination folder
# This is where the backup will be stored
# The source folder name will be automatically appended
destination_folder = C:\\Temp\\Backup
"""
    
    try:
        if not os.path.exists('config.ini'):
            with open('config.ini', 'w', encoding='utf-8') as f:
                f.write(config_content)
            return 'config.ini'
        return 'config.ini'
    except Exception as e:
        print(f"[ERROR] Failed to create config.ini: {str(e)}")
        return None


def main():
    """
    Main entry point of the script.
    """
    try:
        # Display header
        print()
        print("?????????????????????????????????????????????????????????????")
        print("?                                                           ?")
        print("?           PYTHON BACKUP UTILITY - LAUNCHER                ?")
        print("?                                                           ?")
        print("?????????????????????????????????????????????????????????????")
        print()
        
        # Create default config if not found
        config_file = create_default_config()
        if not config_file:
            print("[ERROR] Failed to create configuration file!")
            print()
            input("Press Enter to exit...")
            sys.exit(1)
        
        # Display Python version
        print(f"[INFO] Python version: {platform.python_version()}")
        print()
        print("[INFO] Starting backup...")
        print()
        
        # Run the backup manager
        backup_manager = BackupManager(config_file)
        exit_code = backup_manager.run()
        
        # Show success or failure message
        print()
        if exit_code == 0:
            print("[SUCCESS] Backup completed successfully!")
        else:
            print("[ERROR] Backup failed with errors.")
        
        print()
        input("Press Enter to exit...")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\n[WARNING] Backup interrupted by user.")
        print()
        input("Press Enter to exit...")
        sys.exit(1)
    except Exception as e:
        print(f"[FATAL] Unexpected error: {str(e)}", file=sys.stderr)
        print()
        input("Press Enter to exit...")
        sys.exit(1)


if __name__ == "__main__":
    main()
