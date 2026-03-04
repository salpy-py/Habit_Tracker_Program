import argparse

from .storage import SQLiteStorage
from .tracker import HabitTracker, VALID_PERIODS
from . import analytics


def _format_id(habit_id: str) -> str:
    """Format a habit ID for display.

    We currently display the full ID in the CLI. This helper exists so that
    if you ever decide to switch to shortened IDs, you only change it here.
    """
    return habit_id or ""


def _print_table(headers, rows) -> None:
    """Print a simple aligned table to the terminal.

    This intentionally avoids external dependencies (like tabulate) to keep the
    project lightweight and easy to run on any machine.
    """
    if not rows:
        return

    # Compute column widths based on headers and cell contents.
    column_widths = [len(h) for h in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            column_widths[idx] = max(column_widths[idx], len(str(cell)))

    row_format = "  ".join("{:<" + str(w) + "}" for w in column_widths)

    # Header row + a simple underline row.
    print(row_format.format(*headers))
    print(row_format.format(*["-" * w for w in column_widths]))

    # Data rows.
    for row in rows:
        print(row_format.format(*[str(cell) for cell in row]))


def build_parser() -> argparse.ArgumentParser:
    """Build and return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="habit-tracker",
        description="Habit Tracker (CLI + SQLite): create habits, check off, and analyze streaks.",
    )
    parser.add_argument("--db", default="habits.db", help="Path to SQLite DB file (default: habits.db)")
    subcommands = parser.add_subparsers(dest="cmd", required=True)

    add_cmd = subcommands.add_parser("add", help="Create a new habit")
    add_cmd.add_argument("--name", required=True, help="Habit name")
    add_cmd.add_argument("--period", required=True, choices=VALID_PERIODS, help="daily or weekly")

    edit_cmd = subcommands.add_parser("edit", help="Edit an existing habit")
    edit_cmd.add_argument("--key", required=True, help="Habit name or id")
    edit_cmd.add_argument("--name", help="New habit name")
    edit_cmd.add_argument("--period", choices=VALID_PERIODS, help="New periodicity: daily or weekly")

    delete_cmd = subcommands.add_parser("delete", help="Delete a habit by name or id")
    delete_cmd.add_argument("--key", required=True, help="Habit name or id")

    checkoff_cmd = subcommands.add_parser("checkoff", help="Record a completion for a habit")
    checkoff_cmd.add_argument("--key", required=True, help="Habit name or id")

    subcommands.add_parser("list", help="List all habits")
    subcommands.add_parser("seed", help="Insert predefined habits + 4-week fixture data (idempotent)")

    analyze_cmd = subcommands.add_parser("analyze", help="Run analytics")
    group = analyze_cmd.add_mutually_exclusive_group(required=True)
    group.add_argument("--all", action="store_true", help="Overview for all habits")
    group.add_argument("--period", choices=VALID_PERIODS, help="Filter habits by periodicity")
    group.add_argument("--longest", action="store_true", help="Longest streak across all habits")
    group.add_argument("--habit", dest="habit_key", help="Streaks for one habit (name or id)")

    return parser


def _cmd_add(tracker: HabitTracker, args) -> int:
    habit = tracker.add_habit(args.name, args.period)
    print(f"Created habit: {habit.name} ({habit.periodicity})")
    return 0


def _cmd_edit(tracker: HabitTracker, args) -> int:
    habit = tracker.edit_habit(args.key, new_name=args.name, new_periodicity=args.period)
    print(f"Updated habit: {habit.name} ({habit.periodicity})")
    return 0


def _cmd_delete(tracker: HabitTracker, args) -> int:
    if tracker.delete_habit(args.key):
        print("Habit deleted.")
        return 0
    print("Habit not found.")
    return 2


def _cmd_checkoff(tracker: HabitTracker, args) -> int:
    tracker.check_off(args.key)
    print("Check-off recorded.")
    return 0


def _cmd_list(tracker: HabitTracker) -> int:
    habits = tracker.get_habits()
    if not habits:
        print("No habits found. Use 'add' or 'seed'.")
        return 0

    # Sort by periodicity first, then by name to keep output stable and readable.
    rows = [(h.name, h.periodicity, _format_id(h.id)) for h in habits]
    rows.sort(key=lambda x: (x[1], x[0].lower()))
    _print_table(["Habit", "Period", "ID"], rows)
    return 0


def _cmd_seed(tracker: HabitTracker) -> int:
    print(tracker.seed_fixture())
    return 0


def _cmd_analyze(tracker: HabitTracker, args) -> int:
    if args.all:
        overview_rows = tracker.analyze_overview()
        if not overview_rows:
            print("No habits found.")
            return 0

        table_rows = [(h.name, h.periodicity, cur, lng, _format_id(h.id)) for h, cur, lng in overview_rows]
        table_rows.sort(key=lambda x: (x[1], x[0].lower()))
        _print_table(["Habit", "Period", "Current", "Longest", "ID"], table_rows)
        return 0

    if args.period:
        filtered = analytics.filter_by_periodicity(tracker.get_habits(), args.period)
        if not filtered:
            print(f"No {args.period} habits found.")
            return 0

        rows = [(h.name, _format_id(h.id)) for h in filtered]
        rows.sort(key=lambda x: x[0].lower())
        _print_table(["Habit", "ID"], rows)
        return 0

    if args.longest:
        habit, streak = tracker.analyze_longest_overall()
        if not habit:
            print("No habits found.")
            return 0
        print(f"Longest streak overall: {habit.name} [{habit.periodicity}] = {streak}")
        return 0

    if args.habit_key:
        # Using the tracker's resolver keeps CLI simple (name or ID works).
        habit = tracker._resolve_habit(args.habit_key)
        completions = tracker.get_completions(habit.id)

        current = analytics.current_streak_for(completions, habit.periodicity)
        longest = analytics.longest_streak_for(completions, habit.periodicity)

        _print_table(
            ["Habit", "Period", "Current", "Longest", "Completions", "ID"],
            [(habit.name, habit.periodicity, current, longest, len(completions), _format_id(habit.id))],
        )
        return 0

    # Should never happen because argparse requires one of the options.
    print("Unknown command. Use --help.")
    return 2


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    tracker = HabitTracker(SQLiteStorage(args.db))

    try:
        if args.cmd == "add":
            return _cmd_add(tracker, args)

        if args.cmd == "edit":
            return _cmd_edit(tracker, args)

        if args.cmd == "delete":
            return _cmd_delete(tracker, args)

        if args.cmd == "checkoff":
            return _cmd_checkoff(tracker, args)

        if args.cmd == "list":
            return _cmd_list(tracker)

        if args.cmd == "seed":
            return _cmd_seed(tracker)

        if args.cmd == "analyze":
            return _cmd_analyze(tracker, args)

        # Fallback guard: should not be reached with argparse's required subcommand.
        print("Unknown command. Use --help.")
        return 2

    except ValueError as e:
        # Keep error output user-friendly: show message + hint.
        print(f"Error: {e}")
        print("Hint: run with --help for usage.")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())