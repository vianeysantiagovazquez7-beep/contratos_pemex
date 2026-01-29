import json
from pathlib import Path

STATUS_FILE = Path("data") / "tutorial_status.json"

def _load():
    if not STATUS_FILE.exists():
        STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATUS_FILE.write_text("{}", encoding="utf-8")
    return json.loads(STATUS_FILE.read_text(encoding="utf-8"))

def _save(data):
    STATUS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def is_first_time(usuario: str) -> bool:
    data = _load()
    return not data.get(usuario, {}).get("completed", False)

def mark_completed(usuario: str):
    data = _load()
    data[usuario] = {"completed": True}
    _save(data)
    