import os
import uuid
import json
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, Request, Response, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

load_dotenv()

from auth import verify_password, create_session_token, verify_session_token, SESSION_COOKIE
from analyzer import ProtocolAnalyzer
from pdf_gen import generate_report_pdf
from translations import get_labels

BASE_DIR = Path(__file__).parent.parent
UPLOADS_DIR = BASE_DIR / "uploads"
REPORTS_DIR = BASE_DIR / "reports"
PROTOCOL_PATH = BASE_DIR / "uploads" / "protocol.pdf"
PROTOCOL_TEXT_PATH = BASE_DIR / "uploads" / "protocol_text.txt"
LOGO_PATH = BASE_DIR / "static" / "images" / "logo.png"
USAGE_PATH = BASE_DIR / "uploads" / "usage.json"
DAILY_LIMIT = 20


def get_usage() -> dict:
    today = datetime.now().strftime("%Y-%m-%d")
    if USAGE_PATH.exists():
        data = json.loads(USAGE_PATH.read_text())
        if data.get("date") == today:
            return data
    return {"date": today, "count": 0}


def increment_usage():
    data = get_usage()
    data["count"] += 1
    USAGE_PATH.write_text(json.dumps(data))

UPLOADS_DIR.mkdir(exist_ok=True)
REPORTS_DIR.mkdir(exist_ok=True)
(BASE_DIR / "static" / "images").mkdir(exist_ok=True)

app = FastAPI(title="Genexa CRO Protocol Analyzer")

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

analyzer = ProtocolAnalyzer()


def get_current_user(request: Request) -> bool:
    token = request.cookies.get(SESSION_COOKIE)
    if not token or not verify_session_token(token):
        return False
    return True


def require_auth(request: Request):
    if not get_current_user(request):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


# ── Auth routes ────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/dashboard")
    return RedirectResponse(url="/login")


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if get_current_user(request):
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
async def login(request: Request, password: str = Form(...)):
    if verify_password(password):
        token = create_session_token()
        response = RedirectResponse(url="/dashboard", status_code=302)
        response.set_cookie(
            key=SESSION_COOKIE,
            value=token,
            httponly=True,
            samesite="lax",
            max_age=86400 * 7,
        )
        return response
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "error": "Hatalı şifre. Lütfen tekrar deneyin."},
        status_code=401,
    )


@app.post("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=302)
    response.delete_cookie(SESSION_COOKIE)
    return response


# ── Dashboard ──────────────────────────────────────────────────────────────────

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    if not get_current_user(request):
        return RedirectResponse(url="/login")

    protocol_loaded = PROTOCOL_TEXT_PATH.exists()
    protocol_name = ""
    if protocol_loaded:
        meta_path = BASE_DIR / "uploads" / "protocol_meta.json"
        if meta_path.exists():
            meta = json.loads(meta_path.read_text())
            protocol_name = meta.get("filename", "Protokol yüklendi")

    reports = []
    for report_file in sorted(REPORTS_DIR.glob("*.json"), reverse=True)[:20]:
        try:
            meta = json.loads(report_file.read_text())
            reports.append(meta)
        except Exception:
            pass

    usage = get_usage()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "protocol_loaded": protocol_loaded,
        "protocol_name": protocol_name,
        "reports": reports,
        "usage_count": usage["count"],
        "usage_limit": DAILY_LIMIT,
        "usage_pct": min(100, int(usage["count"] / DAILY_LIMIT * 100)),
    })


# ── Logo upload ────────────────────────────────────────────────────────────────

@app.post("/api/upload-logo")
async def upload_logo(
    request: Request,
    file: UploadFile = File(...),
):
    if not get_current_user(request):
        raise HTTPException(status_code=401)

    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Sadece resim dosyaları kabul edilir.")

    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Dosya boyutu 2MB'ı aşamaz.")

    LOGO_PATH.write_bytes(content)
    return JSONResponse({"success": True, "message": "Logo güncellendi."})


# ── Protocol upload ────────────────────────────────────────────────────────────

