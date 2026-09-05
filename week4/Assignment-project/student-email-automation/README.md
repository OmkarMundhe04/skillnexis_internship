# Student Email Automation Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)]()

A robust, production-ready Python automation tool that reads student details from a CSV file, generates personalized multi-part emails (Plain-text + Responsive HTML), and dispatches them via SMTP (TLS). Designed with safe dry-run simulation by default, per-recipient error recovery, rate limiting, and comprehensive audit logging.

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Installation & Setup](#installation--setup)
  - [1. Clone / Open Directory](#1-clone--open-directory)
  - [2. Create a Virtual Environment](#2-create-a-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
- [Configuration](#configuration)
  - [Environment Variables (.env)](#environment-variables-env)
  - [Google Account (App Password) Setup](#google-account-app-password-setup)
- [Recipient Data Management (CSV)](#recipient-data-management-csv)
- [Usage Guide](#usage-guide)
  - [1. Safe Simulation (Dry-Run Mode)](#1-safe-simulation-dry-run-mode)
  - [2. Live Dispatch (Live Mode)](#2-live-dispatch-live-mode)
  - [3. Command-Line Arguments](#3-command-line-arguments)
- [Understanding Delivery Logs](#understanding-delivery-logs)
- [Customizing the Email Template](#customizing-the-email-template)
- [Automated Testing](#automated-testing)
- [Troubleshooting & FAQ](#troubleshooting--faq)
- [Security Best Practices](#security-best-practices)
- [Future Roadmap](#future-roadmap)
- [License](#license)

---

## Overview

Educational institutions, placement cells, and student organizations frequently need to send personalized announcements (e.g., campus placement updates, test schedules, or orientation details) to hundreds of students.

Instead of unreliable manual emailing or basic classroom scripts that crash on the first invalid email, this tool provides:
- **Resilience**: A single bad email address or connection hiccup does not abort the entire batch.
- **Safety First**: Dry-run mode is enabled by default so no email is ever sent by accident.
- **Modern Standards**: Delivers clean multi-part MIME messages with responsive HTML fallback to plain-text.
- **Audit Trail**: Every outcome (`SENT`, `FAILED`, `DRY_RUN`, `SKIPPED`) is logged with timestamps and error details.

---

## Key Features

- **Personalized Content**: Dynamically injects student names into email subjects, plain-text bodies, and HTML templates.
- **Multi-Part Email Delivery**: Generates RFC-compliant `EmailMessage` objects with synchronized plain-text and rich responsive HTML components.
- **Data Validation & Sanitization**:
  - Handles UTF-8 and UTF-8-BOM encoded CSV files seamlessly.
  - Automatically trims surrounding whitespace on headers and cell values.
  - Validates email formats using RFC-compliant regular expressions.
  - Rejects incomplete or malformed records cleanly without crashing.
- **Default Safe Dry-Run Mode**: Allows testing campaign logic, template rendering, and CSV parsing with zero SMTP connection risk.
- **Rate-Limiting / Delay**: Configurable inter-message delay (`DELAY_SECONDS`) to respect provider sending thresholds and avoid anti-spam throttling.
- **Per-Recipient Error Isolation**: Individual recipient failures are recorded in the log while the batch continues to process remaining students.
- **Secure Secret Management**: Reads SMTP credentials strictly from environment variables via `.env`. No hardcoded credentials.
- **Cross-Platform & Windows-Optimized**: Built with `pathlib.Path` and UTF-8 console streams to eliminate Windows encoding quirks and path separator bugs.
- **Comprehensive CLI Interface**: Supports command-line flag overrides (`--dry-run`, `--live`, `--csv`, `--template`, `--delay`).

---

## Project Structure

```text
student-email-automation/
├── data/
│   └── students.csv                # Recipient dataset (name, email)
├── templates/
│   └── placement_email.html        # Responsive HTML email template
├── logs/
│   └── email_log.csv               # Audit trail of all dispatches and simulations
├── tests/
│   └── test_email_automation.py    # Unit & integration test suite (10 test cases)
├── email_automation.py             # Core automation script & CLI entrypoint
├── start.bat                       # Interactive Windows launcher (Double-click to run)
├── .env.example                    # Template for environment configuration
├── .gitignore                      # Excludes credentials, caches, logs, and venvs
├── requirements.txt                # Project dependencies (python-dotenv)
└── README.md                       # Comprehensive documentation
```

---

## Requirements

- **Python**: Version 3.9 or higher (tested on Python 3.13)
- **Operating System**: Windows 10/11, macOS, or Linux
- **SMTP Account**: Any standard SMTP provider (Gmail, Outlook/Office365, Amazon SES, SendGrid, Mailgun, or institutional SMTP).

---

## Installation & Setup

### 1. Clone / Open Directory

Open your terminal or command prompt and navigate to the project root:

```bash
cd student-email-automation
```

### 2. Create a Virtual Environment

It is recommended to use an isolated virtual environment:

**On Windows (Command Prompt):**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
```

**On Windows (PowerShell):**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

> *Tip for PowerShell:* If script execution is restricted on your machine, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first.

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies

Install the minimal required package (`python-dotenv`):

```bash
pip install -r requirements.txt
```

---

## Configuration

### Environment Variables (.env)

Create your local `.env` file by copying `.env.example`:

**On Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

**On Windows (CMD):**
```cmd
copy .env.example .env
```

**On macOS / Linux:**
```bash
cp .env.example .env
```

Open `.env` in any text editor and fill in your settings:

```env
# Sender credentials
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_character_app_password

# SMTP Server details (Gmail default shown)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587

# Safe simulation mode (keep 'true' during initial testing)
DRY_RUN=true

# Delay in seconds between consecutive emails
DELAY_SECONDS=2
```

### Google Account (App Password) Setup

If you are using a Gmail or Google Workspace account, Google does not allow sending via your standard account password. You must generate a **16-character App Password**:

1. Log into your Google Account and navigate to [Google Account Security](https://myaccount.google.com/security).
2. Ensure **2-Step Verification** is turned **ON**.
3. Search for or navigate to **App Passwords** ([https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)).
4. Enter an app name (e.g., `Student Email Automation`) and click **Create**.
5. Google will display a 16-character passcode (e.g. `abcd efgh ijkl mnop`).
6. Copy this code into your `.env` file for `SENDER_PASSWORD` (spaces are ignored or can be removed).

---

## Recipient Data Management (CSV)

The recipient list is maintained in `data/students.csv`.

### Expected Format

```csv
name,email
Rahul Sharma,rahul@example.com
Priya Patil,priya@example.com
Amit Joshi,amit@example.com
```

### Validation Rules

- **Header columns**: Must include `name` and `email` (case-insensitive, whitespace-tolerant).
- **Whitespace**: Leading and trailing whitespace around names, headers, and emails is automatically trimmed.
- **UTF-8 / BOM**: Files saved with or without UTF-8 BOM are supported seamlessly.
- **Invalid Records**:
  - Missing name: Skipped and logged as `SKIPPED`.
  - Missing email: Skipped and logged as `SKIPPED`.
  - Malformed email address: Skipped and logged as `SKIPPED`.
  - Empty rows: Silently discarded or skipped without interrupting valid rows.

---

## Usage Guide

### ⚡ Quick Launch on Windows (start.bat)

The easiest way to run the project on Windows is using the included **`start.bat`** script. Simply double-click **`start.bat`** in Windows File Explorer, or run:

```cmd
start.bat
```

This interactive launcher will:
1. Automatically activate `.venv` or `venv` if available.
2. Verify Python is installed on your PATH.
3. Present a menu to run **Dry-Run Mode**, **Live Send Mode**, the **Automated Test Suite**, or **Install Requirements**.
4. Keep the terminal window open until you press a key so you can read results comfortably.

---

### 1. Safe Simulation (Dry-Run Mode)

By default, the tool operates in **DRY_RUN** mode. This allows you to verify recipient parsing and examine rendered subjects without connecting to the network or sending real emails:

```bash
python email_automation.py
```

**Sample Terminal Output:**

```text
========================================
     STUDENT EMAIL AUTOMATION TOOL      
========================================
Mode      : DRY RUN (safe simulation)
CSV File  : C:\...\student-email-automation\data\students.csv
Template  : C:\...\student-email-automation\templates\placement_email.html
Log File  : C:\...\student-email-automation\logs\email_log.csv
----------------------------------------
Loading students...
Valid recipients : 3
Invalid records  : 0

--- Dry Run Previews ---
[DRY RUN] Would send to: Rahul Sharma <rahul@example.com>
          Subject: Placement Drive Update – Rahul Sharma
[DRY RUN] Would send to: Priya Patil <priya@example.com>
          Subject: Placement Drive Update – Priya Patil
[DRY RUN] Would send to: Amit Joshi <amit@example.com>
          Subject: Placement Drive Update – Amit Joshi

========================================
                SUMMARY                 
========================================
Processed : 3
Sent      : 0
Failed    : 0
Skipped   : 0
Log File  : C:\...\student-email-automation\logs\email_log.csv
========================================
```

### 2. Live Dispatch (Live Mode)

Once you have verified the preview and configured your credentials in `.env`, execute real sending using either method:

**Option A: Using the `--live` command-line flag:**
```bash
python email_automation.py --live
```

**Option B: Setting `DRY_RUN=false` in `.env`:**
```env
DRY_RUN=false
```
Then run:
```bash
python email_automation.py
```

### 3. Command-Line Arguments

The application accepts helpful CLI options to override defaults dynamically without altering code or `.env`:

| Flag | Description | Example |
| :--- | :--- | :--- |
| `--dry-run` | Force safe simulation mode | `python email_automation.py --dry-run` |
| `--live` | Force live SMTP sending | `python email_automation.py --live` |
| `--csv <path>` | Specify custom student dataset | `python email_automation.py --csv data/batch2026.csv` |
| `--template <path>` | Specify custom HTML template | `python email_automation.py --template templates/exam.html` |
| `--delay <seconds>` | Set delay between consecutive emails | `python email_automation.py --live --delay 3.5` |
| `-h`, `--help` | Show usage manual | `python email_automation.py --help` |

---

## Understanding Delivery Logs

All simulation and delivery events are recorded in `logs/email_log.csv`.

### Log Schema

| Column | Description |
| :--- | :--- |
| `name` | Student's full name |
| `email` | Student's email address |
| `status` | Delivery status: `SENT`, `FAILED`, `DRY_RUN`, or `SKIPPED` |
| `details` | Success confirmation, error description, or skip reason |

### Example Log Entries

```csv
name,email,status,details
Rahul Sharma,rahul@example.com,DRY_RUN,Simulated delivery (DRY_RUN mode active)
Priya Patil,priya@example.com,SENT,Successfully delivered
Amit Joshi,amit@invalid-domain,SKIPPED,Invalid email format 'amit@invalid-domain'
Neha Gupta,neha@example.com,FAILED,SMTPServerDisconnected: Connection reset by peer
```

---

## Customizing the Email Template

The HTML template is located at `templates/placement_email.html`.

- **Personalization Token**: Use `{{name}}` anywhere inside the HTML. The tool replaces this token dynamically with each student's name.
- **Design Structure**:
  - Pre-styled responsive table container compatible with Gmail, Outlook, Apple Mail, and mobile clients.
  - Professional navy header banner with Placement Cell branding.
  - Action callout box for deadlines and document checklists.
  - Clean formal sign-off.
- **Plain-Text Alternative**: The plain-text version in `create_message()` is automatically generated to ensure deliverability to clients that disable HTML.

---

## Automated Testing

The project includes an automated test suite implemented with Python's standard `unittest` framework and mock isolation. It executes completely offline without external services.

Run the test suite with:

```bash
python -m unittest discover tests
```

### Scenarios Covered by Tests

1. **TEST 1**: Valid CSV + `DRY_RUN=true` verification.
2. **TEST 2**: Rejection and logging of invalid emails, missing names, and empty rows.
3. **TEST 3**: Clean error handling when the CSV file is missing (exit code 1, no traceback).
4. **TEST 4**: Clean validation error when attempting live mode without credentials.
5. **TEST 5**: Verifies `smtplib.SMTP` is strictly never called in dry-run mode.
6. **TEST 6**: Simulates an individual recipient failure to ensure subsequent emails continue sending.
7. **TEST 7**: Clean error handling when the HTML template is missing.
8. **TEST 8**: Verifies parsing of CSV files with UTF-8 BOM and irregular whitespace.
9. **TEST 9**: Verifies CLI argument precedence (`--dry-run`, `--live`, `--csv`, etc.).
10. **TEST 10**: Verifies `EmailMessage` structure, dynamic subject formatting, and HTML body substitution.

---

## Troubleshooting & FAQ

### 1. `[EXECUTION ERROR] Missing SMTP credentials!`
- **Cause**: Running in `--live` mode without configuring `SENDER_EMAIL` or `SENDER_PASSWORD`.
- **Fix**: Copy `.env.example` to `.env` and fill in your sender email and password.

### 2. `SMTPAuthenticationError: (535, '5.7.8 Username and Password not accepted')`
- **Cause**: Using your standard Google account password or having 2-Step Verification disabled.
- **Fix**: Follow the [Google Account App Password Setup](#google-account-app-password-setup) guide to generate a 16-character App Password.

### 3. `[DATA ERROR] CSV file not found at: ...`
- **Cause**: Specified CSV path does not exist.
- **Fix**: Check spelling or verify that `data/students.csv` exists.

### 4. `[TEMPLATE ERROR] Email template file not found at: ...`
- **Cause**: HTML template path is incorrect.
- **Fix**: Ensure `templates/placement_email.html` exists or provide the path via `--template`.

---

## Security Best Practices

1. **Never Commit `.env`**: `.gitignore` is configured to exclude `.env`. Keep credentials stored locally only.
2. **Use App Passwords**: Never use your primary email account password. Generate a scoped App Password that can be revoked at any time.
3. **No Secrets in Logs**: The logger strips passwords and sensitive tokens; log files store only recipient status and diagnostic messages.
4. **Legitimate Use Only**: This tool is designed strictly for authorized, educational, and organizational communications. Comply with applicable anti-spam laws (CAN-SPAM, GDPR) and provider rate limits.

---

## Future Roadmap

- [ ] Attachment support (e.g., personalized PDF offer letters or brochures).
- [ ] Multi-template selection based on student department or branch.
- [ ] Failed recipient retry mechanism (`--retry-failed`).
- [ ] Lightweight web UI / FastAPI dashboard for non-technical coordinators.

---

## License

This project is licensed under the MIT License - see the LICENSE file for details.
