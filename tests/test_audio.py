import wave

import numpy as np
import pytest

from core import audio as audio_mod
from core.audio import ReproductorAudio, buscar_dispositivo_entrada, buscar_dispositivo_salida

_DISPOSITIVOS_DE_PRUEBA = [
    {"name": "Salida HDMI", "max_input_channels": 0, "max_output_channels": 2, "default_samplerate": 48000.0},
    {
        "name": "USB PnP Sound Device: Audio (hw:1,0)",
        "max_input_channels": 1,
        "max_output_channels": 0,
        "default_samplerate": 44100.0,
    },
    {
        "name": "UACDemoV10: USB Audio (hw:2,0)",
        "max_input_channels": 0,
        "max_output_channels": 2,
        "default_samplerate": 44100.0,
    },
]


def _mock_query_devices(*args):
    """Imita sd.query_devices(): sin argumentos devuelve la lista completa,
    con un índice devuelve solo ese dispositivo (como el real)."""
    if args:
        return _DISPOSITIVOS_DE_PRUEBA[args[0]]
    return _DISPOSITIVOS_DE_PRUEBA


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
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(_crear_wav_de_prueba(tmp_path))

    assert llamadas == ["play", "wait"]


def test_modo_no_bloqueante_no_espera(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(_crear_wav_de_prueba(tmp_path), bloqueante=False)

    assert llamadas == ["play"]


def test_archivo_inexistente_no_llama_a_sounddevice(tmp_path, monkeypatch):
    llamadas = []
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    monkeypatch.setattr(audio_mod.sd, "play", lambda *a, **k: llamadas.append("play"))
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: llamadas.append("wait"))

    ReproductorAudio().reproducir(tmp_path / "no_existe.wav")

    assert llamadas == []


def test_reproducir_usa_el_indice_del_bafle_encontrado(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    dispositivo_usado = {}
    monkeypatch.setattr(
        audio_mod.sd, "play", lambda *a, **k: dispositivo_usado.update(device=k.get("device"))
    )
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: None)

    ReproductorAudio("UAC").reproducir(_crear_wav_de_prueba(tmp_path))

    assert dispositivo_usado["device"] == 2  # índice de "UACDemoV10" en _DISPOSITIVOS_DE_PRUEBA


def test_reproducir_cae_a_dispositivo_por_defecto_si_no_hay_bafle(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    dispositivo_usado = {}
    monkeypatch.setattr(
        audio_mod.sd, "play", lambda *a, **k: dispositivo_usado.update(device=k.get("device"))
    )
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: None)

    ReproductorAudio("bluetooth").reproducir(_crear_wav_de_prueba(tmp_path))

    assert dispositivo_usado["device"] is None


def test_buscar_dispositivo_salida_encuentra_por_substring(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)

    assert buscar_dispositivo_salida("UAC") == 2


def test_buscar_dispositivo_salida_sin_coincidencia_devuelve_none(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)

    assert buscar_dispositivo_salida("bluetooth") is None


def test_buscar_dispositivo_entrada_encuentra_por_substring(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)

    assert buscar_dispositivo_entrada("USB") == 1


def test_buscar_dispositivo_entrada_no_distingue_mayusculas(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)

    assert buscar_dispositivo_entrada("usb pnp") == 1


def test_buscar_dispositivo_entrada_ignora_dispositivos_de_solo_salida(monkeypatch):
    # "UACDemoV10" (el bafle) también contiene "USB" en su nombre pero es
    # de solo SALIDA (max_input_channels=0) — no debe confundirse con el mic.
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)

    with pytest.raises(SystemExit):
        buscar_dispositivo_entrada("UACDemoV10")


def test_buscar_dispositivo_entrada_sin_coincidencia_lanza_systemexit(monkeypatch):
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)

    with pytest.raises(SystemExit):
        buscar_dispositivo_entrada("bluetooth")


def test_resamplear_ajusta_la_cantidad_de_muestras():
    un_segundo_a_16000hz = np.zeros(16000, dtype=np.int16)

    resampleado = audio_mod._resamplear(un_segundo_a_16000hz, 16000, 44100)

    assert resampleado.dtype == np.int16
    assert resampleado.shape[0] == 44100  # mismo segundo de audio, a 44100 Hz


def test_resamplear_no_hace_nada_si_las_tasas_coinciden():
    audio = np.arange(100, dtype=np.int16)

    resampleado = audio_mod._resamplear(audio, 44100, 44100)

    assert resampleado is audio


def test_reproducir_convierte_la_tasa_si_el_bafle_no_soporta_la_del_archivo(tmp_path, monkeypatch):
    # _crear_wav_de_prueba genera un .wav a 16000 Hz; "UACDemoV10" en
    # _DISPOSITIVOS_DE_PRUEBA solo soporta 44100 Hz (default_samplerate).
    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    llamada = {}
    monkeypatch.setattr(
        audio_mod.sd,
        "play",
        lambda audio, **k: llamada.update(samplerate=k.get("samplerate"), muestras=audio.shape[0]),
    )
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: None)

    ReproductorAudio("UAC").reproducir(_crear_wav_de_prueba(tmp_path))

    assert llamada["samplerate"] == 44100
    assert llamada["muestras"] == 44100  # se convirtió el 1 segundo de 16000 a 44100 Hz


def test_aplicar_ganancia_sin_cambios_si_es_1():
    audio = np.array([100, -100, 200], dtype=np.int16)

    resultado = audio_mod._aplicar_ganancia(audio, 1.0)

    assert resultado is audio


def test_aplicar_ganancia_amplifica():
    audio = np.array([100, -100, 200], dtype=np.int16)

    resultado = audio_mod._aplicar_ganancia(audio, 2.0)

    assert list(resultado) == [200, -200, 400]
    assert resultado.dtype == np.int16


def test_aplicar_ganancia_recorta_para_no_desbordar():
    audio = np.array([30000, -30000], dtype=np.int16)

    resultado = audio_mod._aplicar_ganancia(audio, 2.0)

    limite = np.iinfo(np.int16)
    assert resultado[0] == limite.max
    assert resultado[1] == limite.min


def test_reproducir_aplica_la_ganancia_configurada(tmp_path, monkeypatch):
    ruta = tmp_path / "tono.wav"
    with wave.open(str(ruta), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(44100)  # coincide con el default_samplerate del bafle de prueba, sin resampleo
        wf.writeframes(np.array([1000], dtype=np.int16).tobytes())

    monkeypatch.setattr(audio_mod.sd, "query_devices", _mock_query_devices)
    llamada = {}
    monkeypatch.setattr(
        audio_mod.sd, "play", lambda audio, **k: llamada.update(pico=int(audio.max()))
    )
    monkeypatch.setattr(audio_mod.sd, "wait", lambda: None)

    ReproductorAudio("UAC", ganancia=2.0).reproducir(ruta)

    assert llamada["pico"] == 2000
