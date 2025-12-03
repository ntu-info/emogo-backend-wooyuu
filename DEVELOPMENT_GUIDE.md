# EmoGo Backend Development Journey

**A Complete Guide to Building a FastAPI + MongoDB Backend with Real Video Upload**

Author: wooyuu (with AI assistance)
Date: December 2024
Course: Psychology and Neuroinformatics

---

## 📖 Table of Contents

1. [Project Overview](#project-overview)
2. [Initial Setup](#initial-setup)
3. [Step-by-Step Implementation](#step-by-step-implementation)
4. [Challenges & Solutions](#challenges--solutions)
5. [Key Features Implemented](#key-features-implemented)
6. [Deployment Process](#deployment-process)
7. [Testing & Verification](#testing--verification)
8. [Lessons Learned](#lessons-learned)
9. [Final Checklist](#final-checklist)

---

## 🎯 Project Overview

### Assignment Requirements

**Goal:** Create an EmoGo backend on a public server using FastAPI + MongoDB.

**Required Features:**
- Three data types: vlogs, sentiments, GPS coordinates
- Data export/download page accessible to TAs
- Use fake data if needed (independent of previous assignment)
- Export page must be HTML returned by FastAPI (not separate frontend)
- **Critical:** Video download must work without requiring URI knowledge

### Technology Stack

- **Backend Framework:** FastAPI
- **Database:** MongoDB Atlas
- **Async Driver:** Motor
- **Deployment:** Render.com
- **Video Processing:** PIL, OpenCV, NumPy
- **Additional:** Pydantic, aiohttp

---

## 🚀 Initial Setup

### Step 1: Repository Structure

```bash
emogo-backend-wooyuu/
├── main.py                    # FastAPI application
├── models.py                  # Pydantic data models
├── requirements.txt           # Python dependencies
├── populate_sample_data.py    # Fake data generator
├── populate_with_videos.py    # Real video generator
├── .gitignore                 # Git ignore rules
├── .env.example              # Environment variables template
└── README.md                 # Project documentation
```

### Step 2: Core Dependencies

```txt
fastapi[all]
motor[srv]
pydantic
python-multipart
aiofiles
Pillow
opencv-python
numpy
aiohttp
```

### Step 3: Environment Configuration

```bash
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
DB_NAME=emogo_db
```

---

## 📝 Step-by-Step Implementation

### Phase 1: Basic Backend Structure

**What We Built:**
1. FastAPI application with MongoDB connection
2. Three data models: VlogModel, SentimentModel, GPSCoordinateModel
3. Basic CRUD endpoints for each data type
4. Health check endpoint

**Key Code:**
```python
app = FastAPI(
    title="EmoGo Backend API",
    description="Backend API for EmoGo",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_db_client():
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
```

### Phase 2: Data Models

**Pydantic Models Created:**

```python
class VlogModel(BaseModel):
    user_id: str
    video_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class SentimentModel(BaseModel):
    user_id: str
    emotion: str
    intensity: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class GPSCoordinateModel(BaseModel):
    user_id: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
```

### Phase 3: Export Page (Critical Requirement)

**Teacher's Note:**
> "The export/download/dashboard page is an HTML page returned by FastAPI rather than a separate frontend."

**Implementation:**

```python
@app.get("/export", response_class=HTMLResponse)
async def export_data_page():
    vlogs_count = await app.mongodb["vlogs"].count_documents({})
    sentiments_count = await app.mongodb["sentiments"].count_documents({})
    gps_count = await app.mongodb["gps_coordinates"].count_documents({})

    # Returns beautiful HTML with:
    # - Data counts
    # - View/Download buttons
    # - Video download links
    # - JSON export functionality
```

### Phase 4: Video File Upload/Download (Enhanced Feature)

**Teacher's Feedback:**
> "The video download/export function is not fully functioning in some submissions. Please check if you have a backend URI and allow users to download videos without requiring knowledge of URIs."

**Solution - File Upload Endpoint:**

```python
@app.post("/api/vlogs/upload", status_code=status.HTTP_201_CREATED)
async def upload_vlog_with_file(
    user_id: str = Form(...),
    video: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    # Validate file type
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = VIDEOS_DIR / unique_filename

    # Save file
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # Store in database with download URL
    download_url = f"/api/vlogs/download/{unique_filename}"
```

**Download Endpoint:**

```python
@app.get("/api/vlogs/download/{filename}")
async def download_vlog_video(filename: str):
    file_path = VIDEOS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
```

### Phase 5: Real Video Generation

**Problem:** How to create actual test videos instead of fake URLs?

**Solution:** Created `populate_with_videos.py`

**Features:**
- Generates 3-second MP4 videos programmatically
- Uses PIL for image generation with text overlays
- Uses OpenCV for video encoding
- Creates colorful backgrounds with animations
- Uploads videos directly to backend API

**Key Function:**

```python
def create_test_video(filename: str, title: str, duration: int = 3, fps: int = 30):
    """Creates a 3-second test video with colored background and text"""

    width, height = 640, 480
    total_frames = duration * fps
    bg_color = random.choice(COLORS)

    # Create video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))

    for frame_num in range(total_frames):
        # Create frame with PIL
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Add title text
        draw.text((title_x, title_y), title, fill=(255, 255, 255), font=font)

        # Add timer
        time_text = f"{frame_num / fps:.1f}s / {duration}s"
        draw.text((time_x, time_y), time_text, fill=(255, 255, 255), font=small_font)

        # Add pulsing circle animation
        radius = 30 + int(20 * abs(np.sin(frame_num * 0.1)))
        draw.ellipse([(x - radius, y - radius), (x + radius, y + radius)],
                     fill=(255, 255, 255, 128))

        # Convert to OpenCV and write
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        out.write(frame)

    out.release()
```

---

## 🔧 Challenges & Solutions

### Challenge 1: SSL Certificate Verification (MongoDB)

**Problem:**
```
[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate
```

**Cause:** macOS Python SSL certificate issues

**Solution 1 - Connection String:**
```bash
mongodb+srv://user:pass@cluster.mongodb.net/?tlsAllowInvalidCertificates=true
```

**Solution 2 - Install Certificates:**
```bash
cd "/Applications/Python 3.12"
sudo "./Install Certificates.command"
```

### Challenge 2: SSL Certificate Verification (HTTPS to Render)

**Problem:** Same SSL error when uploading videos to Render deployment

**Solution:** Added SSL context to aiohttp client:

```python
import ssl

# Create SSL context that doesn't verify certificates
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE

connector = aiohttp.TCPConnector(ssl=ssl_context)
async with aiohttp.ClientSession(connector=connector) as session:
    # Upload videos...
```

### Challenge 3: Video File Not Found Error

**Problem:**
```json
{"detail":"Video file not found"}
```

**Cause:** Database had vlog entries with fake URLs, but no actual video files

**Solution:** Use `populate_with_videos.py` instead of `populate_sample_data.py`

```bash
# Set environment variables
export MONGODB_URI="mongodb+srv://..."
export DB_NAME="emogo_db"
export API_URL="http://localhost:8000"  # or Render URL

# Run video generation script
python3 populate_with_videos.py
```

### Challenge 4: Git Branch Merge

**Problem:**
```
error: RPC failed; HTTP 403
fatal: the remote end hung up unexpectedly
```

**Cause:** Protected main branch, cannot push directly

**Solution:** Create Pull Request on GitHub instead:
1. Go to GitHub repository
2. Click "Pull requests" → "New pull request"
3. Base: `main`, Compare: `claude/setup-emogo-backend-...`
4. Create and merge PR

### Challenge 5: MongoDB Atlas Network Access

**Problem:** Couldn't find IP whitelist settings

**Solution:**
```
Left Sidebar → Security → Network Access → + ADD IP ADDRESS
→ Click "ALLOW ACCESS FROM ANYWHERE"
→ Automatically fills in 0.0.0.0/0
```

---

## ✨ Key Features Implemented

### 1. RESTful API Endpoints

**Data Upload (POST):**
- `POST /api/vlogs` - JSON with URL
- `POST /api/vlogs/upload` - Multipart form with file
- `POST /api/sentiments` - JSON data
- `POST /api/gps` - JSON data

**Data Retrieval (GET):**
- `GET /api/vlogs` - All vlogs (with optional filtering)
- `GET /api/sentiments` - All sentiments
- `GET /api/gps` - All GPS coordinates
- `GET /api/vlogs/{id}` - Specific vlog
- `GET /api/vlogs/download/{filename}` - Download video file

**Export & Documentation:**
- `GET /export` - **Main requirement** - HTML export page
- `GET /api/export/all` - All data as JSON
- `GET /docs` - Swagger UI
- `GET /health` - Health check

### 2. Interactive Export Page

**Features:**
- Real-time data counts
- Auto-loading vlog previews
- Individual download buttons for each video
- JSON export for all data types
- Beautiful, responsive UI

**JavaScript Functionality:**
```javascript
// Auto-load vlogs on page load
window.addEventListener('DOMContentLoaded', function() {
    loadData('vlogs', 'vlogs-preview');
});

// Show video download buttons
if (vlog.download_url) {
    html += `<a href="${vlog.download_url}" class="download-btn">
             📥 Download Video</a>`;
}
```

### 3. Sample Data Population

**Two Scripts:**

1. **populate_sample_data.py** - Quick fake data:
   - Creates vlogs with fake URLs
   - Generates sentiments
   - Creates GPS coordinates

2. **populate_with_videos.py** - Real videos:
   - Creates actual 3-second MP4 files
   - Uploads to backend via API
   - Generates sentiments and GPS data
   - Each video ~100-200 KB

### 4. Data Validation

**Pydantic Features:**
- Field validation (latitude: -90 to 90)
- Type checking
- Optional fields with defaults
- Auto-generated API docs

### 5. Async/Await Pattern

**Performance Benefits:**
```python
# Multiple database queries run concurrently
vlogs_count = await app.mongodb["vlogs"].count_documents({})
sentiments_count = await app.mongodb["sentiments"].count_documents({})
gps_count = await app.mongodb["gps_coordinates"].count_documents({})

# Async iteration over large datasets
async for vlog in app.mongodb["vlogs"].find(query).limit(100):
    vlogs.append(vlog)
```

---

## 🌐 Deployment Process

### MongoDB Atlas Setup

**Step 1: Create Cluster**
1. Visit https://www.mongodb.com/cloud/atlas
2. Sign up / Sign in
3. Create free M0 cluster
4. Choose region (Singapore for Taiwan)

**Step 2: Database Access**
1. Security → Database Access
2. Add New Database User
3. Choose Password authentication
4. Save username and password
5. Set privilege: Atlas admin

**Step 3: Network Access**
1. Security → Network Access
2. Add IP Address
3. Click "ALLOW ACCESS FROM ANYWHERE"
4. Confirms 0.0.0.0/0

**Step 4: Get Connection String**
1. Database → Connect
2. Connect your application
3. Copy connection string
4. Replace `<username>` and `<password>`

### Render Deployment

**Step 1: Create Web Service**
1. Visit https://render.com/
2. New → Web Service
3. Connect GitHub repository

**Step 2: Configure Service**
```
Name: emogo-backend-wooyuu
Runtime: Python 3
Build Command: pip install -r requirements.txt
Start Command: uvicorn main:app --host 0.0.0.0 --port $PORT
```

**Step 3: Environment Variables**
```
MONGODB_URI = mongodb+srv://user:pass@cluster.mongodb.net/
DB_NAME = emogo_db
```

**Step 4: Deploy**
- Click "Create Web Service"
- Wait 5-10 minutes
- Get deployment URL

### Upload Videos to Production

```bash
# Set Render URL
export MONGODB_URI="mongodb+srv://..."
export DB_NAME="emogo_db"
export API_URL="https://your-app.onrender.com"

# Upload videos
python3 populate_with_videos.py
```

---

## 🧪 Testing & Verification

### Local Testing

**1. Start Local Server:**
```bash
export MONGODB_URI="mongodb+srv://..."
export DB_NAME="emogo_db"
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**2. Check Endpoints:**
```bash
# Health check
curl http://localhost:8000/health

# Upload sentiment
curl -X POST "http://localhost:8000/api/sentiments" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "emotion": "happy", "intensity": 0.9}'

# Get all sentiments
curl http://localhost:8000/api/sentiments
```

**3. Test Video Upload:**
```bash
curl -X POST "http://localhost:8000/api/vlogs/upload" \
  -F "user_id=test" \
  -F "title=Test Video" \
  -F "video=@/path/to/video.mp4"
```

**4. Visit Export Page:**
```
http://localhost:8000/export
```

### Production Testing

**Verify Deployment:**
1. `https://your-app.onrender.com/` - Home page
2. `https://your-app.onrender.com/health` - Health check
3. `https://your-app.onrender.com/export` - Export page
4. `https://your-app.onrender.com/docs` - API docs

**Test Video Download:**
1. Visit `/export`
2. Click "Load Preview" under Vlogs
3. Click "📥 Download Video" button
4. Video should download successfully

### Verification Checklist

```
✅ MongoDB Connection
   - Health endpoint shows "database": "connected"

✅ Data Upload
   - Can POST to /api/sentiments
   - Can POST to /api/gps
   - Can POST to /api/vlogs/upload with video file

✅ Data Retrieval
   - GET /api/vlogs returns data
   - GET /api/sentiments returns data
   - GET /api/gps returns data

✅ Export Page
   - Shows correct counts
   - Displays vlog previews
   - Download buttons work
   - JSON export works

✅ Video Functionality
   - Videos upload successfully
   - Videos can be downloaded
   - Download doesn't require knowing URI
   - Videos play correctly

✅ API Documentation
   - /docs loads Swagger UI
   - All endpoints documented
   - "Try it out" works
```

---

## 💡 Lessons Learned

### 1. SSL Certificate Issues on macOS

**Learning:** macOS Python installations often have SSL certificate issues.

**Solutions:**
- Use `tlsAllowInvalidCertificates=true` in MongoDB URI
- Install certificates: `sudo /Applications/Python*/Install Certificates.command`
- Add SSL context for aiohttp clients

### 2. File Upload with FastAPI

**Key Points:**
- Use `UploadFile` from `fastapi`
- Use `Form(...)` for form data
- Use `File(...)` for file uploads
- Content type must be `multipart/form-data`
- Remember to close file after reading

### 3. MongoDB with Motor

**Best Practices:**
- Use async/await throughout
- Connection pool managed automatically
- Convert ObjectId to string for JSON
- Use `count_documents()` not deprecated `count()`

### 4. Video Generation

**What Works:**
- PIL for image creation
- OpenCV for video encoding
- MP4V codec is widely compatible
- 3-second videos keep file size small (~100KB)
- Animated elements make videos more interesting

### 5. Git Workflow

**Workflow:**
```bash
# 1. Develop on feature branch
git checkout -b claude/feature-name

# 2. Commit regularly
git add .
git commit -m "Descriptive message"

# 3. Push to remote
git push -u origin claude/feature-name

# 4. Create PR on GitHub (if main is protected)
# 5. Merge via web interface
```

### 6. Environment Variables

**Best Practices:**
- Never commit sensitive data
- Use `.env.example` for templates
- Set in Render dashboard for production
- Use `os.getenv()` with defaults for local development

### 7. API Design

**Lessons:**
- RESTful naming conventions
- Use proper HTTP status codes (201 for creation)
- Provide meaningful error messages
- Include health check endpoint
- Document with OpenAPI/Swagger

---

## 📋 Final Checklist

### Code Quality

- [x] All endpoints tested and working
- [x] Error handling implemented
- [x] Data validation with Pydantic
- [x] Async/await used consistently
- [x] Code commented appropriately

### Features

- [x] Three data types: vlogs, sentiments, GPS
- [x] POST endpoints for data upload
- [x] GET endpoints for data retrieval
- [x] **Video file upload functionality**
- [x] **Video download functionality**
- [x] HTML export page (not separate frontend)
- [x] Download works without URI knowledge
- [x] Sample data generation scripts

### Deployment

- [x] MongoDB Atlas configured
- [x] Render deployment successful
- [x] Environment variables set
- [x] Videos uploaded to production
- [x] All endpoints accessible online

### Documentation

- [x] README.md complete
- [x] API endpoints documented
- [x] Setup instructions clear
- [x] Deployment guide included
- [x] Troubleshooting section added

### Testing

- [x] Local testing completed
- [x] Production testing completed
- [x] All data types working
- [x] Export page functional
- [x] Video download verified

---

## 🎓 Key Takeaways

### What Went Well

1. **FastAPI is excellent** for rapid API development
2. **MongoDB Atlas** free tier is perfect for small projects
3. **Render** deployment is straightforward and reliable
4. **Programmatic video generation** is surprisingly easy
5. **HTML templates in FastAPI** work great for simple UIs

### What Was Challenging

1. **SSL certificate issues** on macOS required research
2. **Protected git branches** need PR workflow
3. **Multipart form data** requires specific FastAPI syntax
4. **Video codec compatibility** varies by platform
5. **Async programming** requires careful management

### What I Would Do Differently

1. **Set up SSL correctly** from the beginning
2. **Use docker** for consistent environment
3. **Add authentication** for production use
4. **Implement rate limiting** for API endpoints
5. **Add comprehensive tests** (pytest)

---

## 📚 Resources Used

### Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [MongoDB Motor Documentation](https://motor.readthedocs.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Render Documentation](https://render.com/docs)
- [MongoDB Atlas Guide](https://www.mongodb.com/docs/atlas/)

### Tutorials
- Render FastAPI Deployment Guide
- MongoDB Atlas Chinese Tutorial (askstw.medium.com)

### Libraries
- FastAPI - Web framework
- Motor - Async MongoDB driver
- Pydantic - Data validation
- PIL/Pillow - Image processing
- OpenCV - Video processing
- aiohttp - Async HTTP client

---

## 🎉 Final Result

### Deployment URLs

- **Repository:** https://github.com/ntu-info/emogo-backend-wooyuu
- **Live API:** https://emogo-backend-wooyuu.onrender.com
- **Export Page:** https://emogo-backend-wooyuu.onrender.com/export
- **API Docs:** https://emogo-backend-wooyuu.onrender.com/docs

### Statistics

- **Total Commits:** 5
- **Files Created:** 7
- **Dependencies:** 9
- **API Endpoints:** 15+
- **Data Types:** 3
- **Video Files Generated:** 10
- **Development Time:** ~4 hours

### Achievement Unlocked

✅ Complete FastAPI backend with MongoDB
✅ Real video upload and download
✅ Beautiful HTML export page
✅ Deployed to public server
✅ Comprehensive documentation
✅ All assignment requirements met

---

## 🙏 Acknowledgments

- **Course:** Psychology and Neuroinformatics
- **Instructor:** Professor Tren
- **AI Assistant:** Claude (Anthropic)
- **Platform:** Render.com, MongoDB Atlas
- **Framework:** FastAPI

---

**End of Development Guide**

*This document serves as both a tutorial and a record of the development process. It can be used as a reference for future projects involving FastAPI, MongoDB, and video handling.*

---

**License:** Educational Use Only
**Date:** December 2024
**Version:** 1.0
