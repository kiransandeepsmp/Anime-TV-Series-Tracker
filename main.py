from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from anime_tracker.app import db
from anime_tracker.backend.models.anime import Anime, Watchlist
from anime_tracker.backend.models.user import User

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Homepage"""
    # Get some featured anime for homepage
    featured_anime = Anime.query.limit(6).all()
    return render_template('index.html', featured_anime=featured_anime)

@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user's watchlist statistics
    stats = current_user.get_watchlist_stats()
    
    # Get recent watchlist items
    recent_items = Watchlist.query.filter_by(user_id=current_user.id)\
                                 .order_by(Watchlist.updated_at.desc())\
                                 .limit(5).all()
    
    # Get currently watching anime
    currently_watching = Watchlist.query.filter_by(user_id=current_user.id, status='watching')\
                                       .order_by(Watchlist.updated_at.desc()).all()
    
    return render_template('dashboard.html', 
                         stats=stats, 
                         recent_items=recent_items,
                         currently_watching=currently_watching)

@main_bp.route('/browse')
def browse():
    """Browse all anime"""
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    genre = request.args.get('genre', '')
    year = request.args.get('year', '', type=str)
    
    query = Anime.query
    
    # Apply filters
    if search:
        query = query.filter(Anime.title.contains(search))
    if genre:
        query = query.filter(Anime.genre.contains(genre))
    if year:
        query = query.filter(Anime.year == int(year))
    
    # Pagination
    per_page = 12
    anime_list = query.paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # Get unique genres and years for filters
    genres = set()
    years = set()
    for anime in Anime.query.all():
        if anime.genre:
            for g in anime.genre.split(', '):
                genres.add(g.strip())
        if anime.year:
            years.add(anime.year)
    
    return render_template('browse.html', 
                         anime_list=anime_list,
                         genres=sorted(genres),
                         years=sorted(years, reverse=True),
                         current_search=search,
                         current_genre=genre,
                         current_year=year)

@main_bp.route('/anime/<int:anime_id>')
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

@main_bp.route('/toggle_theme', methods=['POST'])
@login_required
def toggle_theme():
    """Toggle user's theme preference"""
    current_theme = current_user.theme_preference
    new_theme = 'dark' if current_theme == 'light' else 'light'
    
    current_user.theme_preference = new_theme
    db.session.commit()
    
    return jsonify({'theme': new_theme})
