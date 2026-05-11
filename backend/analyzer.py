import os
import json
import re
from pathlib import Path

import fitz  # PyMuPDF
import google.generativeai as genai

MODEL = "gemini-2.5-flash"

SYSTEM_PROMPT_TEMPLATE = """You are an expert clinical research evaluation assistant working for Genexa CRO. Below is the full text of a clinical trial protocol.

PROTOCOL TEXT:
{protocol_text}

---

Your task: Evaluate patient data against the inclusion/exclusion criteria, biomarker thresholds, dosing requirements, and safety criteria defined in this protocol.

OUTPUT LANGUAGE: {language_instruction}

Respond ONLY with the following JSON structure — no additional text, no markdown code blocks, no explanation:

{{
  "hasta_id": "patient identifier",
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
    "ozet": "{eligible_label} / {not_eligible_label} / {conditional_label}",
    "kriterler": [
      {{
        "kategori": "{inclusion_label} / {exclusion_label}",
        "kriter": "criterion name",
        "beklenen": "protocol expectation",
        "hasta_degeri": "patient value",
        "durum": "{met_label} / {not_met_label} / {unknown_label}",
        "aciklama": "brief explanation"
      }}
    ]
  }},
  "biyomarker_analizi": {{
    "ozet": "...",
    "degerler": [
      {{
        "parametre": "parameter name",
        "hasta_degeri": "...",
        "protokol_esigi": "...",
        "birim": "...",
        "durum": "{normal_label} / {high_label} / {low_label} / {above_label} / {below_label}",
        "klinik_yorum": "..."
      }}
    ]
  }},
  "klinik_bulgular": {{
    "ozet": "...",
    "bulgular": [
      {{
        "bulgu": "finding name",
        "deger": "...",
        "yorum": "..."
      }}
    ]
  }},
  "kohort_onerisi": {{
    "onerilen_part": "Part A / Part B / Part C / {not_eligible_short}",
    "onerilen_kohort": "Cohort 1 / Cohort 2 / etc.",
    "baslangic_dozu": "...",
    "gerekce": "...",
    "ek_notlar": "..."
  }},
  "risk_degerlendirmesi": {{
    "genel_risk": "{low_label_r} / {medium_label_r} / {high_label_r}",
    "riskler": [
      {{
        "risk": "risk name",
        "seviye": "{low_label_r} / {medium_label_r} / {high_label_r}",
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

LANGUAGE_CONFIGS = {
    "tr": {
        "language_instruction": "Write ALL text values in TURKISH.",
        "eligible_label":     "UYGUN",
        "not_eligible_label": "UYGUN DEĞİL",
        "conditional_label":  "KOŞULLU UYGUN",
        "inclusion_label":    "Dahil Etme",
        "exclusion_label":    "Dışlama",
        "met_label":          "KARŞILANDI",
        "not_met_label":      "KARŞILANMADI",
        "unknown_label":      "BİLİNMİYOR",
        "normal_label":       "NORMAL",
        "high_label":         "YÜKSEK",
        "low_label":          "DÜŞÜK",
        "above_label":        "EŞİK ÜSTÜ",
        "below_label":        "EŞİK ALTI",
        "not_eligible_short": "Uygun değil",
        "low_label_r":        "DÜŞÜK",
        "medium_label_r":     "ORTA",
        "high_label_r":       "YÜKSEK",
    },
    "en": {
        "language_instruction": "Write ALL text values in ENGLISH.",
        "eligible_label":     "ELIGIBLE",
        "not_eligible_label": "NOT ELIGIBLE",
        "conditional_label":  "CONDITIONALLY ELIGIBLE",
        "inclusion_label":    "Inclusion",
        "exclusion_label":    "Exclusion",
        "met_label":          "MET",
        "not_met_label":      "NOT MET",
        "unknown_label":      "UNKNOWN",
        "normal_label":       "NORMAL",
        "high_label":         "HIGH",
        "low_label":          "LOW",
        "above_label":        "ABOVE THRESHOLD",
        "below_label":        "BELOW THRESHOLD",
        "not_eligible_short": "Not eligible",
        "low_label_r":        "LOW",
        "medium_label_r":     "MODERATE",
        "high_label_r":       "HIGH",
    },
}

USER_MESSAGE = {
    "tr": """Aşağıdaki hasta verilerini protokole göre değerlendir ve belirtilen JSON formatında Türkçe rapor üret. Sadece JSON döndür:

HASTA VERİLERİ:
{patient_text}""",

    "en": """Evaluate the patient data below against the protocol and return ONLY the JSON report in English:

