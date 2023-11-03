import os
import time
from google.cloud import speech_v1p1beta1 as speech
from google.cloud.speech_v1p1beta1 import types
import pyaudio
from difflib import SequenceMatcher

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
                first_stage(transcript)
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

# 1단계 : 유사도 측정해서 1단계 명령어 출력 및 2단계 명령어 리턴
def first_stage(transcript):
    highest_similarity = 0.0
    most_similar = None

    predefined_sentences = {
        "날씨가 너무 더워": ["에어콘켜", "에어컨작동", "선풍기"],
        "안방이 춥네": ["안방난방온도 올려", "안방난방켜", "따뜻하게해줘"],
        "거실이 어두워": ["거실밝게", "거실불밝게", "거실조명켜", "거실조명켜라", "전체불켜", "전체불켜라", "전체조명켜", "전체조명켜라", "조명밝게"],
        "공기가 탁하네": ["창문열어", "커튼열어", "문열어", "창문열어"],
        "나 외출한다": ["보일러꺼", "보일러 정지", "전체조명꺼", "전체조명꺼라", "전등꺼", "외출모드", "외출모드설정", "외출모드실행"],
        "시원한 것 마실래": ["냉장고", "냉장고로와"],
        "점심은 중국집 배달시켜줘": ["전화번호부", "중국집전화연결", "중국집", "중국집번호", "통화", "전화걸기", "전화통화"],
        "핸드폰 충전해줘": ["충전해", "충전하러가", "충전"],
        "거실 좀 치워놔": ["거실청소"],
        'TV로 뉴스 틀어줘' : ['티비', '뉴스', '뉴스안내','뉴스안내해줘', '뉴스정보'],
        '오늘 일정은 어떻게 돼?' : ['일정검색', '일정관리', '일정관리안내해줘', '일정안내', '일정확인'],
        '아이스크림 넣어줘': ['파워냉동', '냉장고', '냉장고로와'],
        '가스레인지 켜놓고 왔어': ['까스닫아', '까스닫어', '까스밸브', '까스밸브닫아', '까스잠거', '까스잠궈'],
        '안방에 불켜줘': ['안방불켜', '안방불켜라', '안방조명켜', '안방조명켜라'],
        '저녁은 피자먹을래': ['피잣집', '피잣집전화연결', '피잣집 번호', '통화', '전화걸기', '전화통화'],
        '햇빛이 뜨거워': ['커튼닫아', '에어콘켜', '에어컨작동', '선풍기'],
        'TV 소리가 작네': ['티비', '볼륨업', '볼륨높임', '볼륨크게해줄래'],
        '집안이 눅눅하네': ['가습기', '가습기작동'],
        '공부방에 불켜고 따뜻하게 해줘': ['공부방점등', '공부방켜', '공부방난방', '보일러', '보일러작동', '보일러켜줘', '따뜻하게해줘'],
        '누가왔나봐': ['월패드', '월패드보여줘'],
        '이메일 보내줘': ['아웃룩', '이메일보내기', '전자메일', '전자우편', '메일', '메일보내기', '메일작성', '메일전송'],
        '택배왔는지 확인하려고': ['경비실연결', '경비실통화'],
        '침실로 들어갈께': ['침실불켜', '침실전등', '침실전등켜'],
        '나 잔다': ['전체불꺼', '전체불꺼라', '전체조명꺼', '전체조명꺼라', '침실불꺼', '취침모드'],
        '엄마에게 문자보내줘': ['문자메시지', '문자전송', '발신'],
    }
    matchingTable = {
        "날씨가 너무 더워" : "거실로 이동하여 에어콘 앞에서3 초간 정지",
        "안방이 춥네" : "안방으로 이동하여 보일러 스위치 앞에서 3 초간정지",
        "거실이 어두워": "거실로 이동하여 전등스위치 앞에서 3 초간 정지",
        "공기가 탁하네": "거실로 이동하여 창문앞에 3 초간 정지",
        "나 외출한다" : "거실로 이동하여 보일러 스위치 앞에서 3 초간정지, 전등스위치 앞으로 이동하여 3 초간 정지",
        "시원한 것 마실래" : "거실로 이동하여 냉장고 앞에서 3 초간 정지",
        "점심은 중국집 배달시켜줘" : "거실로 이동하여 전화기 앞에서 3 초간 정지",
        "핸드폰 충전해줘" : "거실로 이동하여 충전기 앞에서 3 초간 정지",
        "거실 좀 치워놔" : "거실로 이동하여 청소기 앞에서 3 초간 정지",
        'TV로 뉴스 틀어줘' : "거실로 이동하여 TV 앞에서 3 초간 정지",
        '오늘 일정은 어떻게 돼?' : "안방으로 이동하여 컴퓨터 앞에서 3 초간 정지",
        '아이스크림 넣어줘' : "거실로 이동하여 냉장고 앞에서 3 초간 정지",
        '가스레인지 켜놓고 왔어' : "거실로 이동하여 가스레인지 앞에서 3 초간 정지",
        '안방에 불켜줘' : "안방으로 이동하여 전등스위치 앞에서 3 초간 정지",
        '저녁은 피자먹을래' : "거실로 이동하여 전화기 앞에서 3 초간 정지",
        '햇빛이 뜨거워' : "거실로 이동하여 창문 앞에서 3 초간 정지. 에어콘 앞으로 이동하여 3 초간 정지",
        'TV 소리가 작네' : "거실로 이동하여 TV 앞에서 3 초간 정지",
        '집안이 눅눅하네': "거실로 이동하여 가습기 앞에서 3 초간 정지",
        '공부방에 불켜고 따뜻하게 해줘' : "공부방으로 이동하여 전등스위치 앞에서 3 초간 정지 , 보일러 스위치 앞에서 3 초간정지",
        '누가왔나봐' : "거실로 이동하여 월패드 앞에서 3 초간 정지",
        '이메일 보내줘' : "안방으로 이동하여 컴퓨터 앞에서 3 초간 정지",
        '택배왔는지 확인하려고': "거실로 이동하여 월패드 앞에서 3 초간 정지",
        '침실로 들어갈께' : "침실로 이동하여 전등스위치 앞에서 3 초간 정지",
        '나 잔다' : "침실로 이동하여 전등스위치 앞에서 3 초간 정지",
        '엄마에게 문자보내줘': "거실로 이동하여 전화기 앞에서 3 초간 정지",    
    }
    

    #유사도 측정
    for key, _ in predefined_sentences.items():
        # SequenceMatcher를 사용하여 유사도 계산
        similarity = SequenceMatcher(None, transcript, key).ratio()
        if similarity >= highest_similarity:
            highest_similarity = similarity
            most_similar = key

    # 가장 유사한 문장의 키를 반환합니다 (예: "greeting", "farewell", ...)
    print(f'trasnscript: {transcript}')
    print(f'1단계 명령어:{most_similar}')
    time.sleep(1)
    print(f'2단계 명령어:{predefined_sentences[most_similar]}')
    time.sleep(1)
    print(f'수행 동작 : {matchingTable[most_similar]}')
    print()
    return predefined_sentences[most_similar]

def main():
    print("실시간 STT 시작. 종료하려면 Ctrl+C를 누르세요.")
    stream_audio = StreamAudioToText()
    stream_audio.start()

if __name__ == '__main__':
    main()