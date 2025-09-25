# awschoolteamproject

## 프로젝트 소개
사용자의 현재 기분이나 상황에 맞는 음악 플레이리스트를 추천해주는 웹 기반의 챗봇 서비스입니다. 간단한 대화를 통해 원하는 분위기의 음악을 추천받을 수 있습니다.

## 프로젝트 아키텍처
![초기 아키텍처 구상](./pic/arki1.jpg)
![상세 아키텍처](./pic/arki2.jpg)

## 파일 구조

playlist-bot/
├── app.py              # 백엔드의 모든 것! (Flask 서버, API 로직 전부 여기에)
│
├── templates/
│   └── index.html      # 사용자에게 보여줄 유일한 HTML 페이지
│
├── static/
│   ├── style.css       # 페이지를 꾸미는 CSS 파일
│   └── script.js       # 프론트엔드 기능(API 요청 등)을 담은 JS 파일
│
├── requirements.txt    # 필요한 라이브러리 목록 (pip install -r requirements.txt)
│
└── .env                # API 키를 저장하는 비밀 파일 (aws 연동 및 open ai 연동 키값 저장)


## 주요 기능
* 자연어 입력을 통한 플레이리스트 추천 요청
* OpenAI 및 Gemini API를 활용한 사용자 맞춤형 음악 추천
* 웹 인터페이스를 통한 챗봇과의 실시간 상호작용

## 파일 구조