@app.post("/api/upload-protocol")
async def upload_protocol(
    request: Request,
    file: UploadFile = File(...),
):
    if not get_current_user(request):
        raise HTTPException(status_code=401)

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir.")

    content = await file.read()
    PROTOCOL_PATH.write_bytes(content)

    text = analyzer.extract_pdf_text(PROTOCOL_PATH)
    if not text.strip():
        raise HTTPException(status_code=422, detail="PDF'den metin çıkarılamadı.")

    PROTOCOL_TEXT_PATH.write_text(text, encoding="utf-8")

    meta = {
        "filename": file.filename,
        "uploaded_at": datetime.now().isoformat(),
        "char_count": len(text),
    }
    (BASE_DIR / "uploads" / "protocol_meta.json").write_text(json.dumps(meta, ensure_ascii=False))

    # Reset cached protocol in analyzer
    analyzer.reset_protocol()

    return JSONResponse({"success": True, "message": f"Protokol yüklendi: {file.filename}", "char_count": len(text)})


# ── Patient analysis ───────────────────────────────────────────────────────────

@app.post("/api/analyze-patient")
async def analyze_patient(
    request: Request,
    file: UploadFile = File(...),
    patient_id: str = Form(default=""),
    language: str = Form(default="tr"),
    include_logo: str = Form(default="0"),
):
    if not get_current_user(request):
        raise HTTPException(status_code=401)

    if not PROTOCOL_TEXT_PATH.exists():
        raise HTTPException(status_code=400, detail="Önce bir protokol yüklemelisiniz.")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Sadece PDF dosyaları kabul edilir.")

    lang = language if language in ("tr", "en") else "tr"

    content = await file.read()
    tmp_path = UPLOADS_DIR / f"patient_{uuid.uuid4().hex}.pdf"
    tmp_path.write_bytes(content)

    try:
        patient_text = analyzer.extract_pdf_text(tmp_path)
        if not patient_text.strip():
            raise HTTPException(status_code=422, detail="Hasta PDF'inden metin çıkarılamadı.")

        protocol_text = PROTOCOL_TEXT_PATH.read_text(encoding="utf-8")

        report_data = await analyzer.analyze(protocol_text, patient_text, language=lang)

        report_id = uuid.uuid4().hex[:12]
        pid = patient_id.strip() or report_data.get("hasta_id", f"Patient-{report_id[:6]}")

        meta = {
            "report_id": report_id,
            "patient_id": pid,
            "filename": file.filename,
            "language": lang,
            "created_at": datetime.now().isoformat(),
            "karar": report_data.get("genel_karar", {}).get("durum", ""),
            "karar_text": report_data.get("genel_karar", {}).get("metin", ""),
        }
        (REPORTS_DIR / f"{report_id}.json").write_text(
            json.dumps({**meta, "report": report_data}, ensure_ascii=False, indent=2)
        )

        increment_usage()

        pdf_path = REPORTS_DIR / f"{report_id}.pdf"
        await generate_report_pdf(report_data, pid, pdf_path, language=lang, show_logo=(include_logo == "1"))

        return JSONResponse({
            "success": True,
            "report_id": report_id,
            "patient_id": pid,
            "language": lang,
            "karar": meta["karar"],
            "karar_text": meta["karar_text"],
        })
    finally:
        tmp_path.unlink(missing_ok=True)


# ── Report download ────────────────────────────────────────────────────────────

@app.get("/report/{report_id}")
async def view_report(request: Request, report_id: str):
    if not get_current_user(request):
        return RedirectResponse(url="/login")

    json_path = REPORTS_DIR / f"{report_id}.json"
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Rapor bulunamadı.")

    data = json.loads(json_path.read_text())
    lang = data.get("language", "tr")
    return templates.TemplateResponse("report_view.html", {
        "request": request,
        "report": data.get("report", {}),
        "meta": {k: v for k, v in data.items() if k != "report"},
        "report_id": report_id,
        "L": get_labels(lang),
        "lang": lang,
    })


@app.get("/report/{report_id}/pdf")
async def download_report(request: Request, report_id: str):
    if not get_current_user(request):
        raise HTTPException(status_code=401)

    pdf_path = REPORTS_DIR / f"{report_id}.pdf"
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF raporu bulunamadı.")

    json_path = REPORTS_DIR / f"{report_id}.json"
    patient_id = report_id
    lang = "tr"
    if json_path.exists():
        meta = json.loads(json_path.read_text())
        patient_id = meta.get("patient_id", report_id)
        lang = meta.get("language", "tr")

    labels = get_labels(lang)
    prefix = labels["pdf_filename_prefix"]

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"{prefix}_{patient_id}.pdf",
    )