PATIENT DATA:
{patient_text}""",
}


CRITERIA_KEYWORDS = [
    # English
    "inclusion criteria", "exclusion criteria", "eligibility criteria",
    "inclusion/exclusion", "key eligibility", "study population",
    "dose", "dosing", "cohort", "biomarker", "endpoint", "pharmacokinetic",
    "safety", "stopping rules", "treatment arm", "randomization",
    # Turkish
    "dahil etme", "dışlama", "uygunluk", "doz", "kohort", "biyomarker",
]

MAX_PROTOCOL_CHARS = 10000  # ~2.5K tokens, leaves room for large system prompt + patient


def extract_protocol_criteria(protocol_text: str) -> str:
    """Extract the most relevant sections from a protocol to fit within token limits."""
    if len(protocol_text) <= MAX_PROTOCOL_CHARS:
        return protocol_text

    text_lower = protocol_text.lower()
    sections = []
    collected_chars = 0

    # Find positions of key sections
    positions = []
    for kw in CRITERIA_KEYWORDS:
        idx = text_lower.find(kw)
        while idx != -1 and idx not in positions:
            positions.append(idx)
            idx = text_lower.find(kw, idx + len(kw))

    if not positions:
        # No keywords found — return first chunk
        return protocol_text[:MAX_PROTOCOL_CHARS]

    # Sort and deduplicate, then extract windows around each hit
    positions = sorted(set(positions))
    used_ranges = []

    for pos in positions:
        if collected_chars >= MAX_PROTOCOL_CHARS:
            break
        # Extract a window of 2000 chars around the keyword
        start = max(0, pos - 200)
        end = min(len(protocol_text), pos + 1800)

        # Skip if overlapping with already collected range
        overlap = any(s <= start <= e or s <= end <= e for s, e in used_ranges)
        if overlap:
            continue

        chunk = protocol_text[start:end].strip()
        sections.append(chunk)
        used_ranges.append((start, end))
        collected_chars += len(chunk)

    result = "\n\n---\n\n".join(sections)

    # If still too large, truncate
    if len(result) > MAX_PROTOCOL_CHARS:
        result = result[:MAX_PROTOCOL_CHARS]

    return result


class ProtocolAnalyzer:
    def __init__(self):
        self._model = None

    @property
    def model(self):
        if self._model is None:
            genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
            self._model = genai.GenerativeModel(MODEL)
        return self._model

    def reset_protocol(self):
        pass

    def extract_pdf_text(self, pdf_path: Path) -> str:
        doc = fitz.open(str(pdf_path))
        pages = [page.get_text() for page in doc]
        doc.close()
        return "\n".join(pages)

    async def analyze(self, protocol_text: str, patient_text: str, language: str = "tr") -> dict:
        lang = language if language in LANGUAGE_CONFIGS else "tr"
        cfg = LANGUAGE_CONFIGS[lang]

        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            protocol_text=protocol_text,
            **cfg,
        )
        user_message = USER_MESSAGE[lang].format(patient_text=patient_text)

        model = genai.GenerativeModel(
            model_name=MODEL,
            system_instruction=system_prompt,
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                max_output_tokens=32000,
                response_mime_type="application/json",
            ),
        )
        response = model.generate_content(user_message)

        raw_text = response.text or ""
        return self._parse_json_response(raw_text, lang)

    def _parse_json_response(self, text: str, lang: str = "tr") -> dict:
        text = text.strip()

        # Strip markdown code block if present
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1:
            try:
                return json.loads(text[start:end + 1])
            except json.JSONDecodeError:
                pass

        err = "Rapor oluşturulurken hata oluştu." if lang == "tr" else "An error occurred while generating the report."
        unknown = "BİLİNMİYOR" if lang == "tr" else "UNKNOWN"
        return {
            "hasta_id": unknown,
            "hasta_ozet": {},
            "uygunluk_degerlendirmesi": {"ozet": "HATA", "kriterler": []},
            "biyomarker_analizi": {"ozet": err, "degerler": []},
            "klinik_bulgular": {"ozet": err, "bulgular": []},
            "kohort_onerisi": {"onerilen_part": unknown, "onerilen_kohort": "", "baslangic_dozu": "", "gerekce": text[:200]},
            "risk_degerlendirmesi": {"genel_risk": unknown, "riskler": [], "onerilen_izlem": ""},
            "genel_karar": {"durum": "HATA", "metin": err, "detay": text[:500]},
        }
