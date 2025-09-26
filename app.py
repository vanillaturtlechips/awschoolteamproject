# --------------------------------------------------------------------------
# 필요한 라이브러리들을 불러옵니다. (Import)
# --------------------------------------------------------------------------
import uvicorn  # ASGI 서버 구동을 위한 라이브러리
import google.generativeai as genai  # Gemini AI 모델 사용을 위한 라이브러리
import re  # 정규 표현식 사용 (텍스트에서 특정 패턴을 찾기 위함)
import json  # JSON 데이터 처리
import os  # 운영체제와 상호작용 (환경 변수 등)
from dotenv import load_dotenv  # .env 파일에서 환경 변수를 불러오기 위함
from typing import Optional  # 타입 힌팅 (예: None일 수도 있는 타입 지정)
from PIL import Image  # 이미지 파일 처리를 위한 Pillow 라이브러리

# FastAPI 관련 라이브러리들
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.staticfiles import StaticFiles  # CSS, JS 같은 정적 파일 서빙
from fastapi.responses import HTMLResponse, JSONResponse  # 응답 형식 지정
from fastapi.templating import Jinja2Templates  # HTML 템플릿 사용
from pydantic import BaseModel  # 데이터 유효성 검사 및 형태 정의

# CORS 관련 라이브러리들

from fastapi.middleware.cors import CORSMiddleware # CORS 허용 미들웨어


# --------------------------------------------------------------------------
# 로컬 모듈 및 환경 설정
# --------------------------------------------------------------------------

# 로컬에 있는 search_youtube.py 파일에서 함수들을 불러옵니다.
try:
    from search_youtube import get_youtube_link, get_youtube_thumbnail
except ImportError:
    # 만약 search_youtube.py 파일이 없을 경우를 대비해, 프로그램이 멈추지 않도록 임시 함수를 정의합니다.
    def get_youtube_link(song_title, artist):
        print(f"임시 함수 호출: {artist} - {song_title}의 유튜브 링크를 찾습니다.")
        return f"https://www.youtube.com/results?search_query={artist}+{song_title}"
    def get_youtube_thumbnail(song_title, artist):
        print(f"임시 함수 호출: {artist} - {song_title}의 썸네일을 찾습니다.")
        return "/static/default_cover.jpg"

# .env 파일을 로드하여 그 안의 변수들을 환경 변수로 설정합니다.
load_dotenv()

# 환경 변수에서 API 키를 가져옵니다.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
# 만약 키가 없다면, 에러를 발생시켜 프로그램을 중지시킵니다. (안전장치)
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY가 .env 파일에 설정되지 않았습니다.")
# Gemini 라이브러리에 API 키를 설정합니다.
genai.configure(api_key=GEMINI_API_KEY)

# 사용할 Gemini 모델들을 미리 초기화해둡니다.
text_model = genai.GenerativeModel('gemini-2.5-pro')  # 텍스트 분석용 모델
vision_model = genai.GenerativeModel('gemini-2.5-pro')  # 이미지 분석용 모델

# --------------------------------------------------------------------------
# FastAPI 애플리케이션 설정
# --------------------------------------------------------------------------

# FastAPI 앱 인스턴스를 생성합니다.
app = FastAPI()


# 모든 출처에서의 요청을 허용합니다. 
origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# 정적 파일(static)과 템플릿(templates) 폴더의 경로를 앱에 알려줍니다.
# /static 경로로 오는 요청은 static 폴더 안의 파일들을 보여주라는 의미입니다.
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Pydantic을 사용해 API 요청 본문의 데이터 형식을 미리 정의합니다.
# 이렇게 하면 FastAPI가 자동으로 데이터 유효성을 검사해줍니다.
class TextRequest(BaseModel):
    message: str  # message라는 이름의 문자열 데이터가 반드시 있어야 함

class ColorRequest(BaseModel):
    color: str  # color라는 이름의 문자열 데이터가 반드시 있어야 함

