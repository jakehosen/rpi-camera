---
title: "Raspberry Pi Camera Loop Setup"
output:
  html_document: default
  pdf_document: default
---

```{r setup, include=FALSE}
knitr::opts_chunk$set(echo = TRUE)
```

## Stuff to install first
# Raspberry Pi NoIR Camera Timelapse Setup Instructions

This document provides step-by-step instructions for setting up a Python script that automatically takes photos using a Raspberry Pi NoIR camera every 15 minutes and starts on boot.

## Getting your login setup
* Create a user called "pi".
* Using the GUI (windows) interface, setup your wifi login.
* Open a terminal and type ```sudo raspi-config```.
* When you open this menu, select "1. System Options". Then select "B5 Boot / Auto Login". Then Select "B2 Console Autologin".
* Exit from raspi-config and reboot your system.

## Python Script (timelapse.py)

Create the Python script that will control the camera:

```python
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
```

## Systemd Service (timelapse.service)

Create a systemd service to run the script at boot:

```ini
[Unit]
Description=Raspberry Pi NoIR Camera Timelapse
After=network.target

[Service]
ExecStart=/usr/bin/python3 /home/pi/timelapse.py
WorkingDirectory=/home/pi
StandardOutput=append:/home/pi/timelapse.log
StandardError=append:/home/pi/timelapse.log
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
```

## Installation Steps

### Step 1: Create the Python script
1. Plug-in a USB drive with the files you need and open a terminal on your Raspberry Pi
2. Create the Python script file called timelapse.py and copy it to /home/pi as follows:
   ```bash
   sudo cp timelapse.py /home/pi/
   ```
3. Copy and paste the Python script from above
4. Save and exit (Ctrl+X, then Y, then Enter)
5. Make the script executable:
   ```bash
   sudo chmod +x /home/pi/timelapse.py
   ```

### Step 2: Create the systemd service
1. Create a systemd service file. Copy the file contents above into a file called timelapse.service and copy ito into /etc/systemd/system/ as follows:
   ```bash
   sudo cp timelapse.service /etc/systemd/system/
   ```
2. Copy and paste the service configuration from above
3. Save and exit (Ctrl+X, then Y, then Enter)
4. Make sure that you account is configured to access the files appropriately:
```bash
sudo usermod -a -G video,gpio pi
sudo usermod -a -G i2c,spi pi
```
### Step 3: Enable and start the service
```bash
sudo systemctl daemon-reload
sudo systemctl enable timelapse.service
sudo systemctl start timelapse.service
```

### Step 4: Check the status
```bash
sudo systemctl status timelapse.service
```

## Additional Information

- Photos will be saved to `/home/pi/timelapse/` with filenames like `timelapse_20250402_153000.jpg`
- Logs will be saved to `/home/pi/timelapse.log`
- You can modify the `INTERVAL` variable in the script to change the time between photos
- Make sure your Raspberry Pi NoIR camera is properly connected and enabled in `raspi-config`
- The script uses `libcamera-still` which is standard for Raspberry Pi OS Bullseye and newer

## Managing the Service

To check the service status:
```bash
sudo systemctl status timelapse.service
```

To stop the service:
```bash
sudo systemctl stop timelapse.service
```

To start the service:
```bash
sudo systemctl start timelapse.service
```

To view the logs:
```bash
tail -f /home/pi/timelapse.log
```

## Troubleshooting

If the camera isn't working:
1. Check that the camera is properly connected
2. Ensure the camera is enabled in raspi-config:
   ```bash
   sudo raspi-config
   ```
   Navigate to "Interface Options" > "Camera" and enable it
3. Reboot the Raspberry Pi:
   ```bash
   sudo reboot
   ```

If the service doesn't start:
1. Check the service status:
   ```bash
   sudo systemctl status timelapse.service
   ```
2. Check the logs:
   ```bash
   tail -f /home/pi/timelapse.log
   ```
