from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# db will be injected when the module is imported
db = None

class Anime(db.Model):
    __tablename__ = 'anime'

    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, unique=True)  # MyAnimeList ID
    title = db.Column(db.String(200), nullable=False)
    title_english = db.Column(db.String(200))
    title_japanese = db.Column(db.String(200))
    genre = db.Column(db.String(200))
    year = db.Column(db.Integer)
    description = db.Column(db.Text)
    total_episodes = db.Column(db.Integer, default=1)
    image_url = db.Column(db.String(500))
    streaming_links = db.Column(db.Text)  # JSON string of streaming platforms

    # Additional API fields
    score = db.Column(db.Float)  # MyAnimeList score
    scored_by = db.Column(db.Integer)  # Number of users who scored
    rank = db.Column(db.Integer)  # MyAnimeList rank
    popularity = db.Column(db.Integer)  # MyAnimeList popularity rank
    status = db.Column(db.String(50))  # Airing status
    type = db.Column(db.String(20))  # TV, Movie, OVA, etc.
    source = db.Column(db.String(50))  # Manga, Light novel, etc.
    duration = db.Column(db.String(50))  # Episode duration
    rating = db.Column(db.String(20))  # Age rating
    season = db.Column(db.String(20))  # Season aired

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    watchlist_items = db.relationship('Watchlist', backref='anime', lazy=True)
    
    def get_average_rating(self):
        """Calculate average rating from watchlist items"""
        ratings = [item.rating for item in self.watchlist_items if item.rating]
        return sum(ratings) / len(ratings) if ratings else 0

    def get_streaming_links(self):
        """Parse streaming links from JSON string"""
        if not self.streaming_links:
            return {}
        try:
            import json
            return json.loads(self.streaming_links)
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_streaming_links(self, links_dict):
        """Set streaming links as JSON string"""
        if links_dict:
            import json
            self.streaming_links = json.dumps(links_dict)
        else:
            self.streaming_links = None

    def get_display_title(self):
        """Get the best available title for display"""
        return self.title_english or self.title

    def get_all_titles(self):
        """Get all available titles as a list"""
        titles = [self.title]
        if self.title_english and self.title_english != self.title:
            titles.append(self.title_english)
        if self.title_japanese and self.title_japanese not in titles:
            titles.append(self.title_japanese)
        return titles

    def __repr__(self):
        return f'<Anime {self.title}>'

class Watchlist(db.Model):
    __tablename__ = 'watchlist'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # watching, completed, on_hold, dropped, plan_to_watch
    episodes_watched = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer)  # 1-10 rating
    review = db.Column(db.Text)
    started_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint to prevent duplicate entries
    __table_args__ = (db.UniqueConstraint('user_id', 'anime_id', name='unique_user_anime'),)
    
    def get_progress_percentage(self):
        """Calculate watch progress as percentage"""
        if self.anime.total_episodes == 0:
            return 0
        return min(100, (self.episodes_watched / self.anime.total_episodes) * 100)
    
    def __repr__(self):
        return f'<Watchlist User:{self.user_id} Anime:{self.anime_id} Status:{self.status}>'
