from typing import Any, Dict, List, Optional
from pydantic import BaseModel

class OscalComponentDefinition(BaseModel):
    # Simplified OSCAL structure for the draft
    oscal_version: str = "1.1.2"
    metadata: Dict[str, Any]
    components: List[Dict[str, Any]]
    back_matter: Optional[Dict[str, Any]] = None

class ReviewFeedback(BaseModel):
    iteration: int
    feedback: str
    approved: bool
