# Open Food Facts → MySQL Importer (Python)

A high-performance Python importer for loading large Open Food Facts CSV/TXT datasets into MySQL.

Designed to handle **millions of rows**, extremely large fields, and long-running imports safely.

## Features

- Fast **multi-row batch inserts**
- Import **multiple CSV files from a folder**
- **Resume support** if the script stops
- Automatic **table creation**
- Smart **column name sanitization**
- **Error logging**
- **Progress tracking**
- Supports **very large fields**

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/openfoodfacts-mysql-importer.git
cd openfoodfacts-mysql-importer
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

Recommended Python version:

```text
Python 3.9+
```

## Configuration

Copy `example_config.py` to `config.py` and adjust the values.

```python
MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "your_database"

IMPORT_FOLDER = r"C:\Users\Wouter\Desktop\export"
FILE_PATTERN = "*.csv"
```

## Running the Importer

```bash
python import_openfoodfacts.py
```

## Example Output

```text
CSV field size limit set to: 9223372036854775807
Using Python: C:\Python311\python.exe

Files to import:
 - en.openfoodfacts.org.products.csv

Connecting to MySQL...

Header source file: en.openfoodfacts.org.products.csv
Detected 203 columns.

Processing: en.openfoodfacts.org.products.csv
  Resuming from line 2
  Imported 10,000 rows
  Imported 20,000 rows

Finished en.openfoodfacts.org.products.csv:
  3,425,621 imported
  24 skipped
```

## Performance Benchmarks

Example machine:

```text
CPU: Ryzen 9
RAM: 64GB
Storage: NVMe SSD
MySQL: 8.0
Python: 3.11
```

| Dataset Size | Rows | Import Time |
|---|---:|---:|
| 1 GB | ~900k | ~2 minutes |
| 3 GB | ~3M | ~6 minutes |
| 5 GB | ~5M | ~10 minutes |

Typical speed:

```text
50k – 150k rows / minute
```

Performance depends on disk speed, MySQL configuration, batch size, and RAM.

## Resume System

If the script stops, it can **resume automatically**.

The importer creates:

```text
import_state.json
```

Example:

```json
{
  "en.openfoodfacts.org.products.csv": 1850000
}
```

## Troubleshooting

### `field larger than field limit (131072)`

The script includes a stronger CSV field limit fix at startup.

### MySQL “packet too large”

Increase:

```text
max_allowed_packet = 1G
```

### Script stops halfway

Just run it again:

```bash
python import_openfoodfacts.py
```

It resumes automatically.

## Project Structure

```text
openfoodfacts-mysql-importer/
├── import_openfoodfacts.py
├── example_config.py
├── requirements.txt
├── .gitignore
└── README.md
```

## License

MIT
