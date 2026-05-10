"""
Örnek hasta PDF dosyası oluşturucu.
Çalıştır: python3 create_sample_patient.py
Çıktı: /tmp/ornek_hasta_104.pdf
"""
from weasyprint import HTML, CSS

HTML_CONTENT = """
<!DOCTYPE html>
<html lang="tr">
<head><meta charset="UTF-8"><title>Hasta Veri Formu</title></head>
<body>

<h1>HASTA DEĞERLENDİRME FORMU</h1>
<h2>Protokol: CRN04894-13 — Atumelnant (Pediatrik KAH Faz 2/3)</h2>
<p><strong>Merkez:</strong> Genexa CRO Araştırma Merkezi &nbsp;|&nbsp;
   <strong>Başvuru Tarihi:</strong> 08 Mayıs 2026</p>

<hr>

<h3>1. KİMLİK BİLGİLERİ</h3>
<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr><td width="35%"><strong>Hasta Kodu</strong></td><td>Hasta-104</td></tr>
  <tr><td><strong>Ad Soyad</strong></td><td>A.Y. (gizlenmiş)</td></tr>
  <tr><td><strong>Doğum Tarihi</strong></td><td>12 Mart 2012</td></tr>
  <tr><td><strong>Yaş</strong></td><td>14 yıl 2 ay</td></tr>
  <tr><td><strong>Cinsiyet</strong></td><td>Erkek</td></tr>
  <tr><td><strong>Ağırlık</strong></td><td>52 kg</td></tr>
  <tr><td><strong>Boy</strong></td><td>158 cm</td></tr>
  <tr><td><strong>Vücut Yüzey Alanı (BSA)</strong></td><td>1.50 m²</td></tr>
</table>

<h3>2. TANI VE GENETİK BİLGİLER</h3>
<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr><td width="35%"><strong>Primer Tanı</strong></td><td>Klasik Konjenital Adrenal Hiperplazi (KAH) — Tuz Kaybettiren Form</td></tr>
  <tr><td><strong>Mutasyon</strong></td><td>CYP21A2 biallelik mutasyon — konfirme edildi</td></tr>
  <tr><td><strong>Tanı Yaşı</strong></td><td>Yenidoğan döneminde (3. gün)</td></tr>
  <tr><td><strong>Hastalık Süresi</strong></td><td>14 yıl</td></tr>
</table>

<h3>3. MEVCUT TEDAVİ</h3>
<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr><td width="35%"><strong>İlaç</strong></td><td>Hidrokortizon (Kortef)</td></tr>
  <tr><td><strong>Günlük Doz</strong></td><td>20 mg/gün (bölünmüş dozlar: 10mg sabah, 7mg öğle, 3mg akşam)</td></tr>
  <tr><td><strong>BSA'ya Göre Doz</strong></td><td>13.3 mg/m²/gün</td></tr>
  <tr><td><strong>Tedavi Süresi (stabil)</strong></td><td>Son 3 aydır değişmeden devam ediyor</td></tr>
  <tr><td><strong>Ek İlaç</strong></td><td>Fludrokortizon 0.1 mg/gün</td></tr>
  <tr><td><strong>NaCl Takviyesi</strong></td><td>Yok</td></tr>
</table>

<h3>4. BİYOKİMYASAL / LABORATUVAR SONUÇLARI</h3>
<p><em>Sonuçlar son 4 hafta içinde alınmıştır.</em></p>
<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr bgcolor="#f0f0f0">
    <th>Parametre</th><th>Değer</th><th>Birim</th><th>Referans Aralığı</th>
  </tr>
  <tr><td>Androstenedion (A4)</td><td><strong>380</strong></td><td>ng/dL</td><td>ULN: 115 ng/dL (yaşa göre)</td></tr>
  <tr><td>17-Hidroksiprogesteron (17-OHP)</td><td><strong>2500</strong></td><td>ng/dL</td><td>Normal: &lt;100 ng/dL</td></tr>
  <tr><td>Testosteron (Total)</td><td>420</td><td>ng/dL</td><td>Yaşa göre yüksek</td></tr>
  <tr><td>DHEA-S</td><td>310</td><td>µg/dL</td><td>Referans üstü</td></tr>
  <tr><td>Sabah Kortizol (08:00)</td><td>8.2</td><td>µg/dL</td><td>6–18 µg/dL</td></tr>
  <tr><td>ACTH</td><td>185</td><td>pg/mL</td><td>Normal: &lt;46 pg/mL</td></tr>
  <tr><td>Renin (aktif)</td><td>3.1</td><td>ng/mL/saat</td><td>Normal aralıkta</td></tr>
  <tr><td>Sodyum (Na)</td><td>139</td><td>mEq/L</td><td>136–145 mEq/L ✓</td></tr>
  <tr><td>Potasyum (K)</td><td>4.1</td><td>mEq/L</td><td>3.5–5.0 mEq/L ✓</td></tr>
  <tr><td>AST</td><td>24</td><td>U/L</td><td>&lt;40 U/L ✓</td></tr>
  <tr><td>ALT</td><td>19</td><td>U/L</td><td>&lt;40 U/L ✓</td></tr>
  <tr><td>Kreatinin</td><td>0.72</td><td>mg/dL</td><td>Normal ✓</td></tr>
  <tr><td>HbA1c</td><td>5.4</td><td>%</td><td>&lt;5.7% ✓</td></tr>
  <tr><td>Açlık Glukozu</td><td>88</td><td>mg/dL</td><td>70–100 mg/dL ✓</td></tr>
</table>

<h3>5. KLİNİK BULGULAR</h3>
<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr><td width="35%"><strong>Tanner Evresi</strong></td><td>Evre 4 (pubik kıllanma G4, testis hacmi 12 mL bilateral)</td></tr>
  <tr><td><strong>Kemik Yaşı</strong></td><td>15 yıl 6 ay (kronolojik yaşa göre ileri)</td></tr>
  <tr><td><strong>Boy SDS</strong></td><td>-0.8 (yaşa uygun normal alt sınırda)</td></tr>
  <tr><td><strong>Testis Adrenal Rest Tümörü (TART)</strong></td><td>Yok — skrotal ultrason normal (son 1 ay)</td></tr>
  <tr><td><strong>EKG — QTcF</strong></td><td>410 ms (normal &lt;450 ms) ✓</td></tr>
  <tr><td><strong>Tansiyon</strong></td><td>118/72 mmHg (normal)</td></tr>
  <tr><td><strong>Cushing Bulguları</strong></td><td>Yok</td></tr>
  <tr><td><strong>Akne</strong></td><td>Hafif (grade 1)</td></tr>
  <tr><td><strong>Genel Durum</strong></td><td>İyi, aktif sporcu (futbol)</td></tr>
</table>

<h3>6. ARAŞTIRMA İÇİN ONAY</h3>
<table border="1" cellpadding="6" cellspacing="0" width="100%">
  <tr><td width="35%"><strong>Aydınlatılmış Onam</strong></td><td>Ebeveyn ve çocuk onayı alındı — 05 Mayıs 2026</td></tr>
  <tr><td><strong>Ebeveyn/Vasi</strong></td><td>Anne — imzalı form mevcut</td></tr>
  <tr><td><strong>Çocuk Onayı (Assent)</strong></td><td>Alındı (14 yaş üzeri)</td></tr>
  <tr><td><strong>Daha Önce Araştırma Katılımı</strong></td><td>Hayır</td></tr>
  <tr><td><strong>Gebelik (uygulanamaz)</strong></td><td>Erkek hasta</td></tr>
</table>

<h3>7. EK BİLGİLER</h3>
<p>Hasta ve ailesi protokol hakkında bilgilendirilmiştir. Düzenli takip randevularına uyum iyi.
Başka kronik hastalık bulunmamaktadır. Sigara/alkol kullanımı yok.
Son 4 hafta içinde başka ilaç kullanımı bulunmamaktadır (NSAİİ dahil).</p>

<p>Son adrenal kriz: 3 yıl önce (ateşli hastalık sırasında, hastaneye yatış gerektirdi).</p>

<hr>
<p><em>Bu form araştırma merkezi tarafından hazırlanmıştır. Genexa CRO — Mayıs 2026</em></p>

</body>
</html>
"""

CSS_CONTENT = """
@page { size: A4; margin: 20mm 18mm; }
body { font-family: Arial, sans-serif; font-size: 10pt; color: #1a1a1a; line-height: 1.5; }
h1 { font-size: 14pt; color: #0D2B5E; border-bottom: 2px solid #0D2B5E; padding-bottom: 6px; }
h2 { font-size: 11pt; color: #1565C0; margin-bottom: 4px; }
h3 { font-size: 10.5pt; color: #0D2B5E; margin-top: 16px; margin-bottom: 4px; }
table { width: 100%; border-collapse: collapse; margin-bottom: 10px; font-size: 9.5pt; }
th { background: #0D2B5E; color: white; padding: 6px 8px; text-align: left; }
td { padding: 5px 8px; border: 1px solid #ccc; }
tr:nth-child(even) td { background: #f9f9f9; }
hr { border: none; border-top: 1px solid #ccc; margin: 12px 0; }
p { margin: 4px 0 8px; }
"""

if __name__ == "__main__":
    output = "/tmp/ornek_hasta_104.pdf"
    HTML(string=HTML_CONTENT).write_pdf(output, stylesheets=[CSS(string=CSS_CONTENT)])
    print(f"✓ Örnek hasta PDF oluşturuldu: {output}")
