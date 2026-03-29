"""
Anime API Service - Integration with external anime databases
Supports Jikan API (MyAnimeList) and AniList API
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JikanAPI:
    """
    Jikan API client for fetching anime data from MyAnimeList
    Documentation: https://docs.api.jikan.moe/
    """
    
    BASE_URL = "https://api.jikan.moe/v4"
    RATE_LIMIT_DELAY = 1  # 1 second between requests to respect rate limits
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AnimeTracker/1.0 (https://github.com/your-repo)'
        })
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Implement rate limiting to respect API limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a request to the Jikan API with error handling"""
        self._rate_limit()
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched data from {endpoint}")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed for {endpoint}: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            return None
    
    def search_anime(self, query: str, limit: int = 10) -> List[Dict]:
        """
        Search for anime by title

        Args:
            query: Search query string
            limit: Maximum number of results (default: 10, max: 25)

        Returns:
            List of anime dictionaries with standardized format
        """
        params = {
            'q': query,
            'limit': min(limit, 25),  # API max is 25
        }

        data = self._make_request('anime', params)
        if not data or 'data' not in data:
            return []

        return [self._format_anime_data(anime) for anime in data['data']]
    
    def get_anime_by_id(self, anime_id: int) -> Optional[Dict]:
        """
        Get detailed anime information by MyAnimeList ID
        
        Args:
            anime_id: MyAnimeList anime ID
            
        Returns:
            Formatted anime dictionary or None if not found
        """
        data = self._make_request(f'anime/{anime_id}')
        if not data or 'data' not in data:
            return None
        
        return self._format_anime_data(data['data'])
    
    def get_top_anime(self, limit: int = 25, type_filter: str = None) -> List[Dict]:
        """
        Get top anime from MyAnimeList
        
        Args:
            limit: Number of results (max: 25)
            type_filter: Filter by type (tv, movie, ova, special, ona, music)
            
        Returns:
            List of formatted anime dictionaries
        """
        params = {
            'limit': min(limit, 25)
        }
        if type_filter:
            params['type'] = type_filter
        
        data = self._make_request('top/anime', params)
        if not data or 'data' not in data:
            return []
        
        return [self._format_anime_data(anime) for anime in data['data']]
    
    def get_seasonal_anime(self, year: int = None, season: str = None) -> List[Dict]:
        """
        Get seasonal anime
        
        Args:
            year: Year (default: current year)
            season: Season (winter, spring, summer, fall)
            
        Returns:
            List of formatted anime dictionaries
        """
        if not year:
            year = datetime.now().year
        if not season:
            # Determine current season
            month = datetime.now().month
            if month in [12, 1, 2]:
                season = 'winter'
            elif month in [3, 4, 5]:
                season = 'spring'
            elif month in [6, 7, 8]:
                season = 'summer'
            else:
                season = 'fall'
        
        data = self._make_request(f'seasons/{year}/{season}')
        if not data or 'data' not in data:
            return []
        
        return [self._format_anime_data(anime) for anime in data['data'][:25]]  # Limit results
    
    def _format_anime_data(self, raw_data: Dict) -> Dict:
        """
        Format raw Jikan API data to match our database schema
        
        Args:
            raw_data: Raw anime data from Jikan API
            
        Returns:
            Formatted anime dictionary
        """
        # Extract genres
        genres = []
        if 'genres' in raw_data and raw_data['genres']:
            genres.extend([genre['name'] for genre in raw_data['genres']])
        if 'themes' in raw_data and raw_data['themes']:
            genres.extend([theme['name'] for theme in raw_data['themes']])
        
        # Get the best available image
        image_url = None
        if 'images' in raw_data and 'jpg' in raw_data['images']:
            image_url = raw_data['images']['jpg'].get('large_image_url') or \
                       raw_data['images']['jpg'].get('image_url')
        
        # Format streaming links (if available)
        streaming_links = {}
        if 'streaming' in raw_data and raw_data['streaming']:
            for stream in raw_data['streaming']:
                if 'name' in stream and 'url' in stream:
                    streaming_links[stream['name']] = stream['url']
        
        return {
            'mal_id': raw_data.get('mal_id'),
            'title': raw_data.get('title', 'Unknown Title'),
            'title_english': raw_data.get('title_english'),
            'title_japanese': raw_data.get('title_japanese'),
            'genre': ', '.join(genres) if genres else None,
            'year': raw_data.get('year') or (raw_data.get('aired', {}).get('from', '')[:4] if raw_data.get('aired', {}).get('from') else None),
            'description': raw_data.get('synopsis', '').replace('[Written by MAL Rewrite]', '').strip(),
            'total_episodes': raw_data.get('episodes') or 1,
            'image_url': image_url,
            'streaming_links': json.dumps(streaming_links) if streaming_links else None,
            'score': raw_data.get('score'),
            'scored_by': raw_data.get('scored_by'),
            'rank': raw_data.get('rank'),
            'popularity': raw_data.get('popularity'),
            'status': raw_data.get('status'),
            'type': raw_data.get('type'),
            'source': raw_data.get('source'),
            'duration': raw_data.get('duration'),
            'rating': raw_data.get('rating'),
            'season': raw_data.get('season'),
            'studios': [studio['name'] for studio in raw_data.get('studios', [])],
            'producers': [producer['name'] for producer in raw_data.get('producers', [])],
            'licensors': [licensor['name'] for licensor in raw_data.get('licensors', [])],
        }

