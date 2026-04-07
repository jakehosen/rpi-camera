#!/usr/bin/env python3
# timelapse.py - Takes photos every 15 minutes using libcamera

import os
import time
import datetime
import subprocess
from pathlib import Path

# Configuration
INTERVAL = 15 * 60  # 15 minutes in seconds
SAVE_DIRECTORY = "/home/pi/timelapse"
IMAGE_PREFIX = "timelapse_"

def setup():
    """Create the save directory if it doesn't exist."""
    Path(SAVE_DIRECTORY).mkdir(parents=True, exist_ok=True)
    print(f"Images will be saved to: {SAVE_DIRECTORY}")

def take_photo():
    """Take a photo using libcamera-still and save it with timestamp."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{IMAGE_PREFIX}{timestamp}.jpg"
    filepath = os.path.join(SAVE_DIRECTORY, filename)
    
    try:
        # Using libcamera-still command
        command = [
            "libcamera-still",
            "-o", filepath,
            "--nopreview",
            "--timeout", "1000"  # 1 second timeout
        ]
        
        # Execute the command
        subprocess.run(command, check=True)
        print(f"Photo taken: {filename}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error taking photo: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    """Main function to run the timelapse."""
    setup()
    print("Starting timelapse capture...")
    
    try:
        while True:
            # Take photo
            success = take_photo()
            
            # Wait for the next interval
            print(f"Waiting {INTERVAL} seconds until next capture...")
            time.sleep(INTERVAL)
    except KeyboardInterrupt:
        print("Timelapse capture stopped by user.")
    except Exception as e:
        print(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()

