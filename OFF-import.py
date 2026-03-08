import csv
import json
import re
import sys
import time
from pathlib import Path

import pymysql


# =========================================================
# STRONG CSV FIELD LIMIT FIX
# =========================================================
def set_max_csv_field_size():
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            return max_int
        except OverflowError:
            max_int = int(max_int / 10)


CSV_FIELD_LIMIT = set_max_csv_field_size()
print(f"CSV field size limit set to: {CSV_FIELD_LIMIT}")
print(f"Using Python: {sys.executable}")


# =========================================================
# CONFIG
# =========================================================
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "your_database_name"

TABLE_NAME = "your_table_name"

DELIMITER = "\t"          # Open Food Facts export is usually tab-separated
ENCODING = "utf-8"
BATCH_SIZE = 2000         # Try 2000 first. Increase later if stable.

# ---------------------------------------------------------
# OPTION A: import all matching files from a folder
# ---------------------------------------------------------
IMPORT_FROM_FOLDER = True
IMPORT_FOLDER = r"C:\Users\John\Desktop\export"
FILE_PATTERN = "*.csv"    # Change to *.txt if needed

# ---------------------------------------------------------
# OPTION B: manually specify files
# Used only if IMPORT_FROM_FOLDER = False
# ---------------------------------------------------------
FILES_TO_IMPORT = [
    r"C:\Users\John\Desktop\export\en.openfoodfacts.org.products.csv",
    # r"C:\Users\John\Desktop\export\file2.csv",
]

# ---------------------------------------------------------
# TABLE HANDLING
# ---------------------------------------------------------
CREATE_TABLE_IF_NOT_EXISTS = True
TRUNCATE_TABLE_BEFORE_IMPORT = False

# ---------------------------------------------------------
# MYSQL IMPORT OPTIMIZATION
# ---------------------------------------------------------
SET_SESSION_SQL_MODE = False
DISABLE_FOREIGN_KEY_CHECKS = True
DISABLE_UNIQUE_CHECKS = True

# ---------------------------------------------------------
# RESUME / LOGGING
# ---------------------------------------------------------
ENABLE_RESUME = True
STATE_FILE = "import_state.json"
ERROR_LOG_FILE = "import_errors.log"
PROGRESS_PRINT_EVERY_SECONDS = 1


# =========================================================
# HELPERS
# =========================================================
def sanitize_column_name(name: str, used_names: set) -> str:
    name = name.strip().lower()
    name = re.sub(r"[^\w]+", "_", name)
    name = re.sub(r"_+", "_", name).strip("_")

    if not name:
        name = "col"

    if name[0].isdigit():
        name = f"c_{name}"

    original = name
    counter = 1
    while name in used_names:
        name = f"{original}_{counter}"
        counter += 1

    used_names.add(name)
    return name


def normalize_row(row, expected_len):
    if len(row) < expected_len:
        row = row + [None] * (expected_len - len(row))
    elif len(row) > expected_len:
        row = row[:expected_len]

    normalized = []
    for value in row:
        if value == "":
            normalized.append(None)
        else:
            normalized.append(value)
    return normalized


