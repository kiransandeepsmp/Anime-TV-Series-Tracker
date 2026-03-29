from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import os
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

# Use absolute path for database to ensure consistency
import os
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db_path = os.path.join(project_root, 'anime_tracker.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print(f"📁 Using database: {db_path}")

# Initialize extensions
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Template filters
@app.template_filter('nl2br')
def nl2br_filter(text):
    """Convert newlines to HTML line breaks"""
    if text is None:
        return ''
    return text.replace('\n', '<br>\n')

# Models
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    theme_preference = db.Column(db.String(10), default='light')
    is_admin = db.Column(db.Boolean, default=False)

    watchlist_items = db.relationship('Watchlist', backref='user', lazy=True, cascade='all, delete-orphan')
    discussions = db.relationship('Discussion', backref='user', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('Comment', backref='user', lazy=True, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_watchlist_stats(self):
        stats = {
            'watching': 0, 'completed': 0, 'on_hold': 0,
            'dropped': 0, 'plan_to_watch': 0, 'total': 0
        }
        for item in self.watchlist_items:
            stats[item.status] += 1
            stats['total'] += 1
        return stats

class Anime(db.Model):
    __tablename__ = 'anime'

    id = db.Column(db.Integer, primary_key=True)
    mal_id = db.Column(db.Integer, unique=True, nullable=False)  # MyAnimeList ID
    title = db.Column(db.String(200), nullable=False)
    title_english = db.Column(db.String(200))
    title_japanese = db.Column(db.String(200))
    genre = db.Column(db.String(200))
    year = db.Column(db.Integer)
    description = db.Column(db.Text)
    total_episodes = db.Column(db.Integer, default=1)
    image_url = db.Column(db.String(500))
    streaming_links = db.Column(db.Text)  # JSON string of streaming platform links

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

    watchlist_items = db.relationship('Watchlist', backref='anime', lazy=True)
    discussions = db.relationship('Discussion', backref='anime', lazy=True, cascade='all, delete-orphan')

    def get_average_rating(self):
        ratings = [item.rating for item in self.watchlist_items if item.rating]
        return sum(ratings) / len(ratings) if ratings else 0

    def get_streaming_links(self):
        """Get streaming platform links as a dictionary"""
        if self.streaming_links:
            try:
                return json.loads(self.streaming_links)
            except:
                return {}
        return {}

    def set_streaming_links(self, links_dict):
        """Set streaming platform links from a dictionary"""
        self.streaming_links = json.dumps(links_dict) if links_dict else None

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
    def __init__(self, **kwargs):
        if not kwargs.get('mal_id'):
            raise ValueError("Anime must have a MAL ID (API-sourced only)")
        super().__init__(**kwargs)


class Watchlist(db.Model):
    __tablename__ = 'watchlist'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)
    episodes_watched = db.Column(db.Integer, default=0)
    rating = db.Column(db.Integer)
    review = db.Column(db.Text)
    started_date = db.Column(db.Date)
    completed_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('user_id', 'anime_id', name='unique_user_anime'),)

    def get_progress_percentage(self):
        if self.anime.total_episodes == 0:
            return 0
        return min(100, (self.episodes_watched / self.anime.total_episodes) * 100)

class Discussion(db.Model):
    __tablename__ = 'discussions'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    anime_id = db.Column(db.Integer, db.ForeignKey('anime.id'), nullable=False)
    is_spoiler = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    comments = db.relationship('Comment', backref='discussion', lazy=True, cascade='all, delete-orphan')

    def get_comment_count(self):
        return len(self.comments)

class Comment(db.Model):
    __tablename__ = 'comments'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    discussion_id = db.Column(db.Integer, db.ForeignKey('discussions.id'), nullable=False)
    is_spoiler = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Register API Blueprint
try:
    from backend.routes.api_integration import api_bp
    app.register_blueprint(api_bp)
    print("✅ API Blueprint registered successfully")
except ImportError as e:
    print(f"Warning: Could not import API blueprint: {e}")


# API-Only Validation
def validate_api_anime(anime_data):
    """Validate that anime data comes from API and has required fields"""
    required_fields = ['mal_id', 'title']
    
    for field in required_fields:
        if not anime_data.get(field):
            raise ValueError(f"API anime must have {field}")
    
    if not isinstance(anime_data['mal_id'], int) or anime_data['mal_id'] <= 0:
        raise ValueError("Invalid MAL ID - anime must come from MyAnimeList API")
    
    return True

def create_api_anime_only(anime_data):
    """Create anime entry only from API data"""
    validate_api_anime(anime_data)
    
    # Check if already exists
    existing = Anime.query.filter_by(mal_id=anime_data['mal_id']).first()
    if existing:
        return existing
    
    # Create new anime with API data
    anime = Anime(
        mal_id=anime_data['mal_id'],
        title=anime_data['title'],
        title_english=anime_data.get('title_english'),
        title_japanese=anime_data.get('title_japanese'),
        genre=anime_data.get('genre'),
        year=anime_data.get('year'),
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
    
    db.session.add(anime)
    db.session.commit()
    return anime


# Routes
@app.route('/favicon.ico')
def favicon():
    return '', 204  # No content response for favicon

@app.route('/')
def index():
    featured_anime = Anime.query.limit(6).all()
    return render_template('index.html', featured_anime=featured_anime)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if not username or not email or not password:
            flash('All fields are required!', 'error')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match!', 'error')
            return render_template('auth/register.html')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'error')
            return render_template('auth/register.html')

        user = User(username=username, email=email)
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Registration failed. Please try again.', 'error')

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'error')

    return render_template('auth/login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    stats = current_user.get_watchlist_stats()
    recent_items = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.updated_at.desc()).limit(5).all()
    currently_watching = Watchlist.query.filter_by(user_id=current_user.id, status='watching').all()

    return render_template('dashboard.html', stats=stats, recent_items=recent_items, currently_watching=currently_watching)

