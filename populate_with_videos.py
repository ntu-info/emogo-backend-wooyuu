#!/usr/bin/env python3
"""
Script to populate the database with sample data including REAL video files.
This creates actual 3-second test videos for vlogs.
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import random
from pathlib import Path
import aiohttp
import ssl

# Check if required packages are installed
try:
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    import cv2
except ImportError:
    print("Missing required packages. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "Pillow", "opencv-python", "numpy"])
    from PIL import Image, ImageDraw, ImageFont
    import numpy as np
    import cv2

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "emogo_db")

# Video storage
VIDEOS_DIR = Path("uploads/videos")
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)

# Sample data
SAMPLE_USERS = ["user001", "user002", "user003", "alice_chen", "bob_wang", "charlie_lin"]
SAMPLE_EMOTIONS = ["happy", "sad", "excited", "calm", "anxious", "neutral", "angry", "joyful"]

SAMPLE_LOCATIONS = [
    {"name": "National Taiwan University", "lat": 25.0173, "lon": 121.5397},
    {"name": "Taipei 101", "lat": 25.0330, "lon": 121.5654},
    {"name": "Shilin Night Market", "lat": 25.0880, "lon": 121.5240},
    {"name": "Tamsui", "lat": 25.1677, "lon": 121.4458},
    {"name": "Ximending", "lat": 25.0421, "lon": 121.5071},
    {"name": "Da'an Forest Park", "lat": 25.0263, "lon": 121.5360},
]

SAMPLE_VLOG_TITLES = [
    "My Morning Routine",
    "Weekend Adventure",
    "Coffee Shop Vibes",
    "Campus Life",
    "Night Market Food Tour",
    "Sunset at the Beach",
    "Study Session",
    "Cooking at Home",
    "City Exploration",
    "Relaxing Day Off"
]

SAMPLE_VLOG_DESCRIPTIONS = [
    "Had a great time today!",
    "Exploring new places in the city",
    "Just enjoying the moment",
    "Trying out new things",
    "Beautiful weather today",
    "Spent time with friends",
    "Productive day!",
    "Needed this break",
    "Discovering hidden gems",
    "Simple pleasures"
]

# Color palette for videos
COLORS = [
    (255, 107, 107),  # Red
    (107, 185, 255),  # Blue
    (255, 193, 107),  # Orange
    (144, 238, 144),  # Green
    (221, 160, 221),  # Purple
    (255, 182, 193),  # Pink
    (173, 216, 230),  # Light Blue
    (255, 218, 185),  # Peach
]


def create_test_video(filename: str, title: str, duration: int = 3, fps: int = 30):
    """
    Create a simple test video with colored background and text.

    Args:
        filename: Output filename (will be saved in VIDEOS_DIR)
        title: Text to display on the video
        duration: Video duration in seconds (default 3)
        fps: Frames per second (default 30)
    """
    filepath = VIDEOS_DIR / filename

    # Video properties
    width, height = 640, 480
    total_frames = duration * fps

    # Choose a random color
    bg_color = random.choice(COLORS)

    # Define the codec and create VideoWriter object
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(filepath), fourcc, fps, (width, height))

    print(f"  Creating video: {filename}")

    for frame_num in range(total_frames):
        # Create frame with PIL (easier for text)
        img = Image.new('RGB', (width, height), color=bg_color)
        draw = ImageDraw.Draw(img)

        # Try to use a decent font, fallback to default if not available
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
            small_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20)
        except:
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
                small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 20)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()

        # Add text
        text_color = (255, 255, 255)

        # Title
        title_bbox = draw.textbbox((0, 0), title, font=font)
        title_width = title_bbox[2] - title_bbox[0]
        title_height = title_bbox[3] - title_bbox[1]
        title_x = (width - title_width) // 2
        title_y = height // 2 - 50

        draw.text((title_x, title_y), title, fill=text_color, font=font)

        # Frame counter
        time_text = f"{frame_num / fps:.1f}s / {duration}s"
        time_bbox = draw.textbbox((0, 0), time_text, font=small_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_x = (width - time_width) // 2
        time_y = height // 2 + 20

        draw.text((time_x, time_y), time_text, fill=text_color, font=small_font)

        # Add a pulsing circle animation
        radius = 30 + int(20 * abs(np.sin(frame_num * 0.1)))
        circle_x = width // 2
        circle_y = height - 100
        draw.ellipse(
            [(circle_x - radius, circle_y - radius),
             (circle_x + radius, circle_y + radius)],
            fill=(255, 255, 255, 128)
        )

        # Convert PIL image to OpenCV format
        frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

        # Write frame
        out.write(frame)

    # Release everything
    out.release()

    print(f"  ✓ Created: {filename} ({os.path.getsize(filepath) / 1024:.1f} KB)")

    return filepath


async def upload_vlog_with_video(session, base_url, user_id, title, description, video_path):
    """Upload a vlog with actual video file to the API"""

    url = f"{base_url}/api/vlogs/upload"

    # Prepare the multipart form data
    data = aiohttp.FormData()
    data.add_field('user_id', user_id)
    data.add_field('title', title)
    data.add_field('description', description)

    # Add the video file
    with open(video_path, 'rb') as f:
        data.add_field('video',
                      f,
                      filename=video_path.name,
                      content_type='video/mp4')

        try:
            async with session.post(url, data=data) as response:
                if response.status == 201:
                    result = await response.json()
                    return result
                else:
                    error_text = await response.text()
                    print(f"  ✗ Upload failed: {error_text}")
                    return None
        except Exception as e:
            print(f"  ✗ Upload error: {e}")
            return None


async def populate_vlogs_with_videos(base_url="http://localhost:8000", count=10):
    """Create and upload vlogs with actual video files"""
    print(f"\nCreating {count} vlogs with real video files...")

    # Create SSL context that doesn't verify certificates (for macOS compatibility)
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    connector = aiohttp.TCPConnector(ssl=ssl_context)
    async with aiohttp.ClientSession(connector=connector) as session:
        for i in range(count):
            user_id = random.choice(SAMPLE_USERS)
            title = random.choice(SAMPLE_VLOG_TITLES)
            description = random.choice(SAMPLE_VLOG_DESCRIPTIONS)

            # Create video filename
            video_filename = f"test_vlog_{i+1:02d}.mp4"

            # Create the video file
            video_path = create_test_video(video_filename, f"Vlog #{i+1}", duration=3)

            # Upload to the API
            print(f"  Uploading vlog #{i+1}...")
            result = await upload_vlog_with_video(
                session, base_url, user_id, title, description, video_path
            )

            if result:
                print(f"  ✓ Vlog #{i+1} uploaded successfully (ID: {result.get('id', 'unknown')})")
            else:
                print(f"  ✗ Vlog #{i+1} upload failed")

            # Small delay to avoid overwhelming the server
            await asyncio.sleep(0.1)

    print(f"✓ Created and uploaded {count} vlogs with videos")


async def populate_sentiments(db, count=20):
    """Populate database with sample sentiment entries"""
    print(f"\nCreating {count} sample sentiments...")

    sentiments = []
    for i in range(count):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

        sentiment = {
            "user_id": random.choice(SAMPLE_USERS),
            "emotion": random.choice(SAMPLE_EMOTIONS),
            "intensity": round(random.uniform(0.3, 1.0), 2),
            "note": random.choice([
                "Feeling great today!",
                "Had a rough morning",
                "Really enjoying this",
                "Stressed about exams",
                "Excited for the weekend",
                "Just okay",
                "Best day ever!",
                None
            ]),
            "context": random.choice(["work", "school", "leisure", "social", "personal", None]),
            "timestamp": timestamp
        }
        sentiments.append(sentiment)

    result = await db["sentiments"].insert_many(sentiments)
    print(f"✓ Created {len(result.inserted_ids)} sentiments")


async def populate_gps_coordinates(db, count=15):
    """Populate database with sample GPS coordinate entries"""
    print(f"\nCreating {count} sample GPS coordinates...")

    gps_coords = []
    for i in range(count):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))
        location = random.choice(SAMPLE_LOCATIONS)

        # Add some random variation to coordinates
        lat_offset = random.uniform(-0.005, 0.005)
        lon_offset = random.uniform(-0.005, 0.005)

        gps = {
            "user_id": random.choice(SAMPLE_USERS),
            "latitude": round(location["lat"] + lat_offset, 6),
            "longitude": round(location["lon"] + lon_offset, 6),
            "altitude": round(random.uniform(5, 100), 2),
            "accuracy": round(random.uniform(3, 15), 2),
            "location_name": location["name"],
            "timestamp": timestamp
        }
        gps_coords.append(gps)

    result = await db["gps_coordinates"].insert_many(gps_coords)
    print(f"✓ Created {len(result.inserted_ids)} GPS coordinates")


async def clear_existing_data(db):
    """Clear existing data from collections"""
    print("\nClearing existing data...")

    collections = ["vlogs", "sentiments", "gps_coordinates"]
    for collection in collections:
        result = await db[collection].delete_many({})
        print(f"✓ Deleted {result.deleted_count} documents from {collection}")

    # Also clear video files
    video_files = list(VIDEOS_DIR.glob("*.mp4"))
    for video_file in video_files:
        video_file.unlink()
    print(f"✓ Deleted {len(video_files)} video files")


async def main():
    """Main function to populate sample data with real videos"""
    print("=" * 60)
    print("EmoGo Sample Data Population with REAL VIDEOS")
    print("=" * 60)

    # Get API base URL
    api_url = os.getenv("API_URL", "http://localhost:8000")
    print(f"\nAPI URL: {api_url}")

    # Connect to MongoDB
    print(f"\nConnecting to MongoDB at {MONGODB_URI}...")
    client = AsyncIOMotorClient(MONGODB_URI, tlsAllowInvalidCertificates=True)
    db = client[DB_NAME]

    try:
        # Test connection
        await db.command("ping")
        print("✓ Successfully connected to MongoDB")

        # Ask for confirmation
        print("\nThis will:")
        print("  1. Clear existing data")
        print("  2. Create 10 test videos (3 seconds each)")
        print("  3. Upload vlogs with videos to the API")
        print("  4. Create 20 sample sentiments")
        print("  5. Create 15 sample GPS coordinates")

        response = input("\nContinue? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("Operation cancelled.")
            return

        # Clear existing data
        await clear_existing_data(db)

        # Create and upload vlogs with videos
        await populate_vlogs_with_videos(base_url=api_url, count=10)

        # Populate other data types
        await populate_sentiments(db, count=20)
        await populate_gps_coordinates(db, count=15)

        print("\n" + "=" * 60)
        print("Sample data population completed successfully!")
        print("=" * 60)

        # Show summary
        print("\nDatabase Summary:")
        vlogs_count = await db["vlogs"].count_documents({})
        sentiments_count = await db["sentiments"].count_documents({})
        gps_count = await db["gps_coordinates"].count_documents({})

        print(f"  Vlogs: {vlogs_count}")
        print(f"  Sentiments: {sentiments_count}")
        print(f"  GPS Coordinates: {gps_count}")
        print(f"  Total: {vlogs_count + sentiments_count + gps_count}")

        print(f"\n  Video files created: {len(list(VIDEOS_DIR.glob('*.mp4')))}")
        total_size = sum(f.stat().st_size for f in VIDEOS_DIR.glob('*.mp4'))
        print(f"  Total video size: {total_size / 1024 / 1024:.2f} MB")

        print(f"\nVisit {api_url}/export to see all data with downloadable videos!")

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        raise

    finally:
        client.close()
        print("\nDisconnected from MongoDB")


if __name__ == "__main__":
    asyncio.run(main())
