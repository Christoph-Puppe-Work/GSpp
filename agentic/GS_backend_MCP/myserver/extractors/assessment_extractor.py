import re
from typing import Any, Dict, List

def get_findings(results: Dict[str, Any], risk_level: str = None, state: str = None) -> List[Dict[str, Any]]:
    """Extracts findings from Assessment Results."""
    assessment_results = results.get("assessment-results", {})
    results_list = assessment_results.get("results", [])

    findings = []
    for res in results_list:
        for finding in res.get("findings", []):
            match = True
            if risk_level and finding.get("target", {}).get("status", {}).get("risk-level") != risk_level:
                match = False
            if state and finding.get("target", {}).get("status", {}).get("state") != state:
                match = False

            if match:
                findings.append(finding)
    return findings

def get_subjects(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts assessment subjects from Assessment Results or Assessment Plan."""
    # Try AR
    assessment_results = data.get("assessment-results", {})
    if not assessment_results:
        # Try AP
        assessment_results = data.get("assessment-plan", {})

    return assessment_results.get("assessment-subjects", [])

def filter_assessment_controls(results: Dict[str, Any], regex_filter: str | None = None, selected_only: bool = False) -> List[Dict[str, Any]]:
    """
    Filters controls examined in the assessment.
    If selected_only is True, only returns controls that were actually reviewed in 'results'.
    """
    assessment_results = results.get("assessment-results", {})

    # Combined list of all controls mentioned in the assessment
    all_selections = assessment_results.get("reviewed-controls", {}).get("control-selections", [])

    # If selected_only, we only look at what's in 'results'
    results_list = assessment_results.get("results", [])

    pattern = re.compile(regex_filter, re.IGNORECASE) if regex_filter else None

    controls = []

    source_list = []
    if selected_only:
        for res in results_list:
             source_list.extend(res.get("reviewed-controls", {}).get("control-selections", []))
    else:
        source_list = all_selections

    for selection in source_list:
        for control_id_obj in selection.get("include-controls", []):
            cid = control_id_obj.get("control-id", "")
            if not pattern or pattern.search(cid):
                controls.append(control_id_obj)

    return controls
