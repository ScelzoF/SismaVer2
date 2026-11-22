import os as _os

_COUNTER_PATH = _os.path.join("data", "visit_counter.txt")


def _ensure_data_dir():
    try:
        _os.makedirs("data", exist_ok=True)
        return True
    except Exception:
        return False


def read_visit_counter():
    """Legge il contatore locale; None indica un errore di accesso al file."""
    try:
        if not _os.path.exists(_COUNTER_PATH):
            return 0
        with open(_COUNTER_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
        return int(content) if content.isdigit() else None
    except Exception:
        return None


def increment_visit_counter():
    """Incrementa una volta per sessione browser e restituisce il nuovo valore."""
    if not _ensure_data_dir():
        return None
    count = read_visit_counter()
    if count is None:
        return None
    count += 1
    try:
        with open(_COUNTER_PATH, "w", encoding="utf-8") as f:
            f.write(str(count))
    except Exception:
        return None
    return count
