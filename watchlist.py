from flask import Blueprint, request, redirect, url_for, flash, jsonify, render_template
from flask_login import login_required, current_user
from datetime import datetime, date
from anime_tracker.app import db
from anime_tracker.backend.models.anime import Anime, Watchlist

watchlist_bp = Blueprint('watchlist', __name__)

@watchlist_bp.route('/watchlist')
@login_required
def view_watchlist():
    """View user's watchlist"""
    status_filter = request.args.get('status', 'all')
    
    query = Watchlist.query.filter_by(user_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    watchlist_items = query.order_by(Watchlist.updated_at.desc()).all()
    
    # Get statistics
    stats = current_user.get_watchlist_stats()
    
    return render_template('watchlist.html', 
                         watchlist_items=watchlist_items,
                         stats=stats,
                         current_status=status_filter)

@watchlist_bp.route('/add_to_watchlist', methods=['POST'])
@login_required
def add_to_watchlist():
    """Add anime to user's watchlist"""
    anime_id = request.form.get('anime_id', type=int)
    status = request.form.get('status', 'plan_to_watch')
    
    if not anime_id:
        flash('Invalid anime selection!', 'error')
        return redirect(request.referrer or url_for('main.browse'))
    
    # Check if anime exists
    anime = Anime.query.get(anime_id)
    if not anime:
        flash('Anime not found!', 'error')
        return redirect(request.referrer or url_for('main.browse'))
    
    # Check if already in watchlist
    existing_item = Watchlist.query.filter_by(user_id=current_user.id, anime_id=anime_id).first()
    if existing_item:
        flash(f'{anime.title} is already in your watchlist!', 'warning')
        return redirect(request.referrer or url_for('main.anime_detail', anime_id=anime_id))
    
    # Create new watchlist item
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
    except Exception as e:
        db.session.rollback()
        flash('Failed to add to watchlist. Please try again.', 'error')
    
    return redirect(request.referrer or url_for('main.anime_detail', anime_id=anime_id))

@watchlist_bp.route('/update_watchlist', methods=['POST'])
@login_required
def update_watchlist():
    """Update watchlist item"""
    item_id = request.form.get('item_id', type=int)
    status = request.form.get('status')
    episodes_watched = request.form.get('episodes_watched', type=int)
    rating = request.form.get('rating', type=int)
    review = request.form.get('review', '')
    
    if not item_id:
        return jsonify({'success': False, 'message': 'Invalid item ID'})
    
    # Get watchlist item
    item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        return jsonify({'success': False, 'message': 'Watchlist item not found'})
    
    # Update fields
    if status:
        old_status = item.status
        item.status = status
        
        # Set dates based on status change
        if status == 'watching' and old_status != 'watching':
            item.started_date = date.today()
        elif status == 'completed' and old_status != 'completed':
            item.completed_date = date.today()
            item.episodes_watched = item.anime.total_episodes
    
    if episodes_watched is not None:
        item.episodes_watched = min(episodes_watched, item.anime.total_episodes)
        
        # Auto-complete if all episodes watched
        if item.episodes_watched == item.anime.total_episodes and item.status != 'completed':
            item.status = 'completed'
            item.completed_date = date.today()
    
    if rating is not None and 1 <= rating <= 10:
        item.rating = rating
    
    if review:
        item.review = review
    
    item.updated_at = datetime.utcnow()
    
    try:
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': 'Watchlist updated successfully!',
            'progress': item.get_progress_percentage()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': 'Failed to update watchlist'})

@watchlist_bp.route('/remove_from_watchlist', methods=['POST'])
@login_required
def remove_from_watchlist():
    """Remove anime from watchlist"""
    item_id = request.form.get('item_id', type=int)
    
    if not item_id:
        flash('Invalid item ID!', 'error')
        return redirect(request.referrer or url_for('watchlist.view_watchlist'))
    
    # Get and delete watchlist item
    item = Watchlist.query.filter_by(id=item_id, user_id=current_user.id).first()
    if not item:
        flash('Watchlist item not found!', 'error')
        return redirect(request.referrer or url_for('watchlist.view_watchlist'))
    
    anime_title = item.anime.title
    
    try:
        db.session.delete(item)
        db.session.commit()
        flash(f'{anime_title} removed from your watchlist!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Failed to remove from watchlist. Please try again.', 'error')
    
    return redirect(request.referrer or url_for('watchlist.view_watchlist'))
