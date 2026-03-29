#!/usr/bin/env python3
"""
Script to create test user accounts for the Anime Tracker application.
This script creates various test users with different roles and preferences.
"""

import sys
import os
from datetime import datetime

# Add the anime_tracker directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'anime_tracker'))

from app import app, db, User

def create_test_users():
    """Create test user accounts with different roles and preferences."""
    
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
        test_users = [
            {
                'username': 'admin_user',
                'email': 'admin@animetracker.com',
                'password': 'admin123',
                'is_admin': True,
                'theme_preference': 'dark'
            },
            {
                'username': 'test_user1',
                'email': 'user1@test.com',
                'password': 'password123',
                'is_admin': False,
                'theme_preference': 'light'
            },
            {
                'username': 'test_user2',
                'email': 'user2@test.com',
                'password': 'password123',
                'is_admin': False,
                'theme_preference': 'dark'
            },
            {
                'username': 'anime_fan',
                'email': 'animefan@test.com',
                'password': 'otaku123',
                'is_admin': False,
                'theme_preference': 'light'
            },
            {
                'username': 'reviewer',
                'email': 'reviewer@test.com',
                'password': 'review123',
                'is_admin': False,
                'theme_preference': 'dark'
            },
            {
                'username': 'casual_watcher',
                'email': 'casual@test.com',
                'password': 'casual123',
                'is_admin': False,
                'theme_preference': 'light'
            }
        ]
        
        created_users = []
        skipped_users = []
        
        for user_data in test_users:
            # Check if user already exists
            existing_user = User.query.filter_by(username=user_data['username']).first()
            if existing_user:
                skipped_users.append(user_data['username'])
                continue
            
            # Check if email already exists
            existing_email = User.query.filter_by(email=user_data['email']).first()
            if existing_email:
                skipped_users.append(f"{user_data['username']} (email exists)")
                continue
            
            # Create new user
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                is_admin=user_data['is_admin'],
                theme_preference=user_data['theme_preference']
            )
            user.set_password(user_data['password'])
            
            try:
                db.session.add(user)
                db.session.commit()
                created_users.append(user_data['username'])
                print(f"✅ Created user: {user_data['username']} ({'Admin' if user_data['is_admin'] else 'Regular User'})")
            except Exception as e:
                db.session.rollback()
                print(f"❌ Failed to create user {user_data['username']}: {str(e)}")
                skipped_users.append(f"{user_data['username']} (error)")
        
        # Summary
        print("\n" + "="*50)
        print("📊 TEST USER CREATION SUMMARY")
        print("="*50)
        print(f"✅ Successfully created: {len(created_users)} users")
        print(f"⚠️  Skipped: {len(skipped_users)} users")
        
        if created_users:
            print("\n🎉 Created Users:")
            for username in created_users:
                user = User.query.filter_by(username=username).first()
                role = "Admin" if user.is_admin else "User"
                print(f"   • {username} ({role}) - {user.email}")
        
        if skipped_users:
            print("\n⚠️  Skipped Users:")
            for username in skipped_users:
                print(f"   • {username}")
        
        print("\n📝 LOGIN CREDENTIALS:")
        print("   Username: admin_user | Password: admin123 (Admin)")
        print("   Username: test_user1 | Password: password123")
        print("   Username: anime_fan  | Password: otaku123")
        print("   Username: reviewer   | Password: review123")
        print("   Username: casual_watcher | Password: casual123")
        
        print(f"\n🌐 Access the application at: http://127.0.0.1:5000")
        print("="*50)

if __name__ == '__main__':
    print("🚀 Creating test user accounts for Anime Tracker...")
    create_test_users()
