import asyncio
import base64
import sys
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"
LOGO_PATH = BASE_DIR / "static" / "images" / "logo.png"
DEJAVU_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
DEJAVU_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

def _font_face_css() -> str:
    if not DEJAVU_FONT.exists():
        return ""
    css = f"@font-face {{ font-family: DejaVu; src: url('file://{DEJAVU_FONT}'); font-weight: normal; }}\n"
    if DEJAVU_BOLD.exists():
        css += f"@font-face {{ font-family: DejaVu; src: url('file://{DEJAVU_BOLD}'); font-weight: bold; }}\n"
    return css

PDF_CSS_BASE = """
@page {{ size: A4; margin: 15mm 12mm; }}
{font_face}
body {{ font-family: {font_family}; font-size: 9pt; color: #1a1a2e; line-height: 1.4; }}

.report-header { background-color: #6B0F1A; color: white; padding: 14px 18px; margin-bottom: 14px; }
.report-header-inner { display: flex; align-items: center; }
.report-header-logo { margin-right: 18px; }
.report-header-logo img { height: 48px; width: auto; }
.report-header h1 { font-size: 14pt; font-weight: bold; margin: 0 0 4px 0; color: white; }
.report-header .subtitle { font-size: 9pt; color: #f0c0c8; margin: 0; }
.report-header .meta { font-size: 8pt; color: #d9a0aa; margin: 6px 0 0 0; }

.section { margin-bottom: 12px; border: 1px solid #d0dae8; }
.section-header { background-color: #6B0F1A; color: white; padding: 7px 12px; font-weight: bold; font-size: 9pt; }
.section-body { padding: 10px 12px; }

table { width: 100%; border-collapse: collapse; font-size: 8pt; margin-top: 6px; }
th { background-color: #9B1C33; color: white; padding: 6px 8px; text-align: left; font-size: 8pt; }
td { padding: 5px 8px; border-bottom: 1px solid #e0e8f0; vertical-align: top; }

.status-ok { color: #2E7D32; font-weight: bold; }
.status-fail { color: #C62828; font-weight: bold; }
.status-warn { color: #E65100; font-weight: bold; }

.risk-low { color: #2E7D32; font-weight: bold; }
.risk-medium { color: #E65100; font-weight: bold; }
.risk-high { color: #C62828; font-weight: bold; }

.decision-ok { background-color: #E8F5E9; border: 2px solid #2E7D32; padding: 12px; margin-top: 4px; }
.decision-fail { background-color: #FFEBEE; border: 2px solid #C62828; padding: 12px; margin-top: 4px; }
.decision-warn { background-color: #FFF8E1; border: 2px solid #F57F17; padding: 12px; margin-top: 4px; }
.decision-title { font-size: 12pt; font-weight: bold; margin-bottom: 5px; }
.decision-detail { font-size: 8.5pt; color: #37474F; }

.info-table td { border: none; padding: 4px 8px; }
.info-table td:first-child { color: #5a6a8a; font-size: 8pt; text-transform: uppercase; width: 33%; }
.info-table td:last-child { font-weight: bold; color: #6B0F1A; }

.kohort-box { background-color: #FFF0F2; border: 1px solid #9B1C33; padding: 10px 12px; margin-top: 4px; }
.kohort-title { font-size: 11pt; font-weight: bold; color: #6B0F1A; margin-bottom: 6px; }

.footer { margin-top: 14px; padding-top: 8px; border-top: 1px solid #d0d9e8; font-size: 7.5pt; color: #78909C; text-align: center; }
"""


async def generate_report_pdf(report_data: dict, patient_id: str, output_path: Path, language: str = "tr", show_logo: bool = False):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _render_pdf, report_data, patient_id, output_path, language, show_logo)


def _render_pdf(report_data: dict, patient_id: str, output_path: Path, language: str = "tr", show_logo: bool = False):
    from xhtml2pdf import pisa
    from translations import get_labels

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.filters["status_icon"] = _status_icon
    env.filters["status_class"] = _status_class
    env.filters["durum_icon"] = _durum_icon
    env.filters["durum_class"] = _durum_class
    env.filters["risk_class"] = _risk_class

    # Build CSS with font support
    font_face = _font_face_css()
    font_family = "DejaVu, Helvetica, Arial, sans-serif" if font_face else "Helvetica, Arial, sans-serif"
    pdf_css = PDF_CSS_BASE.format(font_face=font_face, font_family=font_family)

    # Logo as base64 data URL for reliable embedding
    logo_src = ""
    if show_logo and LOGO_PATH.exists():
        logo_data = base64.b64encode(LOGO_PATH.read_bytes()).decode()
        ext = LOGO_PATH.suffix.lstrip(".").lower()
        mime = "image/png" if ext == "png" else f"image/{ext}"
        logo_src = f"data:{mime};base64,{logo_data}"

    template = env.get_template("report_template.html")
    html_content = template.render(
        report=report_data,
        patient_id=patient_id,
        generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
        L=get_labels(language),
        lang=language,
        pdf_css=pdf_css,
        logo_src=logo_src,
    )

    with open(str(output_path), "wb") as f:
        result = pisa.CreatePDF(html_content, dest=f, encoding="utf-8")

    if result.err:
        raise RuntimeError(f"PDF oluşturma hatası: {result.err}")


def _status_icon(status: str) -> str:
    mapping = {
        "KARŞILANDI": "[OK]", "MET": "[OK]",
        "KARŞILANMADI": "[X]", "NOT MET": "[X]",
        "BİLİNMİYOR": "[?]", "UNKNOWN": "[?]",
        "NORMAL": "[OK]", "ABOVE THRESHOLD": "[OK]", "EŞİK ÜSTÜ": "[OK]",
        "YÜKSEK": "[^]", "HIGH": "[^]",
        "DÜŞÜK": "[v]", "LOW": "[v]",
        "EŞİK ALTI": "[X]", "BELOW THRESHOLD": "[X]",
    }
    return mapping.get(status, "-")


def _status_class(status: str) -> str:
    if status in ("KARŞILANDI", "NORMAL", "EŞİK ÜSTÜ", "MET", "ABOVE THRESHOLD"):
        return "status-ok"
    if status in ("KARŞILANMADI", "EŞİK ALTI", "NOT MET", "BELOW THRESHOLD"):
        return "status-fail"
    return "status-warn"


def _durum_icon(durum: str) -> str:
    if "UYGUN" in durum and "DEĞİL" not in durum and "KOŞUL" not in durum:
        return "[OK]"
    if "UYGUN_DEGIL" in durum or "DEĞİL" in durum or "NOT ELIGIBLE" in durum:
        return "[X]"
    return "[!]"


def _durum_class(durum: str) -> str:
    if "UYGUN" in durum and "DEĞİL" not in durum and "KOŞUL" not in durum:
        return "decision-ok"
    if "UYGUN_DEGIL" in durum or "DEĞİL" in durum or "NOT ELIGIBLE" in durum:
        return "decision-fail"
    return "decision-warn"


def _risk_class(risk: str) -> str:
    if risk in ("DÜŞÜK", "LOW"):
        return "risk-low"
    if risk in ("ORTA", "MODERATE"):
        return "risk-medium"
    if risk in ("YÜKSEK", "HIGH", "KRİTİK"):
        return "risk-high"
    return ""
