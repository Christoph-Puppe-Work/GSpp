from typing import List, Optional, Literal
from pydantic import BaseModel, Field

class ReviewFinding(BaseModel):
    severity: Literal["low", "medium", "high"]
    location: str
    message: str
    suggestion: Optional[str] = None

class CisOscalReviewCriteria(BaseModel):
    oscal_json_valid: bool
    component_definition_metadata_complete: bool
    all_controls_resolvable_via_mcp: bool
    no_hallucinated_control_ids: bool
    statements_match_cis_recommendations: bool
    parameters_have_valid_select_values: bool
    overall_verdict: Literal["approve", "request_changes"]
    findings: List[ReviewFinding] = Field(default_factory=list)

class VendorEvidenceReviewCriteria(BaseModel):
    coverage_complete: bool
    source_attribution_accurate: bool
    no_hallucinated_quotes: bool
    overall_verdict: Literal["approve", "request_changes"]
    findings: List[ReviewFinding] = Field(default_factory=list)

class PolicyReviewCriteria(BaseModel):
    consistency_ok: bool
    gpp_mapping_complete: bool
    completeness_ok: bool
    overall_verdict: Literal["approve", "request_changes"]
    findings: List[ReviewFinding] = Field(default_factory=list)
