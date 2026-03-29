"""
API Integration Routes - Handle external anime API operations
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
import json

api_bp = Blueprint('api', __name__)

@api_bp.route('/api/search')
@login_required
def api_search():
    """Search for anime using external APIs"""
    from backend.services.anime_api import anime_api_service

    query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)

    if not query:
        return jsonify({'error': 'Search query is required'}), 400

    try:
        results = anime_api_service.search_anime(query, min(limit, 25))
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500

@api_bp.route('/api/import/<int:mal_id>')
@login_required
def import_anime(mal_id):
    """Import anime from MyAnimeList by ID"""
    from backend.services.anime_api import anime_api_service

    try:
        # Get db and Anime from current app context
        from app import db, Anime

        # Check if anime already exists
        existing_anime = Anime.query.filter_by(mal_id=mal_id).first()
        if existing_anime:
            return jsonify({
                'success': True,
                'message': f'Anime "{existing_anime.title}" already exists in database',
                'anime_id': existing_anime.id,
                'already_exists': True
            })

        # Fetch anime data from API
        anime_data = anime_api_service.get_anime_details(mal_id)
        if not anime_data:
            return jsonify({'error': 'Anime not found or API error'}), 404

        # Import to database
        anime = anime_api_service.import_anime_to_db(anime_data, db.session)
        if not anime:
            return jsonify({'error': 'Failed to import anime to database'}), 500

        return jsonify({
            'success': True,
            'message': f'Successfully imported "{anime.title}"',
            'anime_id': anime.id,
            'anime': {
                'id': anime.id,
                'title': anime.title,
                'year': anime.year,
                'episodes': anime.total_episodes,
                'image_url': anime.image_url
            }
        })

    except Exception as e:
        return jsonify({'error': f'Import failed: {str(e)}'}), 500

@api_bp.route('/api/popular')
@login_required
def get_popular_anime():
    """Get popular anime from MyAnimeList"""
    from backend.services.anime_api import anime_api_service

    limit = request.args.get('limit', 25, type=int)

    try:
        results = anime_api_service.get_popular_anime(min(limit, 25))
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch popular anime: {str(e)}'}), 500

@api_bp.route('/api/seasonal')
@login_required
def get_seasonal_anime():
    """Get seasonal anime"""
    from backend.services.anime_api import anime_api_service

    year = request.args.get('year', type=int)
    season = request.args.get('season')

    try:
        results = anime_api_service.get_seasonal_anime(year, season)
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'season': season,
            'year': year
        })
    except Exception as e:
        return jsonify({'error': f'Failed to fetch seasonal anime: {str(e)}'}), 500

@api_bp.route('/admin/api-browser')
@login_required
def api_browser():
    """Admin page for browsing and importing anime from APIs"""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('admin/api_browser.html')

@api_bp.route('/admin/bulk-import', methods=['POST'])
@login_required
def bulk_import():
    """Bulk import anime from API results"""
    from backend.services.anime_api import anime_api_service

    if not current_user.is_admin:
        return jsonify({'error': 'Admin privileges required'}), 403

    try:
        # Get db and Anime from current app context
        from app import db, Anime

        data = request.get_json()
        mal_ids = data.get('mal_ids', [])

        if not mal_ids:
            return jsonify({'error': 'No anime IDs provided'}), 400

        results = {
            'imported': [],
            'skipped': [],
            'failed': []
        }

        for mal_id in mal_ids:
            try:
                # Check if already exists
                existing = Anime.query.filter_by(mal_id=mal_id).first()
                if existing:
                    results['skipped'].append({
                        'mal_id': mal_id,
                        'title': existing.title,
                        'reason': 'Already exists'
                    })
                    continue

                # Fetch and import
                anime_data = anime_api_service.get_anime_details(mal_id)
                if not anime_data:
                    results['failed'].append({
                        'mal_id': mal_id,
                        'reason': 'API fetch failed'
                    })
                    continue

                anime = anime_api_service.import_anime_to_db(anime_data, db.session)
                if anime:
                    results['imported'].append({
                        'mal_id': mal_id,
                        'title': anime.title,
                        'id': anime.id
                    })
                else:
                    results['failed'].append({
                        'mal_id': mal_id,
                        'title': anime_data.get('title', 'Unknown'),
                        'reason': 'Database import failed'
                    })

            except Exception as e:
                results['failed'].append({
                    'mal_id': mal_id,
                    'reason': str(e)
                })

        return jsonify({
            'success': True,
            'results': results,
            'summary': {
                'imported': len(results['imported']),
                'skipped': len(results['skipped']),
                'failed': len(results['failed'])
            }
        })

    except Exception as e:
        return jsonify({'error': f'Bulk import failed: {str(e)}'}), 500

@api_bp.route('/search-and-add')
@login_required
def search_and_add():
    """Page for searching and adding anime from APIs"""
    return render_template('search_and_add.html')

@api_bp.route('/api/anime-details/<int:mal_id>')
@login_required
def get_anime_details(mal_id):
    """Get detailed anime information from API"""
    from backend.services.anime_api import anime_api_service

    try:
        from app import Anime

        anime_data = anime_api_service.get_anime_details(mal_id)
        if not anime_data:
            return jsonify({'error': 'Anime not found'}), 404

        # Check if already in database
        existing = Anime.query.filter_by(mal_id=mal_id).first()
        anime_data['in_database'] = existing is not None
        if existing:
            anime_data['database_id'] = existing.id

        return jsonify({
            'success': True,
            'anime': anime_data
        })

    except Exception as e:
        return jsonify({'error': f'Failed to fetch anime details: {str(e)}'}), 500
