# Bib File Sorting and Cleaning Tool

## Overview

This Python script is designed to automate the process of organizing and cleaning bibliography files (`.bib`) used in LaTeX projects. It identifies and extracts citations referenced in `.tex` files, matches them with entries in `.bib` files, checks for required fields based on the specified conference format, and outputs two separate files: 

1. `used_sorted_references.bib`: A sorted `.bib` file containing all entries used in the LaTeX project.
2. `unused_sorted_references.bib`: A sorted `.bib` file containing all unused entries from the original bibliography.

Additionally, the script:
- Detects discrepancies in `booktitle` and `journal` naming.
- Standardizes capitalization for titles and authors.
- Reports missing required fields.
- Provides an organized summary of unique fields, book titles, publishers, and journals.

## Features
- **Supports multiple conferences**: Adheres to specific bibliography formats (e.g., CVPR, CHI).
- **Capitalization correction**: Standardizes title and author name formats.
- **Duplicate detection**: Identifies and handles duplicate entries in `.bib` files.
- **Separation of used and unused entries**: Facilitates cleaner `.bib` files for final submissions.
- **Discrepancy reporting**: Highlights inconsistencies in `booktitle` or `journal` fields.

---

## Usage

### Prerequisites
1. **Python 3.x** installed on your system.
2. Required Python libraries: `os`, `re`, `argparse`, `bibtexparser`, `collections`.

Install dependencies using:
```bash
pip install bibtexparser
```

### How to Run

1. **Organize your project directory**:
   - Place all `.tex` files in a single directory.
   - Ensure your `.bib` file(s) are in the same directory or subdirectory. The `.bib` file should match the name specified with `--bib_file`.

2. **Run the script**:
   ```bash
   python script_name.py --project_directory <path_to_project> --bib_file <bib_filename> --conference <conference_name>
   ```
   Replace placeholders with:
   - `<path_to_project>`: Path to the directory containing `.tex` and `.bib` files.
   - `<bib_filename>`: Name of the `.bib` file(s) (default: `reference.bib`).
   - `<conference_name>`: Conference format to follow (e.g., `CVPR`, `CHI`).

   Example:
   ```bash
   python script_name.py --project_directory projects/my_paper --bib_file reference.bib --conference CVPR
   ```

3. **Output Files**:
   - `used_sorted_references.bib`: Contains all cited entries.
   - `unused_sorted_references.bib`: Contains entries not cited in `.tex` files.
   - Reports on discrepancies and missing fields are embedded as comments in these files.

---

## Key Functionalities

- **Citation Extraction**: Parses `.tex` files for citation commands like `\cite{...}` and collects all cited keys.
- **Bibliography Parsing**: Reads and processes `.bib` files to find matching entries for the cited keys.
- **Sorting and Formatting**: Groups entries by type (e.g., `article`, `inproceedings`) and sorts them alphabetically by title.
- **Validation and Reporting**:
  - Validates entries against required fields based on the conference format.
  - Highlights missing fields, discrepancies, and duplicate entries.

---

## Customization

- **Conference Format**: To add or modify conference-specific required fields, update the `conference_format_mapping` dictionary in the script.

---

## Troubleshooting

- **Duplicate Entry Warning**: The script skips duplicate entries in `.bib` files but logs a warning.
- **Missing Fields**: Reports are included in the output `.bib` files as comments. Check and complete these fields manually if necessary.