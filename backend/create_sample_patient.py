"""
Örnek hasta PDF dosyası oluşturucu (fpdf2 kullanır — sistem bağımlılığı yok).
Çalıştır: /opt/genexa-protokol/.venv/bin/python3 create_sample_patient.py
Çıktı: /tmp/ornek_hasta_104.pdf
"""
from fpdf import FPDF

OUTPUT = "/tmp/ornek_hasta_104.pdf"

NAVY  = (13, 43, 94)
BLUE  = (21, 101, 192)
WHITE = (255, 255, 255)
LGRAY = (245, 247, 250)
DGRAY = (55, 71, 79)
GREEN = (46, 125, 50)


class ReportPDF(FPDF):
    def header(self):
        pass

    def section_header(self, title):
        self.set_fill_color(*NAVY)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 9)
        self.cell(0, 7, title, fill=True, ln=True, border=0)
        self.set_text_color(0, 0, 0)

    def two_col_row(self, label, value, fill=False):
        self.set_font("Helvetica", "", 8.5)
        if fill:
            self.set_fill_color(*LGRAY)
        self.set_font("Helvetica", "", 8)
        self.cell(65, 6, label, border="B", fill=fill)
        self.set_font("Helvetica", "B", 8.5)
        self.cell(0, 6, value, border="B", fill=fill, ln=True)

    def table_header(self, cols):
        self.set_fill_color(*BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 7.5)
        for text, width in cols:
            self.cell(width, 6, text, border=1, fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)

    def table_row(self, cells, fill=False):
        if fill:
            self.set_fill_color(*LGRAY)
        self.set_font("Helvetica", "", 8)
        for text, width in cells:
            self.multi_cell(width, 5.5, text, border="B", fill=fill, ln=3)
        self.ln()


pdf = ReportPDF(orientation="P", unit="mm", format="A4")
pdf.set_auto_page_break(auto=True, margin=15)
pdf.add_page()
pdf.set_margins(15, 15, 15)

# ── Başlık ─────────────────────────────────────────────────────────────────────
pdf.set_fill_color(*NAVY)
pdf.set_text_color(*WHITE)
pdf.set_font("Helvetica", "B", 14)
pdf.cell(0, 9, "HASTA DEGERLENDIRME FORMU", fill=True, ln=True, align="C")
pdf.set_font("Helvetica", "", 9)
pdf.cell(0, 6, "Protokol: CRN04894-13 - Atumelnant (Pediatrik KAH Faz 2/3)", fill=True, ln=True, align="C")
pdf.set_font("Helvetica", "", 8)
pdf.cell(0, 5, "Merkez: Genexa CRO Arastirma Merkezi  |  Basvuru: 08 Mayis 2026", fill=True, ln=True, align="C")
pdf.set_text_color(0, 0, 0)
pdf.ln(4)

# ── 1. Kimlik ──────────────────────────────────────────────────────────────────
pdf.section_header("1. KIMLIK BILGILERI")
pdf.set_font("Helvetica", "", 8.5)
rows = [
    ("Hasta Kodu", "Hasta-104"),
    ("Ad Soyad", "A.Y. (gizlenmis)"),
    ("Dogum Tarihi", "12 Mart 2012"),
    ("Yas", "14 yil 2 ay"),
    ("Cinsiyet", "Erkek"),
    ("Agirlik", "52 kg"),
    ("Boy", "158 cm"),
    ("Vucut Yuzey Alani (BSA)", "1.50 m2"),
]
for i, (k, v) in enumerate(rows):
    pdf.two_col_row(k, v, fill=(i % 2 == 0))
pdf.ln(3)

# ── 2. Tanı ────────────────────────────────────────────────────────────────────
pdf.section_header("2. TANI VE GENETIK BILGILER")
rows = [
    ("Primer Tani", "Klasik Konjenital Adrenal Hiperplazi (KAH) - Tuz Kaybettiren Form"),
    ("Mutasyon", "CYP21A2 biallelik mutasyon - konfirme edildi"),
    ("Tani Yasi", "Yenidogan doneminde (3. gun)"),
    ("Hastalik Suresi", "14 yil"),
]
for i, (k, v) in enumerate(rows):
    pdf.two_col_row(k, v, fill=(i % 2 == 0))
pdf.ln(3)

# ── 3. Tedavi ──────────────────────────────────────────────────────────────────
pdf.section_header("3. MEVCUT TEDAVI")
rows = [
    ("Ilac", "Hidrokortizon (Kortef)"),
    ("Gunluk Doz", "20 mg/gun (10mg sabah, 7mg ogle, 3mg aksam)"),
    ("BSA'ya Gore Doz", "13.3 mg/m2/gun"),
    ("Tedavi Suresi (stabil)", "Son 3 aydir degismeden devam ediyor"),
    ("Ek Ilac", "Fludrokortizon 0.1 mg/gun"),
    ("NaCl Takviyesi", "Yok"),
]
for i, (k, v) in enumerate(rows):
    pdf.two_col_row(k, v, fill=(i % 2 == 0))
