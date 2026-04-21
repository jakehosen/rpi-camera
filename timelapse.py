#!/usr/bin/env python3
# motion_camera.py - Monitors for motion and captures images when detected, plus regular timelapse

import os
import time
import datetime
import subprocess
import signal
import numpy as np
import cv2
from pathlib import Path
import threading
import queue

# Configuration
SAVE_DIRECTORY = "/home/jhosen/motion_detection/timelapse"
PIPE_PATH = "/tmp/camera_feed"
IMAGE_PREFIX_MOTION = "motion_"
IMAGE_PREFIX_TIMELAPSE = "timelapse_"
MOTION_THRESHOLD = 25
FRAME_RATE = 10
COOLDOWN_PERIOD = 5
TIMELAPSE_INTERVAL = 900  # Seconds between timelapse photos (900 = 15 minutes)
RESOLUTION = "640x480"

# Global variables
frame_queue = queue.Queue(maxsize=10)
running = True
last_motion_capture_time = 0
last_timelapse_capture_time = 0

def setup():
    Path(SAVE_DIRECTORY).mkdir(parents=True, exist_ok=True)
    print(f"Images will be saved to: {SAVE_DIRECTORY}")
    print(f"Timelapse interval: {TIMELAPSE_INTERVAL} seconds")
    # Create named pipe if it doesn't exist
    if not os.path.exists(PIPE_PATH):
        os.mkfifo(PIPE_PATH)

def capture_image(frame, image_type="motion"):
    """Save the current frame as a JPEG image."""
    global last_motion_capture_time, last_timelapse_capture_time
    
    current_time = time.time()
    
    if image_type == "motion":
        # Check motion capture cooldown
        if current_time - last_motion_capture_time < COOLDOWN_PERIOD:
            return False
        last_motion_capture_time = current_time
        prefix = IMAGE_PREFIX_MOTION
    else:  # timelapse
        # Check timelapse interval
        if current_time - last_timelapse_capture_time < TIMELAPSE_INTERVAL:
            return False
        last_timelapse_capture_time = current_time
        prefix = IMAGE_PREFIX_TIMELAPSE
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{prefix}{timestamp}.jpg"
    filepath = os.path.join(SAVE_DIRECTORY, filename)
    
    try:
        cv2.imwrite(filepath, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])
        if image_type == "motion":
            print(f"Motion detected! Photo captured: {filename}")
        else:
            print(f"Timelapse photo captured: {filename}")
        return True
    except Exception as e:
        print(f"Unexpected error in capture_image: {e}")
        return False

def process_frames():
    """Process video frames to detect motion and handle timelapse."""
    prev_frame = None
    while running:
        try:
            if frame_queue.empty():
                time.sleep(0.1)
                continue
            frame = frame_queue.get()
            
            # Check if it's time for a timelapse photo
            current_time = time.time()
            if current_time - last_timelapse_capture_time >= TIMELAPSE_INTERVAL:
                capture_image(frame, image_type="timelapse")
            
            # Motion detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.GaussianBlur(gray, (21, 21), 0)
            if prev_frame is None:
                prev_frame = gray
                continue
            frame_delta = cv2.absdiff(prev_frame, gray)
            thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
            thresh = cv2.dilate(thresh, None, iterations=2)
            contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            motion_detected = False
            for contour in contours:
                if cv2.contourArea(contour) > MOTION_THRESHOLD:
                    motion_detected = True
                    break
            if motion_detected:
                capture_image(frame, image_type="motion")
            prev_frame = gray
        except Exception as e:
            print(f"Error in process_frames: {e}")
            time.sleep(0.5)

def capture_video_feed():
    """Capture video feed using rpicam-vid via named pipe."""
    global running
    process = None
    try:
        command = [
            "rpicam-vid",
            "--codec", "yuv420",
            "--width", RESOLUTION.split("x")[0],
            "--height", RESOLUTION.split("x")[1],
            "--framerate", str(FRAME_RATE),
            "--timeout", "0",
            "--nopreview",
            "--output", PIPE_PATH
        ]

        # Start rpicam-vid writing to the named pipe
        process = subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Wait for rpicam-vid to initialize and start writing
        time.sleep(3)

        width = int(RESOLUTION.split("x")[0])
        height = int(RESOLUTION.split("x")[1])
        frame_size = width * height * 3 // 2

        # Open the named pipe for reading
        with open(PIPE_PATH, "rb") as pipe:
            while running:
                raw_frame = bytearray()
                bytes_needed = frame_size
                while bytes_needed > 0 and running:
                    chunk = pipe.read(min(65536, bytes_needed))
                    if not chunk:
                        print("Camera stream ended")
                        running = False
                        break
                    raw_frame.extend(chunk)
                    bytes_needed -= len(chunk)

                if not running or len(raw_frame) != frame_size:
                    break

                try:
                    yuv = np.frombuffer(raw_frame, dtype=np.uint8).reshape((height * 3 // 2, width))
                    bgr = cv2.cvtColor(yuv, cv2.COLOR_YUV2BGR_I420)
                    if not frame_queue.full():
                        frame_queue.put(bgr)
                except Exception as e:
                    print(f"Frame conversion error: {e}")
                    continue

    except Exception as e:
        print(f"Error in capture_video_feed: {e}")
    finally:
        if process is not None:
            process.terminate()
            process.wait()
        running = False

def signal_handler(sig, frame):
    global running
    print("Stopping motion detection...")
    running = False

def main():
    global running
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    setup()
    print("Starting motion detection camera with timelapse...")
    try:
        process_thread = threading.Thread(target=process_frames)
        process_thread.daemon = True
        process_thread.start()
        capture_video_feed()
        process_thread.join(timeout=2)
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        running = False
        # Clean up the named pipe
        if os.path.exists(PIPE_PATH):
            os.remove(PIPE_PATH)
        print("Motion detection camera stopped.")

if __name__ == "__main__":
    main()
