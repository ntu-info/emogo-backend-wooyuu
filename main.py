from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Form
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
import os
import shutil
from pathlib import Path
import uuid

from models import (
    VlogModel, SentimentModel, GPSCoordinateModel,
    VlogResponse, SentimentResponse, GPSCoordinateResponse
)

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "emogo_db")

# File storage configuration
UPLOAD_DIR = Path("uploads")
VIDEOS_DIR = UPLOAD_DIR / "videos"

# Create upload directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
VIDEOS_DIR.mkdir(exist_ok=True)

app = FastAPI(
    title="EmoGo Backend API",
    description="Backend API for EmoGo - collecting vlogs, sentiments, and GPS coordinates",
    version="1.0.0"
)

# Mount static files for serving uploaded videos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")


@app.on_event("startup")
async def startup_db_client():
    """Initialize MongoDB connection on startup"""
    app.mongodb_client = AsyncIOMotorClient(MONGODB_URI)
    app.mongodb = app.mongodb_client[DB_NAME]
    print(f"Connected to MongoDB at {MONGODB_URI}")


@app.on_event("shutdown")
async def shutdown_db_client():
    """Close MongoDB connection on shutdown"""
    app.mongodb_client.close()
    print("Disconnected from MongoDB")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>EmoGo Backend API</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #333; }
            .endpoint { background: #f4f4f4; padding: 10px; margin: 10px 0; border-radius: 5px; }
            .method { font-weight: bold; color: #007bff; }
            a { color: #007bff; text-decoration: none; }
            a:hover { text-decoration: underline; }
        </style>
    </head>
    <body>
        <h1>Welcome to EmoGo Backend API</h1>
        <p>This API collects and manages vlogs, sentiments, and GPS coordinates.</p>

        <h2>Available Endpoints:</h2>

        <div class="endpoint">
            <span class="method">POST</span> /api/vlogs - Upload a new vlog (JSON data with video URL)
        </div>

        <div class="endpoint">
            <span class="method">POST</span> /api/vlogs/upload - Upload a vlog with video file (multipart/form-data)
        </div>

        <div class="endpoint">
            <span class="method">POST</span> /api/sentiments - Upload sentiment data
        </div>

        <div class="endpoint">
            <span class="method">POST</span> /api/gps - Upload GPS coordinates
        </div>

        <div class="endpoint">
            <span class="method">GET</span> /api/vlogs - Get all vlogs
        </div>

        <div class="endpoint">
            <span class="method">GET</span> /api/sentiments - Get all sentiments
        </div>

        <div class="endpoint">
            <span class="method">GET</span> /api/gps - Get all GPS coordinates
        </div>

        <div class="endpoint">
            <span class="method">GET</span> <a href="/export">/export</a> - Data export/download page
        </div>

        <div class="endpoint">
            <span class="method">GET</span> <a href="/docs">/docs</a> - Interactive API Documentation (Swagger UI)
        </div>

        <div class="endpoint">
            <span class="method">GET</span> <a href="/redoc">/redoc</a> - Alternative API Documentation (ReDoc)
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


# ==================== VLOG ENDPOINTS ====================

@app.post("/api/vlogs", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_vlog(vlog: VlogModel):
    """Upload a new vlog entry"""
    vlog_dict = vlog.model_dump()
    result = await app.mongodb["vlogs"].insert_one(vlog_dict)
    return {
        "message": "Vlog created successfully",
        "id": str(result.inserted_id)
    }


@app.get("/api/vlogs", response_model=List[dict])
async def get_vlogs(user_id: Optional[str] = None, limit: int = 100):
    """Get all vlogs, optionally filtered by user_id"""
    query = {"user_id": user_id} if user_id else {}
    vlogs = []
    async for vlog in app.mongodb["vlogs"].find(query).limit(limit):
        vlog["_id"] = str(vlog["_id"])
        vlogs.append(vlog)
    return vlogs


@app.get("/api/vlogs/{vlog_id}")
async def get_vlog(vlog_id: str):
    """Get a specific vlog by ID"""
    from bson import ObjectId
    try:
        vlog = await app.mongodb["vlogs"].find_one({"_id": ObjectId(vlog_id)})
        if vlog:
            vlog["_id"] = str(vlog["_id"])
            return vlog
        raise HTTPException(status_code=404, detail="Vlog not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")


@app.post("/api/vlogs/upload", status_code=status.HTTP_201_CREATED)
async def upload_vlog_with_file(
    user_id: str = Form(...),
    video: UploadFile = File(...),
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None)
):
    """Upload a vlog with an actual video file"""

    # Validate file type
    allowed_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm", ".m4v"}
    file_ext = Path(video.filename).suffix.lower()

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = VIDEOS_DIR / unique_filename

    # Save the uploaded file
    try:
        with file_path.open("wb") as buffer:
            shutil.copyfileobj(video.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    finally:
        video.file.close()

    # Get file size
    file_size = file_path.stat().st_size

    # Create vlog entry with file reference
    video_url = f"/uploads/videos/{unique_filename}"
    download_url = f"/api/vlogs/download/{unique_filename}"

    vlog_dict = {
        "user_id": user_id,
        "video_url": video_url,
        "download_url": download_url,
        "original_filename": video.filename,
        "file_size": file_size,
        "title": title,
        "description": description,
        "timestamp": datetime.utcnow()
    }

    result = await app.mongodb["vlogs"].insert_one(vlog_dict)

    return {
        "message": "Vlog uploaded successfully",
        "id": str(result.inserted_id),
        "video_url": video_url,
        "download_url": download_url,
        "file_size": file_size
    }


@app.get("/api/vlogs/download/{filename}")
async def download_vlog_video(filename: str):
    """Download a specific vlog video file"""
    file_path = VIDEOS_DIR / filename

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ==================== SENTIMENT ENDPOINTS ====================

@app.post("/api/sentiments", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_sentiment(sentiment: SentimentModel):
    """Upload new sentiment data"""
    sentiment_dict = sentiment.model_dump()
    result = await app.mongodb["sentiments"].insert_one(sentiment_dict)
    return {
        "message": "Sentiment created successfully",
        "id": str(result.inserted_id)
    }


@app.get("/api/sentiments", response_model=List[dict])
async def get_sentiments(user_id: Optional[str] = None, limit: int = 100):
    """Get all sentiments, optionally filtered by user_id"""
    query = {"user_id": user_id} if user_id else {}
    sentiments = []
    async for sentiment in app.mongodb["sentiments"].find(query).limit(limit):
        sentiment["_id"] = str(sentiment["_id"])
        sentiments.append(sentiment)
    return sentiments


@app.get("/api/sentiments/{sentiment_id}")
async def get_sentiment(sentiment_id: str):
    """Get a specific sentiment by ID"""
    from bson import ObjectId
    try:
        sentiment = await app.mongodb["sentiments"].find_one({"_id": ObjectId(sentiment_id)})
        if sentiment:
            sentiment["_id"] = str(sentiment["_id"])
            return sentiment
        raise HTTPException(status_code=404, detail="Sentiment not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")


# ==================== GPS ENDPOINTS ====================

@app.post("/api/gps", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_gps_coordinate(gps: GPSCoordinateModel):
    """Upload new GPS coordinate data"""
    gps_dict = gps.model_dump()
    result = await app.mongodb["gps_coordinates"].insert_one(gps_dict)
    return {
        "message": "GPS coordinate created successfully",
        "id": str(result.inserted_id)
    }


@app.get("/api/gps", response_model=List[dict])
async def get_gps_coordinates(user_id: Optional[str] = None, limit: int = 100):
    """Get all GPS coordinates, optionally filtered by user_id"""
    query = {"user_id": user_id} if user_id else {}
    gps_coords = []
    async for gps in app.mongodb["gps_coordinates"].find(query).limit(limit):
        gps["_id"] = str(gps["_id"])
        gps_coords.append(gps)
    return gps_coords


@app.get("/api/gps/{gps_id}")
async def get_gps_coordinate(gps_id: str):
    """Get a specific GPS coordinate by ID"""
    from bson import ObjectId
    try:
        gps = await app.mongodb["gps_coordinates"].find_one({"_id": ObjectId(gps_id)})
        if gps:
            gps["_id"] = str(gps["_id"])
            return gps
        raise HTTPException(status_code=404, detail="GPS coordinate not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid ID format: {str(e)}")


# ==================== DATA EXPORT PAGE ====================

@app.get("/export", response_class=HTMLResponse)
async def export_data_page():
    """Data export and download page - THIS IS THE REQUIRED URI FOR THE ASSIGNMENT"""

    # Get counts for each data type
    vlogs_count = await app.mongodb["vlogs"].count_documents({})
    sentiments_count = await app.mongodb["sentiments"].count_documents({})
    gps_count = await app.mongodb["gps_coordinates"].count_documents({})

    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EmoGo Data Export</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 50px auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            h1 {{
                color: #333;
                text-align: center;
            }}
            .container {{
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .data-section {{
                margin: 20px 0;
                padding: 20px;
                background: #f9f9f9;
                border-left: 4px solid #007bff;
                border-radius: 5px;
            }}
            .data-section h2 {{
                color: #007bff;
                margin-top: 0;
            }}
            .count {{
                font-size: 24px;
                font-weight: bold;
                color: #28a745;
            }}
            .download-btn {{
                display: inline-block;
                padding: 10px 20px;
                margin: 10px 10px 10px 0;
                background-color: #007bff;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }}
            .download-btn:hover {{
                background-color: #0056b3;
            }}
            .view-btn {{
                display: inline-block;
                padding: 10px 20px;
                margin: 10px 10px 10px 0;
                background-color: #28a745;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: background-color 0.3s;
            }}
            .view-btn:hover {{
                background-color: #218838;
            }}
            .info {{
                color: #666;
                font-style: italic;
            }}
            .data-preview {{
                margin-top: 10px;
                padding: 10px;
                background: white;
                border: 1px solid #ddd;
                border-radius: 5px;
                max-height: 300px;
                overflow-y: auto;
            }}
            pre {{
                margin: 0;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
        </style>
        <script>
            async function loadData(type, elementId) {{
                try {{
                    const response = await fetch(`/api/${{type}}`);
                    const data = await response.json();

                    // Special handling for vlogs to show video download links
                    if (type === 'vlogs' && Array.isArray(data)) {{
                        let html = '<div style="max-height: 400px; overflow-y: auto;">';
                        if (data.length === 0) {{
                            html += '<p>No vlogs available</p>';
                        }} else {{
                            data.forEach((vlog, index) => {{
                                html += `
                                    <div style="border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px; background: #fafafa;">
                                        <h4 style="margin-top: 0;">Vlog #${{index + 1}}</h4>
                                        <p><strong>User ID:</strong> ${{vlog.user_id}}</p>
                                        <p><strong>Title:</strong> ${{vlog.title || 'N/A'}}</p>
                                        <p><strong>Description:</strong> ${{vlog.description || 'N/A'}}</p>
                                        <p><strong>Timestamp:</strong> ${{vlog.timestamp}}</p>
                                        ${{vlog.file_size ? `<p><strong>File Size:</strong> ${{(vlog.file_size / 1024 / 1024).toFixed(2)}} MB</p>` : ''}}
                                        ${{vlog.download_url ?
                                            `<a href="${{vlog.download_url}}" class="download-btn" style="display: inline-block; margin-top: 10px;">📥 Download Video</a>` :
                                            vlog.video_url ?
                                            `<a href="${{vlog.video_url}}" class="view-btn" style="display: inline-block; margin-top: 10px;" target="_blank">🎥 View Video</a>` :
                                            '<p style="color: #999;">No video available</p>'
                                        }}
                                    </div>
                                `;
                            }});
                        }}
                        html += '</div>';
                        document.getElementById(elementId).innerHTML = html;
                    }} else {{
                        document.getElementById(elementId).innerHTML =
                            '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
                    }}
                }} catch (error) {{
                    document.getElementById(elementId).innerHTML =
                        '<p style="color: red;">Error loading data: ' + error.message + '</p>';
                }}
            }}

            function downloadJSON(type) {{
                fetch(`/api/${{type}}`)
                    .then(response => response.json())
                    .then(data => {{
                        const blob = new Blob([JSON.stringify(data, null, 2)], {{ type: 'application/json' }});
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = `emogo_${{type}}_${{new Date().toISOString().split('T')[0]}}.json`;
                        document.body.appendChild(a);
                        a.click();
                        window.URL.revokeObjectURL(url);
                        document.body.removeChild(a);
                    }})
                    .catch(error => alert('Error downloading data: ' + error.message));
            }}

            // Auto-load vlogs on page load
            window.addEventListener('DOMContentLoaded', function() {{
                loadData('vlogs', 'vlogs-preview');
            }});
        </script>
    </head>
    <body>
        <div class="container">
            <h1>EmoGo Data Export & Download</h1>
            <p class="info">This page allows you to view and download all collected data from the EmoGo application.</p>

            <div class="data-section">
                <h2>📹 Vlogs (Video Logs)</h2>
                <p class="count">Total: {vlogs_count} entries</p>
                <p>Video log entries uploaded by users.</p>
                <a href="/api/vlogs" class="view-btn" target="_blank">View JSON</a>
                <button onclick="loadData('vlogs', 'vlogs-preview')" class="view-btn">Load Preview</button>
                <button onclick="downloadJSON('vlogs')" class="download-btn">Download JSON</button>
                <div id="vlogs-preview" class="data-preview" style="display: none;"></div>
                <script>document.getElementById('vlogs-preview').style.display = 'block';</script>
            </div>

            <div class="data-section">
                <h2>😊 Sentiments (Emotion Data)</h2>
                <p class="count">Total: {sentiments_count} entries</p>
                <p>Emotional state and sentiment data collected from users.</p>
                <a href="/api/sentiments" class="view-btn" target="_blank">View JSON</a>
                <button onclick="loadData('sentiments', 'sentiments-preview')" class="view-btn">Load Preview</button>
                <button onclick="downloadJSON('sentiments')" class="download-btn">Download JSON</button>
                <div id="sentiments-preview" class="data-preview" style="display: none;"></div>
                <script>document.getElementById('sentiments-preview').style.display = 'block';</script>
            </div>

            <div class="data-section">
                <h2>📍 GPS Coordinates (Location Data)</h2>
                <p class="count">Total: {gps_count} entries</p>
                <p>Geographic location data with coordinates and timestamps.</p>
                <a href="/api/gps" class="view-btn" target="_blank">View JSON</a>
                <button onclick="loadData('gps', 'gps-preview')" class="view-btn">Load Preview</button>
                <button onclick="downloadJSON('gps')" class="download-btn">Download JSON</button>
                <div id="gps-preview" class="data-preview" style="display: none;"></div>
                <script>document.getElementById('gps-preview').style.display = 'block';</script>
            </div>

            <div class="data-section">
                <h2>📊 Export All Data</h2>
                <p>Download all three data types in a single operation.</p>
                <a href="/api/export/all" class="download-btn">Download All Data (JSON)</a>
            </div>

            <hr style="margin: 30px 0;">

            <div style="text-align: center;">
                <p><a href="/" style="color: #007bff;">← Back to Home</a> |
                <a href="/docs" style="color: #007bff;">API Documentation</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/api/export/all")
async def export_all_data():
    """Export all data in a single JSON response"""
    vlogs = []
    sentiments = []
    gps_coords = []

    async for vlog in app.mongodb["vlogs"].find():
        vlog["_id"] = str(vlog["_id"])
        vlogs.append(vlog)

    async for sentiment in app.mongodb["sentiments"].find():
        sentiment["_id"] = str(sentiment["_id"])
        sentiments.append(sentiment)

    async for gps in app.mongodb["gps_coordinates"].find():
        gps["_id"] = str(gps["_id"])
        gps_coords.append(gps)

    return {
        "export_date": datetime.utcnow().isoformat(),
        "total_vlogs": len(vlogs),
        "total_sentiments": len(sentiments),
        "total_gps_coordinates": len(gps_coords),
        "data": {
            "vlogs": vlogs,
            "sentiments": sentiments,
            "gps_coordinates": gps_coords
        }
    }


# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        await app.mongodb.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        )