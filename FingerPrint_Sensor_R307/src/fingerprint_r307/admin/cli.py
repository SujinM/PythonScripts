"""
Command-line interface for fingerprint sensor administration.
"""
import sys
import time
from getpass import getpass

from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.core.exceptions import FingerprintSensorError
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.utils.logger import get_logger, setup_logging
from fingerprint_r307.admin.user_manager import UserManager

logger = get_logger(__name__)

# Default admin password (should be changed in production)
ADMIN_PASSWORD = "9510"
MAX_LOGIN_ATTEMPTS = 3


def authenticate() -> bool:
    """
    Authenticate admin user.
    
    Returns:
        True if authentication successful
    """
    print("\n" + "="*50)
    print("FINGERPRINT SENSOR - ADMIN CONFIGURATION")
    print("="*50 + "\n")
    
    for attempt in range(MAX_LOGIN_ATTEMPTS):
        password = getpass(f'Enter admin password (Attempt {attempt + 1}/{MAX_LOGIN_ATTEMPTS}): ')
        
        if password == ADMIN_PASSWORD:
            logger.info("Admin authentication successful")
            return True
        else:
            remaining = MAX_LOGIN_ATTEMPTS - attempt - 1
            if remaining > 0:
                print(f'Incorrect password. {remaining} attempt(s) remaining.\n')
            logger.warning(f"Failed login attempt {attempt + 1}")
    
    print('Maximum login attempts exceeded. Exiting.')
    logger.error("Maximum login attempts exceeded")
    return False


def display_menu():
    """Display main menu."""
    print("\n" + "-"*50)
    print("ADMIN MENU")
    print("-"*50)
    print("1. Enroll New User")
    print("2. Delete User")
    print("3. View All Users")
    print("4. Sensor Information")
    print("5. Exit")
    print("-"*50)


def main():
    """Main entry point for admin CLI."""
    try:
        # Setup logging with console output
        setup_logging(console=True)
        
        # Authenticate admin
        if not authenticate():
            sys.exit(1)
        
        # Initialize sensor
        print("\nInitializing fingerprint sensor...")
        try:
            sensor = FingerprintSensor()
        except FingerprintSensorError as e:
            print(f"Error: {e}")
            logger.error(f"Sensor initialization failed: {e}")
            sys.exit(1)
        
        # Initialize configuration
        config = ConfigManager()
        
        # Initialize user manager
        user_manager = UserManager(sensor, config)
        
        # Display sensor info
        info = sensor.get_sensor_info()
        print(f"\nSensor initialized successfully!")
        print(f"Templates used: {info['templates_used']}/{info['storage_capacity']}")
        
        # Main loop
        while True:
            display_menu()
            choice = input("\nEnter your choice: ").strip()
            
            try:
                if choice == '1':
                    # Enroll new user
                    user_id = input('Enter user ID/name: ').strip()
                    if not user_id:
                        print("Error: User ID cannot be empty")
                        continue
                    
                    user_manager.enroll_user(user_id)
                    
                elif choice == '2':
                    # Delete user
                    try:
                        position_input = input('Enter registration number to delete: ').strip()
                        position = int(position_input)
                        user_manager.delete_user(position)
                    except ValueError:
                        print("Error: Invalid registration number")
                    
                elif choice == '3':
                    # View all users
                    user_manager.view_all_users()
                    
                elif choice == '4':
                    # Sensor information
                    info = sensor.get_sensor_info()
                    print("\n" + "="*50)
                    print("SENSOR INFORMATION")
                    print("="*50)
                    print(f"Port: {info['port']}")
                    print(f"Baud Rate: {info['baudrate']}")
                    print(f"Templates Used: {info['templates_used']}")
                    print(f"Storage Capacity: {info['storage_capacity']}")
                    print(f"Users in Config: {config.get_user_count()}")
                    print("="*50)
                    
                elif choice == '5':
                    # Exit
                    print("\nExiting admin interface...")
                    logger.info("Admin interface closed")
                    break
                    
                else:
                    print("Invalid choice. Please try again.")
                    
            except FingerprintSensorError as e:
                print(f"Operation failed: {e}")
                logger.error(f"Operation error: {e}")
            except KeyboardInterrupt:
                print("\n\nOperation cancelled by user.")
                break
            except Exception as e:
                print(f"Unexpected error: {e}")
                logger.error(f"Unexpected error: {e}")
        
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"Fatal error: {e}")
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
