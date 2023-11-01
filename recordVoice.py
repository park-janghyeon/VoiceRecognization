import os
import keyboard
import subprocess
from datetime import datetime

def generate_filename():
    return f"output.wav" # 녹음된 파일은 output.wav 이름으로 저장

def start_recording(filename):
    cmd = ["arecord", "-D", "plughw:1,0", "-f", "cd", filename] # card번호-1의 녹음장치-0 사용
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def stop_recording(process):
    process.terminate() 

print("Press 'r' to start recording and 'q' to stop.")
    
recording_process = None
while True:
    # 키보드의 r버튼이 눌러져있는 상태일 때
    if keyboard.is_pressed('r') and not recording_process:
        filename = generate_filename()
        recording_process = start_recording(filename)
        print(f"Recording started... Saving to {filename}")
    elif keyboard.is_pressed('q') and recording_process:
        stop_recording(recording_process)
        print("Recording stopped.")
        break