# --------------------------------------------------------------------------
# 핵심 로직 함수: 감정 분석 및 노래 추천
# --------------------------------------------------------------------------
def analyze_and_recommend(user_message: str, image: Optional[Image.Image] = None):
    """사용자의 메시지나 이미지를 분석하여 노래를 추천하고 YouTube 정보를 덧붙입니다."""
    
    # 이미지가 있으면 vision 모델을, 없으면 text 모델을 사용하도록 선택합니다.
    model_to_use = vision_model if image else text_model
    
    # 이미지 유무에 따라 Gemini에게 보낼 명령서(프롬프트)와 요청 데이터를 다르게 구성합니다.
    if image:
        # 이미지가 있을 때의 프롬프트
        prompt_text = "이 이미지의 분위기, 색감, 사물, 상황을 종합적으로 분석해서 그에 어울리는 노래 3곡을 추천해줘. 사용자의 추가 요청사항도 반영해줘."
        request_content = [prompt_text, f"사용자 추가 요청: {user_message}", image]
    else:
        # 텍스트만 있을 때의 프롬프트
        prompt_text = f"""
        당신은 사용자의 기분에 맞춰 노래를 추천해주는 감성적인 AI 챗봇입니다.
        사용자의 요청: "{user_message}"

        위 요청을 분석해서:
        1. 사용자의 감정이나 요청의 핵심을 한 문장으로 요약해주세요. (예: "신나는 드라이브에 어울리는 기분")
        2. 그 상황에 가장 잘 어울리는 노래 3곡을 추천해주세요.
           - 사용자가 특정 장르(예: '팝송', 'J-POP')나 특징을 언급했다면, 반드시 그 요구사항을 반영해야 합니다.
           - 별다른 언급이 없다면, 요청 내용에 가장 어울리는 국가의 노래를 자유롭게 추천해주세요.
        """
        request_content = [prompt_text]

    # Gemini가 응답해야 할 JSON 형식을 명확하게 지시합니다.
    common_response_format = """
    응답은 반드시 아래의 JSON 형식과 동일해야 합니다:
    {{
        "emotion": "분석된 감정 또는 이미지 분위기 요약",
        "recommended_songs": [
            {{"title": "노래 제목", "artist": "가수명"}},
            {{"title": "노래 제목", "artist": "가수명"}},
            {{"title": "노래 제목", "artist": "가수명"}}
        ]
    }}
    """
    request_content.append(common_response_format)
    
    try:
        # 터미널에 로그를 출력하여 현재 상태를 확인합니다.
        print(f"🔍 Gemini API 요청 메시지: {user_message}")
        if image: print("🖼️ 이미지와 함께 요청됨")

        # 준비된 요청 데이터를 Gemini 모델에게 보내 응답을 받습니다.
        response = model_to_use.generate_content(request_content)
        response_text = response.text.strip()
        print(f"🔍 Gemini 원본 응답: '{response_text}'")

        # 응답 텍스트에서 JSON 부분만 추출합니다.
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if not json_match:
            print("❌ 응답에서 JSON 객체를 찾지 못했습니다.")
            return None
            
        json_text = json_match.group()
        
        # 추출한 텍스트를 JSON 객체로 변환(파싱)합니다.
        try:
            result = json.loads(json_text)
        except json.JSONDecodeError:
            # 파싱에 실패하면, 흔한 오류(예: 마지막 쉼표)를 수정하고 다시 시도합니다.
            json_text = re.sub(r',\s*([}\]])', r'\1', json_text)
            result = json.loads(json_text)
        
        # 추천된 각 노래에 대해 YouTube 정보를 추가합니다.
        enriched_songs = []
        for song in result.get('recommended_songs', []):
            song_title, artist = song.get('title'), song.get('artist')
            if not song_title or not artist: continue

            # search_youtube.py의 함수들을 호출합니다.
            youtube_link = get_youtube_link(song_title, artist)
            thumbnail_url = get_youtube_thumbnail(song_title, artist)
            
            # 기존 노래 정보에 유튜브 링크와 썸네일을 추가합니다.
            enriched_songs.append({
                'title': song_title, 'artist': artist,
                'youtube_link': youtube_link or '#',
                'thumbnail': thumbnail_url or '/static/default_cover.jpg'
            })
            
        # 최종 결과에 풍부해진 노래 목록을 담아 반환합니다.
        result['recommended_songs'] = enriched_songs
        return result
        
    except Exception as e:
        # 어떤 단계에서든 오류가 발생하면 터미널에 로그를 남기고 None을 반환합니다.
        print(f"❌ 전체 로직 오류: {e}")
        return None

# --------------------------------------------------------------------------
# API 라우트(경로) 설정: 프론트엔드의 요청을 받아 처리하는 길목
# --------------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
async def serve_home(request: Request):
    """사용자가 처음 접속했을 때 메인 HTML 페이지를 보여줍니다."""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/chat/text", response_class=JSONResponse)
async def handle_text_chat(request_data: TextRequest):
    """텍스트 메시지 요청('/api/chat/text')을 처리합니다."""
    recommendation = analyze_and_recommend(user_message=request_data.message)
    if not recommendation:
        return JSONResponse(status_code=500, content={"error": "추천 데이터를 생성하지 못했습니다."})
    return JSONResponse(content=recommendation)

@app.post("/api/chat/color", response_class=JSONResponse)
async def handle_color_chat(request_data: ColorRequest):
    """색상 선택 요청('/api/chat/color')을 처리합니다."""
    color_messages = {
        "red": "빨간색처럼 열정적이고 강렬한 느낌", "blue": "파란색처럼 차분하고 평온한 느낌",
        "yellow": "노란색처럼 밝고 활기찬 느낌", "green": "초록색처럼 신비롭고 창의적인 느낌",
        "pink": "분홍색처럼 로맨틱하고 부드러운 느낌", "orange": "주황색처럼 따뜻하고 에너지 넘치는 느낌"
    }
    user_message = color_messages.get(request_data.color, "선택한 색상과 어울리는 느낌")
    recommendation = analyze_and_recommend(user_message=user_message)
    if not recommendation:
        return JSONResponse(status_code=500, content={"error": "추천 데이터를 생성하지 못했습니다."})
    return JSONResponse(content=recommendation)

@app.post("/api/chat/image", response_class=JSONResponse)
async def handle_image_chat(image: UploadFile = File(...)):
    """이미지 파일 업로드 요청('/api/chat/image')을 처리합니다."""
    try:
        # 업로드된 파일을 Pillow가 처리할 수 있는 이미지 객체로 변환합니다.
        pil_image = Image.open(image.file)
        recommendation = analyze_and_recommend(user_message="이 이미지와 어울리는 노래", image=pil_image)
        if not recommendation:
            return JSONResponse(status_code=500, content={"error": "이미지 분석 후 추천 데이터를 생성하지 못했습니다."})
        return JSONResponse(content=recommendation)
    except Exception as e:
        print(f"❌ 이미지 처리 오류: {e}")
        return JSONResponse(status_code=500, content={"error": "이미지 파일을 처리하는 중 오류가 발생했습니다."})

# --------------------------------------------------------------------------
# 서버 실행
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # 이 파일이 직접 실행될 때 (예: python app.py) uvicorn 서버를 구동합니다.
    uvicorn.run(app, host="0.0.0.0", port=8000)