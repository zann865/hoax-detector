import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from groq import Groq
from pydantic import BaseModel, Field, ValidationError

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_FILE = BASE_DIR.parent / "frontend" / "index.html"

app = FastAPI(title="HoaxCheck API - by Fauzan Yusa Adicandra")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class BeritaRequest(BaseModel):
    teks: str


class HasilAnalisis(BaseModel):
    label: Literal["HOAKS", "FAKTA"]
    confidence: float = Field(ge=0.0, le=1.0)
    alasan: str
    indikator: list[str] = Field(default_factory=list)
    saran: str


SYSTEM_PROMPT = """
Kamu adalah sistem deteksi hoaks berbasis AI untuk Bahasa Indonesia.
Tugasmu adalah menganalisis teks berita atau klaim yang diberikan dan menentukan apakah itu HOAKS atau FAKTA.

Berikan respons HANYA dalam format JSON berikut (tanpa markdown, tanpa backtick):
{
  "label": "HOAKS" atau "FAKTA",
  "confidence": angka antara 0.0 hingga 1.0,
  "alasan": "Penjelasan singkat 2-3 kalimat mengapa kamu menyimpulkan ini hoaks atau fakta",
  "indikator": ["indikator 1", "indikator 2", "indikator 3"],
  "saran": "Saran singkat untuk pembaca"
}

Panduan analisis:
- Perhatikan klaim yang tidak masuk akal atau berlebihan.
- Cari tanda-tanda judul clickbait atau sensasional.
- Pertimbangkan konteks dan logika informasi.
- Perhatikan penggunaan bahasa emosional berlebihan.
- confidence 0.9+ = sangat yakin, 0.7-0.9 = cukup yakin, 0.5-0.7 = kurang yakin.
"""


def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="GROQ_API_KEY belum dikonfigurasi di server.",
        )
    return Groq(api_key=api_key)


@app.get("/", include_in_schema=False)
async def frontend():
    return FileResponse(FRONTEND_FILE)


@app.get("/health")
async def health_check():
    return {"status": "running"}


@app.post("/deteksi", response_model=HasilAnalisis)
async def deteksi_hoaks(req: BeritaRequest):
    teks = req.teks.strip()
    if not teks:
        raise HTTPException(status_code=400, detail="Teks tidak boleh kosong.")
    if len(teks) < 20:
        raise HTTPException(status_code=400, detail="Teks terlalu pendek, minimal 20 karakter.")

    try:
        response = get_groq_client().chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f'Analisis teks berikut:\n"{teks}"'},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
            max_completion_tokens=1000,
        )

        raw = (response.choices[0].message.content or "").strip()
        return HasilAnalisis.model_validate_json(raw)

    except HTTPException:
        raise
    except ValidationError:
        raise HTTPException(
            status_code=502,
            detail="Respons AI tidak sesuai format hasil analisis. Coba lagi.",
        )
    except Exception:
        raise HTTPException(
            status_code=502,
            detail="Analisis gagal diproses oleh layanan AI. Coba lagi.",
        )
