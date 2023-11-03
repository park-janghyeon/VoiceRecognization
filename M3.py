import serial
import time
import atexit

# OpenCR의 시리얼 포트와 통신 속도 설정
opencr_port = '/dev/ttyACM0'  # OpenCR이 연결된 시리얼 포트
baudrate = 115200  # OpenCR의 통신 속도 (bps)

# 시리얼 통신을 위한 객체 생성
ser = serial.Serial(opencr_port, baudrate, timeout=1)

# 로봇을 직진시키는 함수
def move_forward(distance_meters):
    # 'F'는 'Forward'를 나타내며, 다음 숫자는 직진할 거리를 미터 단위로 나타냅니다.
    command = f"F {distance_meters}\n"
    ser.write(command.encode('utf-8'))  # 명령을 인코딩하여 OpenCR에 보냅니다.
    print(f"Moving forward {distance_meters} meters")
    # 로봇이 이동하는 동안 대기할 수 있도록 충분한 시간을 기다립니다.
    # 실제 대기 시간은 로봇의 속도에 따라 조정되어야 합니다.
    time.sleep(distance_meters * 10)  # 예시로 거리에 비례하여 대기 시간을 설정합니다.

# 로봇을 1미터 직진시킵니다.
if __name__ == "__main__":
    move_forward(1)

# 프로그램 종료 시 시리얼 통신 종료
def close_serial_connection():
    if ser.is_open:
        ser.close()

# 프로그램 종료시 시리얼 통신을 정확히 종료하기 위한 처리
atexit.register(close_serial_connection)