def create_table(cursor, table_name, columns):
    cols_sql = ",\n".join([f"`{col}` LONGTEXT NULL" for col in columns])
    sql = f"""
    CREATE TABLE IF NOT EXISTS `{table_name}` (
        `id_import` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
        {cols_sql},
        PRIMARY KEY (`id_import`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    cursor.execute(sql)


def truncate_table(cursor, table_name):
    cursor.execute(f"TRUNCATE TABLE `{table_name}`")


def get_files_to_import():
    if IMPORT_FROM_FOLDER:
        folder = Path(IMPORT_FOLDER)
        if not folder.exists():
            print(f"ERROR: Import folder does not exist: {folder}")
            sys.exit(1)

        files = sorted([p for p in folder.glob(FILE_PATTERN) if p.is_file()])
    else:
        files = [Path(f) for f in FILES_TO_IMPORT if Path(f).is_file()]

    if not files:
        print("ERROR: No files found to import.")
        sys.exit(1)

    return files


def read_and_prepare_header(file_path: Path):
    with open(file_path, "r", encoding=ENCODING, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=DELIMITER, quotechar='"')
        try:
            raw_header = next(reader)
        except StopIteration:
            raise ValueError(f"File is empty: {file_path}")

    used_names = set()
    sanitized = [sanitize_column_name(col, used_names) for col in raw_header]
    return raw_header, sanitized


def build_multirow_insert_sql(table_name, columns, row_count):
    col_list = ", ".join([f"`{c}`" for c in columns])
    single_row_placeholders = "(" + ", ".join(["%s"] * len(columns)) + ")"
    all_placeholders = ", ".join([single_row_placeholders] * row_count)
    return f"INSERT INTO `{table_name}` ({col_list}) VALUES {all_placeholders}"


def flatten_batch(batch):
    flat = []
    for row in batch:
        flat.extend(row)
    return flat


def optimize_session(cursor):
    if SET_SESSION_SQL_MODE:
        cursor.execute("SET SESSION sql_mode = ''")

    if DISABLE_FOREIGN_KEY_CHECKS:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")

    if DISABLE_UNIQUE_CHECKS:
        cursor.execute("SET UNIQUE_CHECKS = 0")


def restore_session(cursor):
    if DISABLE_FOREIGN_KEY_CHECKS:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")

    if DISABLE_UNIQUE_CHECKS:
        cursor.execute("SET UNIQUE_CHECKS = 1")


def insert_batch(cursor, table_name, columns, batch):
    if not batch:
        return

    sql = build_multirow_insert_sql(table_name, columns, len(batch))
    params = flatten_batch(batch)
    cursor.execute(sql, params)


def load_state():
    if not ENABLE_RESUME:
        return {}

    state_path = Path(STATE_FILE)
    if not state_path.exists():
        return {}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    if not ENABLE_RESUME:
        return

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def clear_state():
    if not ENABLE_RESUME:
        return

    state_path = Path(STATE_FILE)
    if state_path.exists():
        state_path.unlink()


def log_error(message):
    with open(ERROR_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(message + "\n")


def get_resume_line(state, file_path: Path):
    return int(state.get(str(file_path), 2))


def set_resume_line(state, file_path: Path, next_line_number: int):
    state[str(file_path)] = next_line_number
    save_state(state)


def mark_file_done(state, file_path: Path):
    state[str(file_path)] = "done"
    save_state(state)


def is_file_done(state, file_path: Path):
    return state.get(str(file_path)) == "done"


def import_single_file(cursor, conn, file_path: Path, table_name: str, columns, state):
    expected_len = len(columns)
    imported = 0
    skipped = 0
    batch = []
    last_print = time.time()

    resume_line = get_resume_line(state, file_path)

    with open(file_path, "r", encoding=ENCODING, errors="replace", newline="") as f:
        reader = csv.reader(f, delimiter=DELIMITER, quotechar='"')

        # Skip header
        try:
            next(reader)
        except StopIteration:
            return 0, 0

        # Move forward to resume line
        current_line = 2
        while current_line < resume_line:
            try:
                next(reader)
                current_line += 1
            except StopIteration:
                mark_file_done(state, file_path)
                return 0, 0

        print(f"  Resuming from line {current_line:,} in {file_path.name}")

        last_line_number = current_line - 1

        for line_number, row in enumerate(reader, start=current_line):
            last_line_number = line_number
            try:
                normalized = normalize_row(row, expected_len)
                batch.append(normalized)

                if len(batch) >= BATCH_SIZE:
                    insert_batch(cursor, table_name, columns, batch)
                    conn.commit()
                    imported += len(batch)
                    batch = []

                    # Save resume point after successful commit
                    set_resume_line(state, file_path, line_number + 1)

                    now = time.time()
                    if now - last_print >= PROGRESS_PRINT_EVERY_SECONDS:
                        print(
                            f"  Imported {imported:,} rows from {file_path.name} "
                            f"(current line {line_number:,})",
                            end="\r"
                        )
                        last_print = now

            except Exception as row_error:
                skipped += 1
                msg = f"[{file_path.name}] Skipped row {line_number}: {row_error}"
                print(f"\n  {msg}")
                log_error(msg)
                set_resume_line(state, file_path, line_number + 1)

        if batch:
            insert_batch(cursor, table_name, columns, batch)
            conn.commit()
            imported += len(batch)
            set_resume_line(state, file_path, last_line_number + 1)

    mark_file_done(state, file_path)
    print(f"\n  Finished {file_path.name}: {imported:,} imported, {skipped:,} skipped")
    return imported, skipped


# =========================================================
# MAIN
# =========================================================
def main():
    start_time = time.time()
    state = load_state()

    files = get_files_to_import()
    print("Files to import:")
    for f in files:
        done_marker = " [DONE]" if is_file_done(state, f) else ""
        print(f" - {f}{done_marker}")

    print("\nConnecting to MySQL...")
    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DATABASE,
        charset="utf8mb4",
        autocommit=False,
        cursorclass=pymysql.cursors.Cursor,
    )

    total_imported = 0
    total_skipped = 0
    files_imported = 0
    files_skipped = 0

    try:
        with conn.cursor() as cursor:
            optimize_session(cursor)
            conn.commit()

            # Build schema from first file
            first_file = files[0]
            raw_header, columns = read_and_prepare_header(first_file)

            print(f"\nHeader source file: {first_file.name}")
            print(f"Detected {len(columns)} columns.")

            if CREATE_TABLE_IF_NOT_EXISTS:
                print("Creating table if needed...")
                create_table(cursor, TABLE_NAME, columns)
                conn.commit()

            if TRUNCATE_TABLE_BEFORE_IMPORT:
                print("Truncating table before import...")
                truncate_table(cursor, TABLE_NAME)
                conn.commit()
                state = {}
                save_state(state)

            expected_header = raw_header

            # Import all files
            for file_path in files:
                if is_file_done(state, file_path):
                    print(f"\nSkipping {file_path.name}: already marked done in resume state.")
                    continue

                print(f"\nProcessing: {file_path.name}")

                try:
                    current_raw_header, _ = read_and_prepare_header(file_path)

                    if current_raw_header != expected_header:
                        msg = f"Skipped {file_path.name}: header does not match first file."
                        print(f"  {msg}")
                        log_error(msg)
                        files_skipped += 1
                        continue

                    imported, skipped = import_single_file(
                        cursor, conn, file_path, TABLE_NAME, columns, state
                    )
                    total_imported += imported
                    total_skipped += skipped
                    files_imported += 1

                except Exception as file_error:
                    conn.rollback()
                    msg = f"ERROR in file {file_path.name}: {file_error}"
                    print(f"  {msg}")
                    log_error(msg)
                    files_skipped += 1

            restore_session(cursor)
            conn.commit()

    except Exception as e:
        conn.rollback()
        msg = f"FATAL ERROR: {e}"
        print(f"\n{msg}")
        log_error(msg)
        raise

    finally:
        conn.close()

    elapsed = time.time() - start_time

    print("\n=========================================================")
    print("IMPORT FINISHED")
    print("=========================================================")
    print(f"Files imported successfully : {files_imported}")
    print(f"Files skipped               : {files_skipped}")
    print(f"Total rows imported         : {total_imported:,}")
    print(f"Total rows skipped          : {total_skipped:,}")
    print(f"Time taken                  : {elapsed:.2f} seconds")
    print(f"Resume state file           : {Path(STATE_FILE).resolve()}")
    print(f"Error log file              : {Path(ERROR_LOG_FILE).resolve()}")


if __name__ == "__main__":
    main()