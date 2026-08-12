import wave

import pytest

from core import audio as audio_mod
from core.audio import ReproductorAudio, buscar_dispositivo_entrada

_DISPOSITIVOS_DE_PRUEBA = [
    {"name": "Salida HDMI", "max_input_channels": 0},
    {"name": "USB PnP Sound Device: Audio (hw:1,0)", "max_input_channels": 1},
    {"name": "UACDemoV10: USB Audio (hw:2,0)", "max_input_channels": 0},
]


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


def test_buscar_dispositivo_entrada_encuentra_por_substring(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)

    assert buscar_dispositivo_entrada("USB") == 1


def test_buscar_dispositivo_entrada_no_distingue_mayusculas(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)

    assert buscar_dispositivo_entrada("usb pnp") == 1


def test_buscar_dispositivo_entrada_ignora_dispositivos_de_solo_salida(monkeypatch):
    # "UACDemoV10" (el bafle) también contiene "USB" en su nombre pero es
    # de solo SALIDA (max_input_channels=0) — no debe confundirse con el mic.
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)

    with pytest.raises(SystemExit):
        buscar_dispositivo_entrada("UACDemoV10")


def test_buscar_dispositivo_entrada_sin_coincidencia_lanza_systemexit(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)

    with pytest.raises(SystemExit):
        buscar_dispositivo_entrada("bluetooth")
