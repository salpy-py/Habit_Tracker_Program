# Habit Tracker (CLI + SQLite)

This repository contains a habit tracking application built in **Python**. The program runs entirely in the terminal (CLI) and stores data in a local **SQLite** database so habits and check-offs persist between sessions.

The project focuses on clean structure, correct streak logic (daily vs weekly), and testability (pytest)

---

## Table of Contents

1. [Key Features](#key-features)  
2. [How Streaks Work](#how-streaks-work)  
3. [Project Structure](#project-structure)  
4. [Requirements](#requirements)  
5. [Installation](#installation)  
6. [Running the App](#running-the-app)  
7. [Command Reference](#command-reference)  
8. [Analytics Reference](#analytics-reference)  
9. [Using the Predefined Dataset](#using-the-predefined-dataset)  
10. [Running Unit Tests](#running-unit-tests)  


---

## Key Features

### Habit management (CRUD)
- Create a habit with:
  - a **name** (unique)
  - a **periodicity**: `daily` or `weekly`
- Edit a habit:
  - rename
  - change periodicity
- List all habits
- Delete a habit (and its completion history)

### Check-offs (completion tracking)
- Record a completion at the **current time**
- Optionally record a completion at a **specific timestamp** (useful for testing without waiting days)

### Analytics
- Overview of all habits, including:
  - **current streak**
  - **longest streak**
- Filter habits by periodicity (`daily` / `weekly`)
- Longest streak overall across all habits (**shows ties**, not only one habit)
- One-habit analytics view (current/longest/completion count)

### Persistence
- Data is stored in SQLite:
  - habits are stored once
  - completions are stored as timestamped events
- Data persists between sessions as long as you use the same `.db` file

### Testing
- Pytest unit test suite included
- Uses **4 weeks** of deterministic time-series fixture data to verify streak logic
- Tests cover:
  - habit creation/editing/deletion
  - completion recording behavior
  - analytics correctness and edge cases
  - SQLite schema constraints (FK cascade, uniqueness of completions, meta table)

---

## How Streaks Work

A **streak is measured in periods**, not raw check-offs.

### Daily periodicity
- One “successful period” = at least one completion on a calendar day
- Multiple check-offs in the same day still count as **one** for streak purposes
- A daily streak is the number of consecutive days completed without a missed day

### Weekly periodicity
- One “successful period” = at least one completion in an ISO week (e.g., `2026-W05`)
- Multiple check-offs within the same ISO week still count as **one** successful week
- A weekly streak is the number of consecutive ISO weeks completed without skipping a week

### Current streak definition used in this project
In this project, **current streak** is defined as:

> the streak ending at the **most recently completed period**  
> (not necessarily “as of today/this week”).

This keeps analytics deterministic and easy to unit test without relying on the system clock.

---

## Project Structure

High-level structure:

- `main.py`  
  Entry point. Runs the CLI.

- `habit_tracker/cli.py`  
  CLI argument parsing (argparse) and user-facing output formatting.

- `habit_tracker/tracker.py`  
  Business logic (“service layer”):
  - validates input
  - resolves habits by name or id
  - calls the storage layer
  - calls analytics functions

- `habit_tracker/storage.py`  
  SQLite persistence layer:
  - initializes schema (tables + indexes)
  - CRUD operations for habits
  - insert/read operations for completions
  - meta table for idempotent fixture seeding

- `habit_tracker/analytics.py`  
  Analytics functions:
  - filter habits by periodicity
  - derive daily/week period keys
  - compute longest streak per habit
  - compute current streak per habit
  - compute best habit overall

- `habit_tracker/time_utils.py`  
  Time and bucketing helpers:
  - convert timestamps to daily keys (`YYYY-MM-DD`)
  - convert timestamps to ISO week keys (`YYYY-W##`)
  - ISO week boundary logic

- `habit_tracker/models.py`  
  Domain model (`Habit` dataclass) used across the app.

- `habit_tracker/predefined_data.py`  
  Deterministic predefined habits + 4-week fixture completion data used in tests.

- `tests/`  
  Pytest unit tests (CRUD tests, analytics tests, edge cases, SQLite behavior, time-utils checks).

---

## Requirements

- Python **3.7+**
- A terminal (PowerShell / CMD / Terminal)
- Recommended: create a virtual environment

---

## Installation

### Windows PowerShell (recommended)

```powershell
cd habit_tracker_program
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If activation is blocked:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

### Windows CMD

```bat
cd /d path\to\habit_tracker_program
py -m venv .venv
.\.venv\Scripts\activate.bat
pip install -r requirements.txt
```

### macOS / Linux

```bash
cd path/to/habit_tracker_program
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## Running the App

Run commands from the folder that contains `main.py`.

### Show global help

```bash
python main.py --help
```

### Database note (important)

By default, the app uses `habits.db` in the current directory.


```bash
python main.py list
```

---

## Command Reference

All commands follow this pattern:

```bash
python main.py <command> [options]
```

### Add a habit

```bash
python main.py add --name "Read 20 minutes" --period daily
python main.py add --name "Clean room" --period weekly
```

### Edit a habit

`--key` can be **name or id**.

Rename:

```bash
python main.py edit --key "Read 20 minutes" --name "Read Book"
```

Change periodicity:

```bash
python main.py edit --key "Read Book" --period weekly
```

### List habits

```bash
python main.py list
```

### Delete a habit

```bash
python main.py delete --key "Read Book"
```

### Check off a habit

Use current time:

```bash
python main.py checkoff --key "Drink 2L water"
```

Use a specific timestamp (ISO format):

```bash
python main.py checkoff --key "Drink 2L water" --at "2026-01-05T12:00:00"
```

Timestamp format:

- `YYYY-MM-DDTHH:MM:SS`  
  Example: `2026-01-05T12:00:00`

---

## Analytics Reference

### Overview (current + longest for every habit)

```bash
python main.py analyze --all
```

### Filter habits by periodicity

```bash
python main.py analyze --period daily
python main.py analyze --period weekly
```

### Longest streak/streaks overall

```bash
python main.py analyze --longest
```

### One habit detail view

```bash
python main.py analyze --habit "Clean Room" 
```

---

## Using the Predefined Dataset

This project includes a deterministic fixture dataset:

- **5 predefined habits** (at least one daily and one weekly)
- **4 weeks of completion history** per habit

To insert it:

```bash
python main.py seed
```

Seeding is **idempotent**, meaning you can run it more than once without duplicating records.

---

## Running Unit Tests

This project uses **pytest**.

Run all tests:

```bash
python -m pytest
```

Run a specific test file:

```bash
python -m pytest tests/test_habit_crud.py -q
python -m pytest tests/test_sqlite_handler.py -q
python -m pytest tests/test_time_utils.py -q
```

What the tests cover:

- Habit CRUD: create, edit, delete, validation cases
- Check-off behavior: adds completions, ignores duplicates where expected
- Analytics: filtering, period bucketing, current/longest streak calculations
- Edge cases: gaps in streak, multiple check-offs in same period, unsorted input
- SQLite behavior: schema created correctly, FK cascade works, uniqueness works


---

## License

This project is intended for academic/portfolio use only.
