from pydantic import BaseModel, Field
from typing import List

class ImageMetadata(BaseModel):
    subject: str = Field(
        ..., 
        description="The specific subject of the image, such as 'red fox'."
    )
    category: str = Field(
        ..., 
        description="The broader classification, such as 'animal'."
    )
    attributes: List[str] = Field(
        ..., 
        description="A list of relevant visual or semantic attributes, like ['orange fur', 'wild', 'forest']."
    )
    caption: str = Field(
        ..., 
        description="A clear descriptive sentence explaining what is in the image."
    )
    confidence: float = Field(
        ..., 
        ge=0.0, 
        le=1.0, 
        description="A score between 0.0 and 1.0 indicating certainty. Low-confidence results must be flagged."
    )
