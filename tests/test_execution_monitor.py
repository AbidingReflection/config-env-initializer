import sqlite3
from pathlib import Path
from config_env_initializer.execution_monitor import Execution_Monitor
import time


def test_execution_monitor_success(tmp_path):
    """Marks script as successful when no exceptions occur."""
    db_path = tmp_path / "execution.db"
    sql_path = Path(__file__).parent.parent / "sql" / "execution_metrics.sql"
    CONFIG = {"execution_monitor_db_path": str(db_path)}

    db_path.parent.mkdir(parents=True, exist_ok=True)
    with open(sql_path, "r", encoding="utf-8") as f:
        sqlite3.connect(db_path).executescript(f.read())

    with Execution_Monitor(CONFIG, "test_script") as monitor:
        monitor.run_section("example", lambda: 42)

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT execution_failed FROM script_executions")
    result = cur.fetchone()
    conn.close()

    assert result[0] == 0


def test_execution_monitor_failure(tmp_path):
    """Marks script as failed when an uncaught exception occurs."""
    db_path = tmp_path / "execution.db"
    sql_path = Path(__file__).parent.parent / "sql" / "execution_metrics.sql"
    CONFIG = {"execution_monitor_db_path": str(db_path)}

    with open(sql_path, "r", encoding="utf-8") as f:
        sqlite3.connect(db_path).executescript(f.read())

    def will_fail():
        raise RuntimeError("intentional failure")

    try:
        with Execution_Monitor(CONFIG, "failing_script") as monitor:
            monitor.run_section("fail", will_fail)
    except RuntimeError:
        pass

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT execution_failed FROM script_executions")
    result = cur.fetchone()
    conn.close()

    assert result[0] == 1


def test_section_start_and_end_timestamps(tmp_path):
    """Ensures section start and end timestamps are properly recorded."""
    db_path = tmp_path / "execution.db"
    sql_path = Path(__file__).parent.parent / "sql" / "execution_metrics.sql"
    CONFIG = {"execution_monitor_db_path": str(db_path)}

    with open(sql_path, "r", encoding="utf-8") as f:
        sqlite3.connect(db_path).executescript(f.read())

    with Execution_Monitor(CONFIG, "timing_test") as monitor:
        monitor.run_section("wait", lambda: time.sleep(0.05))

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT start_ts, end_ts, duration_ms FROM section_executions")
    start, end, duration = cur.fetchone()
    conn.close()

    assert end > start
    assert duration >= 50


def test_multiple_sections_are_recorded(tmp_path):
    """Records multiple sequential sections under one script."""
    db_path = tmp_path / "execution.db"
    sql_path = Path(__file__).parent.parent / "sql" / "execution_metrics.sql"
    CONFIG = {"execution_monitor_db_path": str(db_path)}

    with open(sql_path, "r", encoding="utf-8") as f:
        sqlite3.connect(db_path).executescript(f.read())

    with Execution_Monitor(CONFIG, "multi_section_test") as monitor:
        monitor.run_section("part1", lambda: 1)
        monitor.run_section("part2", lambda: 2)

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT section_name FROM section_executions")
    sections = {row[0] for row in cur.fetchall()}
    conn.close()

    assert sections == {"part1", "part2"}


def test_section_failure_does_not_mark_script_failed(tmp_path):
    """Ensures exceptions handled inside a section do not mark script as failed."""
    db_path = tmp_path / "execution.db"
    sql_path = Path(__file__).parent.parent / "sql" / "execution_metrics.sql"
    CONFIG = {"execution_monitor_db_path": str(db_path)}

    with open(sql_path, "r", encoding="utf-8") as f:
        sqlite3.connect(db_path).executescript(f.read())

    def recoverable():
        try:
            raise ValueError("Handled internally")
        except ValueError:
            pass

    with Execution_Monitor(CONFIG, "handled_error") as monitor:
        monitor.run_section("recover", recoverable)

    conn = sqlite3.connect(db_path)
    cur = conn.execute("SELECT execution_failed FROM script_executions")
    result = cur.fetchone()
    conn.close()

    assert result[0] == 0
