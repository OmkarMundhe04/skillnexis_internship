"""
Comprehensive Test Suite for Student Email Automation Tool
==========================================================
Validates all requirements specified in Section 20:
- TEST 1: Valid CSV + DRY_RUN=true -> No email sent, personalized output, DRY_RUN logged.
- TEST 2: Invalid email & empty rows -> Safely skipped, logged as SKIPPED, execution continues.
- TEST 3: Missing CSV -> Graceful error handling without raw traceback.
- TEST 4: Missing credentials in LIVE mode -> Clear error message.
- TEST 5: DRY_RUN guarantees -> Confirms SMTP is never contacted.
- TEST 6: Simulated failed recipient in LIVE mode -> Isolated failure, remaining emails sent.
- TEST 7: Template missing -> Graceful error handling.
- TEST 8: CSV with whitespace / UTF-8 BOM -> Properly parsed and stripped.
- TEST 9: CLI argument parsing & overrides -> Verifies flag handling.
- TEST 10: Email personalization & structure -> Validates EmailMessage fields and HTML substitution.
"""

import csv
import io
import smtplib
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure student-email-automation root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import email_automation
from email_automation import (
    Config,
    create_message,
    load_config,
    load_students,
    load_template,
    main,
    send_all,
    validate_email,
)


class TestStudentEmailAutomation(unittest.TestCase):
    """Unit and integration tests for email automation tool."""

    def setUp(self):
        """Create a temporary directory for isolated test files."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.test_dir.name)

        # Standard test template
        self.template_path = self.root / "placement_email.html"
        self.template_path.write_text(
            "<html><body>Hi {{name}}, Welcome to placement drive!</body></html>",
            encoding="utf-8",
        )

        # Standard valid CSV
        self.csv_path = self.root / "students.csv"
        self.csv_path.write_text(
            "name,email\nRahul Sharma,rahul@example.com\nPriya Patil,priya@example.com\n",
            encoding="utf-8",
        )

        self.log_path = self.root / "email_log.csv"

    def tearDown(self):
        """Clean up temporary directory."""
        self.test_dir.cleanup()

    # --- TEST 1 & TEST 5: Valid CSV + DRY_RUN=true (SMTP is never contacted) ---
    @patch("smtplib.SMTP")
    def test_dry_run_mode_never_contacts_smtp(self, mock_smtp):
        """Ensure DRY_RUN=true never initializes SMTP and logs DRY_RUN records."""
        config = Config(
            sender_email="test@example.com",
            sender_password="secret_password",
            dry_run=True,
            csv_path=self.csv_path,
            template_path=self.template_path,
            log_path=self.log_path,
        )

        template = load_template(config.template_path)
        students, skipped = load_students(config.csv_path)
        self.assertEqual(len(students), 2)
        self.assertEqual(len(skipped), 0)

        # Capture output
        captured_stdout = io.StringIO()
        with patch("sys.stdout", captured_stdout):
            summary = send_all(students, skipped, config, template)

        # SMTP must NOT be called at all
        mock_smtp.assert_not_called()

        self.assertEqual(summary["processed"], 2)
        self.assertEqual(summary["sent"], 0)
        self.assertEqual(summary["failed"], 0)
        self.assertEqual(summary["skipped"], 0)

        # Check log file
        self.assertTrue(self.log_path.exists())
        with self.log_path.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["status"], "DRY_RUN")
            self.assertEqual(rows[0]["name"], "Rahul Sharma")
            self.assertEqual(rows[1]["status"], "DRY_RUN")
            self.assertEqual(rows[1]["name"], "Priya Patil")

    # --- TEST 2: Invalid email and empty rows are safely skipped ---
    def test_invalid_records_handling(self):
        """Ensure invalid emails and empty names/emails are rejected safely."""
        bad_csv = self.root / "bad_students.csv"
        bad_csv.write_text(
            "name,email\n"
            ",\n"                            # completely empty
            "Rahul,\n"                       # missing email
            ",rahul@example.com\n"           # missing name
            "Amit,invalid-email\n"           # invalid email format
            "Neha Sharma,neha@valid.org\n",  # valid record
            encoding="utf-8",
        )

        valid, skipped = load_students(bad_csv)
        self.assertEqual(len(valid), 1)
        self.assertEqual(valid[0]["name"], "Neha Sharma")
        self.assertEqual(valid[0]["email"], "neha@valid.org")
        self.assertEqual(len(skipped), 4)

        # Verify reasons are captured
        reasons = [r["reason"] for r in skipped]
        self.assertTrue(any("Missing email" in r for r in reasons))
        self.assertTrue(any("Missing name" in r for r in reasons))
        self.assertTrue(any("Invalid email format" in r for r in reasons))

        # Test logging skipped records
        config = Config(
            sender_email="test@example.com",
            sender_password="secret",
            dry_run=True,
            log_path=self.log_path,
        )
        template = "Hi {{name}}"
        send_all(valid, skipped, config, template)

        with self.log_path.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            # 4 skipped + 1 dry_run
            self.assertEqual(len(rows), 5)
            skipped_rows = [r for r in rows if r["status"] == "SKIPPED"]
            self.assertEqual(len(skipped_rows), 4)

    # --- TEST 3: Missing CSV file returns clean error ---
    def test_missing_csv_file(self):
        """Missing CSV must exit cleanly with code 1 and a descriptive message."""
        non_existent_csv = self.root / "does_not_exist.csv"
        captured_stderr = io.StringIO()
        captured_stdout = io.StringIO()

        with patch("sys.stderr", captured_stderr), patch("sys.stdout", captured_stdout):
            exit_code = main(["--csv", str(non_existent_csv)])

        self.assertEqual(exit_code, 1)
        error_output = captured_stderr.getvalue()
        self.assertIn("[DATA ERROR]", error_output)
        self.assertIn("CSV file not found", error_output)

    # --- TEST 4: Missing .env credentials in LIVE mode ---
    def test_missing_credentials_in_live_mode(self):
        """LIVE mode without sender email or password must fail with clear message."""
        captured_stderr = io.StringIO()
        captured_stdout = io.StringIO()

        # Clear env variables during this test
        with patch.dict(email_automation.os.environ, {"SENDER_EMAIL": "", "SENDER_PASSWORD": ""}, clear=True):
            with patch("sys.stderr", captured_stderr), patch("sys.stdout", captured_stdout):
                exit_code = main(["--live", "--csv", str(self.csv_path), "--template", str(self.template_path)])

        self.assertEqual(exit_code, 1)
        error_output = captured_stderr.getvalue()
        self.assertIn("[EXECUTION ERROR]", error_output)
        self.assertIn("Missing SMTP credentials", error_output)

    # --- TEST 6: One simulated failed recipient in LIVE mode ---
    @patch("smtplib.SMTP")
    def test_individual_recipient_failure_does_not_stop_batch(self, mock_smtp_class):
        """If one recipient delivery fails, subsequent recipients must still be sent."""
        mock_server = MagicMock()
        mock_smtp_class.return_value.__enter__.return_value = mock_server

        # Simulate: First recipient succeeds, second fails with exception, third succeeds
        students = [
            {"name": "Rahul Sharma", "email": "rahul@example.com"},
            {"name": "Priya Patil", "email": "priya@example.com"},
            {"name": "Amit Joshi", "email": "amit@example.com"},
        ]

        def send_side_effect(msg):
            recipient = msg["To"]
            if recipient == "priya@example.com":
                raise smtplib.SMTPRecipientsRefused({"priya@example.com": (550, b"User not found")})
            return {}

        mock_server.send_message.side_effect = send_side_effect

        config = Config(
            sender_email="admin@college.edu",
            sender_password="valid_app_password",
            dry_run=False,
            delay_seconds=0.0,
            log_path=self.log_path,
        )

        summary = send_all(students, [], config, "Hi {{name}}")

        self.assertEqual(summary["processed"], 3)
        self.assertEqual(summary["sent"], 2)
        self.assertEqual(summary["failed"], 1)
        self.assertEqual(summary["skipped"], 0)

        # Check log entries
        with self.log_path.open("r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
            self.assertEqual(len(rows), 3)
            self.assertEqual(rows[0]["name"], "Rahul Sharma")
            self.assertEqual(rows[0]["status"], "SENT")
            self.assertEqual(rows[1]["name"], "Priya Patil")
            self.assertEqual(rows[1]["status"], "FAILED")
            self.assertIn("SMTPRecipientsRefused", rows[1]["details"])
            self.assertEqual(rows[2]["name"], "Amit Joshi")
            self.assertEqual(rows[2]["status"], "SENT")

    # --- TEST 7: Template missing returns clean error ---
    def test_missing_template_file(self):
        """Missing template must exit cleanly with code 1 and descriptive message."""
        non_existent_template = self.root / "missing_template.html"
        captured_stderr = io.StringIO()
        captured_stdout = io.StringIO()

        with patch("sys.stderr", captured_stderr), patch("sys.stdout", captured_stdout):
            exit_code = main(["--template", str(non_existent_template), "--csv", str(self.csv_path)])

        self.assertEqual(exit_code, 1)
        error_output = captured_stderr.getvalue()
        self.assertIn("[TEMPLATE ERROR]", error_output)
        self.assertIn("template file not found", error_output.lower())

    # --- TEST 8: CSV with whitespace and UTF-8 BOM ---
    def test_csv_with_spaces_and_utf8_bom(self):
        """Ensure UTF-8 BOM and extraneous whitespace around headers and cells parse accurately."""
        bom_csv = self.root / "bom_students.csv"
        # Write with UTF-8 BOM and spaced headers/values
        bom_content = "\ufeff  Name  ,  Email  \n  Karan Mehra  ,   karan@example.com  \n"
        bom_csv.write_bytes(bom_content.encode("utf-8"))

        valid, skipped = load_students(bom_csv)
        self.assertEqual(len(valid), 1)
        self.assertEqual(len(skipped), 0)
        self.assertEqual(valid[0]["name"], "Karan Mehra")
        self.assertEqual(valid[0]["email"], "karan@example.com")

    # --- TEST 9: CLI argument parsing & overrides ---
    def test_cli_argument_overrides(self):
        """Test CLI arguments override environment defaults."""
        custom_csv = self.root / "custom.csv"
        custom_template = self.root / "custom.html"

        cfg_dry = load_config(["--dry-run", "--csv", str(custom_csv), "--delay", "5.5"])
        self.assertTrue(cfg_dry.dry_run)
        self.assertEqual(cfg_dry.csv_path, custom_csv.resolve())
        self.assertEqual(cfg_dry.delay_seconds, 5.5)

        cfg_live = load_config(["--live", "--template", str(custom_template)])
        self.assertFalse(cfg_live.dry_run)
        self.assertEqual(cfg_live.template_path, custom_template.resolve())

    # --- TEST 10: Email message structure and dynamic content ---
    def test_create_message_structure(self):
        """Verify dynamic subject insertion, sender, recipient, plain text, and HTML body."""
        template = "<p>Hi {{name}}, congratulations!</p>"
        msg = create_message(
            name="Sneha Kapoor",
            recipient="sneha@example.org",
            sender_email="placement@college.edu",
            html_template=template,
        )

        self.assertEqual(msg["Subject"], "Placement Drive Update – Sneha Kapoor")
        self.assertEqual(msg["From"], "placement@college.edu")
        self.assertEqual(msg["To"], "sneha@example.org")

        # Check payload parts (plain text + html)
        parts = list(msg.iter_parts())
        self.assertEqual(len(parts), 2)

        plain_part = parts[0]
        html_part = parts[1]

        self.assertEqual(plain_part.get_content_type(), "text/plain")
        self.assertIn("Hi Sneha Kapoor,", plain_part.get_content())

        self.assertEqual(html_part.get_content_type(), "text/html")
        self.assertIn("Hi Sneha Kapoor, congratulations!", html_part.get_content())

    # --- Additional: Email validation test cases ---
    def test_validate_email_edge_cases(self):
        """Test varied email address formats."""
        self.assertTrue(validate_email("user@domain.com"))
        self.assertTrue(validate_email("first.last@sub.domain.co.in"))
        self.assertTrue(validate_email("user+tag@example.org"))

        self.assertFalse(validate_email(""))
        self.assertFalse(validate_email("plainaddress"))
        self.assertFalse(validate_email("@missinguser.com"))
        self.assertFalse(validate_email("user@"))
        self.assertFalse(validate_email("user@domain"))
        self.assertFalse(validate_email("user space@domain.com"))


if __name__ == "__main__":
    unittest.main()
