# Habit Tracker: CLI + SQLite

Command-line Habit Tracker that saves everything locally using **SQLite**.
You can add habits, edit them, check them off, and analyze streaks.

---

## Prerequisites

- **Python 3.7+**
- A terminal (Command Prompt / PowerShell / macOS Terminal / Linux shell)

> No servers or accounts needed — data stays in a local SQLite database file.

---

## Install dependencies

```bash
pip install -r requirements.txt
```

---

## Run the app

From the folder where `main.py` is located:

```bash
python main.py --help
```

Commands: `add`, `edit`, `delete`, `checkoff`, `list`, `seed`, `analyze`.

---

## Quick start (demo data)

### Seed demo data

```bash
python main.py seed
```

The command inserts:
- **5 predefined habits**
- **4 weeks of fixture completions**

If you run it again, it won’t duplicate anything:

```bash
python main.py seed
```

Expected message:
- `Fixture already seeded. Skipping.`

---

## List habits

```bash
python main.py list
```

---

## Add a habit

```bash
python main.py add --name "Meditate" --period daily
```

Valid `--period` values:
- `daily`
- `weekly`

---

## Edit a habit

Edit by **name** or **id**:

```bash
python main.py edit --key "Meditate" --name "Meditate (10 min)"
python main.py edit --key "Meditate (10 min)" --period weekly
```

---

## Check off a habit

```bash
python main.py checkoff --key "Meditate (10 min)"
```

Each check-off saves a timestamp in the database.

---

## Analytics

### Overview (current + longest streak)

```bash
python main.py analyze --all
```

### Filter by periodicity

```bash
python main.py analyze --period daily
python main.py analyze --period weekly
```

### Longest streak overall

```bash
python main.py analyze --longest
```

### One habit details

```bash
python main.py analyze --habit "Meditate (10 min)"
```

---

## Delete a habit

```bash
python main.py delete --key "Meditate (10 min)"
```

---

## Run unit tests

This project includes a `tests/` folder using **pytest**.

```bash
pytest -q
```

The tests cover:
- habit creation, editing, deletion
- all analytics functions
- streak correctness for daily vs weekly habits using **4 weeks of predefined time-series data**

---

## Notes about repository hygiene

A `.gitignore` is included to avoid committing generated files such as:
- `__pycache__/`
- `.pytest_cache/`
- `*.db` (SQLite database files)
