from pathlib import Path
import json
import scrapy
from hanoicine.items import HanoicineItem, SessionItem, TheaterItem
import re


class RapquocgiaSpider(scrapy.Spider):
    name = "rapquocgia"
    
    # Cinema information for Trung tâm chiếu phim quốc gia
    CINEMA_NAME = "Trung tâm chiếu phim quốc gia"
    CINEMA_ADDRESS = "87 Láng Hạ, Quận Ba Đình, Tp. Hà Nội"
    CINEMA_ID = "TTCPQG"  # Theater ID for rapquocgia

    def start_requests(self):
        urls = [
            "https://chieuphimquocgia.com.vn/movies"
        ]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        filename = f"rapquocgia.html"
        Path(filename).write_bytes(response.body)
        self.log(f"Saved file {filename}")

        # First yield the theater information
        theater_item = TheaterItem()
        theater_item['name'] = self.CINEMA_NAME
        theater_item['address'] = self.CINEMA_ADDRESS
        theater_item['theaterID'] = self.CINEMA_ID
        yield theater_item

        # Extract film and session data from the response
        yield from self.extract_film_data(response)

    def extract_film_data(self, response):
        """Extract film and session data from the JSON embedded in the response"""
        try:
            content = response.text
            
            # First, extract film data using the reliable pattern
            film_pattern = r'\\"Id\\":(\d+),\\"FilmNameEn\\":\\".*?\\",\\"FilmName\\":\\"(.*?)\\",.*?\\"Category\\":\\"(.*?)\\",.*?\\"VersionCode\\":\\"(.*?)\\",.*?\\"ImageUrl\\":\\"(.*?)\\"'
            film_matches = re.findall(film_pattern, content, re.DOTALL)
            
            self.logger.info(f"Found {len(film_matches)} films")
            
            # Extract films first
            for film_id, film_name, category, version_code, image_url in film_matches:
                film_item = self.create_film_item(film_id, film_name, category, version_code, image_url)
                yield film_item
            
            # Now extract session data separately
            # Look for complete film objects with session data
            # Pattern to find the lstSession arrays and their content
            session_pattern = r'\\"Id\\":(\d+),.*?\\"FilmName\\":\\".*?\\",.*?\\"lstSession\\":\[(.*?)\]'
            session_matches = re.findall(session_pattern, content, re.DOTALL)
            
            self.logger.info(f"Found session data for {len(session_matches)} films")
            
            for film_id, sessions_json in session_matches:
                if sessions_json.strip():
                    # Extract individual sessions from the lstSession array
                    individual_sessions = self.extract_individual_sessions(sessions_json, film_id)
                    for session in individual_sessions:
                        yield session
                        
        except Exception as e:
            self.logger.error(f"Error extracting film data: {e}")
            import traceback
            traceback.print_exc()

    def extract_individual_sessions(self, sessions_json, film_id):
        """Extract individual session objects from the lstSession JSON array"""
        sessions = []
        try:
            # Pattern to match individual session objects in the array
            # Looking for: {"Id":374361,"PlanCinemaId":12028,"ProjectDate":"2025-06-03T00:00:00","ProjectTime":"2025-06-03T16:50:00","FilmId":10704,...}
            session_obj_pattern = r'\{\\"Id\\":(\d+),\\"PlanCinemaId\\":(\d+),\\"ProjectDate\\":\\"([^"]+)\\",\\"ProjectTime\\":\\"([^"]+)\\",\\"FilmId\\":(\d+)'
            
            session_matches = re.findall(session_obj_pattern, sessions_json)
            
            print(f"  Found {len(session_matches)} sessions for film {film_id}")
            
            for session_id, cinema_id, project_date, project_time, session_film_id in session_matches:
                if session_film_id == str(film_id):  # Ensure it matches the film
                    session_item = SessionItem()
                    session_item['sessionID'] = session_id
                    session_item['filmID'] = film_id
                    session_item['time'] = project_time
                    session_item['date'] = project_date.split('T')[0] if 'T' in project_date else project_date
                    session_item['language'] = ''  # Could extract from other fields if needed
                    session_item['format'] = ''  # Could extract if available
                    session_item['firstClass'] = ''
                    session_item['cinemaID'] = self.CINEMA_ID  # Use our cinema ID instead of PlanCinemaId
                    
                    print(f"    Session {session_id}: {project_time} at {self.CINEMA_NAME}")
                    sessions.append(session_item)
                    
        except Exception as e:
            self.logger.error(f"Error extracting individual sessions: {e}")
            import traceback
            traceback.print_exc()
            
        return sessions

    def create_film_item(self, film_id, film_name, category, version_code, image_url):
        """Create a film item from extracted data"""
        print(f"Film ID: {film_id}, Full Name: {film_name}")
        
        # Extract title (part before first "-") and age limit info
        if "-" in film_name:
            title = film_name.split("-", 1)[0].strip()
            age_part = film_name.split("-", 1)[1].strip()
        else:
            title = film_name.strip()
            age_part = ""
        
        # Extract age limit from the part after "-" or from parentheses
        age_limit = ""
        if age_part:
            # Look for age ratings like T18, T16, P, K, C18
            age_match = re.search(r'^([TPC]\d+|[TPKC])(?:\s|$)', age_part)
            if age_match:
                age_limit = age_match.group(1)
        
        # If no age limit found in the part after "-", try parentheses in full name
        if not age_limit:
            age_patterns = [r'\(([TPC]\d+)\)', r'\(([TPC])\)', r'\(([K])\)']
            for pattern in age_patterns:
                age_match = re.search(pattern, film_name, re.IGNORECASE)
                if age_match:
                    age_limit = age_match.group(1)
                    break
        
        # Determine movie type based on film name
        movie_type = ""
        if re.search(r'phụ đề', film_name, re.IGNORECASE):
            movie_type = "Phụ đề"
        elif re.search(r'lồng tiếng', film_name, re.IGNORECASE):
            movie_type = "Lồng tiếng"
        
        # Create comprehensive film item
        film_item = HanoicineItem()
        film_item['id'] = None  # Database auto-increment ID
        film_item['rqg_film_id'] = int(film_id)  # Rapquocgia film ID
        film_item['title'] = title
        film_item['age_limit'] = age_limit
        film_item['movie_type'] = movie_type
        film_item['format'] = version_code  # 2D, 3D, etc.
        film_item['genre'] = category  # Kinh dị, Hành động, etc.
        film_item['image_url'] = image_url.replace('\\/', '/')  #rapquocgia image url
        film_item['movie_url'] = ''  
        
        print(f"  Clean Title: {title}")
        print(f"  Age Limit: {age_limit}, Type: {movie_type}, Format: {version_code}, Genre: {category}")
        
        return film_item

    def create_film_item_from_json(self, film_data):
        """Create a film item from JSON data"""
        return self.create_film_item(
            film_data['Id'],
            film_data['FilmName'],
            film_data.get('Category', ''),
            film_data.get('VersionCode', ''),
            film_data.get('ImageUrl', '')
        )

    def create_session_item(self, session_data, film_id):
        """Create a session item from JSON session data"""
        session_item = SessionItem()
        session_item['sessionID'] = session_data.get('Id', '')
        session_item['filmID'] = film_id
        session_item['time'] = session_data.get('ProjectTime', '')
        session_item['date'] = session_data.get('ProjectDate', '').split('T')[0] if session_data.get('ProjectDate') else ''
        session_item['language'] = ''  # Could map from LanguageCode
        session_item['format'] = ''  # Could extract if available
        session_item['firstClass'] = ''
        session_item['cinemaID'] = self.CINEMA_ID  # Use our cinema ID instead of PlanCinemaId
        
        print(f"    Session ID: {session_data.get('Id')}, Time: {session_data.get('ProjectTime')} at {self.CINEMA_NAME}")
        return session_item
