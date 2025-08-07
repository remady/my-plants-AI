
from pydantic import BaseModel, Field

class PlantInfo(BaseModel):
    """Structured information about a plant."""
    plant_name: str = Field(..., description="The common name of the plant.")
    scientific_name: str = Field(..., description="The scientific name of the plant.")
    description: str = Field(..., description="A brief description of the plant.")
    care_instructions: str = Field(..., description="Instructions for caring for the plant.")
