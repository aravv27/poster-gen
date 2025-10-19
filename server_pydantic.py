from pydantic import BaseModel, Field
from typing import Optional, Dict
class GenerateRequest(BaseModel):
    prompt: str
    width: Optional[int] = 1920
    height: Optional[int] = 1080

class GenerateResponse(BaseModel):
    job_id: str
    status: str
    message: str

class StatusResponse(BaseModel):
    job_id: str
    status: str  # processing, completed, failed, partial
    current_phase: Optional[str] = None
    progress: int  # 0-100
    message: str
    image_ready: bool = False
    phases_rendered: Dict[str, bool] = Field(default_factory=dict)

class ResultResponse(BaseModel):
    job_id: str
    status: str
    image: Optional[str] = None  # base64 encoded image
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    phase: Optional[str] = None