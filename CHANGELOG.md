# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

### Guiding Principles
- Changelogs are for humans, not machines.
- There should be an entry for every single version.
- The same types of changes should be grouped.
- Versions and sections should be linkable.
- The latest version comes first.
- The release date of each version is displayed.
- Mention whether you follow Semantic Versioning.

### Types of changes
- **Added** for new features.
- **Changed** for changes in existing functionality.
- **Deprecated** for soon-to-be removed features.
- **Removed** for now removed features.
- **Fixed** for any bug fixes.
- **Security** in case of vulnerabilities.

## [1.0.0] - 2026-03-08

### Added
- Initial public release of the **Open Food Facts → MySQL Importer**.
- High-performance Python importer for large Open Food Facts datasets.
- Automatic MySQL table creation from CSV header.
- Support for importing **multiple CSV files from a folder**.
- Multi-row batch insert system for improved import speed.
- Resume support using `import_state.json` to continue interrupted imports.
- Error logging to `import_errors.log`.
- Column name sanitization to generate valid MySQL column names.
- Automatic normalization of rows to match header length.
- Automatic handling of empty values (`"" → NULL`).
- Configurable batch size for performance tuning.
- Example configuration file (`example_config.py`).
- GitHub-ready project structure.
- Full project documentation (`README.md`).
- Implemented **multi-row SQL insert batching** for faster imports.
- Disabled MySQL `FOREIGN_KEY_CHECKS` and `UNIQUE_CHECKS` during import to reduce overhead.
- Added configurable batch commit intervals.
- Achieved typical import speeds of **50k–150k rows per minute** depending on hardware.

### Fixed
- Python CSV parser limit causing: ```field larger than field limit (131072)``` by dynamically increasing the CSV field size limit.

## [0.1.0] - 2026-03-07

### Added
- Initial prototype importer.
- Basic CSV reader using Python `csv` module.
- Single-file import support.
- Basic MySQL insert logic.
- Preliminary error handling.

### Changed
- Refactored code structure to support modular helper functions.
- Added configuration section for database credentials and import paths.

## [0.0.1] - 2026-03-07

### Added
- Proof-of-concept script to test importing Open Food Facts dataset into MySQL.
- Basic CSV parsing and row insertion.