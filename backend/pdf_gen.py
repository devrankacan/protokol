import asyncio
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"


async def generate_report_pdf(report_data: dict, patient_id: str, output_path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _render_pdf, report_data, patient_id, output_path)


def _render_pdf(report_data: dict, patient_id: str, output_path: Path):
    from weasyprint import HTML, CSS

    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)))
    env.filters["status_icon"] = _status_icon
    env.filters["status_class"] = _status_class
    env.filters["durum_icon"] = _durum_icon
    env.filters["durum_class"] = _durum_class
    env.filters["risk_class"] = _risk_class

    template = env.get_template("report_template.html")
    html_content = template.render(
        report=report_data,
        patient_id=patient_id,
        generated_at=datetime.now().strftime("%d.%m.%Y %H:%M"),
    )

    css = CSS(string=_pdf_css())
    HTML(string=html_content, base_url=str(BASE_DIR)).write_pdf(
        str(output_path),
        stylesheets=[css],
    )


def _status_icon(status: str) -> str:
    mapping = {
        "KARŞILANDI": "✅",
        "KARŞILANMADI": "❌",
        "BİLİNMİYOR": "⚠️",
        "NORMAL": "✅",
        "YÜKSEK": "⬆️",
        "DÜŞÜK": "⬇️",
        "EŞİK ÜSTÜ": "✅",
        "EŞİK ALTI": "❌",
    }
    return mapping.get(status, "—")


def _status_class(status: str) -> str:
    if status in ("KARŞILANDI", "NORMAL", "EŞİK ÜSTÜ"):
        return "status-ok"
    if status in ("KARŞILANMADI", "EŞİK ALTI"):
        return "status-fail"
    return "status-warn"


def _durum_icon(durum: str) -> str:
    if "UYGUN" in durum and "DEĞİL" not in durum and "KOŞUL" not in durum:
        return "✅"
    if "UYGUN_DEGIL" in durum or "DEĞİL" in durum:
        return "❌"
    if "KOŞUL" in durum or "KOSULLU" in durum:
        return "⚠️"
    return "—"


def _durum_class(durum: str) -> str:
    if "UYGUN" in durum and "DEĞİL" not in durum and "KOŞUL" not in durum:
        return "decision-ok"
    if "UYGUN_DEGIL" in durum or "DEĞİL" in durum:
        return "decision-fail"
    return "decision-warn"


def _risk_class(risk: str) -> str:
    if risk == "DÜŞÜK":
        return "risk-low"
    if risk == "ORTA":
        return "risk-medium"
    if risk in ("YÜKSEK", "KRİTİK"):
        return "risk-high"
    return "risk-unknown"


def _pdf_css() -> str:
    return """
@page {
    size: A4;
    margin: 15mm 12mm 15mm 12mm;
    @top-center {
        content: "GENEXA CRO — KLİNİK ARAŞTIRMA DEĞERLENDİRME RAPORU";
        font-size: 8pt;
        color: #666;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    @bottom-right {
        content: "Sayfa " counter(page) " / " counter(pages);
        font-size: 8pt;
        color: #666;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
    font-family: 'Helvetica Neue', Arial, sans-serif;
    font-size: 9pt;
    color: #1a1a2e;
    line-height: 1.4;
}

.report-header {
    background: linear-gradient(135deg, #0D2B5E 0%, #1565C0 100%);
    color: white;
    padding: 18px 20px;
    border-radius: 8px;
    margin-bottom: 16px;
}

.report-header h1 { font-size: 16pt; font-weight: 700; margin-bottom: 4px; }
.report-header .subtitle { font-size: 9pt; opacity: 0.85; }
.report-header .meta { margin-top: 10px; font-size: 8pt; opacity: 0.75; }

.section {
    margin-bottom: 14px;
    border: 1px solid #e0e6f0;
    border-radius: 6px;
    overflow: hidden;
    page-break-inside: avoid;
}

.section-header {
    background: #0D2B5E;
    color: white;
    padding: 8px 14px;
    font-weight: 700;
    font-size: 9.5pt;
    display: flex;
    align-items: center;
    gap: 8px;
}

.section-body { padding: 12px 14px; }

.info-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
}

.info-item { display: flex; flex-direction: column; }
.info-label { font-size: 7.5pt; color: #5a6a8a; text-transform: uppercase; letter-spacing: 0.3px; }
.info-value { font-size: 9.5pt; font-weight: 600; color: #0D2B5E; }

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
}

th {
    background: #1565C0;
    color: white;
    padding: 7px 9px;
    text-align: left;
    font-weight: 600;
    font-size: 8pt;
}

td {
    padding: 6px 9px;
    border-bottom: 1px solid #e8edf5;
    vertical-align: top;
}

tr:nth-child(even) td { background: #f5f7fa; }

.status-ok { color: #2E7D32; font-weight: 700; }
.status-fail { color: #C62828; font-weight: 700; }
.status-warn { color: #E65100; font-weight: 700; }

.risk-low { color: #2E7D32; font-weight: 700; }
.risk-medium { color: #E65100; font-weight: 700; }
.risk-high { color: #C62828; font-weight: 700; }
.risk-unknown { color: #546E7A; }

.decision-box {
    border-radius: 8px;
    padding: 14px 18px;
    margin-top: 4px;
}

.decision-ok { background: #E8F5E9; border: 2px solid #2E7D32; }
.decision-fail { background: #FFEBEE; border: 2px solid #C62828; }
.decision-warn { background: #FFF8E1; border: 2px solid #F57F17; }

.decision-title {
    font-size: 13pt;
    font-weight: 800;
    margin-bottom: 6px;
}

.decision-ok .decision-title { color: #1B5E20; }
.decision-fail .decision-title { color: #B71C1C; }
.decision-warn .decision-title { color: #E65100; }

.decision-detail { font-size: 8.5pt; color: #37474F; line-height: 1.5; }

.kohort-box {
    background: #E3F2FD;
    border: 1px solid #1565C0;
    border-radius: 6px;
    padding: 12px;
}

.kohort-box .kohort-title { font-size: 11pt; font-weight: 700; color: #0D2B5E; margin-bottom: 8px; }
.kohort-field { display: flex; gap: 8px; margin-bottom: 4px; font-size: 8.5pt; }
.kohort-field .label { color: #5a6a8a; min-width: 110px; }
.kohort-field .value { font-weight: 600; color: #0D2B5E; }

.risk-item {
    display: flex;
    gap: 12px;
    padding: 7px 10px;
    border-radius: 4px;
    margin-bottom: 5px;
    font-size: 8.5pt;
    align-items: flex-start;
}

.risk-item .risk-label { font-weight: 700; min-width: 70px; }
.risk-item.risk-low { background: #F1F8E9; }
.risk-item.risk-medium { background: #FFF3E0; }
.risk-item.risk-high { background: #FFEBEE; }

.footer {
    margin-top: 16px;
    padding-top: 10px;
    border-top: 1px solid #d0d9e8;
    font-size: 7.5pt;
    color: #78909C;
    text-align: center;
}
"""
