import os
from types import SimpleNamespace

os.environ.setdefault("GROQ_API_KEY", "test-key")
from fastapi.testclient import TestClient
import backend.main as app_module


class FakeCompletions:
    def create(self, **kwargs):
        assert kwargs["model"] == "llama-3.3-70b-versatile"
        assert kwargs["response_format"] == {"type": "json_object"}
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=(
                '{"label":"HOAKS","confidence":0.91,'
                '"alasan":"Klaim berlebihan tanpa sumber yang dapat diverifikasi.",'
                '"indikator":["klaim absolut","tanpa sumber"],'
                '"saran":"Periksa sumber resmi sebelum membagikan."}'
            )))]
        )


class FakeClient:
    chat = SimpleNamespace(completions=FakeCompletions())


def run_tests():
    client = TestClient(app_module.app)
    assert client.get("/").status_code == 200
    assert "HoaxCheck" in client.get("/").text
    assert 'const API_URL = "/deteksi"' in client.get("/").text
    assert client.get("/health").json() == {"status": "running"}
    assert client.post("/deteksi", json={"teks": ""}).status_code == 400
    assert client.post("/deteksi", json={"teks": "terlalu pendek"}).status_code == 400

    original = app_module.get_groq_client
    app_module.get_groq_client = lambda: FakeClient()
    try:
        response = client.post(
            "/deteksi",
            json={"teks": "Klaim contoh dengan jumlah karakter yang cukup untuk diuji."},
        )
    finally:
        app_module.get_groq_client = original

    assert response.status_code == 200
    assert response.json()["label"] == "HOAKS"
    assert response.json()["confidence"] == 0.91
    print("All application checks passed.")


if __name__ == "__main__":
    run_tests()
