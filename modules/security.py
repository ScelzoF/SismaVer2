
def increment_visit_counter():
    import os

    path = "data"
    filename = "visit_counter.txt"
    counter_path = os.path.join(path, filename)

    # Assicurati che la cartella esista
    try:
        os.makedirs(path, exist_ok=True)
    except:
        return 0

    count = 0
    try:
        # Leggi il valore attuale se il file esiste
        if os.path.exists(counter_path):
            with open(counter_path, "r") as f:
                content = f.read().strip()
                if content.isdigit():
                    count = int(content)
        # Incrementa
        count += 1
        with open(counter_path, "w") as f:
            f.write(str(count))
    except:
        return 0

    return count
