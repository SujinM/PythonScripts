"""
User management module for fingerprint enrollment and deletion.
"""
import os
import time
import tempfile
from pathlib import Path
from typing import Optional

from pyfingerprint.pyfingerprint import FINGERPRINT_CHARBUFFER1, FINGERPRINT_CHARBUFFER2

from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.core.exceptions import EnrollmentError, DeletionError
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.utils.logger import get_logger

logger = get_logger(__name__)


class UserManager:
    """
    Manages user enrollment, deletion, and fingerprint operations.
    """
    
    def __init__(self, sensor: FingerprintSensor, config: ConfigManager):
        """
        Initialize user manager.
        
        Args:
            sensor: Fingerprint sensor instance
            config: Configuration manager instance
        """
        self.sensor = sensor
        self.config = config
    
    def enroll_user(self, user_id: str) -> bool:
        """
        Enroll a new user fingerprint.
        
        Args:
            user_id: User identifier/name
            
        Returns:
            True if enrollment successful
            
        Raises:
            EnrollmentError: If enrollment fails
        """
        try:
            logger.info(f"Starting enrollment for user: {user_id}")
            print(f'Enrolling fingerprint for user {user_id}.')
            print('Place your finger on the sensor...')
            
            # First scan
            while not self.sensor.read_image():
                pass
            
            self.sensor.convert_image(FINGERPRINT_CHARBUFFER1)
            
            # Check if finger already enrolled
            position, _ = self.sensor.search_template()
            if position >= 0:
                user_info = self.config.get_user(position)
                existing_name = user_info['name'] if user_info else 'Unknown'
                logger.warning(f"Fingerprint already enrolled at position {position}")
                print(f'This fingerprint is already enrolled as "{existing_name}" at position #{position}')
                return False
            
            print('Remove finger...')
            time.sleep(2)
            
            print('Place the same finger again...')
            
            # Second scan
            while not self.sensor.read_image():
                pass
            
            self.sensor.convert_image(FINGERPRINT_CHARBUFFER2)
            
            # Compare characteristics
            if self.sensor.compare_characteristics() == 0:
                logger.error("Fingerprints do not match")
                raise EnrollmentError('Fingers do not match. Please try again.')
            
            # Create and store template
            self.sensor.create_template()
            position = self.sensor.store_template()
            
            # Save to configuration
            self.config.add_user(position, user_id)
            
            print(f'{user_id} enrolled successfully!')
            print(f'Registration Number: #{position}')
            logger.info(f"User '{user_id}' enrolled at position {position}")
            
            # Download fingerprint image
            self._download_fingerprint_image(user_id)
            
            return True
            
        except EnrollmentError:
            raise
        except Exception as e:
            logger.error(f"Enrollment failed: {e}")
            raise EnrollmentError(f"Failed to enroll user: {e}") from e
    
    def delete_user(self, position: int) -> bool:
        """
        Delete enrolled user.
        
        Args:
            position: Template position number
            
        Returns:
            True if deletion successful
            
        Raises:
            DeletionError: If deletion fails
        """
        try:
            logger.info(f"Deleting user at position {position}")
            
            # Check if user exists in config
            user_info = self.config.get_user(position)
            if not user_info:
                logger.warning(f"User not found in configuration at position {position}")
                print('User not found in configuration file.')
                return False
            
            user_name = user_info['name']
            
            # Delete from sensor
            if self.sensor.delete_template(position):
                # Delete from configuration
                self.config.remove_user(position)
                print(f"User '{user_name}' deleted successfully.")
                logger.info(f"User '{user_name}' deleted from position {position}")
                return True
            else:
                logger.error(f"Failed to delete template from sensor at position {position}")
                print('Failed to delete user from sensor.')
                return False
                
        except Exception as e:
            logger.error(f"Deletion failed: {e}")
            raise DeletionError(f"Failed to delete user: {e}") from e
    
    def view_all_users(self):
        """Display all enrolled users."""
        users = self.config.get_all_users()
        
        if not users:
            print("No users enrolled.")
            return
        
        print("\n" + "="*60)
        print(f"{'Position':<10} {'User ID':<30} {'Enrolled':<10}")
        print("="*60)
        
        for user in users:
            print(f"{user['position']:<10} {user['name']:<30} {user['enrolled']:<10}")
        
        print("="*60)
        print(f"Total users: {len(users)}")
    
    def _download_fingerprint_image(self, user_name: str):
        """
        Download fingerprint image to file.
        
        Args:
            user_name: Name to use in filename
        """
        try:
            print('Place your finger on the sensor to download image...')
            
            while not self.sensor.read_image():
                pass
            
            print('Downloading image (this may take a while)...')
            
            # Generate unique filename
            temp_dir = tempfile.gettempdir()
            base_name = f"fingerprint_{user_name}"
            filename = self._get_unique_filename(temp_dir, base_name, 'bmp')
            
            self.sensor.download_image(filename)
            print(f'Image saved to: {filename}')
            logger.info(f"Fingerprint image saved: {filename}")
            
        except Exception as e:
            logger.warning(f"Failed to download image: {e}")
            print(f'Warning: Could not download image - {e}')
    
    @staticmethod
    def _get_unique_filename(directory: str, base_name: str, extension: str) -> str:
        """
        Generate unique filename.
        
        Args:
            directory: Directory path
            base_name: Base filename
            extension: File extension
            
        Returns:
            Unique file path
        """
        counter = 1
        while True:
            filename = os.path.join(directory, f"{base_name}_{counter}.{extension}")
            if not os.path.exists(filename):
                return filename
            counter += 1
