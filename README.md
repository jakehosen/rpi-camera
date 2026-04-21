# Raspberry Pi NoIR Camera Timelapse Setup Instructions

This document provides step-by-step instructions for setting up a Python script that automatically takes photos using a Raspberry Pi NoIR camera every 15 minutes and starts on boot.

## Connecting your device
* Plug in your device and it will automatically connect to the **eiot** wifi network.
* Connect to your device. Type the following into the terminal ```ssh student@iotcamXX``` (replace XX with your device ID). Ask the prof for passwords.
* Once you've confirmed that your device is up and running we can start getting things setup. Keep the ssh session open, we'll use it in a minute.

## Installation Steps

### Step 1: Create the Python script
1. Download the timelapse.py file and use the networking protocol **scp** to transmit the data.
2. Open a new Windows Powershell or other terminal window.
3. Make sure you are navigated to the directory on your computer with timelapse.py. Then type the following (again remember to replace XX with your device id):
   ```bash
   sudo scp timelapse.py student@iotcamXX:/home/student/
   ```
5. Go to your ssh window and enter the following:
   ```bash
   sudo chmod +x /home/student/timelapse.py
   ```

### Step 2: Create the systemd service
1. Transfer the systemd service file into /etc/systemd/system/ as follows:
   ```bash
   sudo scp timelapse.service student@iotcamXX:/etc/systemd/system/
   ```
3. Got back to your SSH session. Make sure that you account is configured to access the files appropriately:
```bash
sudo usermod -a -G video,gpio student
sudo usermod -a -G i2c,spi student
```
### Step 3: Enable and start the service
Enter the following commands while still in your ssh window.
```bash
sudo systemctl daemon-reload
sudo systemctl enable ~/timelapse.service
sudo systemctl start timelapse.service
```

### Step 4: Check the status
```bash
sudo systemctl status timelapse.service
```

## Additional Information

- Photos will be saved to `/home/student/timelapse/` with filenames like `timelapse_20250402_153000.jpg`
- Logs will be saved to `/home/student/timelapse.log`
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
tail -f /home/student/timelapse.log
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
   tail -f /home/student/timelapse.log
   ```



   ## Getting your data
   At the end of the deployment, your photos will be stored in /home/student/timelapse. You can access your photos using scp to transfer the images over the network using the following command. Go to your homee directory and make a photo called rpi_photos. Then use this command to download the photos to rpi_photos:
   ```
   scp student@iotcamXX:/home/student/timelapse/* ~/rpi_photos
   ```
