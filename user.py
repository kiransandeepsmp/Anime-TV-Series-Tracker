from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# db will be injected when the module is imported
db = None

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    theme_preference = db.Column(db.String(10), default='light')  # 'light' or 'dark'
    
    # Relationships
    watchlist_items = db.relationship('Watchlist', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if provided password matches hash"""
        return check_password_hash(self.password_hash, password)
    
    def get_watchlist_stats(self):
        """Get user's watchlist statistics"""
        stats = {
            'watching': 0,
            'completed': 0,
            'on_hold': 0,
            'dropped': 0,
            'plan_to_watch': 0,
            'total': 0
        }
        
        for item in self.watchlist_items:
            stats[item.status] += 1
            stats['total'] += 1
            
        return stats
    
    def __repr__(self):
        return f'<User {self.username}>'
