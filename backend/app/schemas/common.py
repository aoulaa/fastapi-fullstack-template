from pydantic import BaseModel


class Message(BaseModel):
    """Generic message response schema"""

    message: str
