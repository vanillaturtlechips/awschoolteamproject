## 백엔드 작업 

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import google.generativeai as genai
import requests
import re
import json
import os
from dotenv import load_dotenv  # 추가
from search_youtube import get_youtube_link, get_youtube_thumbnail  # 추가

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-pro')

app = FastAPI()
templates = Jinja2Templates(directory="templates")

def fix_json_format(json_text):
    """잘못된 JSON 형식 수정 시도"""
    try:
        # 흔한 JSON 오류들 수정
        fixed = json_text.replace("'", '"')  # 작은따옴표를 큰따옴표로
        fixed = re.sub(r',\s*}', '}', fixed)  # 마지막 쉼표 제거
        fixed = re.sub(r',\s*]', ']', fixed)  # 마지막 쉼표 제거
        
        print(f"🔧 JSON 수정 시도: {fixed}")
        return fixed
    except:
        return None


def analyze_emotion_and_recommend(user_message):
    """사용자 메시지에서 감정을 분석하고 음악 추천"""
    
    prompt = f"""
    사용자가 다음과 같이 말했습니다: "{user_message}"
    
    위 메시지를 분석해서:
    1. 사용자의 감정을 "~한 기분" 형태로 분석
    2. 그 감정에 맞는 한국 음악 3곡 추천

    응답 형식:
    {{
        "emotion": "예시: 차분하고 우울한 기분",
        "recommended_songs": [
            {{"title": "노래제목", "artist": "가수명"}},
            {{"title": "노래제목", "artist": "가수명"}},
            {{"title": "노래제목", "artist": "가수명"}}
        ]
     }}
    """
    
    try:
        print(f"🔍 요청 메시지: {user_message}")
        
        response = model.generate_content(prompt)
        print(f"🔍 Gemini 원본 응답: '{response.text}'")
        print(f"🔍 응답 길이: {len(response.text)}")
        
        if not response.text or len(response.text.strip()) == 0:
            print("❌ 빈 응답 받음")
            return None
            
        response_text = response.text.strip()
        
        # 더 강력한 JSON 추출
        # 1. ```json 코드 블록 제거
        response_text = re.sub(r'```json\s*', '', response_text)
        response_text = re.sub(r'```\s*', '', response_text)
        
        # 2. JSON 객체 찾기
        json_pattern = r'\{[^{}]*\{[^{}]*\}[^{}]*\}'  # 중첩된 JSON 패턴
        json_match = re.search(json_pattern, response_text, re.DOTALL)
        
        if json_match:
            json_text = json_match.group()
            print(f"🔍 추출된 JSON: {json_text}")
        else:
            # 간단한 JSON 패턴 시도
            simple_json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if simple_json_match:
                json_text = simple_json_match.group()
                print(f"🔍 간단 패턴으로 추출: {json_text}")
            else:
                print(f"❌ JSON 패턴을 찾을 수 없음: {response_text}")
                return None
        
        # JSON 파싱 시도
        try:
            result = json.loads(json_text)
            print(f"✅ 파싱 성공!")

            enriched_songs = []
            for song in result['recommended_songs']:
                song_title = song['title']
                artist = song['artist']
                
                # YouTube 링크 및 썸네일 검색
                print(f"🎵 YouTube 검색 중: {artist} - {song_title}")
                youtube_url = get_youtube_link(song_title, artist)
                thumbnail_url = get_youtube_thumbnail(song_title, artist)
                
                # 곡 정보에 YouTube 정보 추가
                enriched_song = {
                    'title': song_title,
                    'artist': artist,
                    'youtube_url': youtube_url or '#',  # 링크가 없으면 #
                    'thumbnail': thumbnail_url or '/static/default_cover.jpg'
                }
                enriched_songs.append(enriched_song)
            
            # 결과에 YouTube 정보가 포함된 곡 목록 반환
            result['recommended_songs'] = enriched_songs
            return result
        
        except json.JSONDecodeError as parse_error:
            print(f"❌ JSON 파싱 실패: {parse_error}")
            print(f"❌ 파싱 시도 텍스트: '{json_text}'")
            
            # 수동으로 JSON 수정 시도
            fixed_json = fix_json_format(json_text)
            if fixed_json:
                try:
                    result = json.loads(fixed_json)
                    print(f"✅ 수정 후 파싱 성공!")
                    return result
                except:
                    pass
            
            return None
        
    except Exception as e:
        print(f"❌ 전체 오류: {e}")
        return None

@app.get("/", response_class=HTMLResponse)
async def form_get(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/", response_class=HTMLResponse)
async def process_chat(request: Request, color: str = Form(...)):
    """색상 선택 처리 라우트"""
    
    color_messages = {
        "red": "빨간색을 선택했어요. 열정적이고 강렬한 느낌",
        "blue": "파란색을 선택했어요. 차분하고 평온한 느낌", 
        "yellow": "노란색을 선택했어요. 밝고 활기찬 느낌",
        "green": "초록색을 선택했어요. 신비롭고 창의적인 느낌",
        "pink": "분홍색을 선택했어요. 로맨틱하고 부드러운 느낌",
        "orange": "주황색을 선택했어요. 따뜻하고 에너지 넘치는 느낌"
    }
    
    user_message = color_messages.get(color, "색상을 선택했어요")
    
    recommendation_data = analyze_emotion_and_recommend(user_message)
    
    if not recommendation_data:
        return templates.TemplateResponse("index.html", {
            "request": request,
            "selected_color": color,
            "error": "죄송합니다. 잠시 후 다시 시도해주세요.",
            "show_result": True
        })
    
    return templates.TemplateResponse("index.html", {
        "request": request,
        "selected_color": color,
        "emotion_analysis": recommendation_data['emotion'],
        "recommended_songs": recommendation_data['recommended_songs'],
        "show_result": True
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
