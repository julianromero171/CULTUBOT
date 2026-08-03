import wave

from core import audio as audio_mod
from core.audio import ReproductorAudio


def _crear_wav_de_prueba(tmp_path):
    ruta = tmp_path / "prueba.wav"
    with wave.open(str(ruta), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(b"\x00\x00" * 16000)  # 1 segundo de silencio
    return ruta


def test_modo_bloqueante_por_defecto_espera(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(_crear_wav_de_prueba(tmp_path))

    assert llamadas == ["play", "wait"]


def test_modo_no_bloqueante_no_espera(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(_crear_wav_de_prueba(tmp_path), bloqueante=False)

    assert llamadas == ["play"]


def test_archivo_inexistente_no_llama_a_sounddevice(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(tmp_path / "no_existe.wav")

    assert llamadas == []
