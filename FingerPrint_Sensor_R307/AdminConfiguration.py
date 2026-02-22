import os
import configparser
import tempfile
import time
from pyfingerprint.pyfingerprint import PyFingerprint
from pyfingerprint.pyfingerprint import FINGERPRINT_CHARBUFFER1
from pyfingerprint.pyfingerprint import FINGERPRINT_CHARBUFFER2


# Configuration file path
config_file_path = os.path.expanduser("~/.fingerprint_config.ini")

# Function to read configuration data
def read_config():
    config = configparser.ConfigParser()
    try:
        config.read(config_file_path)
    except configparser.Error as e:
        print(f"Error reading configutation: {e}")
        config = None
    return config

# Function to write configuration data
def write_config(config):
    try:
        with open(config_file_path, 'w') as configfile:
            config.write(configfile)
        return True
    except (IOError, configparser.Error) as e:
        print(f"Error writing configuration: {e}")
        return False

# Function to initialize the fingerprint Sensor
def initialize_sensor():
    try:
        return PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        exit(1)

# Function to add a user
def add_user(fingerprint_sensor,config):
    # Tries to enroll new finger
    try:
        user_id = input('Enter user ID: ')
    
        # Check if the user ID already exists
        if config.has_section(user_id):
            print('User already exists.')
            return
        
        print(f'Enrolling fingerprint for user {user_id}. Place your finger on the sensor...')
        while (fingerprint_sensor.readImage() == False ):
            pass

        ## Converts read image to characteristics and stores it in charbuffer 1
        fingerprint_sensor.convertImage(FINGERPRINT_CHARBUFFER1)
        ## Checks if finger is already enrolled
        result = fingerprint_sensor.searchTemplate()
        positionNumber = result[0]

        if ( positionNumber >= 0 ):
            print('User already exists at position #' + str(positionNumber))
            #exit(0)
            return

        print('Remove finger...')
        time.sleep(2)

        print('Waiting for same finger again...')

        while (fingerprint_sensor.readImage() == False ):
            pass

         ## Converts read image to characteristics and stores it in charbuffer 2
        fingerprint_sensor.convertImage(FINGERPRINT_CHARBUFFER2)

        ## Compares the charbuffers
        if (fingerprint_sensor.compareCharacteristics() == 0 ):
            raise Exception('Fingers do not match')
        
        ## Creates a template
        fingerprint_sensor.createTemplate()

        ## Saves template at new position number
        positionNumber = fingerprint_sensor.storeTemplate()
        strPositionNumber = str(positionNumber)
        # Add user to configuration
        config.add_section(strPositionNumber)
        config.set(strPositionNumber, 'Name', user_id )
        config.set(strPositionNumber, 'Enrolled', 'True')
        success = write_config(config)

        if success:
            print(f'{user_id} Enrolled successfully!')
            print('New Registration Number#' + str(positionNumber))
            download_fingerprint(fingerprint_sensor,user_id)
        else:
            print ("Writing Failure")
            fingerprint_sensor.deleteTemplate(positionNumber)

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        #exit(1)
        return


# Function to delete a user
def delete_user(fingerprint_sensor,config):
    # Tries to delete the template of the finger
    try:
        positionNumber = input('Please enter the Register Number you want to delete: ')
        positionNumber = int(positionNumber)
        strPositionNumber = str(positionNumber)
        user_id = config.get(strPositionNumber,"Name")
        #if ( fingerprint_sensor.deleteTemplate(positionNumber) == True ):
            #print('User deleted!')
        if config.has_section(strPositionNumber):
            if (fingerprint_sensor.deleteTemplate(positionNumber) == True ):
                config.remove_section(strPositionNumber)
                write_config(config)
                print(f'User {user_id} deleted successfully.')
            else:
                print('User not found in Sensor.')
        else:
            print('User not found in Configuration File.')

    
    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        #exit(1)
        return
    
# Function to delete a user
def download_fingerprint(fingerprint_sensor,userName):
    try:
        print('Place your finger on the sensor to download image ...')

        ## Wait that finger is read
        while (fingerprint_sensor.readImage() == False ):
            pass

        print('Downloading image (this take a while)...')
        temp_dir = tempfile.gettempdir()
        base_name = "fingerprint_"+userName
        ext = "bmp"
        unique_filename = get_unique_filename(os.path.join(temp_dir,base_name),ext)
        #imageDestination =  tempfile.gettempdir() + '/fingerprint.bmp'
        fingerprint_sensor.downloadImage(unique_filename)

        print('The image was saved to "' + unique_filename + '".')

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        return
    

# Function to get Unique file name
def get_unique_filename(base_filename, extension):
    counter = 1
    while True:
        new_filename = f"{base_filename}_{counter}.{extension}"
        if not os.path.exists(new_filename):
            return new_filename
        counter += 1  

# Function to view all users
def view_all_users(config):
    for RegisterNumber in config.sections():
        print(f'Register Number : {RegisterNumber} , User ID: {config.get(RegisterNumber, "Name")}, Enrolled: {config.get(RegisterNumber, "Enrolled")}')


if __name__ == '__main__':

    # Initialize fingerprint sensor
    fingerprint_sensor = initialize_sensor()

    ## Gets some sensor information
    print('Currently used templates: ' + str(fingerprint_sensor.getTemplateCount()) +'/'+ str(fingerprint_sensor.getStorageCapacity()))

    if fingerprint_sensor:

        # Read configuration data
        config = read_config()
        if config:
            password = input('Enter password: ')
            for i in range(3):
                if password != '9510':
                    print(f'Incorrect password. Try Again. {i} Attempt ...')
                    
                    if i==3 :
                        time.sleep(2)
                        exit(0)
                else:
                    Flag = True
                    break

            if Flag:
                while True:
                    # Menu
                    print('\n1. Add User\n2. Delete User\n3. View All Users\n4. Exit')
                    choice = input('Enter your choice: ')

                    if choice == '1':
                        add_user(fingerprint_sensor,config)
                    elif choice == '2':
                        delete_user(fingerprint_sensor,config)
                    elif choice == '3':
                        view_all_users(config)
                    elif choice == '4':
                        break
                    else:
                        print('Invalid choice. Please try again.')
        else:
            print("Reading Configutaion Failure")
            time.sleep(3)
            exit(0)