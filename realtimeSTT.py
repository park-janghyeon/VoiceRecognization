import os
import time
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import types
import pyaudio

# Google STT 인증 정보 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, 'challenge-395408-6472f6ef3591.json')
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = CREDENTIALS_PATH

count = 0
MAX_STREAM_MINUTES = 4.5  # 5분 전에 스트림을 재시작합니다.

class StreamAudioToText:
    def __init__(self, rate=44100, chunk=220500):  
        self.rate = rate  
        self.chunk = chunk  
        self.client = speech.SpeechClient()
        self.config = types.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code='ko-KR'
        )
        self.streaming_config = types.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True
        )
        self.audio_interface = pyaudio.PyAudio()
        self.audio_stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=1  # 여기에 장치 번호를 지정
        )
        self.start_time = time.time()

    def listen_print_loop(self, responses):
        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            
            transcript = result.alternatives[0].transcript

            if result.is_final:
                global count
                count += 1
                print(f'{count}:{transcript}')
                break

    def start(self):
        while True: 
            try:
                if time.time() - self.start_time > MAX_STREAM_MINUTES * 60:
                    self.restart_stream()
                    
                audio_data = self.audio_stream.read(self.chunk, exception_on_overflow=False)
                request = types.StreamingRecognizeRequest(audio_content=audio_data)
                responses = self.client.streaming_recognize(self.streaming_config, [request])
                self.listen_print_loop(responses)
            
            except IOError as e:
                print(f"IOError: {e}")
                # 여기서 오류를 처리하고 필요한 경우 스트림을 재시작할 수 있습니다.
                self.restart_stream()


    def restart_stream(self):
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.audio_interface.terminate()
        
        self.audio_interface = pyaudio.PyAudio()
        self.audio_stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=self.rate,
            input=True,
            frames_per_buffer=self.chunk,
            input_device_index=1  # 여기에 장치 번호를 지정
        )
        self.start_time = time.time()
        
def main():
    print("실시간 STT 시작. 종료하려면 Ctrl+C를 누르세요.")
    stream_audio = StreamAudioToText()
    stream_audio.start()

if __name__ == '__main__':
    main()
