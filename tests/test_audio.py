import wave

import pytest

from core import audio as audio_mod
from core.audio import ReproductorAudio, buscar_dispositivo_entrada, buscar_dispositivo_salida

_DISPOSITIVOS_DE_PRUEBA = [
    {"name": "Salida HDMI", "max_input_channels": 0, "max_output_channels": 2},
    {"name": "USB PnP Sound Device: Audio (hw:1,0)", "max_input_channels": 1, "max_output_channels": 0},
    {"name": "UACDemoV10: USB Audio (hw:2,0)", "max_input_channels": 0, "max_output_channels": 2},
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
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(_crear_wav_de_prueba(tmp_path))

    assert llamadas == ["play", "wait"]


def test_modo_no_bloqueante_no_espera(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(_crear_wav_de_prueba(tmp_path), bloqueante=False)

    assert llamadas == ["play"]


def test_archivo_inexistente_no_llama_a_sounddevice(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(tmp_path / "no_existe.wav")

    assert llamadas == []


def test_reproducir_usa_el_indice_del_bafle_encontrado(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)
    dispositivo_usado = {}
    monkeypatch.setattr(
        audio_mod.sd, "play", lambda *a, **k: dispositivo_usado.update(device=k.get("device"))
    )
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: None)

    ReproductorAudio("UAC").reproducir(_crear_wav_de_prueba(tmp_path))

    assert dispositivo_usado["device"] == 2  # índice de "UACDemoV10" en _DISPOSITIVOS_DE_PRUEBA


def test_reproducir_cae_a_dispositivo_por_defecto_si_no_hay_bafle(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)
    dispositivo_usado = {}
    monkeypatch.setattr(
        audio_mod.sd, "play", lambda *a, **k: dispositivo_usado.update(device=k.get("device"))
    )
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: None)

    ReproductorAudio("bluetooth").reproducir(_crear_wav_de_prueba(tmp_path))

    assert dispositivo_usado["device"] is None


def test_buscar_dispositivo_salida_encuentra_por_substring(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)

    assert buscar_dispositivo_salida("UAC") == 2


def test_buscar_dispositivo_salida_sin_coincidencia_devuelve_none(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", lambda: _DISPOSITIVOS_DE_PRUEBA)

    assert buscar_dispositivo_salida("bluetooth") is None


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
