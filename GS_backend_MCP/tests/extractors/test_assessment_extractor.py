import pytest
from GS_backend_MCP.myserver.extractors import assessment_extractor

def test_get_findings():
    results = {
        "assessment-results": {
            "results": [
                {
                    "findings": [
                        {"id": "f1", "target": {"status": {"risk-level": "high", "state": "open"}}},
                        {"id": "f2", "target": {"status": {"risk-level": "low", "state": "closed"}}}
                    ]
                }
            ]
        }
    }

    # Filter by risk-level
    findings = assessment_extractor.get_findings(results, risk_level="high")
    assert len(findings) == 1
    assert findings[0]["id"] == "f1"

    # Filter by state
    findings = assessment_extractor.get_findings(results, state="closed")
    assert len(findings) == 1
    assert findings[0]["id"] == "f2"

def test_get_subjects():
    results = {
        "assessment-results": {
            "assessment-subjects": [{"id": "s1", "type": "component"}]
        }
    }
    subjects = assessment_extractor.get_subjects(results)
    assert len(subjects) == 1
    assert subjects[0]["id"] == "s1"
