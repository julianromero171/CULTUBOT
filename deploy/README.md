# deploy/

`cultubot.service` — unidad de systemd para que CultuBot arranque solo
al encender la Raspberry Pi, sin necesitar SSH ni el PC conectado.
Pensado para el día de la competencia (no para mientras se sigue
desarrollando/probando cambios interactivamente).

## Instalar

```bash
sudo cp ~/CULTUBOT/deploy/cultubot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable cultubot.service   # arranca solo en cada boot
sudo systemctl start cultubot.service    # arrancarlo ahora, sin reiniciar
```

## Ver qué está haciendo

```bash
sudo systemctl status cultubot
journalctl -u cultubot -f          # logs en vivo, Ctrl+C para salir de ver (no lo detiene)
```

## Detenerlo (para volver a correr `python3 main.py` manualmente sin que choquen por el mic/bafle/puerto serial)

```bash
sudo systemctl stop cultubot
sudo systemctl disable cultubot    # para que tampoco arranque en el próximo boot
```

## Importante

Mientras el servicio esté activo, tiene el micrófono/bafle/puerto
serial tomados — si intentas correr `python3 main.py` a mano al mismo
tiempo va a fallar. Siempre `sudo systemctl stop cultubot` antes de
probar cambios manualmente.
