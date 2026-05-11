import asyncio
from pathlib import Path
from datetime import datetime

from fpdf import FPDF

BASE_DIR = Path(__file__).parent.parent
LOGO_PATH = BASE_DIR / "static" / "images" / "logo.png"
DEJAVU_FONT = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
DEJAVU_BOLD = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")

CRIMSON  = (107, 15,  26)
CRIMSON2 = (155, 28,  51)
WHITE    = (255, 255, 255)
LGRAY    = (245, 247, 250)
DGRAY    = ( 55,  71,  79)
GREEN    = ( 46, 125,  50)
GREEN_BG = (232, 245, 233)
RED      = (198,  40,  40)
RED_BG   = (255, 235, 238)
ORANGE   = (230, 81,   0)
ORANGE_BG= (255, 248, 225)
TEXT     = ( 26,  32,  51)
BLUE_LBL = ( 90, 106, 138)


async def generate_report_pdf(report_data: dict, patient_id: str, output_path: Path, language: str = "tr", show_logo: bool = False):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _render_pdf, report_data, patient_id, output_path, language, show_logo)


def _render_pdf(report_data: dict, patient_id: str, output_path: Path, language: str = "tr", show_logo: bool = False):
    from translations import get_labels

    L = get_labels(language)
    generated_at = datetime.now().strftime("%d.%m.%Y %H:%M")

    pdf = GenexaPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=14)

    if DEJAVU_FONT.exists():
        pdf.add_font("DejaVu", "", str(DEJAVU_FONT))
    if DEJAVU_BOLD.exists():
        pdf.add_font("DejaVu", "B", str(DEJAVU_BOLD))
    pdf.FONT = "DejaVu" if DEJAVU_FONT.exists() else "Helvetica"

    pdf.add_page()
    pdf.set_margins(12, 12, 12)

    # ── Header ──────────────────────────────────────────────────────────────
    pdf.set_fill_color(*CRIMSON)
    pdf.set_text_color(*WHITE)
    header_h = 28 if show_logo and LOGO_PATH.exists() else 22
    pdf.rect(0, 0, 210, header_h, "F")

    if show_logo and LOGO_PATH.exists():
        try:
            pdf.image(str(LOGO_PATH), x=12, y=4, h=14)
        except Exception:
            pass
        txt_x = 70
    else:
        txt_x = 12

    pdf.set_xy(txt_x, 5)
    pdf.set_font(pdf.FONT, "B", 13)
    pdf.cell(0, 7, L.get("report_title", "KLİNİK ARAŞTIRMA DEĞERLENDİRME RAPORU"), ln=True)
    pdf.set_x(txt_x)
    pdf.set_font(pdf.FONT, "", 8)
    pdf.set_text_color(240, 192, 200)
    pdf.cell(0, 5, L.get("report_subtitle", "Genexa Clinical Research Organization — Protokol Uygunluk Analizi"), ln=True)
    pdf.set_x(txt_x)
    pdf.set_text_color(217, 160, 170)
    pdf.set_font(pdf.FONT, "", 7.5)
    meta_line = f"{L.get('patient_label','Hasta')}: {patient_id}   |   {L.get('report_date_label','Rapor Tarihi')}: {generated_at}"
    pdf.cell(0, 5, meta_line, ln=True)

    pdf.set_text_color(*TEXT)
    pdf.set_y(header_h + 4)

    # ── Section 1: Hasta Özeti ───────────────────────────────────────────────
    ozet = report_data.get("hasta_ozet", {})
    pdf.section_header(f"01  {L.get('s1_title','HASTA KİMLİK ÖZETİ')}")
    rows = [
        (L.get("full_name", "Ad Soyad"),     ozet.get("isim_soyisim", "")),
        (L.get("dob", "Doğum Tarihi"),        ozet.get("dogum_tarihi", "")),
        (L.get("age", "Yaş"),                 ozet.get("yas", "")),
        (L.get("gender", "Cinsiyet"),         ozet.get("cinsiyet", "")),
        (L.get("weight", "Ağırlık"),          ozet.get("agirlik", "")),
        (L.get("height", "Boy"),              ozet.get("boy", "")),
        (L.get("bsa", "BSA"),                 ozet.get("bsa", "")),
        (L.get("diagnosis", "Tanı"),          ozet.get("tani", "")),
        (L.get("mutation", "Mutasyon"),       ozet.get("mutasyon", "")),
    ]
    for i, (label, val) in enumerate(rows):
        if val:
            pdf.info_row(label, val, i % 2 == 0)
    pdf.ln(3)

    # ── Section 2: Uygunluk ─────────────────────────────────────────────────
    uyg = report_data.get("uygunluk_degerlendirmesi", {})
    pdf.section_header(f"02  {L.get('s2_title','PROTOKOL UYGUNLUK DEĞERLENDİRMESİ')} — {uyg.get('ozet','')}")
    cols = [
        (L.get("th_category","Kategori"), 30),
        (L.get("th_criterion","Kriter"), 45),
        (L.get("th_expected","Beklenen"), 40),
        (L.get("th_patient_value","Hasta Değeri"), 35),
        (L.get("th_status","Durum"), 30),
    ]
    pdf.table_header(cols)
    for i, k in enumerate(uyg.get("kriterler", [])):
        durum = k.get("durum", "")
        color = GREEN if "KARŞILANDI" in durum or durum in ("MET",) else (RED if "KARŞILANMADI" in durum or durum in ("NOT MET",) else ORANGE)
        pdf.table_row([
            (k.get("kategori",""), 30),
            (k.get("kriter",""), 45),
            (k.get("beklenen",""), 40),
            (k.get("hasta_degeri",""), 35),
            (f"[{'OK' if color==GREEN else 'X' if color==RED else '!'}] {durum}", 30),
        ], i % 2 == 0, status_col=4, status_color=color)
    pdf.ln(3)

    # ── Section 3: Biyomarker ────────────────────────────────────────────────
    bio = report_data.get("biyomarker_analizi", {})
    pdf.section_header(f"03  {L.get('s3_title','BİYOMARKER ANALİZİ')}")
    pdf.summary_text(bio.get("ozet",""))
    cols = [
        (L.get("th_parameter","Parametre"), 38),
        (L.get("th_patient_val","Hasta Değeri"), 28),
        (L.get("th_threshold","Protokol Eşiği"), 28),
        (L.get("th_unit","Birim"), 18),
        (L.get("th_status","Durum"), 28),
        (L.get("th_clinical","Klinik Yorum"), 42),
    ]
    pdf.table_header(cols)
    for i, b in enumerate(bio.get("degerler", [])):
        durum = b.get("durum","")
        color = GREEN if durum in ("NORMAL","ABOVE THRESHOLD","EŞİK ÜSTÜ") else (RED if durum in ("YÜKSEK","HIGH","EŞİK ALTI","BELOW THRESHOLD") else ORANGE)
        pdf.table_row([
            (b.get("parametre",""), 38),
            (b.get("hasta_degeri",""), 28),
            (b.get("protokol_esigi",""), 28),
            (b.get("birim",""), 18),
            (durum, 28),
            (b.get("klinik_yorum",""), 42),
        ], i % 2 == 0, status_col=4, status_color=color)
    pdf.ln(3)

    # ── Section 4: Klinik Bulgular ───────────────────────────────────────────
    klin = report_data.get("klinik_bulgular", {})
    pdf.section_header(f"04  {L.get('s4_title','KLİNİK BULGULAR')}")
    pdf.summary_text(klin.get("ozet",""))
    cols = [
        (L.get("th_finding","Bulgu"), 55),
        (L.get("th_value","Değer"), 40),
        (L.get("th_interpretation","Yorum"), 89),
    ]
    pdf.table_header(cols)
    for i, b in enumerate(klin.get("bulgular", [])):
        pdf.table_row([
            (b.get("bulgu",""), 55),
            (b.get("deger",""), 40),
            (b.get("yorum",""), 89),
        ], i % 2 == 0)
    pdf.ln(3)

    # ── Section 5: Kohort ────────────────────────────────────────────────────
    koh = report_data.get("kohort_onerisi", {})
    pdf.section_header(f"05  {L.get('s5_title','KOHORT ÖNERİSİ')}")
    pdf.set_fill_color(255, 240, 242)
    pdf.set_draw_color(155, 28, 51)
    x = pdf.get_x(); y = pdf.get_y()
    pdf.set_font(pdf.FONT, "B", 10)
    pdf.set_text_color(*CRIMSON)
    pdf.cell(0, 7, f"{koh.get('onerilen_part','')} — {koh.get('onerilen_kohort','')}", ln=True)
    pdf.set_text_color(*TEXT)
    pdf.kv_row(L.get("starting_dose","Başlangıç Dozu"), koh.get("baslangic_dozu",""))
    pdf.kv_row(L.get("rationale","Gerekçe"), koh.get("gerekce",""))
    if koh.get("ek_notlar"):
        pdf.kv_row(L.get("additional_notes","Ek Notlar"), koh.get("ek_notlar",""))
    pdf.ln(3)

    # ── Section 6: Risk ──────────────────────────────────────────────────────
    rsk = report_data.get("risk_degerlendirmesi", {})
    pdf.section_header(f"06  {L.get('s6_title','RİSK DEĞERLENDİRMESİ')} — {L.get('general_risk','Genel Risk')}: {rsk.get('genel_risk','')}")
    for r in rsk.get("riskler", []):
        sev = r.get("seviye","")
        color = GREEN if sev in ("DÜŞÜK","LOW") else (RED if sev in ("YÜKSEK","HIGH") else ORANGE)
        pdf.risk_row(sev, r.get("risk",""), r.get("aciklama",""), color)
    if rsk.get("onerilen_izlem"):
        pdf.kv_row(L.get("recommended_monitoring", "Önerilen İzlem"), rsk.get("onerilen_izlem", ""))
    pdf.ln(3)

    # ── Section 7: Genel Karar ───────────────────────────────────────────────
    karar = report_data.get("genel_karar", {})
    pdf.section_header(f"07  {L.get('s7_title','GENEL KARAR')}")
    durum = karar.get("durum","")
    if "UYGUN_DEGIL" in durum or "NOT ELIGIBLE" in durum or durum == "UYGUN DEĞİL":
        bg, border, tc = RED_BG, RED, RED
        icon = "[X]"
    elif "KOŞULLU" in durum or "CONDITIONAL" in durum:
        bg, border, tc = ORANGE_BG, ORANGE, ORANGE
        icon = "[!]"
    else:
        bg, border, tc = GREEN_BG, GREEN, GREEN
        icon = "[OK]"

    pdf.set_fill_color(*bg)
    pdf.set_draw_color(*border)
    pdf.rect(pdf.get_x(), pdf.get_y(), 186, 2, "F")
    pdf.set_font(pdf.FONT, "B", 11)
    pdf.set_text_color(*tc)
    pdf.cell(0, 8, f"{icon}  {karar.get('metin','')}", ln=True)
    pdf.set_font(pdf.FONT, "", 8.5)
    pdf.set_text_color(*DGRAY)
    pdf.multi_cell(0, 5, karar.get("detay",""))
    pdf.ln(3)

    # ── Footer ───────────────────────────────────────────────────────────────
    pdf.set_y(-16)
    pdf.set_draw_color(208, 217, 232)
    pdf.line(12, pdf.get_y(), 198, pdf.get_y())
    pdf.set_font(pdf.FONT, "", 7)
    pdf.set_text_color(*DGRAY)
    footer = f"{L.get('footer_auto','Bu rapor otomatik olarak üretilmiştir.')}   |   {L.get('footer_disclaimer','Klinik kararlar yetkili araştırmacı tarafından verilmelidir.')}   |   {generated_at}"
    pdf.cell(0, 5, footer, align="C")

    pdf.output(str(output_path))


