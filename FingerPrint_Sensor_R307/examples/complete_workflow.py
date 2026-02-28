"""
Example: Complete enrollment and verification workflow
Demonstrates user enrollment, verification, and deletion.
"""
import time
from fingerprint_r307.core.sensor import FingerprintSensor
from fingerprint_r307.utils.config import ConfigManager
from fingerprint_r307.admin.user_manager import UserManager
from fingerprint_r307.reader.verifier import FingerprintVerifier


def enroll_users_example():
    """Example of enrolling multiple users."""
    print("\n=== User Enrollment Example ===\n")
    
    # Initialize components
    sensor = FingerprintSensor()
    config = ConfigManager()
    user_manager = UserManager(sensor, config)
    
    # List of users to enroll
    users = ["Alice", "Bob", "Charlie"]
    
    for user_id in users:
        print(f"\nEnrolling user: {user_id}")
        print("-" * 40)
        try:
            if user_manager.enroll_user(user_id):
                print(f"✓ {user_id} enrolled successfully!")
            else:
                print(f"✗ Failed to enroll {user_id}")
        except Exception as e:
            print(f"Error enrolling {user_id}: {e}")
        
        time.sleep(1)  # Brief pause between enrollments


def verify_users_example():
    """Example of verifying enrolled users."""
    print("\n=== User Verification Example ===\n")
    
    # Initialize components
    sensor = FingerprintSensor()
    config = ConfigManager()
    
    # Custom callback for successful verification
    def on_verified(user_name, position, accuracy):
        print(f"\n{'='*50}")
        print(f"ACCESS GRANTED")
        print(f"{'='*50}")
        print(f"User: {user_name}")
        print(f"Position: #{position}")
        print(f"Accuracy: {accuracy}")
        print(f"{'='*50}\n")
    
    # Create verifier
    verifier = FingerprintVerifier(
        sensor=sensor,
        config=config,
        on_success=on_verified
    )
    
    # Verify a few fingerprints
    print("Place finger on sensor (3 verification attempts)")
    for i in range(3):
        print(f"\nAttempt {i+1}/3:")
        try:
            verifier.verify()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(2)


def list_users_example():
    """Example of listing all enrolled users."""
    print("\n=== List All Users Example ===\n")
    
    config = ConfigManager()
    users = config.get_all_users()
    
    if not users:
        print("No users enrolled.")
        return
    
    print(f"Total enrolled users: {len(users)}\n")
    print(f"{'Position':<10} {'Name':<20} {'Status':<10}")
    print("-" * 40)
    
    for user in users:
        print(f"{user['position']:<10} {user['name']:<20} {user['enrolled']:<10}")


def delete_user_example(position: int):
    """Example of deleting a user."""
    print(f"\n=== Delete User Example ===\n")
    
    sensor = FingerprintSensor()
    config = ConfigManager()
    user_manager = UserManager(sensor, config)
    
    try:
        if user_manager.delete_user(position):
            print(f"✓ User at position {position} deleted successfully")
        else:
            print(f"✗ Failed to delete user at position {position}")
    except Exception as e:
        print(f"Error: {e}")


def main():
    """Main workflow example."""
    print("="*60)
    print("FINGERPRINT SENSOR - COMPLETE WORKFLOW EXAMPLE")
    print("="*60)
    
    while True:
        print("\nSelect an example to run:")
        print("1. Enroll Users")
        print("2. Verify Users")
        print("3. List All Users")
        print("4. Delete User")
        print("5. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        try:
            if choice == '1':
                enroll_users_example()
            elif choice == '2':
                verify_users_example()
            elif choice == '3':
                list_users_example()
            elif choice == '4':
                position = int(input("Enter position number to delete: "))
                delete_user_example(position)
            elif choice == '5':
                print("\nExiting...")
                break
            else:
                print("Invalid choice")
        except KeyboardInterrupt:
            print("\n\nOperation cancelled")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == '__main__':
    main()
