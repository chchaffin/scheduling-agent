# app/prompts/loader.py
from pathlib import Path
PROMPTS_DIR = Path(__file__).parent

def workflows() -> list[str]:
    # auto-discover workflow prompt dirs, skipping internals
    return [
        d.name for d in PROMPTS_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("_")
    ]

def load_prompt(workflow: str, name: str) -> str:
    return (PROMPTS_DIR / workflow / f"{name}.md").read_text(encoding="utf-8")

def load_fragment(name: str) -> str:
    return (PROMPTS_DIR / "_fragments" / f"{name}.md").read_text(encoding="utf-8")
