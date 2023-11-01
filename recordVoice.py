import os
import keyboard
import subprocess
from datetime import datetime

def generate_filename():
    return f"output.wav"

def start_recording(filename):
    cmd = ["arecord", "-D", "plughw:1", "-f", "cd", filename] # plughw 번호가 1번
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def stop_recording(process):
    process.terminate()

print("Press 'r' to start recording and 'q' to stop.")
    
recording_process = None
while True:
    if keyboard.is_pressed('r') and not recording_process:
        filename = generate_filename()
        recording_process = start_recording(filename)
        print(f"Recording started... Saving to {filename}")
    elif keyboard.is_pressed('q') and recording_process:
        stop_recording(recording_process)
        print("Recording stopped.")
        break
