import tarfile
import torchaudio
import os
from io import BytesIO
from google.cloud import speech_v1
from google.cloud.speech_v1.types import RecognitionConfig
import tkinter as tk
import threading

# torchaudio 백엔드 설정 "sountfile"
torchaudio.set_audio_backend("soundfile")
# google API 환경변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\sunbin\\challenge-395408-6472f6ef3591.json"
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:\\Users\\sunbin\\challenge-395408-6472f6ef3591.json"

def sample_recognize(file_obj, rate):
    # Google Cloud Speech-to-Text API를 사용하여 오디오 파일에서 텍스트 추출
    client = speech_v1.SpeechClient()
    language_code = "ko-KR" # 언어 : 한국어
    encoding = RecognitionConfig.AudioEncoding.LINEAR16 # 인코딩 방식: LINEAR16
    config = {
        "language_code": language_code,
        "sample_rate_hertz": rate,
        "encoding": encoding
    }
    content = file_obj.read()
    audio = {"content": content}
    response = client.recognize(config=config, audio=audio)
    
    # 응답에서 텍스트 추출하여 GUI에 표시
    for result in response.results:
        show_text("{}".format(result.alternatives[0].transcript))

def segment_audio(file_name, segment_length=50):
    # 오디오 파일을 세그먼트로 분할 - 현재 50초
    waveform, sample_rate = torchaudio.load(file_name, format="wav")
    total_frames = waveform.size(1)
    segment_frames = sample_rate * segment_length
    segments = []

    for start in range(0, total_frames, segment_frames):
        end = start + segment_frames
        segments.append(waveform[:, start:end]) # 모든 채널, start to end
    
    return segments, sample_rate

def process_audio_files():
    # tar.gz 파일에서 FLAC 오디오 파일들을 추출하고 Google STT API로 전송
    file_name = "sampleVoice.wav"
    
    segments, sample_rate = segment_audio(file_name)
    
    for segment in segments:
        # 각 세그먼트를 BytesIO 객체로 변환
        buffer = BytesIO()
        
        # PCM 형식으로 WAV 파일 저장
        torchaudio.save(
            buffer,
            segment,
            sample_rate,
            format="wav", 
            encoding="PCM_S", 
            bits_per_sample=16
        )
        
        buffer.seek(0)
        sample_recognize(buffer, sample_rate)


def threaded_process_audio_files():
    # 별도의 스레드 호출
    thread = threading.Thread(target=process_audio_files)
    thread.start()

def show_text(output_text):
    # GUI Text 위젯에 텍스트 추가
    text_widget.insert(tk.END, output_text + "\n")

# GUI 초기화
root = tk.Tk()
root.title("Text")
    
# Text 위젯 (출력 텍스트를 표시할 곳)
text_widget = tk.Text(root, wrap=tk.WORD, width=100, height=40)
text_widget.pack(pady=10, padx=10)

# 오디오 파일 처리 버튼
process_button = tk.Button(root, text="Process STT", command=threaded_process_audio_files())
process_button.pack(pady=10)

# GUI 메인 루프 실행
root.mainloop()