import serial
import time

opencr_port = '/dev/ttyACM0'  # OpenCR이 연결된 시리얼 포트
baudrate = 115200  # 통신 속도

# 시리얼 포트를 열고
ser = serial.Serial(opencr_port, baudrate, timeout=1)

# OpenCR에 'ping' 명령 보내기
ser.write(b'ping\n')

# OpenCR로부터 'pong' 대기
response = ser.readline().decode().strip()

if response == 'pong':
    print("OpenCR is communicating successfully!")
else:
    print("Failed to communicate with OpenCR. Response was:", response)

# 시리얼 포트 닫기
ser.close()
