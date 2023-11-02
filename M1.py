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
                    self.most_similar(transcript)
                    break

    #가장 유사도가 높은 단어를 출력하는 메소드
    def most_similar(self,transcript):
        highest_similarity = 0.0
        most_similar = None
        global count
        count += 1
        
        predescribed_words = [        
            "가격", "거실난방꺼라", "건조헹굼", "과거", "기분어때", "날씨안내해줘", "녹음", "다음",
            "가기", "거실난방온도내려", "걷기동작", "과거현재미래", "기어", "날씨정보", "녹음리스트", "다음메뉴",
            "가스닫아", "거실난방온도올려", "걸어", "관광레저테마파크", "기억", "날짜", "녹화", "다음명령",
            "가스밸브", "거실난방외출", "걸어줘", "관광정보", "기차시간", "날짜시간변경", "논술교육", "다음목록",
            "가스밸브닫아", "거실난방켜", "검색", "교육정보", "기차표", "날짜정렬", "논술정보", "다음문제도전",
            "가습기", "거실난방켜라", "검색하기", "교육콘텐츠", "까스닫아", "남쪽", "높은", "다음으로",
            "가습기작동", "거실로와", "검색해줘", "구간반복", "까스닫어", "내려가", "누리마루", "다이어리",
            "가습기정지", "거실밝게", "게임", "구두", "까스밸브", "내문서", "누리마루홍보관", "닫기",
            "가열헹굼", "거실불꺼", "경로", "구십층", "까스밸브닫아", "내일", "누리마루소개", "달력",
            "가장작게", "거실불꺼라", "경보기능", "구월", "까스잠거", "내일날씨", "누워", "답장",
            "가져오기", "거실불밝게", "경비실연결", "구층", "까스잠궈", "냉동온도설정", "눈감아", "대유증권",
            "가져와", "거실불어둡게", "경비실통화", "국어학습", "께임", "냉수헹굼", "눈떠", "더하기",
            "가족보기", "거실불켜", "계산기", "국제금융단지", "꼬리흔들어", "냉장고", "뉴스", "도구",
            "간단히", "거실불켜라", "계속", "국제비즈니스", "꽃", "냉장고로와", "뉴스안내", "도구모음",
            "감성모드", "거실소등", "골프", "굵게", "꽃새나무", "냉장온도설정", "뉴스안내안내해줘", "도리도리",
            "감성모드실행", "거실어둡게", "곱하기", "그룹선택", "끊기", "네비게이션", "뉴스안내해줘", "도마크",
            "감시", "거실점등", "공가져와", "그만", "끝내기", "네이버", "뉴스정보", "도시안내",
            "감시해", "거실조명꺼", "공부방꺼", "그쪽으로", "끝으로", "네이트", "느리게", "도우미",
            "개발개요", "거실조명꺼라", "공부방난방", "기념일", "나를봐", "네트워크연결", "다국어홍보시스템", "도움말",
            "개인일정관리", "거실조명켜", "공부방소등", "기념촬영", "나무", "네트워크연결끊기", "다른", "도움말항목",
            "거꾸로", "거실조명켜라", "공부방점등", "기념촬영하기", "나의정보", "년", "다른이름으로저장", "도착일",
            "거리", "거실청소", "공부방켜", "기능및역할", "난방모드", "노래방안내", "다른집통화", "도청시설안내",
            "거리측정", "거절", "공을가져와", "기록", "날봐", "노래방안내해줘", "다시입력", "돌아",
            "거실난방", "건강", "공지사항", "기본값복원", "날씨", "노트", "다시찍기", "돌아가",        
            "거실난방꺼", "건강지수", "공찾아", "기본자세", "날씨안내", "노트편집", "다시한번", "돌아봐",
            "동관", "라디오켜", "메인화면", "문자메세지", "받지마", "변환해", "부산시티투어", "사진앨범",
            "동기화", "라이브러리추가", "메일", "문자전송", "발신", "별표", "북쪽", "사진앨범안내해줘",
            "동명검색", "래프팅", "메일내용", "문잠가", "발신메세지", "보관", "붙여넣기", "사진찍기",
            "동봉하기", "로봇이란", "메일보내기", "문잠가줘", "밝게", "보기", "뷰모드", "사층",
            "동영상유씨씨", "로비문열어", "메일작성", "문제", "밥솥", "보내기", "뷰어", "삭제",
            "동요", "리스트", "메일전송", "문화특강", "방문리스트", "보낸사람", "뷰어정보", "삭제해",        
            "동쪽", "마스코트", "메일제목", "미디어검색", "방문자리스트", "보안", "비디오", "삼십층",
            "되감기", "마이크", "메일확인", "미디어라이브러리", "방범리스트", "보여줘", "비디오설정", "삼층",
            "둘리", "마지막결과보기", "명령", "미디어정보", "방범모드", "보일러", "비밀기능", "상세",
            "둘리야", "말하기", "몇시", "미디어플레이어", "방이로와", "보일러꺼", "비상연락", "상위",
            "뒤로", "멈춰", "몇시야", "미래", "방일로와", "보일러작동", "비상정지", "상자",
            "뒤로가", "메뉴", "몇시입니까", "미리보기", "배경화면설정", "보일러정지", "비용정산", "상태표시줄",
            "뒤로돌아", "메뉴삭제", "모니터링해", "밑으로", "배고파", "보일러켜", "비전", "새",
            "뒤로돌아가", "메뉴선택", "모두보내기", "바람방향설정", "배달", "복도", "비전및목표", "새로고침",
            "뒤쪽으로", "메모", "모두선택", "바로가기", "배터리잔량", "복사", "빠르게", "새로만들기",
            "드라마", "메모등록", "모드설정", "바로가기만들기", "백과사전", "복사하기", "빠른새로고침", "새로압축",
            "듣고", "메모리", "모든카테고리", "바로가기붙여넣기", "백라이트", "복원", "빵", "새메일",
            "듣기시작", "메모있어", "목록", "바이오리듬", "백업", "본관", "사람찾기", "새파일",
            "들려줘", "메모장", "목록삭제", "반대로", "백층", "볼륨", "사랑해", "새폴더",
            "등록", "메모재생", "목록선택", "반만내려", "번지점프", "볼륨낮춤", "사십층", "서관",
            "등록정보", "메모해", "목요일", "반복", "번호", "볼륨높임", "사용자이름", "서바이벌게임",
            "등산", "메모확인", "목표", "반복해", "벨소리", "볼륨다운", "사전", "서비스안내해줘"
        ]

        print(f'transcript : {transcript}')
        if transcript in predescribed_words:
            print(f'{count}:{transcript}')
     
        else:
            for word in predescribed_words:
                similarity = SequenceMatcher(None, transcript, word).ratio()
                if similarity >= highest_similarity:
                    highest_similarity = similarity
                    most_similar = word
            print(f'{count}:{most_similar}')


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