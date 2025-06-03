from pydantic import BaseModel
from typing import Optional, Dict, Any

class OCRResponse(BaseModel):
    success: bool
    text: str
    message: str
    error: Optional[str] = None

class CCCDResponse(BaseModel):
    status: str
    extracted_data: Dict[str, Any] 