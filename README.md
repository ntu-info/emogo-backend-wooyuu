[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/e7FBMwSa)
[![Open in Visual Studio Code](https://classroom.github.com/assets/open-in-vscode-2e0aaae1b6195c2367325f4f02e2d04e9abb55f0b24a779b69b11b9e10269abc.svg)](https://classroom.github.com/online_ide?assignment_repo_id=21880288&assignment_repo_type=AssignmentRepo)

# EmoGo Backend API

A FastAPI-based backend service for the EmoGo application, designed to collect and manage three types of data:
- 📹 **Vlogs** (Video logs)
- 😊 **Sentiments** (Emotion data)
- 📍 **GPS Coordinates** (Location data)

## 🎯 Data Export/Download URI

**The data export and download page can be accessed at:**

```
https://your-deployment-url.onrender.com/export
```

This page allows TAs and instructors to:
- View all collected vlogs, sentiments, and GPS coordinates
- Download data in JSON format (individually or all at once)
- See real-time counts of each data type

### Alternative Data Access Methods

- **Individual data endpoints:**
  - Vlogs: `https://your-deployment-url.onrender.com/api/vlogs`
  - Sentiments: `https://your-deployment-url.onrender.com/api/sentiments`
  - GPS Coordinates: `https://your-deployment-url.onrender.com/api/gps`

- **Export all data:** `https://your-deployment-url.onrender.com/api/export/all`

- **API Documentation (Swagger UI):** `https://your-deployment-url.onrender.com/docs`

## 🚀 Features

- RESTful API built with FastAPI
- MongoDB Atlas integration for data persistence
- Async/await pattern for high performance
- **Video file upload and download support** - Upload actual video files, not just URLs!
- **Interactive HTML data export/download page** - TAs can download videos directly
- Interactive API documentation (Swagger UI & ReDoc)
- Data validation with Pydantic models
- Sample data population script for testing
- Health check endpoint for monitoring

## 📋 API Endpoints

### Data Upload Endpoints (POST)

- `POST /api/vlogs` - Upload a new vlog entry (JSON with video URL)
- `POST /api/vlogs/upload` - Upload a vlog with actual video file (multipart/form-data)
- `POST /api/sentiments` - Upload sentiment/emotion data
- `POST /api/gps` - Upload GPS coordinate data

### Data Retrieval Endpoints (GET)

- `GET /api/vlogs` - Retrieve all vlogs (with optional user_id filter)
- `GET /api/sentiments` - Retrieve all sentiments (with optional user_id filter)
- `GET /api/gps` - Retrieve all GPS coordinates (with optional user_id filter)
- `GET /api/vlogs/{id}` - Get specific vlog by ID
- `GET /api/sentiments/{id}` - Get specific sentiment by ID
- `GET /api/gps/{id}` - Get specific GPS coordinate by ID

### Export & Documentation

- `GET /export` - Interactive data export/download page (with video downloads!)
- `GET /api/export/all` - Export all data as JSON
- `GET /api/vlogs/download/{filename}` - Download a specific video file
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /health` - Health check endpoint

## 🛠️ Technology Stack

- **Framework:** FastAPI
- **Database:** MongoDB Atlas
- **Database Driver:** Motor (async MongoDB driver)
- **Data Validation:** Pydantic
- **Deployment:** Render.com (or any cloud platform)

## 📦 Installation & Local Development

### Prerequisites

- Python 3.8+
- MongoDB Atlas account (or local MongoDB instance)

### Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd emogo-backend-wooyuu
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set environment variables:
```bash
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"
export DB_NAME="emogo_db"
```

4. Run the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

### Populating Sample Data

To populate the database with fake/sample data for testing:

```bash
python populate_sample_data.py
```

This script will:
- Clear existing data (after confirmation)
- Create 10 sample vlogs
- Create 20 sample sentiments
- Create 15 sample GPS coordinates

This addresses the requirement that fake data can be used to populate the backend database.

## ☁️ Deployment on Render

### Step 1: Set Up MongoDB Atlas

1. Create a MongoDB Atlas account at https://www.mongodb.com/cloud/atlas
2. Create a new cluster (free tier is sufficient)
3. Set allowed IP to `0.0.0.0/0` (allow all IPs)
4. Create a database user with username and password
5. Get your connection string (format: `mongodb+srv://username:password@cluster.mongodb.net/`)

### Step 2: Deploy to Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Configure the service:
   - **Name:** emogo-backend (or your preferred name)
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`

4. Add environment variables:
   - `MONGODB_URI`: Your MongoDB connection string
   - `DB_NAME`: `emogo_db` (or your preferred database name)

5. Click "Create Web Service"

### Step 3: Verify Deployment

Once deployed, visit:
- `https://your-app.onrender.com/` - Home page
- `https://your-app.onrender.com/export` - Data export page
- `https://your-app.onrender.com/docs` - API documentation
- `https://your-app.onrender.com/health` - Health check

## 📝 Data Models

### Vlog Model
```json
{
  "user_id": "string",
  "video_url": "string",
  "title": "string (optional)",
  "description": "string (optional)",
  "duration": "number (optional)",
  "timestamp": "datetime (auto-generated)"
}
```

### Sentiment Model
```json
{
  "user_id": "string",
  "emotion": "string",
  "intensity": "number (0-1)",
  "note": "string (optional)",
  "context": "string (optional)",
  "timestamp": "datetime (auto-generated)"
}
```

### GPS Coordinate Model
```json
{
  "user_id": "string",
  "latitude": "number (-90 to 90)",
  "longitude": "number (-180 to 180)",
  "altitude": "number (optional)",
  "accuracy": "number (optional)",
  "location_name": "string (optional)",
  "timestamp": "datetime (auto-generated)"
}
```

## 🧪 Testing the API

### Using curl

```bash
# Upload a vlog with JSON (video URL)
curl -X POST "http://localhost:8000/api/vlogs" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "video_url": "https://example.com/video.mp4",
    "title": "My Day"
  }'

# Upload a vlog with actual video file
curl -X POST "http://localhost:8000/api/vlogs/upload" \
  -F "user_id=user123" \
  -F "title=My Day" \
  -F "description=A great day!" \
  -F "video=@/path/to/your/video.mp4"

# Upload sentiment
curl -X POST "http://localhost:8000/api/sentiments" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "emotion": "happy",
    "intensity": 0.8
  }'

# Upload GPS coordinate
curl -X POST "http://localhost:8000/api/gps" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "latitude": 25.0330,
    "longitude": 121.5654
  }'

# Get all vlogs
curl "http://localhost:8000/api/vlogs"
```

### Using the Interactive API Docs

Visit `http://localhost:8000/docs` for an interactive Swagger UI where you can test all endpoints directly in your browser.

## 📊 Database Collections

The application uses three MongoDB collections:
- `vlogs` - Stores video log entries
- `sentiments` - Stores emotion/sentiment data
- `gps_coordinates` - Stores location data

## 🔒 Security Notes

- In production, restrict MongoDB Atlas IP whitelist to only necessary IPs
- Use environment variables for sensitive data (never commit credentials)
- Consider adding authentication/authorization for production use
- Implement rate limiting for API endpoints

## 📄 License

This project is created for educational purposes as part of a course assignment.

## 👥 Author

Created by wooyuu for the EmoGo Backend Assignment

---

**Note:** Remember to replace `https://your-deployment-url.onrender.com` with your actual deployment URL after deploying to Render!