class GenexaPDF(FPDF):
    FONT = "Helvetica"

    def section_header(self, title: str):
        self.set_fill_color(*CRIMSON)
        self.set_text_color(*WHITE)
        self.set_font(self.FONT, "B", 9)
        self.cell(0, 7, title, fill=True, new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(*TEXT)
        self.ln(1)

    def info_row(self, label: str, value: str, fill: bool = False):
        if fill:
            self.set_fill_color(*LGRAY)
        self.set_font(self.FONT, "", 7.5)
        self.set_text_color(*BLUE_LBL)
        self.cell(55, 5.5, label, fill=fill)
        self.set_font(self.FONT, "B", 8)
        self.set_text_color(*TEXT)
        self.multi_cell(0, 5.5, value, fill=fill, new_x="LMARGIN", new_y="NEXT")

    def table_header(self, cols: list):
        self.set_fill_color(*CRIMSON2)
        self.set_text_color(*WHITE)
        self.set_font(self.FONT, "B", 7.5)
        for text, width in cols:
            self.cell(width, 6, text, border=1, fill=True)
        self.ln()
        self.set_text_color(*TEXT)

    def table_row(self, cells: list, fill: bool = False, status_col: int = -1, status_color=None):
        if fill:
            self.set_fill_color(*LGRAY)
        self.set_font(self.FONT, "", 7.5)
        x_start = self.get_x()
        y_start = self.get_y()
        max_h = 5.5
        for i, (text, width) in enumerate(cells):
            if i == status_col and status_color:
                self.set_text_color(*status_color)
                self.set_font(self.FONT, "B", 7.5)
            else:
                self.set_text_color(*TEXT)
                self.set_font(self.FONT, "", 7.5)
            self.multi_cell(width, 5.5, text, border="B", fill=fill, new_x="RIGHT", new_y="TOP")
        self.set_xy(x_start, y_start + max_h)
        self.ln(0.5)
        self.set_text_color(*TEXT)

    def summary_text(self, text: str):
        if not text:
            return
        self.set_font(self.FONT, "", 8)
        self.set_text_color(55, 71, 79)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def kv_row(self, label: str, value: str):
        self.set_font(self.FONT, "B", 8)
        self.set_text_color(*BLUE_LBL)
        self.cell(40, 5.5, label + ":")
        self.set_font(self.FONT, "", 8)
        self.set_text_color(*TEXT)
        self.multi_cell(0, 5.5, value, new_x="LMARGIN", new_y="NEXT")

    def risk_row(self, level: str, name: str, desc: str, color):
        self.set_font(self.FONT, "B", 8)
        self.set_text_color(*color)
        self.cell(22, 5.5, level)
        self.set_font(self.FONT, "B", 8)
        self.set_text_color(*TEXT)
        self.cell(50, 5.5, name)
        self.set_font(self.FONT, "", 7.5)
        self.set_text_color(*DGRAY)
        self.multi_cell(0, 5.5, desc, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)
