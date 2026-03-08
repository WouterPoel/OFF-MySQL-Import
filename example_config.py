# Copy this file to config.py and edit as needed.

MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = ""
MYSQL_DATABASE = "your_database"

TABLE_NAME = "openfoodfacts_products"

DELIMITER = "\t"          # Open Food Facts export is usually tab-separated
ENCODING = "utf-8"
BATCH_SIZE = 2000

IMPORT_FROM_FOLDER = True
IMPORT_FOLDER = r"C:\Users\John\Desktop\export"
FILE_PATTERN = "*.csv"

FILES_TO_IMPORT = [
    r"C:\Users\John\User\export\en.openfoodfacts.org.products.csv",
]

CREATE_TABLE_IF_NOT_EXISTS = True
TRUNCATE_TABLE_BEFORE_IMPORT = False

SET_SESSION_SQL_MODE = False
DISABLE_FOREIGN_KEY_CHECKS = True
DISABLE_UNIQUE_CHECKS = True

ENABLE_RESUME = True
STATE_FILE = "import_state.json"
ERROR_LOG_FILE = "import_errors.log"
PROGRESS_PRINT_EVERY_SECONDS = 1
