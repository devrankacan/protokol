import os
import json
import re
from pathlib import Path

import fitz  # PyMuPDF
import anthropic

MODEL = "claude-opus-4-7"

SYSTEM_PROMPT_TEMPLATE = """Sen Genexa CRO için çalışan uzman bir klinik araştırma değerlendirme asistanısın. Aşağıda bir klinik araştırma protokolünün tam metni bulunmaktadır.

PROTOKOL METNİ:
{protocol_text}

---

Görevin: Sana verilecek hasta verilerini bu protokoldeki dahil edilme/dışlanma kriterlerine, biyomarker eşiklerine, doz gereksinimlerine ve güvenlik kriterlerine göre değerlendirmek ve yapılandırılmış bir Türkçe rapor üretmektir.

RAPOR FORMATI: Yanıtını SADECE aşağıdaki JSON yapısında ver, başka hiçbir metin ekleme:

{{
  "hasta_id": "hasta kimlik bilgisi",
  "hasta_ozet": {{
    "isim_soyisim": "...",
    "dogum_tarihi": "...",
    "yas": "...",
    "cinsiyet": "...",
    "agirlik": "...",
    "boy": "...",
    "bsa": "...",
    "tani": "...",
    "mutasyon": "...",
    "basvuru_tarihi": "..."
  }},
  "uygunluk_degerlendirmesi": {{
    "ozet": "UYGUN / UYGUN DEĞİL / KOŞULLU UYGUN",
    "kriterler": [
      {{
        "kategori": "Dahil Etme / Dışlama",
        "kriter": "Kriterin adı",
        "beklenen": "Protokol beklentisi",
        "hasta_degeri": "Hastanın değeri",
        "durum": "KARŞILANDI / KARŞILANMADI / BİLİNMİYOR",
        "aciklama": "Kısa açıklama"
      }}
    ]
  }},
  "biyomarker_analizi": {{
    "ozet": "...",
    "degerler": [
      {{
        "parametre": "Parametre adı",
        "hasta_degeri": "...",
        "protokol_esigi": "...",
        "birim": "...",
        "durum": "NORMAL / YÜKSEK / DÜŞÜK / EŞİK ÜSTÜ / EŞİK ALTI",
        "klinik_yorum": "..."
      }}
    ]
  }},
  "klinik_bulgular": {{
    "ozet": "...",
    "bulgular": [
      {{
        "bulgu": "Bulgu adı",
        "deger": "...",
        "yorum": "..."
      }}
    ]
  }},
  "kohort_onerisi": {{
    "onerilen_part": "Part A / Part B / Part C / Uygun değil",
    "onerilen_kohort": "Kohort 1 / Kohort 2 / vb.",
    "baslangic_dozu": "...",
    "gerekce": "...",
    "ek_notlar": "..."
  }},
  "risk_degerlendirmesi": {{
    "genel_risk": "DÜŞÜK / ORTA / YÜKSEK",
    "riskler": [
      {{
        "risk": "Risk adı",
        "seviye": "DÜŞÜK / ORTA / YÜKSEK",
        "aciklama": "..."
      }}
    ],
    "onerilen_izlem": "..."
  }},
  "genel_karar": {{
    "durum": "UYGUN / UYGUN_DEGIL / KOSULLU",
    "metin": "...",
    "detay": "..."
  }}
}}"""


class ProtocolAnalyzer:
    def __init__(self):
        self._client = None
        self._protocol_cached = False

    @property
    def client(self) -> anthropic.Anthropic:
        if self._client is None:
            self._client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        return self._client

    def reset_protocol(self):
        self._protocol_cached = False

    def extract_pdf_text(self, pdf_path: Path) -> str:
        doc = fitz.open(str(pdf_path))
        pages = []
        for page in doc:
            pages.append(page.get_text())
        doc.close()
        return "\n".join(pages)

    async def analyze(self, protocol_text: str, patient_text: str) -> dict:
        system_content = SYSTEM_PROMPT_TEMPLATE.format(protocol_text=protocol_text)

        user_message = f"""Aşağıdaki hasta verilerini protokole göre değerlendir ve belirtilen JSON formatında rapor üret:

HASTA VERİLERİ:
{patient_text}

Tüm kriterleri tek tek incele, eksik bilgileri "BİLİNMİYOR" olarak işaretle, biyomarker değerlerini protokol eşikleriyle karşılaştır ve kapsamlı bir değerlendirme yap."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=8000,
            thinking={"type": "adaptive"},
            system=[
                {
                    "type": "text",
                    "text": system_content,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[
                {"role": "user", "content": user_message}
            ],
        )

        raw_text = ""
        for block in response.content:
            if block.type == "text":
                raw_text = block.text
                break

        return self._parse_json_response(raw_text)

    def _parse_json_response(self, text: str) -> dict:
        # Try direct parse first
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Extract JSON from markdown code block
        match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Find first { ... } block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        # Return error structure
        return {
            "hasta_id": "Bilinmiyor",
            "hasta_ozet": {},
            "uygunluk_degerlendirmesi": {"ozet": "HATA", "kriterler": []},
            "biyomarker_analizi": {"ozet": "Analiz hatası", "degerler": []},
            "klinik_bulgular": {"ozet": "Analiz hatası", "bulgular": []},
            "kohort_onerisi": {"onerilen_part": "Bilinmiyor", "onerilen_kohort": "", "baslangic_dozu": "", "gerekce": "JSON parse hatası: " + text[:200]},
            "risk_degerlendirmesi": {"genel_risk": "BİLİNMİYOR", "riskler": [], "onerilen_izlem": ""},
            "genel_karar": {"durum": "HATA", "metin": "Rapor oluşturulurken hata oluştu.", "detay": text[:500]},
        }