@app.route('/add_to_watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    anime_id = request.form.get('anime_id', type=int)
    status = request.form.get('status', 'plan_to_watch')

    if not anime_id:
        flash('Invalid anime selection!', 'error')
        return redirect(request.referrer or url_for('index'))

    anime = Anime.query.get(anime_id)
    if not anime:
        flash('Anime not found!', 'error')
        return redirect(request.referrer or url_for('index'))

    existing_item = Watchlist.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()
    if existing_item:
        flash(f'{anime.title} is already in your watchlist!', 'warning')
        return redirect(request.referrer or url_for('index'))

    watchlist_item = Watchlist(
        user_id=current_user.id,
        anime_id=anime_id,
        status=status,
        started_date=date.today() if status == 'watching' else None
    )

    try:
        db.session.add(watchlist_item)
        db.session.commit()
        flash(f'{anime.title} added to your watchlist!', 'success')
    except:
        db.session.rollback()
        flash('Failed to add to watchlist. Please try again.', 'error')

    return redirect(request.referrer or url_for('index'))

@app.route('/watchlist')
@login_required
def view_watchlist():
    status_filter = request.args.get('status', 'all')

    query = Watchlist.query.filter_by(user_id=current_user.id)

    if status_filter != 'all':
        query = query.filter_by(status=status_filter)

    watchlist_items = query.order_by(Watchlist.updated_at.desc()).all()
    stats = current_user.get_watchlist_stats()

    return render_template('watchlist.html',
                         watchlist_items=watchlist_items,
                         stats=stats,
                         current_status=status_filter)

@app.route('/browse')
def browse():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    genre_filter = request.args.get('genre', '')
    year_filter = request.args.get('year', type=int)
    sort_by = request.args.get('sort', 'title')

    query = Anime.query

    # Apply filters
    if search:
        query = query.filter(Anime.title.contains(search))

    if genre_filter:
        query = query.filter(Anime.genre.contains(genre_filter))

    if year_filter:
        query = query.filter(Anime.year == year_filter)

    # Apply sorting
    if sort_by == 'year':
        query = query.order_by(Anime.year.desc())
    elif sort_by == 'rating':
        # For now, sort by title as we'd need a complex query for average rating
        query = query.order_by(Anime.title)
    else:  # default to title
        query = query.order_by(Anime.title)

    per_page = 12
    anime_list = query.paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Get unique genres and years for filter dropdowns
    genres = db.session.query(Anime.genre).distinct().filter(Anime.genre.isnot(None)).all()
    genres = [g[0] for g in genres if g[0]]
    all_genres = set()
    for genre_string in genres:
        all_genres.update([g.strip() for g in genre_string.split(',')])

    years = db.session.query(Anime.year).distinct().filter(Anime.year.isnot(None)).order_by(Anime.year.desc()).all()
    years = [y[0] for y in years if y[0]]

    return render_template('browse.html',
                         anime_list=anime_list,
                         current_search=search,
                         current_genre=genre_filter,
                         current_year=year_filter,
                         current_sort=sort_by,
                         available_genres=sorted(all_genres),
                         available_years=years)

@app.route('/anime/<int:anime_id>')
def anime_detail(anime_id):
    """Anime detail page"""
    anime = Anime.query.get_or_404(anime_id)

    # Get user's watchlist item if logged in
    user_item = None
    if current_user.is_authenticated:
        user_item = Watchlist.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()

    # Get average rating and total users
    average_rating = anime.get_average_rating()
    total_users = len(anime.watchlist_items)

    return render_template('anime_detail.html',
                         anime=anime,
                         user_item=user_item,
                         average_rating=average_rating,
                         total_users=total_users)

@app.route('/update_watchlist_item/<int:item_id>', methods=['POST'])
@login_required
def update_watchlist_item(item_id):
    item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        flash('Watchlist item not found!', 'error')
        return redirect(url_for('view_watchlist'))

    # Update status
    new_status = request.form.get('status')
    if new_status and new_status in ['watching', 'completed', 'on_hold', 'dropped', 'plan_to_watch']:
        item.status = new_status
        if new_status == 'watching' and not item.started_date:
            item.started_date = date.today()
        elif new_status == 'completed':
            item.completed_date = date.today()
            item.episodes_watched = item.anime.total_episodes

    # Update episodes watched
    episodes_watched = request.form.get('episodes_watched', type=int)
    if episodes_watched is not None and episodes_watched >= 0:
        item.episodes_watched = min(episodes_watched, item.anime.total_episodes)
        if item.episodes_watched == item.anime.total_episodes and item.status != 'completed':
            item.status = 'completed'
            item.completed_date = date.today()

    # Update rating
    rating = request.form.get('rating', type=int)
    if rating is not None and 1 <= rating <= 10:
        item.rating = rating

    # Update review
    review = request.form.get('review', '').strip()
    if review:
        item.review = review

    try:
        db.session.commit()
        flash(f'Updated {item.anime.title} successfully!', 'success')
    except:
        db.session.rollback()
        flash('Failed to update. Please try again.', 'error')

    return redirect(url_for('view_watchlist'))

@app.route('/remove_from_watchlist/<int:item_id>', methods=['POST'])
@login_required
def remove_from_watchlist(item_id):
    item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        flash('Watchlist item not found!', 'error')
        return redirect(url_for('view_watchlist'))

    anime_title = item.anime.title
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'Removed {anime_title} from your watchlist!', 'info')
    except:
        db.session.rollback()
        flash('Failed to remove item. Please try again.', 'error')

    return redirect(url_for('view_watchlist'))

