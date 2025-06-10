import sys
import time
import sqlite3
from pathlib import Path
import config_env_initializer


def _get_sql_path(filename="execution_metrics.sql") -> Path:
    """Returns the full path to a SQL file in the package."""
    return Path(config_env_initializer.__file__).resolve().parent / "sql" / filename


class Execution_Monitor:
    """Tracks script and section execution metrics in SQLite."""

    def __init__(self, CONFIG, script_name, start_ts=None):
        """Initializes DB connection and logs script start."""
        self.config = CONFIG
        self.logger = self.config["logger"]
        self.script_name = script_name
        self.log_file_name = CONFIG.get('log_file_name')
        self.execution_failed = False
        self.current_section = None

        self.db_path = self._resolve_db_path()
        self._initialize_db_if_missing()
        self._connect_to_db()
        self.execution_id = self._insert_script_record(start_ts)

        self.logger.debug(f"[Execution_Monitor] Initialized with script '{self.script_name}', db at {self.db_path}")

    def __enter__(self):
        """Enters context manager."""
        self.logger.info(f'[Execution_Monitor] Script "{self.script_name}" started.')
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Finalizes script record and logs outcome."""
        if exc_type is not None:
            self.execution_failed = True
            self.logger.error(f'[Execution_Monitor] Script "{self.script_name}" failed: {exc_type.__name__}: {exc_value}')
        else:
            self.logger.info(f'[Execution_Monitor] Script "{self.script_name}" completed successfully.')
        self.finalize_script_db_record()
        return False  # Let exceptions propagate

    def _resolve_db_path(self):
        """Returns the resolved DB path, using default if missing."""
        db_path = self.config.get('execution_monitor_db_path')
        if not db_path:
            caller_path = Path(sys.argv[0]).resolve()
            db_path = caller_path.parent / "db" / "execution_metrics.db"
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return db_path

    def _initialize_db_if_missing(self):
        """Creates the DB schema if the DB doesn't exist."""
        if self.db_path.exists():
            return
        sql_path = _get_sql_path()
        with open(sql_path, "r", encoding="utf-8") as f:
            sql = f.read()
        conn = sqlite3.connect(self.db_path)
        conn.executescript(sql)
        conn.commit()
        conn.close()
        self.logger.info(f"[Execution_Monitor] Created new DB using {sql_path}")

    def _connect_to_db(self):
        """Establishes DB connection with WAL mode."""
        self.conn = sqlite3.connect(self.db_path, timeout=30, isolation_level=None)
        self.conn.execute("PRAGMA journal_mode=WAL;")
        self.conn.execute("PRAGMA synchronous=NORMAL;")
        self.cursor = self.conn.cursor()

    def _insert_script_record(self, start_ts=None):
        """Inserts a new script_executions record and returns the ID."""
        data = {
            "script_name": self.script_name,
            "start_ts": start_ts or self._now(),
        }
        if self.log_file_name:
            data["log_file_name"] = self.log_file_name
        execution_id = self._insert("script_executions", data)
        self.logger.debug(f"[Execution_Monitor] Inserted script execution ID {execution_id}")
        return execution_id

    def _now(self):
        """Returns current time in milliseconds."""
        return int(time.time_ns() / 1_000_000)

    def _insert(self, table, data):
        """Inserts a row into a given table."""
        sql = f"INSERT INTO {table} ({', '.join(data.keys())}) VALUES ({', '.join(['?'] * len(data))})"
        return self._execute_with_retry(sql, tuple(data.values())).lastrowid

    def _update(self, table, updates, where):
        """Updates rows in a given table using WHERE clause."""
        set_clause = ', '.join([f"{k}=?" for k in updates])
        where_clause, values = self._build_where_clause(where)
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        values = list(updates.values()) + values
        self._execute_with_retry(sql, values)

    def _build_where_clause(self, where):
        """Builds SQL WHERE clause and associated values."""
        clause, values = [], []
        for k, v in where.items():
            if v is None:
                clause.append(f"{k} IS NULL")
            else:
                clause.append(f"{k}=?")
                values.append(v)
        return ' AND '.join(clause), values

    def _execute_with_retry(self, sql, values, retries=5, delay=0.1):
        """Executes SQL with retry logic for locked DB."""
        for attempt in range(retries):
            try:
                self.cursor.execute(sql, values)
                self.conn.commit()
                return self.cursor
            except sqlite3.OperationalError as e:
                if "database is locked" in str(e):
                    self.logger.warning(f"[Execution_Monitor] DB locked. Retrying in {delay*(attempt+1):.2f}s...")
                    time.sleep(delay * (attempt + 1))
                else:
                    self.logger.exception(f"[Execution_Monitor] SQL error: {e}")
                    raise
        raise Exception("SQLite write failed after retries")

    def run_section(self, section_name, func):
        """Times a section automatically and records it to the DB."""
        self.current_section = section_name
        self._insert(
            "section_executions",
            {
                "execution_id": self.execution_id,
                "section_name": section_name,
                "start_ts": self._now()
            }
        )
        self.logger.info(f'[Execution_Monitor] Section "{section_name}" started.')
        try:
            return func()
        finally:
            self._update(
                "section_executions",
                {"end_ts": self._now()},
                {
                    "execution_id": self.execution_id,
                    "section_name": section_name,
                    "end_ts": None
                }
            )
            self.logger.info(f'[Execution_Monitor] Section "{section_name}" ended.')
            self.current_section = None

    def finalize_script_db_record(self, end_ts=None):
        """Finalizes the script execution DB entry and closes DB."""
        updates = {"end_ts": end_ts or self._now()}
        if self.execution_failed:
            updates["execution_failed"] = 1
        try:
            self._update("script_executions", updates, {"execution_id": self.execution_id})
            self.logger.debug(f"[Execution_Monitor] Finalized script record with updates: {updates}")
        finally:
            self.conn.close()
            self.logger.debug(f"[Execution_Monitor] Closed DB connection.")
