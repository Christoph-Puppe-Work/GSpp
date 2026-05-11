# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Unit tests for lightweight prompt and routing contracts."""


def test_classifier_prompt_routes_new_ssp_to_govern() -> None:
    """Creating a new SSP must route directly to Phase 1 instead of asking for
    another confirmation turn."""
    from app.prompts import load_prompt

    prompt = load_prompt("classifier")

    assert "SSP erstellen" in prompt
    assert 'route="govern"' in prompt
    assert "Do not ask" in prompt
    assert "route_to_phase" in prompt


def test_phase1_prompt_uses_one_backend_read_attempt() -> None:
    """Phase 1 must not fan out across backend tools after a failed read."""
    from app.prompts import load_prompt

    prompt = load_prompt("phase1_governance")

    assert "Call exactly one backend tool" in prompt
    assert "get_oscal_model_raw" in prompt
    assert 'model_enum = "ssp"' in prompt
    assert "Do not retry failed tool calls" in prompt
    assert "Do not call `list_oscal_models`" in prompt
