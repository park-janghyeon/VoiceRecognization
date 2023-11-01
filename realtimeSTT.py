import os
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import types
import pyaudio

# Google STT 인증 정보 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "challenge-395408-6472f6ef3591.json"

class StreamAudioToText:
    def __init__(self, rate=44100, chunk=1024):
        # 초기화
        self.rate = rate  # 샘플링 비율 
        self.chunk = chunk  # 한 번에 읽을 오디오 데이터 크기
        
        # Google Cloud Speech Client 설정
        self.client = speech.SpeechClient()
        
        # 인식 설정: 한국어, LINEAR16 인코딩, 주어진 샘플링 비율 사용
        self.config = types.RecognitionConfig(
            encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
            sample_rate_hertz=self.rate,
            language_code='ko-KR' # 언어코드는 한국어
        )
        
        # 스트리밍 인식 설정
        self.streaming_config = types.StreamingRecognitionConfig(
            config=self.config,
            interim_results=True  # 중간 결과 계속해서 반환
        )
        
        # pyaudio를 사용한 오디오 인터페이스 설정
        self.audio_interface = pyaudio.PyAudio()
        self.audio_stream = self.audio_interface.open(
            format=pyaudio.paInt16,
            channels=1, # 채널 수는 1
            rate=self.rate, # rate는 44100
            input=True,
            frames_per_buffer=self.chunk,
        )

    def listen_print_loop(self, responses):
        # 받은 응답을 처리하고 CLI에 텍스트 표시
        for response in responses:
            if not response.results:
                continue
            result = response.results[0]
            if not result.alternatives:
                continue
            # 변환된 텍스트 추출
            transcript = result.alternatives[0].transcript
            # 텍스트를 CLI에 출력
            print(transcript)

    def start(self):
        # 오디오 스트리밍 시작
        requests = (types.StreamingRecognizeRequest(audio_content=self.audio_stream.read(self.chunk)) for _ in range(0, int(self.rate / self.chunk)))
        responses = self.client.streaming_recognize(self.streaming_config, requests)
        self.listen_print_loop(responses)
        # 오디오 스트림 종료
        self.audio_stream.stop_stream()
        self.audio_stream.close()
        self.audio_interface.terminate()
        
def main():
    print("실시간 STT 시작. 종료하려면 Ctrl+C를 누르세요.")
    stream_audio = StreamAudioToText()
    stream_audio.start()

if __name__ == '__main__':
    main()