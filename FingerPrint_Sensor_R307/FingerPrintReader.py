import hashlib
import time
import logging
import os
import configparser
import RPi.GPIO as GPIO
from pyfingerprint.pyfingerprint import PyFingerprint
from pyfingerprint.pyfingerprint import FINGERPRINT_CHARBUFFER1

GPIO_PIN = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(GPIO_PIN, GPIO.OUT)

# Configuration file path
config_file_path = os.path.expanduser("~/.fingerprint_config.ini")

# Log file path
log_file_path = os.path.expanduser("~/.fingerprint_log.txt")

# Configure the logging module
logging.basicConfig(
    filename=log_file_path,
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s: %(message)s",
)

# Function to initialize the fingerprint Sensor
def initialize_sensor():
    try:
        return PyFingerprint('/dev/ttyUSB0', 57600, 0xFFFFFFFF, 0x00000000)

    except Exception as e:
        print('The fingerprint sensor could not be initialized!')
        print('Exception message: ' + str(e))
        logging.error('The fingerprint sensor could not be initialized!')
        logging.error('Exception message: ' + str(e))
        exit(1)


# Function to read configuration data
def read_config():
    config = configparser.ConfigParser()
    try:
        config.read(config_file_path)
    except configparser.Error as e:
        print(f"Error reading configutation: {e}")
        logging.error(f"Error reading configuration: {e}")
        config = None
    return config

## Tries to search the finger and calculate hash
def verify_fingerprint(fingerprint_sensor,config):
    try:
        print('Place the finger on the Sensor...')
        ## Wait that finger is read
        while (fingerprint_sensor.readImage() == False ):
            pass

        ## Converts read image to characteristics and stores it in charbuffer 1
        fingerprint_sensor.convertImage(FINGERPRINT_CHARBUFFER1)

        ## Searchs template
        result = fingerprint_sensor.searchTemplate()

        positionNumber = result[0]
        accuracyScore = result[1]
        strPositionNumber = str(positionNumber)

        if ( positionNumber == -1 ):
            print('No match found!')
            logging.error('No match found!')
            return False
        
        else:
            if config.has_section(strPositionNumber):
                user_id = config.get(strPositionNumber, "Name")
                #print('Found User at position #' + str(positionNumber))
                print(f'{user_id} found at position {strPositionNumber}')
                print('The accuracy score is: ' + str(accuracyScore))
                logging.info(f'{user_id} found at position {strPositionNumber}')
                logging.info('The accuracy score is: ' + str(accuracyScore))
                do_Logic()
                return True
            else:
                print('User not found at configuration file')
                print(f'Position Number {strPositionNumber}')
                logging.error('User not found in the configuration file')
                logging.error(f'Position Number {strPositionNumber}')

    except Exception as e:
        print('Operation failed!')
        print('Exception message: ' + str(e))
        logging.error('Operation failed!')
        logging.error('Exception message: ' + str(e))
        return False
    

def do_Logic():
    GPIO.output(GPIO_PIN, GPIO.HIGH)  # Set GPIO pin high
    time.sleep(5)  # Keep the GPIO high for 5 seconds
    GPIO.output(GPIO_PIN, GPIO.LOW)  # Set GPIO pin low
    

if __name__ == '__main__':

    # Initialize fingerprint sensor
    fingerprint_sensor = initialize_sensor()
    # Read configuration data
    config = read_config()
    if config:
        while True:
            if fingerprint_sensor:
                verified_user = verify_fingerprint(fingerprint_sensor,config)

                #GPIO.cleanup()
    else:
        print("Configuration Reading Failure")
        time.sleep(3)
        exit(0)