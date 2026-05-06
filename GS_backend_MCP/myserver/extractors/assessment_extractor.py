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

def get_subjects(results: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extracts assessment subjects from Assessment Results."""
    assessment_results = results.get("assessment-results", {})
    return assessment_results.get("assessment-subjects", [])

def filter_assessment_controls(results: Dict[str, Any], regex_filter: str) -> List[Dict[str, Any]]:
    """Filters controls examined in the assessment."""
    assessment_results = results.get("assessment-results", {})
    results_list = assessment_results.get("results", [])

    pattern = re.compile(regex_filter, re.IGNORECASE) if regex_filter else None

    controls = []
    for res in results_list:
        reviewed_controls = res.get("reviewed-controls", {}).get("control-selections", [])
        for selection in reviewed_controls:
            for control_id in selection.get("include-controls", []):
                if not pattern or pattern.search(control_id.get("control-id", "")):
                    controls.append(control_id)
    return controls
