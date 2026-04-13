
import os as _os

_COUNTER_PATH = _os.path.join("data", "visit_counter.txt")


def _ensure_data_dir():
    try:
        _os.makedirs("data", exist_ok=True)
        return True
    except Exception:
        return False


def read_visit_counter():
    """Legge il contatore senza incrementarlo."""
    try:
        if _os.path.exists(_COUNTER_PATH):
            with open(_COUNTER_PATH, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    return int(content)
    except Exception:
        pass
    return 0


def increment_visit_counter():
    """Incrementa il contatore di una unità e restituisce il nuovo valore."""
    if not _ensure_data_dir():
        return 0
    count = read_visit_counter()
    count += 1
    try:
        with open(_COUNTER_PATH, "w") as f:
            f.write(str(count))
    except Exception:
        return 0
    return count
