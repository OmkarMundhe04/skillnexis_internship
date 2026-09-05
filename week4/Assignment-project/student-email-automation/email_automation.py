"""
Student Email Automation Tool
=============================
Automates sending personalized, multi-part (Plain-text & HTML) emails to students
from a CSV recipient list using Python's smtplib and EmailMessage.

Features:
- UTF-8 and UTF-8-BOM CSV parsing with whitespace stripping.
- Robust validation for missing fields and malformed email addresses.
- Default safe DRY_RUN mode preventing accidental live dispatches.
- Dynamic personalization for subjects, plain-text body, and responsive HTML templates.
- Per-recipient exception handling ensuring a single failure never aborts the batch.
- Comprehensive CSV delivery and audit logging (SENT, FAILED, DRY_RUN, SKIPPED).
- Secure credential management via .env and full CLI argument overrides.
"""

from __future__ import annotations

import argparse
import csv
import logging
import os
import re
import smtplib
import sys
import time
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

from dotenv import load_dotenv

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Base paths
BASE_DIR = Path(__file__).resolve().parent

# Configure console logging for diagnostics
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)

# Standard RFC 5322 compatible email validation pattern
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)+$"
)


@dataclass
class Config:
    """Application configuration container."""

    sender_email: str
    sender_password: str
    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    dry_run: bool = True
    delay_seconds: float = 2.0
    csv_path: Path = BASE_DIR / "data" / "students.csv"
    template_path: Path = BASE_DIR / "templates" / "placement_email.html"
    log_path: Path = BASE_DIR / "logs" / "email_log.csv"


def parse_arguments(args: Optional[Sequence[str]] = None) -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Student Email Automation Tool - Send personalized placement updates."
    )
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--dry-run",
        action="store_true",
        default=None,
        help="Simulate email sending without connecting to SMTP (default behavior).",
    )
    mode_group.add_argument(
        "--live",
        action="store_true",
        default=None,
        help="Execute real email delivery via configured SMTP credentials.",
    )

    parser.add_argument(
        "--csv",
        type=Path,
        default=None,
        help="Custom path to the students CSV file (default: data/students.csv).",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Custom path to the HTML email template (default: templates/placement_email.html).",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=None,
        help="Delay in seconds between consecutive emails in LIVE mode (default: 2.0).",
    )

    return parser.parse_args(args)


def load_config(cli_args: Optional[Sequence[str]] = None) -> Config:
    """Load configuration from .env and apply optional CLI flag overrides."""
    env_path = BASE_DIR / ".env"
    if env_path.exists():
        load_dotenv(dotenv_path=env_path)

    # Base values from environment with sensible fallbacks
    sender_email = os.getenv("SENDER_EMAIL", "").strip()
    sender_password = os.getenv("SENDER_PASSWORD", "").strip()
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com").strip()

    # Safe integer conversion for port
    try:
        smtp_port = int(os.getenv("SMTP_PORT", "587").strip())
    except ValueError:
        logging.warning("Invalid SMTP_PORT in environment. Falling back to default 587.")
        smtp_port = 587

    # Safe float conversion for delay
    try:
        delay_seconds = float(os.getenv("DELAY_SECONDS", "2").strip())
    except ValueError:
        logging.warning("Invalid DELAY_SECONDS in environment. Falling back to default 2.0.")
        delay_seconds = 2.0

    # Default dry_run is True unless explicitly set to 'false', '0', or 'no'
    raw_dry_run = os.getenv("DRY_RUN", "true").strip().lower()
    dry_run = raw_dry_run not in ("false", "0", "no")

    # Optional path overrides from environment
    csv_path = Path(os.getenv("CSV_FILE", str(BASE_DIR / "data" / "students.csv")))
    template_path = Path(os.getenv("HTML_TEMPLATE", str(BASE_DIR / "templates" / "placement_email.html")))
    log_path = Path(os.getenv("LOG_FILE", str(BASE_DIR / "logs" / "email_log.csv")))

    # Resolve relative paths against BASE_DIR
    if not csv_path.is_absolute():
        csv_path = BASE_DIR / csv_path
    if not template_path.is_absolute():
        template_path = BASE_DIR / template_path
    if not log_path.is_absolute():
        log_path = BASE_DIR / log_path

    # Apply CLI argument overrides if provided
    if cli_args:
        parsed = parse_arguments(cli_args)

        if parsed.dry_run is True:
            dry_run = True
        elif parsed.live is True:
            dry_run = False

        if parsed.csv is not None:
            csv_path = parsed.csv.resolve()
        if parsed.template is not None:
            template_path = parsed.template.resolve()
        if parsed.delay is not None:
            delay_seconds = max(0.0, parsed.delay)

    return Config(
        sender_email=sender_email,
        sender_password=sender_password,
        smtp_server=smtp_server,
        smtp_port=smtp_port,
        dry_run=dry_run,
        delay_seconds=delay_seconds,
        csv_path=csv_path,
        template_path=template_path,
        log_path=log_path,
    )


