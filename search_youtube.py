import requests
import os
from dotenv import load_dotenv

load_dotenv()

def get_youtube_link(song_title: str, artist: str) -> str:
    """
    YouTube에서 음악 비디오를 검색하여 링크 반환
    
    Args:
        song_title: 노래 제목
        artist: 아티스트명
    
    Returns:
        YouTube URL 또는 None
    """
    try:
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_api_key:
            print("YouTube API 키가 설정되지 않았습니다.")
            return None
        
        search_queries = [
            f"{artist} {song_title} official mv",
            f"{artist} {song_title} official music video", 
            f"{artist} {song_title}",
            f"{song_title} {artist}"
        ]        

        for search_query in search_queries:
            print(f"검색 시도: {search_query}")
            
            # YouTube Data API 호출
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                'part': 'snippet',
                'q': search_query,
                'type': 'video',
                'maxResults': 5,  # 여러 결과를 받아서 필터링
                'key': youtube_api_key,
                'order': 'relevance'  # 관련성 순으로 정렬
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()  # HTTP 에러 체크
            
            data = response.json()

            if 'items' in data and data['items']:
                # 관련성 높은 비디오 찾기
                for item in data['items']:
                    video_id = item['id']['videoId']
                    video_title = item['snippet']['title'].lower()
                    video_description = item['snippet']['description'].lower()
                    
                    # 아티스트명이나 곡명이 제목 또는 설명에 포함되어 있는지 확인
                    if (song_title.lower() in video_title or 
                        artist.lower() in video_title or
                        song_title.lower() in video_description or
                        artist.lower() in video_description):
                        
                        youtube_url = f"https://www.youtube.com/watch?v={video_id}"
                        print(f"YouTube 링크 찾음: {youtube_url}")
                        return youtube_url

                # 필터링된 결과가 없으면 첫 번째 결과 사용
                first_video_id = data['items'][0]['id']['videoId']
                youtube_url = f"https://www.youtube.com/watch?v={first_video_id}"
                print(f"기본 결과 사용: {youtube_url}")
                return youtube_url
            
            else:
                print(f"'{search_query}' 검색 결과가 없습니다. 다음 검색어 시도...")
                continue
        
        # 모든 검색어가 실패한 경우
        print("모든 검색어로 시도했지만 결과를 찾을 수 없습니다.")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"네트워크 오류: {e}")
        return None
    except requests.exceptions.Timeout:
        print("YouTube API 응답 시간 초과")
        return None
    except KeyError as e:
        print(f"API 응답 파싱 오류: {e}")
        return None
    except Exception as e:
        print(f"YouTube 검색 중 예기치 못한 오류: {e}")
        return None

def get_youtube_thumbnail(song_title: str, artist: str) -> str:
    """
    YouTube에서 음악 비디오의 썸네일 이미지 URL 반환
    
    Args:
        song_title: 노래 제목
        artist: 아티스트명
    
    Returns:
        썸네일 URL 또는 None
    """
    try:
        youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        if not youtube_api_key:
            return None
        
        search_query = f"{artist} {song_title} official mv"
        
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': search_query,
            'type': 'video',
            'maxResults': 1,
            'key': youtube_api_key,
            'order': 'relevance'
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if 'items' in data and data['items']:
            thumbnail_url = data['items'][0]['snippet']['thumbnails']['high']['url']
            return thumbnail_url
        
        return None
        
    except Exception as e:
        print(f"썸네일 검색 오류: {e}")
        return None

if __name__ == "__main__":
    # 테스트
    test_cases = [
        ("좋은 날", "아이유"),
        ("Spring Day", "BTS"),
        ("LILAC", "아이유"),
        ("에잇", "아이유"),
        ("Dynamite", "BTS")
    ]
    
    print("=== YouTube 링크 검색 테스트 ===")
    for title, artist in test_cases:
        print(f"\n🎵 테스트: {artist} - {title}")
        
        # 링크 검색
        link = get_youtube_link(title, artist)
        print(f"링크: {link}")
        
        # 썸네일 검색
        thumbnail = get_youtube_thumbnail(title, artist)
        print(f"썸네일: {thumbnail}")
        
        print("-" * 50)

    pass