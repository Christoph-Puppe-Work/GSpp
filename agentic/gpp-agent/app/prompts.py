import re
import yaml
from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent / "prompts"

def load_prompt(prompt_id: str) -> str:
    path = _PROMPTS_DIR / f"{prompt_id}.md"
    if not path.exists():
        raise FileNotFoundError(f"Prompt {prompt_id} not found at {path}")

    text = path.read_text(encoding="utf-8")

    # Strip YAML frontmatter
    m = re.match(r"^---\n(.*?)\n---\n(.*)", text, re.DOTALL)
    if not m: return text

    # Optional: frontmatter = yaml.safe_load(m.group(1))
    return m.group(2).strip()
