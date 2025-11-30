from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class VlogModel(BaseModel):
    """Model for video log entries"""
    user_id: str
    video_url: str
    title: Optional[str] = None
    description: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration: Optional[float] = None  # in seconds

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "video_url": "https://example.com/video.mp4",
                "title": "My Day",
                "description": "A great day!",
                "duration": 120.5
            }
        }


class SentimentModel(BaseModel):
    """Model for sentiment/emotion data"""
    user_id: str
    emotion: str  # e.g., happy, sad, angry, neutral, etc.
    intensity: float = Field(ge=0.0, le=1.0)  # 0-1 scale
    note: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    context: Optional[str] = None  # additional context

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "emotion": "happy",
                "intensity": 0.8,
                "note": "Had a great meeting today",
                "context": "work"
            }
        }


class GPSCoordinateModel(BaseModel):
    """Model for GPS location data"""
    user_id: str
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    altitude: Optional[float] = None  # in meters
    accuracy: Optional[float] = None  # in meters
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    location_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user123",
                "latitude": 25.0330,
                "longitude": 121.5654,
                "altitude": 10.0,
                "accuracy": 5.0,
                "location_name": "Taipei"
            }
        }


class VlogResponse(VlogModel):
    """Response model with MongoDB ID"""
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class SentimentResponse(SentimentModel):
    """Response model with MongoDB ID"""
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True


class GPSCoordinateResponse(GPSCoordinateModel):
    """Response model with MongoDB ID"""
    id: str = Field(alias="_id")

    class Config:
        populate_by_name = True
