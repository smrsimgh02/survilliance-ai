import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

class Detection(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    camera_id: str
    class_name: str
    confidence: float
    xcenter: float
    ycenter: float
    width: float
    height: float
    timestamp: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)

class Camera(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    url: str
    location: Optional[str] = None
    status: str = "active"
