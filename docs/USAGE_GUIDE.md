# SSN Redactor — Usage Guide

A step-by-step guide for non-technical users.

---

## What Does This Tool Do?

This tool scans your PDF and JPG files for Social Security Numbers (SSNs) and blacks them out automatically.

It looks for SSNs written like:
- `123-45-6789`
- `123 45 6789`
- `123456789`

It replaces them with: **XXX-XX-XXXX**

Your original files are **never changed**. Redacted copies are saved in a separate folder.

Everything runs on **your computer**. Nothing is sent online.

---

## How to Get the App

### If someone gave you `SSN Redactor.exe`

You're all set. Skip to **"Using the Desktop App"** below.

### If you need to build it yourself

1. Go to https://github.com/codepros100-dev/pdf-ssn-redactor
2. Click the green **Code** button, then click **Download ZIP**
3. Unzip the folder anywhere on your computer
4. Open the unzipped folder
5. Double-click **`setup.bat`**
6. Wait for it to finish (it installs everything automatically)
7. When it says **SUCCESS**, your app is at `dist\SSN Redactor.exe`

That's it. You can now copy `SSN Redactor.exe` anywhere and use it.

> **Note:** If you don't have Python installed, `setup.bat` will install it for you. You may need to close and re-run `setup.bat` one time after Python installs.

---

## Using the Desktop App

### Step 1: Open the App

Double-click `SSN Redactor.exe`. A window will appear.

### Step 2: Select Your Folder

Click **Browse** and navigate to the folder that contains your PDF or JPG files. Select it and click OK.

### Step 3: Start Redaction

Click **Start Redaction**. The progress bar will animate while files are being processed.

### Step 4: Check Results

When finished, the Results panel shows a report for each file. Your redacted files are in a new folder called `redacted_pdfs` inside your original folder.

---

## Using the Command Line

### Step 1: Open a Terminal

Press the **Windows key**, type `cmd`, and press Enter.

### Step 2: Navigate to the Tool

```
cd C:\path\to\pdf-ssn-redactor
```

### Step 3: Run the Tool

```
python -m ssn_redactor "C:\Users\YourName\Desktop\my_files"
```

Replace the path with the actual folder containing your files.

**Tips:**
- You can drag and drop a folder onto the terminal to paste its path.
- Wrap paths in quotes if they contain spaces.

### Step 4: Check Results

A report prints in the terminal. Redacted files are in `my_files\redacted_pdfs`.

---

## Common Questions

**Will it change my original files?**
No. Originals are never touched. Redacted copies go into the `redacted_pdfs` subfolder.

**What file types does it support?**
PDF files (`.pdf`) and image files (`.jpg`, `.jpeg`).

**What if my PDF is a scanned image (no selectable text)?**
The tool will report "no text layer" and skip that file. Convert it to JPG first, then run the tool on the JPG.

**I got an error about "Tesseract not found".**
Tesseract is needed for JPG files only. If you only have PDFs, this won't affect you. If you need JPG support, run `setup.bat` again or install Tesseract manually.

**Is my data sent anywhere?**
No. Everything runs 100% locally on your computer. No internet connection is needed.

**Can I use a custom output folder name?**
With the CLI, yes: `python -m ssn_redactor -o my_output "C:\path\to\folder"`

**I double-clicked `setup.bat` and it said Python is not recognized.**
Close the window, then double-click `setup.bat` again. The first run installs Python, but the terminal needs to restart to see it.
