# Open Food Facts MySQL Import

## What is Open Food Facts? 
**Open Food Facts** is an awesome project that provides a database of food products with ingredients, allergens, nutrition facts and all the tidbits of information they can find on product labels. 

**Open Food Facts** is a non-profit association of volunteers. 25.000+ contributors like you have added 4 million products from 150 countries using our cross-platform Flutter app for Android & iPhone or their camera to scan barcodes and upload pictures of products and their labels.

Data about food is of public interest and has to be open. The complete database is published as open data and can be reused by anyone and for any use. Check-out the cool reuses or make your own!

You can check out the project at: [Open Food Facts](https://world.openfoodfacts.org/) and find their
GitHub at: [Open Food Facts GitHub](https://github.com/openfoodfacts)

## Key features of the script

- multi-file CSV import  
- automatic MySQL schema creation  
- batch inserts for speed  
- resume after interruption  
- corrupted row handling  
- error logging  
- extremely large field support  
- scalable to millions of rows  

## Open Food Facts MySQL Import script

### 1. CSV / Data Handling Functions

```sanitize_column_name(name, used_names)```

**Purpose:**

Converts a column name from the CSV header into a safe MySQL column name.

#### What it does:
- lowercases the name
- removes invalid characters
- replaces spaces with _
- ensures uniqueness
- prevents names starting with numbers

**Example:**

```"Product Name (EN)" → product_name_en```

```normalize_row(row, expected_len)```

**Purpose:**

Ensures every row has the same number of fields as the header.

**What it does:**
- pads missing columns with None
- trims extra columns
- converts empty strings "" to NULL

**Example:**

```["apple", "fruit"] ``` 

```→ ["apple", "fruit", None, None]```

### 2. Database Table Functions

```create_table(cursor, table_name, columns)```

**Purpose:**

Creates the MySQL table automatically if it doesn't exist.

**Important details:**
- every column becomes ```LONGTEXT```
- adds an auto-increment ```id_import```
- uses ```utf8mb4```

```truncate_table(cursor, table_name)```

**Purpose:**

Deletes all rows from the table.

**Used when:**

```TRUNCATE_TABLE_BEFORE_IMPORT = True```

### 3. File Handling Functions

**Purpose:**

Builds the list of files to import.

#### **Supports two modes:**

**Folder mode**

```IMPORT_FOLDER = ...```

```FILE_PATTERN = "*.csv"```

**Manual list mode**

```FILES_TO_IMPORT = [...]```

```read_and_prepare_header(file_path)```

**Purpose:**

Reads the first row (header) of the CSV file.

Returns:

```raw_header```

```sanitized_header```

The sanitized header becomes the MySQL column names.

### 4. SQL Insert Functions

```build_multirow_insert_sql(table_name, columns, row_count)```

**Purpose:**

Builds a multi-row INSERT statement.

Example generated SQL:

[
 [1,2],

 [3,4]
]

becomes:

```[1,2,3,4]```

```insert_batch(cursor, table_name, columns, batch)```

**Purpose:**

Executes the multi-row SQL insert.

**Steps:**
**1.** build SQL
**2.** flatten parameters
**3.** execute query

### 5. MySQL Performance Optimization Functions

**Purpose:**

Temporarily disables expensive MySQL checks to speed up imports.

Disables:

```FOREIGN_KEY_CHECKS```

```UNIQUE_CHECKS```

This significantly improves insert performance.

```restore_session(cursor)```

**Purpose:**

Restores MySQL settings after import.

### 6. Resume System Functions

The importer supports resuming if interrupted.

State stored in:

```import_state.json```

```load_state()```

**Purpose:**

Loads saved progress from the resume file.

**Example**

```
{
  "file1.csv": 45000,
  "file2.csv": "done"
}
```

```save_state(state)```

**Purpose:**

Writes updated resume progress to disk.

```clear_state()```

**Purpose:**

Deletes the resume state file for a fresh import.

```get_resume_line(state, file_path)```

**Purpose:**

Returns the line number where import should resume.

Default:

```2 (after header)```

```set_resume_line(state, file_path, next_line_number)```

**Purpose:**

Updates resume position after each committed batch.

```mark_file_done(state, file_path)```

**Purpose:**

Marks a file as fully imported

Ecample in state file:

```"file.csv": "done"```

```is_file_done(state, file_path)```

**Purpose:**

Checks if a file has already been completely imported.

Prevents duplicate imports.

### 7. Logging Functions

```log_error(message)```

**Purpose:**

Writes error messages to:

```import_errors.log```

Used for:
- corrupted rows
- parsing failures
- header mismatches
- file processing errors

### 8. Import Engine

```import_single_file(cursor, conn, file_path, table_name, columns, state)```

**Purpose:**

Core import function.

Steps performed:

**1.** open CSV file  
**2.** skip header  
**3.** resume from saved line  
**4.** read rows  
**5.** normalize rows  
**6.** batch insert  
**7.** commit transaction  
**8.** update resume state  
**9.** log row errors  
**10.** mark file complete  

### 9. Main Controller

```main()```

**Purpose:**

Coordinates the entire import process.

Steps:

**1.** load resume state  
**2.** discover files to import  
**3.** connect to MySQL  
**4.** create table if necessary  
**5.** iterate through files  
**6.** call import_single_file  
**7.** restore MySQL settings  
**8.** print final summary  

### 10. Program Entry Point

```if __name__ == "__main__":```

Runs:

```main()```

This ensures the script executes when run directly.

### Complete Function List

```
sanitize_column_name()  
normalize_row()  
create_table()  
truncate_table()  
get_files_to_import()  
read_and_prepare_header()  
build_multirow_insert_sql()  
flatten_batch()  
optimize_session()  
restore_session()  
insert_batch()  
load_state()  
save_state()  
clear_state()  
log_error()  
get_resume_line()  
set_resume_line()  
mark_file_done()  
is_file_done()  
import_single_file()  
main()  
```

**Total functions: 20**