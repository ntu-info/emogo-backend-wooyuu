#!/usr/bin/env python3
"""
Script to populate the database with sample/fake data for testing and demonstration.
This addresses the requirement that fake data can be used to populate the backend DB.
"""

import asyncio
import os
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import random

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "emogo_db")

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


async def populate_vlogs(db, count=10):
    """Populate database with sample vlog entries"""
    print(f"\nCreating {count} sample vlogs...")

    vlogs = []
    for i in range(count):
        timestamp = datetime.utcnow() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

        vlog = {
            "user_id": random.choice(SAMPLE_USERS),
            "video_url": f"https://example.com/videos/sample_{i+1}.mp4",
            "title": random.choice(SAMPLE_VLOG_TITLES),
            "description": random.choice(SAMPLE_VLOG_DESCRIPTIONS),
            "duration": round(random.uniform(30, 300), 2),  # 30 seconds to 5 minutes
            "timestamp": timestamp
        }
        vlogs.append(vlog)

    result = await db["vlogs"].insert_many(vlogs)
    print(f"✓ Created {len(result.inserted_ids)} vlogs")


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


async def main():
    """Main function to populate sample data"""
    print("=" * 60)
    print("EmoGo Sample Data Population Script")
    print("=" * 60)

    # Connect to MongoDB
    print(f"\nConnecting to MongoDB at {MONGODB_URI}...")
    client = AsyncIOMotorClient(MONGODB_URI)
    db = client[DB_NAME]

    try:
        # Test connection
        await db.command("ping")
        print("✓ Successfully connected to MongoDB")

        # Ask for confirmation
        print("\nThis will clear existing data and populate with sample data.")
        response = input("Continue? (yes/no): ")

        if response.lower() not in ['yes', 'y']:
            print("Operation cancelled.")
            return

        # Clear existing data
        await clear_existing_data(db)

        # Populate with sample data
        await populate_vlogs(db, count=10)
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

    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        raise

    finally:
        client.close()
        print("\nDisconnected from MongoDB")


if __name__ == "__main__":
    asyncio.run(main())
