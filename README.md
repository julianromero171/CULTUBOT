# CultuBot

Robot dibujador de sitios turísticos de Cúcuta activado por voz. Escucha el nombre de un lugar (biblioteca, cerro de tasajero, ferrocarril, templo histórico, café), pregunta qué formato prefieres, y ejecuta la acción: dibuja el sitio con una CNC de dos ejes, reproduce una narración pregrabada, o ambas cosas.

## Arquitectura

```
┌─────────────────────────────┐              ┌───────────────────────────┐
│         Raspberry Pi 5      │              │      ESP32 DevKit V1      │
│  ─────────────────────      │              │  ─────────────────────    │
│  • Mic USB (Vosk STT es)    │  USB Serial  │  • FluidNC v4.0.4         │
│  • Bafle USB (.wav out)     │◄────────────►│  • 2x A4988 → NEMA17 X/Y  │
│  • Máquina de estados       │   115200 bd  │  • Micro servo (Z)        │
│  • Envío G-code a ESP32     │              │  • Finales de carrera     │
└─────────────────────────────┘              │  • Micro-SD (para gcode)  │
                                             └───────────────────────────┘
```

La Raspberry es el "cerebro conversacional": entiende la voz, gestiona el diálogo, reproduce audios, y decide qué G-code enviar. La ESP32 con FluidNC es el "cerebro motriz": recibe G-code por Serial y mueve los motores.

## Hardware requerido

|Componente|Especificación|
|-|-|
|Raspberry Pi 5|Con Raspberry Pi OS (Debian trixie o superior)|
|ESP32 DevKit V1|Chip ESP32-WROOM-32 (D0WD-V3 o similar)|
|Steppers|2× NEMA17 (17HS4401 o similar)|
|Drivers|2× A4988 (con condensadores 100µF/16V)|
|Servo|Micro servo RC (SG90, MG996R, etc.)|
|Finales de carrera|2× (uno por eje)|
|Micro-SD|Para el ESP32, mínimo 1GB|
|Micrófono USB|Cualquier PnP genérico|
|Bafle USB|Cualquier UAC-Class|
|Fuente motores|DC 8-12V, mínimo 2A|
|Regulador 5V|7805 + condensadores para el servo|
|Cable Ethernet|Para conexión RPi ↔ PC durante desarrollo|
|Cable USB|RPi ↔ ESP32 (data, no solo carga)|

Ver diagrama de circuito completo en el `fluidnc/config.yaml` — los pines exactos están documentados en cada eje.

## Software requerido

### Raspberry Pi

* **Python 3.13+**
* **Vosk** (STT offline, modelo español)
* **sounddevice + PortAudio** (captura/reproducción de audio)
* **pyserial** (comunicación con ESP32)
* **scipy** (opcional, para resample de mayor calidad)
* **espeak-ng** (opcional, para generar audios placeholder)

### ESP32

* **FluidNC v4.0.4+** (firmware CNC compatible con Grbl)

## Instalación

### 1\. Raspberry Pi

```bash
# Clonar el repo
git clone https://github.com/julianromero171/CULTUBOT.git
cd CULTUBOT

# Dependencias de sistema
sudo apt update
sudo apt install -y libportaudio2 python3-scipy patchelf espeak-ng

# Dependencias Python (RPi con Python 3.13 requiere --break-system-packages)
pip3 install --break-system-packages -r requirements.txt

# Parche a Vosk: libvosk.so pide executable stack que el kernel de trixie
# bloquea por seguridad. Se quita con patchelf.
patchelf --clear-execstack \~/.local/lib/python3.13/site-packages/vosk/libvosk.so

# Descargar el modelo Vosk español (\~40MB)
mkdir -p models \&\& cd models
wget https://alphacephei.com/vosk/models/vosk-model-small-es-0.42.zip
unzip vosk-model-small-es-0.42.zip
rm vosk-model-small-es-0.42.zip
cd ..

# Verificar imports
python3 -c "import sounddevice, vosk, serial, numpy; print('deps OK')"
```

### 2\. Instalar FluidNC en el ESP32

Descargar el paquete oficial de Windows desde GitHub:

👉 **https://github.com/bdring/FluidNC/releases/latest**

