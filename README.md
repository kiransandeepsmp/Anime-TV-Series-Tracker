# 🎬 Anime Tracker

A comprehensive web-based anime tracking application built with Flask. Track your anime watchlist, discover new series, engage with the community, and get personalized recommendations.

## ✨ Features

### 🔐 User Management
- User registration and authentication
- Secure login/logout system
- User profiles with detailed statistics
- Dark/Light theme toggle with persistence

### 📝 Watchlist Management
- Track anime across 5 status categories:
  - 📺 **Watching** - Currently watching
  - ✅ **Completed** - Finished watching
  - ⏸️ **On Hold** - Temporarily paused
  - ❌ **Dropped** - Discontinued watching
  - 📋 **Plan to Watch** - Want to watch later
- Episode progress tracking with visual progress bars
- Rating system (1-10 scale)
- Personal reviews and notes
- Start/completion date tracking

### 🔍 Discovery & Browse
- **MyAnimeList API Integration** - Access to 50,000+ anime database
- Advanced search functionality
- Filter by genre, year, rating, and status
- Popular and seasonal anime recommendations
- Detailed anime information pages with streaming links

### 💬 Community Features
- Discussion boards for each anime
- Comment system with threading
- Spoiler protection with click-to-reveal
- Community-driven reviews and ratings

### 🎯 Smart Recommendations
- Personalized recommendations based on your ratings
- Genre-based suggestions
- Popular anime fallback for new users
- Intelligent scoring algorithm

### 👑 Admin Panel
- User management and statistics
- Anime database management
- Discussion moderation tools
- Bulk import functionality
- System analytics dashboard

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- pip (Python package manager)

### Installation

1. **Clone or download the project**
   ```bash
   cd anime-tracker
   ```

2. **Create virtual environment**
   ```bash
   python3 -m venv anime_tracker/venv
   source anime_tracker/venv/bin/activate  # On Windows: anime_tracker\venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create test users (optional)**
   ```bash
   python3 create_test_users.py
   ```

5. **Run the application**
   ```bash
   cd anime_tracker
   python3 app.py
   ```

6. **Access the application**
   - Open your browser and go to: `http://127.0.0.1:5000`

## 🔑 Test Accounts

If you ran the test user creation script, you can use these accounts:

| Username | Password | Role |
|----------|----------|------|
| admin_user | admin123 | Admin |
| test_user1 | password123 | User |
| anime_fan | otaku123 | User |
| reviewer | review123 | User |
| casual_watcher | casual123 | User |

## 📱 Usage Guide

### For Regular Users

1. **Register/Login** - Create an account or use test credentials
2. **Search Anime** - Use "Add Anime" to search MyAnimeList database
3. **Build Watchlist** - Add anime to your watchlist with status
4. **Track Progress** - Update episodes watched and ratings
5. **Discover** - Browse popular/seasonal anime and get recommendations
6. **Engage** - Join discussions and share reviews

### For Administrators

1. **Admin Dashboard** - Access via user dropdown menu
2. **User Management** - View and manage user accounts
3. **Content Management** - Manage anime database and discussions
4. **API Browser** - Advanced search and bulk import tools
5. **Analytics** - View system statistics and usage data

## 🛠️ Technical Stack

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Database**: SQLite (development) / PostgreSQL (production ready)
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap
- **API**: Jikan API (MyAnimeList integration)
- **Authentication**: Session-based with secure password hashing

## 📊 Project Structure

```
anime-tracker/
├── anime_tracker/
│   ├── app.py                 # Main Flask application
│   ├── backend/
│   │   ├── models/           # Database models
│   │   ├── routes/           # Route handlers
│   │   └── services/         # External API services
│   ├── static/
│   │   ├── css/             # Stylesheets
│   │   ├── js/              # JavaScript files
│   │   └── images/          # Static images
│   └── templates/           # HTML templates
├── anime_tracker.db         # SQLite database
├── create_test_users.py     # Test user creation script
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables (Optional)
- `SECRET_KEY` - Flask secret key (defaults to development key)
- `DATABASE_URL` - Database connection string
- `DEBUG` - Enable/disable debug mode

### Database
- Development: SQLite (`anime_tracker.db`)
- Production: Configure `DATABASE_URL` for PostgreSQL/MySQL

## 🚀 Deployment

### Development
```bash
python3 app.py
```

### Production
Use a WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 🆘 Support

For issues, questions, or contributions:
- Create an issue in the repository
- Check the documentation
- Review the code comments

## 🎉 Acknowledgments

- **MyAnimeList** - Anime database via Jikan API
- **Flask Community** - Excellent web framework
- **Bootstrap** - Responsive UI components

---

**Happy Anime Tracking!** 🎬✨