@app.route('/profile')
@login_required
def profile():
    stats = current_user.get_watchlist_stats()

    # Get detailed statistics
    completed_items = Watchlist.query.filter_by(user_id=current_user.id, status='completed').all()
    rated_items = Watchlist.query.filter_by(user_id=current_user.id).filter(Watchlist.rating.isnot(None)).all()

    # Calculate additional stats
    total_episodes = sum(item.episodes_watched for item in current_user.watchlist_items)
    avg_rating = sum(item.rating for item in rated_items) / len(rated_items) if rated_items else 0

    # Get recent activity
    recent_updates = Watchlist.query.filter_by(user_id=current_user.id).order_by(Watchlist.updated_at.desc()).limit(10).all()

    # Get favorite genres (from completed/rated anime)
    genre_counts = {}
    for item in completed_items + rated_items:
        if item.anime.genre:
            genres = [g.strip() for g in item.anime.genre.split(',')]
            for genre in genres:
                genre_counts[genre] = genre_counts.get(genre, 0) + 1

    favorite_genres = sorted(genre_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    return render_template('profile.html',
                         stats=stats,
                         total_episodes=total_episodes,
                         avg_rating=round(avg_rating, 1),
                         recent_updates=recent_updates,
                         favorite_genres=favorite_genres,
                         completed_count=len(completed_items),
                         rated_count=len(rated_items))

@app.route('/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    current_theme = current_user.theme_preference
    new_theme = 'dark' if current_theme == 'light' else 'light'

    current_user.theme_preference = new_theme
    db.session.commit()

    return jsonify({'theme': new_theme})

# Discussion Routes
@app.route('/anime/<int:anime_id>/discussions')
def anime_discussions(anime_id):
    anime = Anime.query.get_or_404(anime_id)
    page = request.args.get('page', 1, type=int)

    discussions = Discussion.query.filter_by(anime_id=anime_id)\
                                .order_by(Discussion.created_at.desc())\
                                .paginate(page=page, per_page=10, error_out=False)

    return render_template('discussions.html', anime=anime, discussions=discussions)

@app.route('/anime/<int:anime_id>/discussions/new', methods=['GET', 'POST'])
@login_required
def create_discussion(anime_id):
    anime = Anime.query.get_or_404(anime_id)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        is_spoiler = bool(request.form.get('is_spoiler'))

        if not title or not content:
            flash('Title and content are required!', 'error')
            return render_template('create_discussion.html', anime=anime)

        discussion = Discussion(
            title=title,
            content=content,
            user_id=current_user.id,
            anime_id=anime_id,
            is_spoiler=is_spoiler
        )

        try:
            db.session.add(discussion)
            db.session.commit()
            flash('Discussion created successfully!', 'success')
            return redirect(url_for('view_discussion', discussion_id=discussion.id))
        except:
            db.session.rollback()
            flash('Failed to create discussion. Please try again.', 'error')

    return render_template('create_discussion.html', anime=anime)

@app.route('/discussion/<int:discussion_id>')
def view_discussion(discussion_id):
    discussion = Discussion.query.get_or_404(discussion_id)
    page = request.args.get('page', 1, type=int)

    comments = Comment.query.filter_by(discussion_id=discussion_id)\
                           .order_by(Comment.created_at.asc())\
                           .paginate(page=page, per_page=20, error_out=False)

    return render_template('view_discussion.html', discussion=discussion, comments=comments)

@app.route('/discussion/<int:discussion_id>/comment', methods=['POST'])
@login_required
def add_comment(discussion_id):
    discussion = Discussion.query.get_or_404(discussion_id)
    content = request.form.get('content', '').strip()
    is_spoiler = bool(request.form.get('is_spoiler'))

    if not content:
        flash('Comment content is required!', 'error')
        return redirect(url_for('view_discussion', discussion_id=discussion_id))

    comment = Comment(
        content=content,
        user_id=current_user.id,
        discussion_id=discussion_id,
        is_spoiler=is_spoiler
    )

    try:
        db.session.add(comment)
        db.session.commit()
        flash('Comment added successfully!', 'success')
    except:
        db.session.rollback()
        flash('Failed to add comment. Please try again.', 'error')

    return redirect(url_for('view_discussion', discussion_id=discussion_id))

@app.route('/discussions')
def all_discussions():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    anime_filter = request.args.get('anime', type=int)

    query = Discussion.query

    if search:
        query = query.filter(Discussion.title.contains(search))

    if anime_filter:
        query = query.filter_by(anime_id=anime_filter)

    discussions = query.order_by(Discussion.created_at.desc())\
                      .paginate(page=page, per_page=15, error_out=False)

    # Get anime list for filter dropdown
    anime_list = Anime.query.order_by(Anime.title).all()

    return render_template('all_discussions.html',
                         discussions=discussions,
                         anime_list=anime_list,
                         current_search=search,
                         current_anime=anime_filter)

# Recommendation Routes
@app.route('/recommendations')
@login_required
def recommendations():
    # Get user's ratings and preferences
    user_ratings = Watchlist.query.filter_by(user_id=current_user.id)\
                                 .filter(Watchlist.rating.isnot(None))\
                                 .all()

    if not user_ratings:
        # If no ratings, show popular anime
        popular_anime = Anime.query.join(Watchlist)\
                                  .group_by(Anime.id)\
                                  .order_by(db.func.count(Watchlist.id).desc())\
                                  .limit(12).all()
        return render_template('recommendations.html',
                             recommendations=popular_anime,
                             recommendation_type='popular',
                             message='Start rating anime to get personalized recommendations!')

    # Get recommendations based on user preferences
    recommendations = get_user_recommendations(current_user.id)

    return render_template('recommendations.html',
                         recommendations=recommendations,
                         recommendation_type='personalized')

def get_user_recommendations(user_id, limit=12):
    """Generate personalized recommendations for a user"""
    # Get user's highly rated anime (rating >= 7)
    liked_anime = Watchlist.query.filter_by(user_id=user_id)\
                                .filter(Watchlist.rating >= 7)\
                                .all()

    if not liked_anime:
        return []

    # Extract preferred genres
    genre_scores = {}
    for item in liked_anime:
        if item.anime.genre:
            genres = [g.strip() for g in item.anime.genre.split(',')]
            for genre in genres:
                genre_scores[genre] = genre_scores.get(genre, 0) + item.rating

    # Get anime user hasn't watched
    watched_anime_ids = [item.anime_id for item in
                        Watchlist.query.filter_by(user_id=user_id).all()]

    # Find similar anime based on genres and ratings
    recommendations = []
    candidate_anime = Anime.query.filter(~Anime.id.in_(watched_anime_ids)).all()

    for anime in candidate_anime:
        if anime.genre:
            score = 0
            genres = [g.strip() for g in anime.genre.split(',')]
            for genre in genres:
                if genre in genre_scores:
                    score += genre_scores[genre]

            # Add popularity bonus
            popularity = len(anime.watchlist_items)
            avg_rating = anime.get_average_rating()

            final_score = score + (popularity * 0.1) + (avg_rating * 0.5)

            if final_score > 0:
                recommendations.append((anime, final_score))

    # Sort by score and return top recommendations
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [anime for anime, score in recommendations[:limit]]

# Admin Routes
def admin_required(f):
    """Decorator to require admin access"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('Admin access required!', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    # Get statistics
    total_users = User.query.count()
    total_anime = Anime.query.count()
    total_discussions = Discussion.query.count()
    total_watchlist_items = Watchlist.query.count()

    # Recent activity
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_discussions = Discussion.query.order_by(Discussion.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_anime=total_anime,
                         total_discussions=total_discussions,
                         total_watchlist_items=total_watchlist_items,
                         recent_users=recent_users,
                         recent_discussions=recent_discussions)

@app.route('/admin/users')
@login_required
@admin_required
def admin_users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = User.query
    if search:
        query = query.filter(User.username.contains(search))

    users = query.order_by(User.created_at.desc())\
                 .paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/users.html', users=users, current_search=search)

@app.route('/admin/anime')
@login_required
@admin_required
def admin_anime():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')

    query = Anime.query
    if search:
        query = query.filter(Anime.title.contains(search))

    anime_list = query.order_by(Anime.created_at.desc())\
                     .paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/anime.html', anime_list=anime_list, current_search=search)

# DISABLED API-ONLY: Manual anime addition route
# @app.route('/admin/anime/add', methods=['GET', 'POST'])
# @login_required
# @admin_required
def admin_add_anime_disabled():
    """Disabled - Use API search instead"""
    flash('Manual anime addition is disabled. Use API search instead.', 'info')
    return redirect(url_for('api.search_and_add'))

# Original function disabled for API-only mode - use API search instead

@app.route('/admin/anime/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_anime():
    """Redirect to API search - manual addition disabled"""
    flash('Manual anime addition is disabled. Use API search to add anime from MyAnimeList.', 'info')
    return redirect(url_for('api.search_and_add'))

@app.route('/admin/discussions')
@login_required
@admin_required
def admin_discussions():
    page = request.args.get('page', 1, type=int)

    discussions = Discussion.query.order_by(Discussion.created_at.desc())\
                                 .paginate(page=page, per_page=20, error_out=False)

    return render_template('admin/discussions.html', discussions=discussions)


@app.route('/test-api')
@login_required
def test_api():
    """Test route for API functionality"""
    from backend.services.anime_api import anime_api_service
    
    try:
        # Test search
        search_results = anime_api_service.search_anime("Naruto", limit=3)
        
        # Test popular
        popular_results = anime_api_service.get_popular_anime(limit=3)
        
        # Test seasonal
        seasonal_results = anime_api_service.get_seasonal_anime()
        
        return jsonify({
            'success': True,
            'search_count': len(search_results),
            'popular_count': len(popular_results),
            'seasonal_count': len(seasonal_results),
            'sample_search': search_results[0] if search_results else None,
            'sample_popular': popular_results[0] if popular_results else None,
            'sample_seasonal': seasonal_results[0] if seasonal_results else None
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':

    with app.app_context():
        # Create database tables
        db.create_all()

        # Make first user admin if no admin exists
        if not User.query.filter_by(is_admin=True).first():
            first_user = User.query.first()
            if first_user:
                first_user.is_admin = True
                db.session.commit()
                print(f"Made {first_user.username} an admin!")

        # Database is now API-only - no sample data needed
        # All anime come from MyAnimeList API

    app.run(debug=True, host='0.0.0.0', port=5000)