Bajar `fluidnc-vX.Y.Z-win64.zip`, descomprimir en un PC Windows con el ESP32 conectado por USB (necesita driver CP210x — https://www.silabs.com/interface/usb-bridges/classic/device.cp2102), y luego:

```powershell
cd fluidnc-vX.Y.Z-win64

# Borrar cualquier firmware previo
.\\erase.bat

# Flashear FluidNC WiFi
.\\install-wifi.bat
```

Al terminar, `fluidterm.bat` arranca automáticamente y verás el banner `Grbl 4.0 \[FluidNC vX.Y.Z (esp32-wifi) '$' for help]`.

### 3\. Cargar `config.yaml` en el ESP32

El `config.yaml` define pines, motores, servo, límites y SD para tu circuito específico. Este proyecto trae uno listo en `fluidnc/config.yaml` con los pines del diagrama de circuito. Hay tres formas de subirlo:

#### Método A — FluidTerm (más simple, requiere cable USB al PC)

1. Con FluidTerm corriendo (`fluidterm.bat` desde el paquete de instalación):
2. Presiona **Ctrl+U**
3. Cuando pida el path, escribe la ruta al `config.yaml` de este repo, ej:

```
   C:\\Users\\Usuario\\Desktop\\Claudio\\config.yaml
   ```

4. Enter, espera "Received XXXX bytes to file /littlefs/config.yaml"
5. Presiona **Ctrl+R** para reiniciar el ESP32
6. Verifica en el banner que **NO** aparezca `\[MSG:ERR: Cannot open configuration file:config.yaml]`

#### Método B — WebUI (via WiFi, sin cable)

FluidNC crea automáticamente una red WiFi llamada **`FluidNC`** (sin password). Desde un celular o cualquier equipo con WiFi:

1. Conéctate a la red **`FluidNC`**
2. Abre el navegador en **http://192.168.0.1**
3. Ve a la sección **Files** o **LocalFS**
4. Sube el `config.yaml` local
5. Botón **Reset** para reiniciar el ESP32

#### Método C — Vía micro-SD (offline, cuando el ESP32 ya está en producción)

1. Con una lectora de micro-SD, monta la tarjeta
2. Copia `config.yaml` a la raíz de la SD
3. Insértala en el módulo micro-SD del ESP32
4. Reinicia el ESP32
5. FluidNC detecta el archivo y usa la config

**Nota:** en el `fluidnc/config.yaml` de este repo, el macro `startup\_line0: "$X"` ejecuta un unlock automático en cada boot, para evitar el error `error:1` que aparece cuando la máquina arranca en estado Alarm.

## Configuración

Las siguientes variables de entorno permiten adaptar el bot sin editar código:

|Variable|Default|Descripción|
|-|-|-|
|`CULTUBOT\_PUERTO\_ESP32`|`/dev/ttyUSB0`|Puerto serial de la ESP32 (`/dev/ttyACM0` si usa CDC)|
|`CULTUBOT\_BAUDIOS\_ESP32`|`115200`|Velocidad serial (FluidNC default)|
|`CULTUBOT\_RUTA\_MODELO\_VOSK`|`models/vosk-model-small-es-0.42`|Ruta al modelo Vosk|
|`CULTUBOT\_DISPOSITIVO\_MIC`|`USB`|Substring del nombre del micrófono|
|`CULTUBOT\_DISPOSITIVO\_BAFLE`|`UAC`|Substring del nombre del bafle|
|`CULTUBOT\_GANANCIA\_AUDIO`|`1.0`|Ganancia digital extra para el bafle (1.5 = +50%)|

Ejemplo:

```bash
export CULTUBOT\_PUERTO\_ESP32=/dev/ttyACM0
export CULTUBOT\_DISPOSITIVO\_MIC="PnP"
python3 main.py
```

## Ejecución

```bash
python3 -u main.py
```

Salida esperada:

```
\[main] Conectado a la ESP32 en /dev/ttyUSB0
...vosk model loads...
==================================================
CultuBot iniciado
Micrófono: \[1] USB PnP Sound Device: Audio (hw:3,0)
Tasa mic: 44100 Hz  ->  Vosk: 16000 Hz (resample: scipy)
Estoy escuchando...
Di "salir" para cerrar el programa.
==================================================
```

## Comandos de voz

|Estado|Comandos válidos|Efecto|
|-|-|-|
|DORMIDO|`cultura`, `culto`|Activa el bot|
|ESPERANDO\_ORDEN|`biblioteca`, `cerro`, `cerro de tasajero`, `ferrocarril`, `locomotora`, `templo`, `templo histórico`, `café`|Elige sitio y pregunta opción|
|CONFIRMANDO|`dibujo`, `dibujo con audio`, `dibujo y audio`, `solo audio`, `solamente audio`|Ejecuta la opción elegida|
|Cualquier estado|`salir`|Cierra el programa|

**Palabra de activación** — no se usa "cultubot" porque esa palabra no existe en el diccionario Vosk español. En su lugar se usa "cultura" o "culto", y `core/normalizador.py` las convierte internamente a "cultubot" para el matcher.

## Estructura del proyecto

```
CULTUBOT/
├── main.py                   # Punto de entrada
├── config.py                 # Configuración por variables de entorno
├── escuchar.py               # Captura audio, resample, feed a Vosk
├── requirements.txt
├── audio/                    # .wav pregrabados (bienvenida, sitios, etc.)
├── core/
│   ├── acciones.py           # Ejecutor de acciones + interfaces
│   ├── audio.py              # ReproductorAudio con resample al bafle
│   ├── comandos.py           # Interpretación texto -> Accion
│   ├── estados.py            # Máquina de estados
│   ├── lugares.py            # Catálogo de sitios con alias
│   ├── mensajes.py           # Catálogo de audios fijos
│   ├── normalizador.py       # cultura/culto -> cultubot
│   └── vocabulario.py        # Gramática restringida para Vosk
├── interface/
│   └── esp32\_serial.py       # Streaming G-code al ESP32 con $X + \[MSG:] filter
├── drawings/                 # .gcode por sitio
├── fluidnc/
│   ├── config.yaml           # Config real del ESP32 (este proyecto)
│   ├── config\_ejemplo.yaml   # Plantilla vacía con TODOs
│   └── README.md
├── herramientas/             # Diagnósticos: probar\_microfono, validar\_gcode, etc.
└── tests/                    # pytest, 43+ tests
```

## Troubleshooting

### `input overflow` en la consola

Vosk no alcanza a procesar audio en tiempo real. Con el resample a 16 kHz + scipy debería ser \~0.5-1 overflow/seg (tolerable). Si es más:

```bash
# Forzar resample con numpy naive (20× más rápido, algo de aliasing)
sed -i 's|\_RESAMPLE\_METODO = "scipy"|\_RESAMPLE\_METODO = "numpy"|' escuchar.py
```

### `No se encontró ningún micrófono cuyo nombre contenga "USB"`

Tu mic tiene otro nombre. Lista dispositivos:

```bash
python3 -c "import sounddevice as sd; print(sd.query\_devices())"
```

Y ajusta `CULTUBOT\_DISPOSITIVO\_MIC` a un substring del nombre real.

### `No se pudo abrir el puerto /dev/ttyUSB0`

* El ESP32 no está conectado, o
* Windows Firewall/ModemManager está bloqueando el puerto
* Verifica con `ls /dev/ttyUSB\* /dev/ttyACM\*`

Si aparece como `/dev/ttyACM0`, exporta `CULTUBOT\_PUERTO\_ESP32=/dev/ttyACM0`.

### `OSError: cannot enable executable stack` al importar vosk

Kernel Linux moderno bloquea binarios con executable stack. Fix:

```bash
patchelf --clear-execstack \~/.local/lib/python3.13/site-packages/vosk/libvosk.so
```

Si tienes que reinstalar vosk, reaplicar el patch (o hacerlo parte del script de setup).

### `\[ESP32Serial] error:1 en línea N`

FluidNC rechaza una línea de G-code. Causas:

* **La ESP32 está en estado Alarm** — el `interface/esp32\_serial.py` envía `$X` al conectar para desbloquear. Si aún así falla, verifica que ese código esté actualizado.
* **Bytes non-ASCII en el G-code** — el mismo módulo filtra comentarios `;` inline para evitar acentos que FluidNC v4 rechaza. Verifica que tus `.gcode` no tengan acentos fuera de comentarios.

### `Cannot open configuration file:config.yaml` en el ESP32

Falta subir el `config.yaml` al filesystem del ESP32. Ver sección "Cargar config.yaml en el ESP32" arriba.

### El bafle no reproduce audio

* Verifica volumen ALSA:

```bash
  cat /proc/asound/cards          # ver número de tarjeta
  amixer -c <N> sset PCM 100%     # subir volumen
  ```

* Asegúrate que `DISPOSITIVO\_BAFLE` matchea el nombre real del bafle
* Los `.wav` de espeak-ng son placeholders robóticos; reemplázalos por audios reales

## Herramientas útiles

```bash
# Simular conversación sin hardware (voz vía texto en la consola)
python3 herramientas/simular\_conversacion.py

# Probar el mic y ver qué reconoce Vosk sin la máquina de estados
python3 herramientas/probar\_microfono.py

# Validar que un .gcode se puede parsear
python3 herramientas/validar\_gcode.py drawings/cerro\_tasajero.gcode

# Correr la suite de tests
pytest
```

## Créditos

Proyecto CultuBot — Cúcuta, Colombia. WRO (World Robot Olympiad).
Autores: julianromero171, Carlozeto, crastojulian.

Firmware CNC: [FluidNC](https://github.com/bdring/FluidNC) por Bart Dring.
STT offline: [Vosk API](https://alphacephei.com/vosk/) por Alpha Cephei.

