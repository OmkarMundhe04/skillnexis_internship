"""
Student Email Automation Web Dashboard Backend
===============================================
FastAPI application providing an interactive web dashboard, real-time SSE progress
streaming for email campaigns, CSV recipient management, HTML template editor,
audit log viewer, and SMTP connectivity testing.
"""

from __future__ import annotations

import asyncio
import csv
import json
import logging
import os
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Import core business logic from email_automation
from email_automation import (
    BASE_DIR,
    Config,
    create_message,
    initialize_log,
    load_config,
    load_students,
    load_template,
    log_result,
    validate_email,
)

app = FastAPI(
    title="Student Email Automation Dashboard",
    description="Web dashboard for managing and dispatching personalized student email campaigns",
    version="2.0.0",
)

# Allow CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Directories
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR.mkdir(parents=True, exist_ok=True)
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)


def sanitize_secret(text: str, secret: Optional[str]) -> str:
    """Scrub sensitive credentials from any error output, logs, or string responses."""
    if not secret or not text:
        return text
    clean = secret.strip()
    res = text.replace(clean, "[REDACTED]")
    no_spaces = clean.replace(" ", "")
    if no_spaces:
        res = res.replace(no_spaces, "[REDACTED]")
    return res

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
jinja_templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# Request models
class TemplateUpdateRequest(BaseModel):
    html: str


class StudentAddRequest(BaseModel):
    name: str
    email: str


class StudentRemoveRequest(BaseModel):
    email: str