pdf.ln(3)

# ── 4. Lab ─────────────────────────────────────────────────────────────────────
pdf.section_header("4. BIYOKIMYASAL / LABORATUVAR SONUCLARI")
pdf.set_font("Helvetica", "I", 7.5)
pdf.cell(0, 5, "Sonuclar son 4 hafta icinde alinmistir.", ln=True)
pdf.ln(1)

cols = [("Parametre", 60), ("Deger", 25), ("Birim", 25), ("Referans", 70)]
pdf.table_header(cols)
lab = [
    ("Androstenedion (A4)", "380", "ng/dL", "ULN: 115 ng/dL"),
    ("17-Hidroksiprog. (17-OHP)", "2500", "ng/dL", "Normal: <100 ng/dL"),
    ("Testosteron (Total)", "420", "ng/dL", "Yasa gore yuksek"),
    ("DHEA-S", "310", "ug/dL", "Referans ustu"),
    ("Sabah Kortizol (08:00)", "8.2", "ug/dL", "6-18 ug/dL"),
    ("ACTH", "185", "pg/mL", "Normal: <46 pg/mL"),
    ("Renin (aktif)", "3.1", "ng/mL/saat", "Normal aralikta"),
    ("Sodyum (Na)", "139", "mEq/L", "136-145 mEq/L [NORMAL]"),
    ("Potasyum (K)", "4.1", "mEq/L", "3.5-5.0 mEq/L [NORMAL]"),
    ("AST", "24", "U/L", "<40 U/L [NORMAL]"),
    ("ALT", "19", "U/L", "<40 U/L [NORMAL]"),
    ("Kreatinin", "0.72", "mg/dL", "Normal"),
    ("HbA1c", "5.4", "%", "<5.7% [NORMAL]"),
    ("Aclik Glukozu", "88", "mg/dL", "70-100 mg/dL [NORMAL]"),
]
for i, row in enumerate(lab):
    pdf.table_row([(v, w) for v, (_, w) in zip(row, cols)], fill=(i % 2 == 0))
pdf.ln(3)

# ── 5. Klinik ──────────────────────────────────────────────────────────────────
pdf.section_header("5. KLINIK BULGULAR")
rows = [
    ("Tanner Evresi", "Evre 4 (G4, testis hacmi 12 mL bilateral)"),
    ("Kemik Yasi", "15 yil 6 ay (kronolojik yasa gore ileri)"),
    ("Boy SDS", "-0.8 (normal alt sinirda)"),
    ("TART (Testis Adrenal Rest)", "Yok - skrotal ultrason normal (son 1 ay)"),
    ("EKG - QTcF", "410 ms (normal <450 ms) [NORMAL]"),
    ("Tansiyon", "118/72 mmHg (normal)"),
    ("Cushing Bulgulari", "Yok"),
    ("Akne", "Hafif (grade 1)"),
    ("Genel Durum", "Iyi, aktif sporcu (futbol)"),
]
for i, (k, v) in enumerate(rows):
    pdf.two_col_row(k, v, fill=(i % 2 == 0))
pdf.ln(3)

# ── 6. Onay ───────────────────────────────────────────────────────────────────
pdf.section_header("6. ARASTIRMA ICIN ONAY")
rows = [
    ("Aydinlatilmis Onam", "Ebeveyn ve cocuk onavi alindi - 05 Mayis 2026"),
    ("Ebeveyn/Vasi", "Anne - imzali form mevcut"),
    ("Cocuk Onavi (Assent)", "Alindi (14 yas uzeri)"),
    ("Daha Once Katilim", "Hayir"),
    ("Gebelik", "Erkek hasta - gecerli degil"),
]
for i, (k, v) in enumerate(rows):
    pdf.two_col_row(k, v, fill=(i % 2 == 0))
pdf.ln(3)

# ── 7. Ek ─────────────────────────────────────────────────────────────────────
pdf.section_header("7. EK BILGILER")
pdf.set_font("Helvetica", "", 8.5)
pdf.multi_cell(0, 5.5,
    "Hasta ve ailesi protokol hakkinda bilgilendirilmistir. Duzenli takip randevularina uyum iyi. "
    "Baska kronik hastalik bulunmamaktadir. Sigara/alkol kullanimi yok. "
    "Son 4 hafta icinde baska ilac kullanimi bulunmamaktadir (NSAII dahil). "
    "Son adrenal kriz: 3 yil once (atesleli hastalik sirasinda, hastaneye yatis gerektirdi)."
)
pdf.ln(4)

# ── Footer ─────────────────────────────────────────────────────────────────────
pdf.set_font("Helvetica", "I", 7.5)
pdf.set_text_color(*DGRAY)
pdf.cell(0, 5, "Bu form arastirma merkezi tarafindan hazirlanmistir. Genexa CRO - Mayis 2026", align="C", ln=True)

pdf.output(OUTPUT)
print(f"Ornek hasta PDF olusturuldu: {OUTPUT}")
