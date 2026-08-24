import threading
import time

from core.systemd_watchdog import WatchdogSystemd, _sd_notify


def test_sd_notify_sin_notify_socket_no_hace_nada(monkeypatch):
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)

    _sd_notify("WATCHDOG=1")  # no debe lanzar ninguna excepcion


def test_iniciar_sin_notify_socket_no_arranca_hilo(monkeypatch):
    monkeypatch.delenv("NOTIFY_SOCKET", raising=False)
    hilos_creados = []
    monkeypatch.setattr(
        threading,
        "Thread",
        lambda *a, **k: hilos_creados.append(1) or threading.Thread(target=lambda: None),
    )

    WatchdogSystemd().iniciar()

    assert hilos_creados == []  # no corriendo bajo systemd: no hace falta el hilo


def test_marcar_progreso_actualiza_la_marca_de_tiempo():
    wd = WatchdogSystemd()
    marca_inicial = wd._ultimo_progreso

    time.sleep(0.05)  # margen generoso: la resolucion de time.monotonic() en Windows puede ser ~15ms
    wd.marcar_progreso()

    assert wd._ultimo_progreso > marca_inicial


def test_iniciar_con_notify_socket_manda_ready(monkeypatch, tmp_path):
    llamadas = []
    monkeypatch.setattr("core.systemd_watchdog._sd_notify", lambda msg: llamadas.append(msg))
    monkeypatch.setenv("NOTIFY_SOCKET", str(tmp_path / "notify.sock"))
    monkeypatch.setattr(threading, "Thread", lambda *a, **k: type("H", (), {"start": lambda self: None})())

    WatchdogSystemd().iniciar()

    assert "READY=1" in llamadas