class SettingsUpdateRequest(BaseModel):
    sender_email: Optional[str] = None
    sender_password: Optional[str] = None
    smtp_server: Optional[str] = None
    smtp_port: Optional[int] = None
    delay_seconds: Optional[float] = None
    dry_run: Optional[bool] = None


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Serve the main interactive dashboard."""
    return jinja_templates.TemplateResponse(request, "dashboard.html")


@app.get("/api/status")
async def get_status() -> Dict[str, Any]:
    """Return system status, SMTP config overview, and recipient counts."""
    config = load_config()

    # Mask password for security
    has_password = bool(config.sender_password)
    masked_email = config.sender_email if config.sender_email else "Not configured"

    valid_students: List[Dict[str, str]] = []
    skipped_records: List[Dict[str, str]] = []
    csv_error: Optional[str] = None

    if config.csv_path.exists():
        try:
            valid_students, skipped_records = load_students(config.csv_path)
        except Exception as exc:
            csv_error = str(exc)

    template_exists = config.template_path.exists()

    return {
        "sender_email": masked_email,
        "has_credentials": bool(config.sender_email and has_password),
        "smtp_server": config.smtp_server,
        "smtp_port": config.smtp_port,
        "dry_run_default": config.dry_run,
        "delay_seconds": config.delay_seconds,
        "csv_filename": config.csv_path.name,
        "csv_exists": config.csv_path.exists(),
        "csv_error": csv_error,
        "valid_count": len(valid_students),
        "skipped_count": len(skipped_records),
        "template_exists": template_exists,
        "log_path": str(config.log_path.relative_to(BASE_DIR)) if config.log_path.is_relative_to(BASE_DIR) else str(config.log_path),
    }


@app.get("/api/students")
async def get_students() -> Dict[str, Any]:
    """Return parsed valid recipients and skipped invalid rows."""
    config = load_config()
    if not config.csv_path.exists():
        return {
            "valid": [],
            "skipped": [],
            "csv_filename": config.csv_path.name,
            "error": "CSV file does not exist yet. Please upload a student CSV list.",
        }

    try:
        valid_students, skipped_records = load_students(config.csv_path)
        return {
            "valid": valid_students,
            "skipped": skipped_records,
            "csv_filename": config.csv_path.name,
            "error": None,
        }
    except Exception as exc:
        return {
            "valid": [],
            "skipped": [],
            "csv_filename": config.csv_path.name,
            "error": str(exc),
        }


@app.post("/api/students/add")
async def add_student(payload: StudentAddRequest) -> Dict[str, Any]:
    """Directly add a new student recipient to the list."""
    name = payload.name.strip()
    email = payload.email.strip()

    if not name:
        raise HTTPException(status_code=400, detail="Student name cannot be empty.")
    if not email:
        raise HTTPException(status_code=400, detail="Student email cannot be empty.")
    if not validate_email(email):
        raise HTTPException(status_code=400, detail=f"Invalid email address format: '{email}'")

    config = load_config()
    csv_file = config.csv_path
    csv_file.parent.mkdir(parents=True, exist_ok=True)

    existing_records = []
    if csv_file.exists() and csv_file.stat().st_size > 0:
        with csv_file.open("r", newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                normalized = {col.strip().lower(): col for col in reader.fieldnames if col}
                name_col = normalized.get("name", "name")
                email_col = normalized.get("email", "email")
                for row in reader:
                    r_name = (row.get(name_col) or "").strip()
                    r_email = (row.get(email_col) or "").strip()
                    if r_email.lower() == email.lower():
                        raise HTTPException(
                            status_code=400,
                            detail=f"Student with email '{email}' already exists ({r_name}).",
                        )
                    if r_name and r_email:
                        existing_records.append({"name": r_name, "email": r_email})

    existing_records.append({"name": name, "email": email})

    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email"])
        for record in existing_records:
            writer.writerow([record["name"], record["email"]])

    return {
        "success": True,
        "message": f"Successfully added {name} <{email}>.",
        "student": {"name": name, "email": email},
        "total_count": len(existing_records),
    }


@app.post("/api/students/remove")
async def remove_student(payload: StudentRemoveRequest) -> Dict[str, Any]:
    """Remove a student recipient by email."""
    target_email = payload.email.strip().lower()
    if not target_email:
        raise HTTPException(status_code=400, detail="Email is required.")

    config = load_config()
    csv_file = config.csv_path
    if not csv_file.exists():
        raise HTTPException(status_code=404, detail="Student list is empty.")

    remaining_records = []
    removed_name = None

    with csv_file.open("r", newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            raise HTTPException(status_code=400, detail="CSV file is empty.")
        normalized = {col.strip().lower(): col for col in reader.fieldnames if col}
        name_col = normalized.get("name", "name")
        email_col = normalized.get("email", "email")
        for row in reader:
            r_name = (row.get(name_col) or "").strip()
            r_email = (row.get(email_col) or "").strip()
            if r_email.lower() == target_email:
                removed_name = r_name
                continue
            if r_name or r_email:
                remaining_records.append({"name": r_name, "email": r_email})

    if removed_name is None:
        raise HTTPException(status_code=404, detail=f"No student found with email '{payload.email}'.")

    with csv_file.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email"])
        for record in remaining_records:
            writer.writerow([record["name"], record["email"]])

    return {
        "success": True,
        "message": f"Successfully removed {removed_name} <{payload.email}>.",
        "removed_email": payload.email,
        "total_count": len(remaining_records),
    }


@app.post("/api/upload-csv")
async def upload_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
    """Upload a new students CSV file and validate its content."""
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are supported.")

    config = load_config()
    content = await file.read()

    # Backup existing if present
    if config.csv_path.exists():
        backup_path = config.csv_path.with_suffix(".csv.bak")
        try:
            backup_path.write_bytes(config.csv_path.read_bytes())
        except Exception:
            pass

    # Write uploaded content
    config.csv_path.parent.mkdir(parents=True, exist_ok=True)
    config.csv_path.write_bytes(content)

    # Validate updated CSV
    try:
        valid_students, skipped_records = load_students(config.csv_path)
        return {
            "success": True,
            "message": f"Successfully loaded {len(valid_students)} valid recipients ({len(skipped_records)} skipped).",
            "valid_count": len(valid_students),
            "skipped_count": len(skipped_records),
        }
    except Exception as exc:
        # Revert if backup exists
        backup_path = config.csv_path.with_suffix(".csv.bak")
        if backup_path.exists():
            config.csv_path.write_bytes(backup_path.read_bytes())
        raise HTTPException(status_code=400, detail=f"CSV validation failed: {str(exc)}")


@app.get("/api/template")
async def get_template() -> Dict[str, Any]:
    """Return raw template content and personalized HTML preview with sample data."""
    config = load_config()
    if not config.template_path.exists():
        raise HTTPException(status_code=404, detail="Email template file not found.")

    raw_html = config.template_path.read_text(encoding="utf-8")
    sample_preview = raw_html.replace("{{name}}", "Alex Morgan")

    return {
        "raw_html": raw_html,
        "sample_preview": sample_preview,
        "filename": config.template_path.name,
    }


@app.post("/api/template")
async def update_template(payload: TemplateUpdateRequest) -> Dict[str, Any]:
    """Save updated HTML template to disk."""
    config = load_config()
    if not payload.html or not payload.html.strip():
        raise HTTPException(status_code=400, detail="Template content cannot be empty.")

    config.template_path.parent.mkdir(parents=True, exist_ok=True)
    config.template_path.write_text(payload.html, encoding="utf-8")

    sample_preview = payload.html.replace("{{name}}", "Alex Morgan")
    return {
        "success": True,
        "message": "Template updated successfully.",
        "sample_preview": sample_preview,
    }


@app.post("/api/test-connection")
async def test_smtp_connection() -> Dict[str, Any]:
    """Test SMTP connection and credentials without dispatching an email."""
    config = load_config()
    if not config.sender_email or not config.sender_password:
        return {
            "success": False,
            "message": "SENDER_EMAIL or SENDER_PASSWORD is not set in .env or cloud environment.",
        }

    try:
        # Run blocking SMTP network call in executor
        def _check_smtp():
            with smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=15) as server:
                server.starttls()
                server.login(config.sender_email, config.sender_password)
            return True

        await asyncio.to_thread(_check_smtp)
        return {
            "success": True,
            "message": f"Successfully connected and authenticated with {config.smtp_server}:{config.smtp_port} as {config.sender_email}!",
        }
    except smtplib.SMTPAuthenticationError as err:
        return {
            "success": False,
            "message": (
                "SMTP Authentication failed. Please verify your 16-character Google App Password "
                "(with 2-Step Verification enabled), not your personal account password."
            ),
            "details": sanitize_secret(str(err), config.sender_password),
        }
    except Exception as exc:
        sanitized = sanitize_secret(str(exc), config.sender_password)
        return {
            "success": False,
            "message": f"SMTP Connection failed: {type(exc).__name__} - {sanitized}",
            "details": sanitized,
        }


@app.get("/api/logs")
async def get_logs(limit: int = 200) -> Dict[str, Any]:
    """Return parsed audit logs from email_log.csv in reverse chronological order."""
    config = load_config()
    log_file = config.log_path

    if not log_file.exists():
        return {"logs": [], "total": 0}

    logs = []
    try:
        with log_file.open("r", newline="", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames:
                for row in reader:
                    logs.append({
                        "name": row.get("name", "").strip(),
                        "email": row.get("email", "").strip(),
                        "status": row.get("status", "UNKNOWN").strip(),
                        "details": row.get("details", "").strip(),
                    })
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed reading log file: {str(exc)}")

    # Most recent entries first
    logs.reverse()
    return {
        "logs": logs[:limit],
        "total": len(logs),
    }


@app.post("/api/clear-logs")
async def clear_logs() -> Dict[str, Any]:
    """Clear all records from email_log.csv and write a fresh header."""
    config = load_config()
    initialize_log(config.log_path)
    # Re-create empty
    with config.log_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "email", "status", "details"])

    return {"success": True, "message": "Log file cleared successfully."}


@app.get("/api/stream-campaign")
async def stream_campaign(
    mode: str = "dry_run",
    delay: float = 1.0,
):
    """
    Server-Sent Events (SSE) endpoint streaming real-time dispatch progress.
    mode: 'dry_run' | 'live'
    delay: seconds between consecutive emails
    """
    config = load_config()
    is_dry_run = mode.lower() != "live"
    delay_seconds = max(0.0, min(delay, 10.0))

    async def event_generator() -> AsyncGenerator[str, None]:
        initialize_log(config.log_path)

        # 1. Load students
        try:
            valid_students, skipped_records = load_students(config.csv_path)
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'error': f'Failed loading CSV: {str(exc)}'})}\n\n"
            return

        # 2. Load template
        try:
            html_template = load_template(config.template_path)
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'error': f'Failed loading template: {str(exc)}'})}\n\n"
            return

        total_recipients = len(valid_students)

        # Log skipped CSV records
        for record in skipped_records:
            log_result(
                config.log_path,
                name=record.get("name", ""),
                email=record.get("email", ""),
                status="SKIPPED",
                details=record.get("reason", "Invalid CSV record"),
            )

        # Emit init event
        init_payload = {
            "total": total_recipients,
            "skipped": len(skipped_records),
            "mode": "DRY RUN" if is_dry_run else "LIVE SEND",
            "delay": delay_seconds,
        }
        yield f"event: init\ndata: {json.dumps(init_payload)}\n\n"

        if total_recipients == 0:
            done_payload = {
                "summary": {
                    "processed": 0,
                    "sent": 0,
                    "failed": 0,
                    "skipped": len(skipped_records),
                }
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
            return

        sent_count = 0
        failed_count = 0

        # --- DRY RUN DISPATCH ---
        if is_dry_run:
            for idx, student in enumerate(valid_students, start=1):
                name, email = student["name"], student["email"]
                log_result(config.log_path, name, email, "DRY_RUN", "Simulated delivery (DRY_RUN active)")

                progress_payload = {
                    "current": idx,
                    "total": total_recipients,
                    "percentage": round((idx / total_recipients) * 100, 1),
                    "name": name,
                    "email": email,
                    "status": "DRY_RUN",
                    "details": f"Simulated dispatch to {name} <{email}>",
                }
                yield f"event: progress\ndata: {json.dumps(progress_payload)}\n\n"

                # Brief simulation interval for smooth UI visualization
                sim_delay = min(0.3, delay_seconds if delay_seconds > 0 else 0.1)
                await asyncio.sleep(sim_delay)

            done_payload = {
                "summary": {
                    "processed": total_recipients,
                    "sent": 0,
                    "failed": 0,
                    "skipped": len(skipped_records),
                    "dry_run": True,
                }
            }
            yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"
            return

        # --- LIVE SMTP DISPATCH ---
        if not config.sender_email or not config.sender_password:
            err_msg = "Missing credentials: SENDER_EMAIL and SENDER_PASSWORD must be configured in environment."
            yield f"event: error\ndata: {json.dumps({'error': err_msg})}\n\n"
            return

        yield f"event: status\ndata: {json.dumps({'message': f'Connecting to SMTP server {config.smtp_server}:{config.smtp_port}...'})}\n\n"

        server = None
        try:
            def _connect_smtp():
                s = smtplib.SMTP(config.smtp_server, config.smtp_port, timeout=30)
                s.starttls()
                s.login(config.sender_email, config.sender_password)
                return s

            server = await asyncio.to_thread(_connect_smtp)
            yield f"event: status\ndata: {json.dumps({'message': 'SMTP authenticated successfully. Sending emails...'})}\n\n"

            for idx, student in enumerate(valid_students, start=1):
                name, email = student["name"], student["email"]
                status = "SENT"
                details = "Successfully delivered"

                try:
                    def _send_one(to_name, to_email):
                        msg = create_message(to_name, to_email, config.sender_email, html_template)
                        server.send_message(msg)

                    await asyncio.to_thread(_send_one, name, email)
                    sent_count += 1
                    log_result(config.log_path, name, email, "SENT", details)
                except Exception as exc:
                    failed_count += 1
                    status = "FAILED"
                    err_msg = sanitize_secret(str(exc), config.sender_password)
                    details = f"{type(exc).__name__}: {err_msg}"
                    log_result(config.log_path, name, email, "FAILED", details)

                progress_payload = {
                    "current": idx,
                    "total": total_recipients,
                    "percentage": round((idx / total_recipients) * 100, 1),
                    "name": name,
                    "email": email,
                    "status": status,
                    "details": details,
                }
                yield f"event: progress\ndata: {json.dumps(progress_payload)}\n\n"

                if delay_seconds > 0 and idx < total_recipients:
                    await asyncio.sleep(delay_seconds)

        except Exception as exc:
            sanitized = sanitize_secret(str(exc), config.sender_password)
            yield f"event: error\ndata: {json.dumps({'error': f'SMTP Error: {type(exc).__name__} - {sanitized}'})}\n\n"
            return
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

        done_payload = {
            "summary": {
                "processed": total_recipients,
                "sent": sent_count,
                "failed": failed_count,
                "skipped": len(skipped_records),
                "dry_run": False,
            }
        }
        yield f"event: done\ndata: {json.dumps(done_payload)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    print(f"Starting Student Email Automation Dashboard on http://{host}:{port}")
    uvicorn.run("app:app", host=host, port=port, reload=False)