def validate_email(email: str) -> bool:
    """Validate email address format using standard regex."""
    if not email or len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email))


def load_students(csv_path: Path) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
    """
    Read and validate student records from the CSV file.

    Handles UTF-8 and UTF-8-BOM, strips whitespace, and validates fields.
    Returns:
        (valid_students, skipped_records)
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found at: {csv_path}")

    valid_students: List[Dict[str, str]] = []
    skipped_records: List[Dict[str, str]] = []

    with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if not reader.fieldnames:
            raise ValueError(f"CSV file '{csv_path.name}' is empty or missing a header row.")

        # Normalize header keys: lowercase and strip whitespace
        normalized_fieldnames = {col.strip().lower(): col for col in reader.fieldnames if col}
        if "name" not in normalized_fieldnames or "email" not in normalized_fieldnames:
            raise ValueError(
                f"CSV must contain 'name' and 'email' header columns. Found: {list(reader.fieldnames)}"
            )

        name_col = normalized_fieldnames["name"]
        email_col = normalized_fieldnames["email"]

        for row_idx, raw_row in enumerate(reader, start=2):
            raw_name = raw_row.get(name_col)
            raw_email = raw_row.get(email_col)

            name = (raw_name or "").strip()
            email = (raw_email or "").strip()

            # Check for missing values
            if not name or not email:
                reason = "Missing name" if not name and email else (
                    "Missing email" if name and not email else "Empty row / missing name and email"
                )
                logging.warning("Row %d skipped: %s (name='%s', email='%s')", row_idx, reason, name, email)
                skipped_records.append({"name": name, "email": email, "reason": reason})
                continue

            # Check email syntax
            if not validate_email(email):
                reason = f"Invalid email format '{email}'"
                logging.warning("Row %d skipped: %s", row_idx, reason)
                skipped_records.append({"name": name, "email": email, "reason": reason})
                continue

            valid_students.append({"name": name, "email": email})

    return valid_students, skipped_records


def load_template(template_path: Path) -> str:
    """Read the HTML email template from disk."""
    if not template_path.exists():
        raise FileNotFoundError(f"Email template file not found at: {template_path}")
    return template_path.read_text(encoding="utf-8")


def create_message(
    name: str,
    recipient: str,
    sender_email: str,
    html_template: str,
) -> EmailMessage:
    """
    Construct a personalized multi-part (plain-text + HTML) EmailMessage.
    """
    msg = EmailMessage()
    msg["From"] = sender_email or "no-reply@example.com"
    msg["To"] = recipient
    msg["Subject"] = f"Placement Drive Update – {name}"

    plain_text = f"""Hi {name},

We are pleased to inform you about the upcoming placement drive.

Please complete your registration before the deadline and keep your resume and required documents ready.

Best wishes for your placement!

