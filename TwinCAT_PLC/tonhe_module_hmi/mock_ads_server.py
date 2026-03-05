import time
import random
import threading
import pyads
from pyads import constants

# Constants for the local ADS server
# The AmsNetId 5.1.204.160.1.1 is defined in tone_config.xml
# For a mock server, we typically bind to 127.0.0.1 and port 851.
AMS_NET_ID = "127.0.0.1.1.1" # For a local test, it's easier to use local NetID. 
PORT = 851

def run_mock_server():
    print("Starting mock ADS server on Port {}...".format(PORT))
    
    # We will use the built in routing features in pyads. 
    # But full server implementation requires a C++ ADS server or a complex setup.
    # In python, pyads doesn't have a built-in 'Server' class we can just run to listen to incoming connections and serve variable names.

    # However, since the client app connects to an IP and Port and reads/writes variables by name,
    # the easiest way to mock this in python without TwinCAT installed is to patch the client connection or provide a dummy server.

    pass

if __name__ == '__main__':
    run_mock_server()