class AnimeAPIService:
    """
    Main service class for anime API operations
    Handles multiple API sources and provides unified interface
    """
    
    def __init__(self):
        self.jikan = JikanAPI()
    
    def search_anime(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for anime across all available APIs"""
        return self.jikan.search_anime(query, limit)
    
    def get_anime_details(self, mal_id: int) -> Optional[Dict]:
        """Get detailed anime information by MyAnimeList ID"""
        return self.jikan.get_anime_by_id(mal_id)
    
    def get_popular_anime(self, limit: int = 25) -> List[Dict]:
        """Get popular anime from MyAnimeList"""
        return self.jikan.get_top_anime(limit)
    
    def get_seasonal_anime(self, year: int = None, season: str = None) -> List[Dict]:
        """Get current or specified seasonal anime"""
        return self.jikan.get_seasonal_anime(year, season)
    
    def import_anime_to_db(self, anime_data: Dict, db_session=None) -> Optional[Any]:
        """
        Import anime data to database

        Args:
            anime_data: Formatted anime data dictionary
            db_session: Database session (optional, will use app context if not provided)

        Returns:
            Created Anime object or None if failed
        """
        try:
            # Import Anime model and db inside the function to avoid circular imports
            from app import Anime, db

            # Use provided session or default to app db session
            if db_session is None:
                db_session = db.session

            # Check if anime already exists by MAL ID or title
            existing_anime = None
            if anime_data.get('mal_id'):
                existing_anime = Anime.query.filter_by(mal_id=anime_data['mal_id']).first()

            if not existing_anime:
                existing_anime = Anime.query.filter_by(title=anime_data['title']).first()

            if existing_anime:
                logger.info(f"Anime '{anime_data['title']}' already exists in database")
                return existing_anime

            # Create new anime entry
            anime = Anime(
                mal_id=anime_data.get('mal_id'),
                title=anime_data['title'],
                title_english=anime_data.get('title_english'),
                title_japanese=anime_data.get('title_japanese'),
                genre=anime_data.get('genre'),
                year=int(anime_data['year']) if anime_data.get('year') else None,
                description=anime_data.get('description'),
                total_episodes=anime_data.get('total_episodes', 1),
                image_url=anime_data.get('image_url'),
                streaming_links=anime_data.get('streaming_links'),
                score=anime_data.get('score'),
                scored_by=anime_data.get('scored_by'),
                rank=anime_data.get('rank'),
                popularity=anime_data.get('popularity'),
                status=anime_data.get('status'),
                type=anime_data.get('type'),
                source=anime_data.get('source'),
                duration=anime_data.get('duration'),
                rating=anime_data.get('rating'),
                season=anime_data.get('season')
            )

            db_session.add(anime)
            db_session.commit()

            logger.info(f"Successfully imported anime: {anime_data['title']}")
            return anime

        except Exception as e:
            db_session.rollback()
            logger.error(f"Failed to import anime '{anime_data.get('title', 'Unknown')}': {str(e)}")
            return None

# Global service instance
anime_api_service = AnimeAPIService()
