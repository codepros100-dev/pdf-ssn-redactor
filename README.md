# SSN Redactor

A local command-line and desktop tool that scans PDF and JPG files for U.S. Social Security Numbers and produces permanently redacted copies.

**All processing runs 100% on your machine. No data is sent to any external service.**

## Features

- Detects SSNs in three formats: `123-45-6789`, `123 45 6789`, `123456789`
- Replaces detected SSNs with `XXX-XX-XXXX`
- Supports PDF files (text-layer extraction) and JPG/JPEG images (OCR via Tesseract)
- Preserves original files — redacted copies go to a separate output folder
- Two interfaces: GUI desktop app and CLI
- Prints a per-file redaction report

## Quick Start

### Option A: Desktop App (no terminal needed)

Double-click the executable:

```
dist\SSN Redactor\SSN Redactor.exe
```

1. Click **Browse** and select the folder with your PDFs/JPGs
2. Click **Start Redaction**
3. Check the `redacted_pdfs` subfolder for results

### Option B: Command Line

```bash
python -m ssn_redactor.cli "C:\path\to\your\folder"
```

Example output:

```
Processing 3 file(s) in C:\Users\you\Documents\invoices ...
  [1/3] invoice_01.pdf
  [2/3] scan_02.jpg
  [3/3] letter_03.pdf

========================================================
  SSN Redaction Report
========================================================
  invoice_01.pdf                           2 SSN(s) redacted
  scan_02.jpg                              1 SSN(s) redacted
  letter_03.pdf                            0 SSNs found
========================================================
  Total SSNs redacted: 3
  Output: C:\Users\you\Documents\invoices\redacted_pdfs
========================================================
```

### CLI Options

```
usage: ssn-redactor [-h] [-o OUTPUT_DIR] [-v] folder

positional arguments:
  folder                Path to a folder containing PDF and/or JPG files.

options:
  -h, --help            Show this help message and exit.
  -o, --output-dir      Name of the output subdirectory (default: "redacted_pdfs").
  -v, --version         Show version and exit.
```

## Installation & Building the Executable

### Easy Way (recommended)

One script does everything — installs Python, Tesseract, dependencies, and builds the exe:

```
git clone https://github.com/codepros100-dev/pdf-ssn-redactor.git
cd pdf-ssn-redactor
setup.bat
```

That's it. When it finishes, your exe is at `dist\SSN Redactor.exe`.

### Manual Way (step by step)

If you prefer to do it yourself:

**Step 1: Install Python 3.10 or newer**

Download from [python.org](https://www.python.org/downloads/) or run:
```
winget install Python.Python.3.12
```
During install, check **"Add Python to PATH"**.

**Step 2: Install Tesseract OCR** (only needed for JPG files)
```
winget install UB-Mannheim.TesseractOCR
```

**Step 3: Clone and enter the project**
```
git clone https://github.com/codepros100-dev/pdf-ssn-redactor.git
cd pdf-ssn-redactor
```

**Step 4: Install Python packages**
```
pip install -r requirements-dev.txt
```

**Step 5: Build the exe**
```
build.bat
```

The app is output to `dist\SSN Redactor\SSN Redactor.exe`. Copy the entire `SSN Redactor` folder anywhere to use it.

## Project Structure

```
pdf-ssn-redactor/
    ssn_redactor/
        __init__.py         Package metadata and version
        __main__.py         Enables `python -m ssn_redactor`
        engine.py           Core detection and redaction logic
        cli.py              Command-line interface
        gui.py              Desktop GUI (CustomTkinter)
    docs/
        USAGE_GUIDE.md      Step-by-step guide for non-technical users
    .gitignore
    setup.bat               One-click setup & build (installs everything)
    build.bat               Build script (if dependencies are already installed)
    LICENSE                 MIT
    README.md               This file
    requirements.txt        Runtime dependencies
    requirements-dev.txt    Build dependencies (adds PyInstaller)
```

## How It Works

1. **PDF files**: Text is extracted with [pdfplumber](https://github.com/jsvine/pdfplumber). SSNs are located using regex. [PyMuPDF](https://pymupdf.readthedocs.io/) applies permanent redaction annotations over each match.

2. **JPG files**: [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) extracts word-level bounding boxes. SSNs are detected in the OCR text, matched back to pixel coordinates, and covered with white rectangles plus placeholder text.

3. **Output**: Redacted copies are saved to a `redacted_pdfs` subfolder. Original files are never modified.

## Security Notes

- **No network calls.** The tool works fully offline. No telemetry, no analytics.
- **Original files are never modified** — only copies are written to the output folder.
- **SSN data is never logged.** Error messages are sanitized to prevent SSN leakage.
- **Input validation:**
  - Files over 500 MB are rejected.
  - PDFs over 10,000 pages are rejected.
  - Images over 100 megapixels are rejected (decompression bomb guard).
  - Output directory names are validated against path traversal attacks.
- **SSN regex** validates area/group/serial ranges per SSA rules (rejects 000, 666, 900-999 area numbers, 00 group, 0000 serial).

## License

MIT — see [LICENSE](LICENSE).