Regards,
Placement Cell
"""
    msg.set_content(plain_text)

    # Insert personalized name into the HTML template
    personalized_html = html_template.replace("{{name}}", name)
    msg.add_alternative(personalized_html, subtype="html")

    return msg


def initialize_log(log_path: Path) -> None:
    """Ensure log directory and CSV log file with correct header exist."""
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        # Write header if file does not exist or is completely empty
        if not log_path.exists() or log_path.stat().st_size == 0:
            with log_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "email", "status", "details"])
    except OSError as err:
        logging.error("Failed to initialize log file at %s: %s", log_path, err)


def log_result(log_path: Path, name: str, email: str, status: str, details: str = "") -> None:
    """Safely append a single recipient delivery outcome to the CSV log."""
    try:
        with log_path.open("a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([name, email, status, details])
    except OSError as err:
        logging.error("Failed writing to log file %s: %s", log_path, err)


def send_all(
    students: List[Dict[str, str]],
    skipped_records: List[Dict[str, str]],
    config: Config,
    html_template: str,
) -> Dict[str, int]:
    """
    Dispatch emails to all valid students or simulate delivery in DRY_RUN mode.

    Returns dictionary containing processed, sent, failed, and skipped counts.
    """
    initialize_log(config.log_path)

    # Log any previously skipped CSV records for complete auditability
    for record in skipped_records:
        log_result(
            config.log_path,
            name=record.get("name", ""),
            email=record.get("email", ""),
            status="SKIPPED",
            details=record.get("reason", "Invalid CSV record"),
        )

    # --- DRY RUN MODE ---
    if config.dry_run:
        print("\n--- Dry Run Previews ---")
        for student in students:
            name, email = student["name"], student["email"]
            subject = f"Placement Drive Update – {name}"
            print(f"[DRY RUN] Would send to: {name} <{email}>")
            print(f"          Subject: {subject}")
            log_result(config.log_path, name, email, "DRY_RUN", "Simulated delivery (DRY_RUN mode active)")

        return {
            "processed": len(students),
            "sent": 0,
            "failed": 0,
            "skipped": len(skipped_records),
        }

    # --- LIVE SEND MODE ---
    if not config.sender_email or not config.sender_password:
        raise ValueError(
            "Missing SMTP credentials! SENDER_EMAIL and SENDER_PASSWORD must be configured "
            "in .env to execute LIVE mode."
        )

    sent_count = 0
    failed_count = 0
    total_recipients = len(students)

    print(f"\nConnecting to SMTP server {config.smtp_server}:{config.smtp_port}...")

    try:
        with smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=30) as server:
            server.starttls()
            server.login(config.sender_email, config.sender_password)
            print("Authentication successful. Beginning email dispatch...\n")

            for idx, student in enumerate(students, start=1):
                name, email = student["name"], student["email"]
                try:
                    msg = create_message(name, email, config.sender_email, html_template)
                    server.send_message(msg)
                    sent_count += 1
                    log_result(config.log_path, name, email, "SENT", "Successfully delivered")
                    print(f"[{idx}/{total_recipients}] [SENT] {name} <{email}>")
                except Exception as exc:
                    failed_count += 1
                    error_msg = f"{type(exc).__name__}: {str(exc)}"
                    log_result(config.log_path, name, email, "FAILED", error_msg)
                    print(f"[{idx}/{total_recipients}] [FAILED] {name} <{email}> -> {error_msg}")

                # Rate limiting delay between consecutive emails
                if config.delay_seconds > 0 and idx < total_recipients:
                    time.sleep(config.delay_seconds)

    except smtplib.SMTPAuthenticationError as err:
        raise RuntimeError(
            "SMTP Authentication Error: Invalid email or password.\n"
            "If you are using Gmail, make sure 2-Step Verification is enabled and you are "
            "using a 16-character App Password (not your normal Google account password)."
        ) from err
    except (smtplib.SMTPConnectError, TimeoutError, OSError) as err:
        raise RuntimeError(
            f"SMTP Connection Error: Unable to connect to {config.smtp_server}:{config.smtp_port}.\n"
            f"Please verify your internet connection, server host, and port settings. Details: {err}"
        ) from err

    return {
        "processed": len(students),
        "sent": sent_count,
        "failed": failed_count,
        "skipped": len(skipped_records),
    }


def main(cli_args: Optional[Sequence[str]] = None) -> int:
    """Application entrypoint."""
    if cli_args is None:
        cli_args = sys.argv[1:]
    try:
        config = load_config(cli_args)
    except Exception as err:
        sys.stdout.flush()
        print(f"\n[CONFIGURATION ERROR] {err}", file=sys.stderr)
        return 1

    mode_label = "DRY RUN (safe simulation)" if config.dry_run else "LIVE SEND (actual dispatch)"

    print("========================================")
    print("     STUDENT EMAIL AUTOMATION TOOL      ")
    print("========================================")
    print(f"Mode      : {mode_label}")
    print(f"CSV File  : {config.csv_path}")
    print(f"Template  : {config.template_path}")
    print(f"Log File  : {config.log_path}")
    if not config.dry_run:
        print(f"Delay     : {config.delay_seconds}s between emails")
    print("----------------------------------------")
    print("Loading students...")
    sys.stdout.flush()

    # Validate template existence early
    try:
        html_template = load_template(config.template_path)
    except Exception as err:
        sys.stdout.flush()
        print(f"\n[TEMPLATE ERROR] {err}", file=sys.stderr)
        return 1

    # Load students from CSV
    try:
        valid_students, skipped_records = load_students(config.csv_path)
    except Exception as err:
        sys.stdout.flush()
        print(f"\n[DATA ERROR] {err}", file=sys.stderr)
        return 1

    print(f"Valid recipients : {len(valid_students)}")
    print(f"Invalid records  : {len(skipped_records)}")
    sys.stdout.flush()

    if not valid_students and not skipped_records:
        print("\nNotice: The CSV file contains no student records.")
        return 0

    # Dispatch emails or simulate
    try:
        summary = send_all(valid_students, skipped_records, config, html_template)
    except Exception as err:
        sys.stdout.flush()
        print(f"\n[EXECUTION ERROR] {err}", file=sys.stderr)
        return 1

    print("\n========================================")
    print("                SUMMARY                 ")
    print("========================================")
    print(f"Processed : {summary['processed']}")
    print(f"Sent      : {summary['sent']}")
    print(f"Failed    : {summary['failed']}")
    print(f"Skipped   : {summary['skipped']}")
    print(f"Log File  : {config.log_path}")
    print("========================================\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
