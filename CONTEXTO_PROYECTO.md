# CultuBot — Contexto para continuar en Claude Code

Este documento resume todo lo decidido y construido hasta ahora, para que
puedas retomar el proyecto en Claude Code sin perder contexto de la
conversación anterior.

## Hardware real, mensajes hablados y reconocimiento por alias (2026-08-15)

Con la Raspberry Pi 5 física ya en uso (mic USB y bafle USB conectados),
salieron varios problemas que solo aparecen con hardware real (no se
detectan en el PC de desarrollo) y se corrigieron:

- **Micrófono y bafle USB no soportan 16000 Hz nativo** (chips baratos,
  solo 44100/48000 Hz): `escuchar.py`, `herramientas/probar_microfono.py`
  y `core/audio.py` ahora detectan la tasa real del dispositivo
  (`buscar_dispositivo_entrada`/`buscar_dispositivo_salida` en
  `core/audio.py`) en vez de forzar 16000 Hz. `ReproductorAudio` además
  **resamplea** el audio a la tasa que el bafle sí soporta si no coinciden
  (los `.wav` reales no todos comparten tasa).
- **"cultubot" no existe en el diccionario del modelo de Vosk** (nombre
  inventado) — la gramática restringida lo descartaba silenciosamente y
  el robot nunca se activaba. Se cambió la palabra de activación a
  "cultura"/"culto" (`core/vocabulario.py`), que sí existen y que
  `core/normalizador.py` ya convertía a "cultubot" internamente.
- **Volumen bajo:** el bafle usaba el control ALSA `PCM` muy bajo por
  defecto — se subió a 100% (`amixer -c <tarjeta> sset PCM 100%`, la
  tarjeta se identifica con `cat /proc/asound/cards`). Además se agregó
  `config.GANANCIA_AUDIO` (env `CULTUBOT_GANANCIA_AUDIO`) como ganancia
  digital adicional en `core/audio.py`, con recorte (clipping) automático
  para no distorsionar si se sube demasiado.
- **Catálogo actualizado:** el sitio "locomotora" se renombró a
  **"ferrocarril"** (mismo lugar, nuevo nombre/audio). "casa de
  santander" ya se había reemplazado antes por "templo historico".
  Catálogo final: biblioteca, cerro de tasajero, templo historico,
  ferrocarril, cafe.
- **Reconocimiento por alias reales:** `core/lugares.py`'s `Lugar` ahora
  admite `alias` (tupla de palabras reales adicionales que también
  activan el lugar, ej. decir solo "cerro" en vez de "cerro de
  tasajero", o "locomotora" para "ferrocarril"). Importante: los alias
  deben ser **palabras reales que existan en el diccionario del modelo**
  — se probó que sílabas sueltas (ej. "ce", "to", "ca") normalmente NO
  están en el diccionario y Vosk las ignora igual que pasó con
  "cultubot"/"tasajero", así que no sirven para "acelerar" el
  reconocimiento. Antes de agregar un alias nuevo, conviene verificar
  contra el modelo real (ver más abajo).
- **El robot ahora "habla" en los puntos clave de la conversación**, sin
  agregar TTS (sigue la misma decisión de siempre: audio pregrabado).
  Nuevo `core/mensajes.py` cataloga los audios fijos y `core/acciones.py`
  (`Ejecutor`) los reproduce además de imprimir el texto por consola:
  `bienvenida.wav` al activarse, `eleccion_<sitio>.wav` +
  `dibujo_con_audio_o_sin_audio.wav` al preguntar la opción, y
  `despedida.wav` al salir.

### Cómo verificar si una palabra existe en el diccionario del modelo (sin micrófono)

```bash
python3 -c "import json; from vosk import Model, KaldiRecognizer; m = Model('/home/cultubot/CULTUBOT/models/vosk-model-small-es-0.42'); g = json.dumps(['palabra1','palabra2','[unk]']); KaldiRecognizer(m, 16000, g)"
```

Si no aparece ningún `WARNING ... Ignoring word missing in vocabulary`,
la palabra existe y se puede usar como clave o alias con confianza.

## Reestructuración del 2026-08-03 (sobre lo existente, sin reescribir)

Se reestructuró el proyecto para que quede en estado profesional
mientras se espera el hardware físico. No se tocó la lógica que ya
funcionaba (máquina de estados, interpretación de comandos, protocolo
serial send-and-wait) — solo se le agregó alrededor:

- **Control de versiones:** el proyecto ahora es un repo git (antes no
  lo era). Primer commit = snapshot del estado previo a reestructurar.
- **Dependencias declaradas:** `requirements.txt` (runtime: vosk,
  sounddevice, numpy, pyserial) y `requirements-dev.txt` (+ pytest).
  Antes solo estaban mencionadas en prosa en este mismo documento.
- **Configuración externa:** `config.py` en la raíz lee `PUERTO_ESP32`,
  `BAUDIOS_ESP32` y `RUTA_MODELO_VOSK` de variables de entorno
  (`CULTUBOT_PUERTO_ESP32`, etc.) con los mismos defaults de antes.
  `main.py` ya no tiene esas constantes hardcodeadas.
- **`ESP32Serial` ahora es testeable:** `interface/esp32_serial.py`
  acepta un `transporte` inyectado en el constructor (para tests); si no
  se pasa nada, se comporta exactamente igual que antes (abre un
  `serial.Serial` real). El protocolo en sí no cambió.
- **Suite de pruebas automatizadas (`tests/`, pytest):** cubre máquina
  de estados, interpretación de comandos, normalizador, catálogo de
  lugares, gramática de Vosk, el `Ejecutor` completo (con fakes de
  voz/serial/audio), el modo no bloqueante de audio, **y el protocolo
  real de `ESP32Serial`** (envío línea por línea, filtrado de
  comentarios, detección de `error`, timeout) usando un transporte falso
  en memoria — sin necesitar la ESP32 física. 43 tests, todos en verde.
- **Audio no bloqueante:** `ReproductorAudio.reproducir()` ahora acepta
  `bloqueante=False` para no esperar a que termine la narración (sigue
  siendo bloqueante por defecto, para no romper el comportamiento
  anterior). Habilita, si se quiere más adelante, correr dibujo y
  narración en paralelo.
- **Harness manual sin hardware:** `herramientas/simular_conversacion.py`
  simula la conversación completa escribiendo texto (sin micrófono, sin
  modelo Vosk, sin ESP32) — útil para probar cambios y para demos
  rápidas mientras no hay hardware disponible.

Lo que **no** cambió a propósito (para no sobre-ingenierizar): el
proyecto sigue siendo un script que corre directo en la Raspberry Pi, no
se convirtió en un paquete instalable; no se generó contenido real
(gcode de los sitios, audios grabados) porque eso requiere arte/contenido
real, no reestructuración de código; y la decisión de protocolo
send-and-wait sigue igual, solo se hizo testeable.

## Qué es CultuBot

Robot para WRO Future Engineers que interactúa por voz y dibuja sitios
turísticos de Cúcuta con una CNC basada en ESP32. Debe funcionar 100%
offline, sin APIs de pago ni LLMs pesados.

## Arquitectura (dos cerebros)

- **Raspberry Pi 5 (4GB)** — cerebro IA: escucha (Vosk), interpreta
  comandos, decide, controla el flujo por una máquina de estados, manda
  el gcode a la ESP32 y reproduce audios pregrabados.
- **ESP32 con FluidNC** — cerebro motor: solo ejecuta gcode, controla
  A4988 + NEMA17 + finales de carrera. No hace IA.

## Decisión de comunicación (importante, ya se descartó la alternativa)

Se evaluaron dos opciones para que la Raspberry le mande el dibujo a la
ESP32:

1. **WiFi/HTTP al portal cautivo de FluidNC** (subir el .txt y pedir que
   lo ejecute) — descartada como método de tiempo real.
2. **USB Serial, streaming de gcode línea por línea con protocolo
   send-and-wait (`ok`/`error`)** — la elegida. Es el método estándar de
   Grbl/FluidNC, más confiable que depender de WiFi durante la
   competencia.

El portal web de FluidNC solo se usa **una vez**, para subir
`fluidnc/config.yaml` con el wiring real (pines de motores/limit
switches). En tiempo de ejecución todo es por cable USB.

## Decisión de voz: no hay TTS

Se descartó Piper (y cualquier TTS). Los audios de cada sitio turístico
son archivos `.wav` **pregrabados de antemano**, ubicados en `audio/`, y
se reproducen tal cual con `sounddevice` (misma librería que ya se usa
para el micrófono, sin dependencias nuevas). Los mensajes cortos del
sistema ("Hola, ¿en qué puedo ayudarte?", "Hasta luego") por ahora solo
se imprimen en consola (`VozConsola`) — no se hablan, porque no hay TTS.
Si más adelante quieren que esos mensajes también suenen, habría que
grabarlos como .wav fijos también (mismo mecanismo que las narraciones).

## Mejora de reconocimiento de voz (sin reentrenar Vosk)

Vosk-small tiene poca precisión con lenguaje libre. Como CultuBot solo
necesita reconocer un vocabulario fijo y pequeño, se usa **gramática
restringida** (`core/vocabulario.py`): se le pasa a `KaldiRecognizer` la
lista exacta de frases válidas (lugares, opciones, activación, "salir"),
así el reconocedor no tiene que adivinar entre todo el español. Esto no
es reentrenar el modelo (eso requeriría dataset + GPU), es restringir el
espacio de búsqueda — la técnica correcta para este caso de uso.

## Flujo conversacional (dos pasos para dibujar)

```
Usuario: "Cultubot"
Robot:   "Hola, ¿en qué puedo ayudarte?"          [DORMIDO -> ESPERANDO_ORDEN]

Usuario: "Dibuja la biblioteca"
Robot:   "Encontré Biblioteca Pública. ¿Quieres el dibujo,
          dibujo con audio, o solo audio?"         [-> CONFIRMANDO]

Usuario: "Dibujo con audio"
Robot:   "Preparando el dibujo..." -> envía gcode por Serial
Robot:   "Este es Biblioteca Pública." -> reproduce audio/biblioteca.wav
                                                    [-> DIBUJANDO -> NARRANDO -> FINALIZADO -> ESPERANDO_ORDEN]

Usuario: "Salir"
Robot:   "Hasta luego."                            [-> DORMIDO]
```

Máquina de estados completa en `core/estados.py` (`Estado` enum +
`MaquinaEstados`, transiciones validadas explícitamente).

## Estructura de carpetas y qué va en cada una

```
CULTUBOT/
├── main.py               Composition root: arma todas las dependencias e inicia el loop.
├── config.py             Configuración (puerto/baudios ESP32, ruta modelo Vosk) desde variables de entorno.
├── escuchar.py           Clase Escuchador: captura mic -> Vosk -> normaliza -> interpreta -> ejecuta.
├── requirements.txt      Dependencias de runtime (vosk, sounddevice, numpy, pyserial).
├── requirements-dev.txt  requirements.txt + pytest.
├── conftest.py           Vacío; hace que pytest agregue la raíz al sys.path.
├── .gitignore            venv/, models/, __pycache__/, *.pyc, .pytest_cache/.
├── core/
│   ├── estados.py         Enum Estado + clase MaquinaEstados (máquina de estados real y validada).
│   ├── comandos.py        Interpreta texto -> Accion/Opcion. Puro, no muta estado.
│   ├── acciones.py         Ejecutor: aplica transiciones + dispara efectos (voz, serial, audio).
│   ├── lugares.py           Catálogo de sitios turísticos (Lugar dataclass).
│   ├── normalizador.py      Corrige errores típicos de STT antes de interpretar.
│   ├── audio.py             ReproductorAudio: reproduce los .wav con sounddevice (bloqueante o no). REAL, no stub.
│   └── vocabulario.py       Gramática restringida para Vosk (mejora precisión).
├── interface/
│   └── esp32_serial.py      ESP32Serial: streaming real de gcode por USB, transporte inyectable para tests. REAL, no stub.
├── tests/                   Suite pytest: estados, comandos, normalizador, lugares, vocabulario, acciones, audio, esp32_serial (con transporte falso).
├── herramientas/
│   └── simular_conversacion.py  Simula la conversación completa por texto, sin mic/Vosk/ESP32.
├── drawings/                Archivos .gcode por sitio (biblioteca, cerro_tasajero, templo_historico, ferrocarril, cafe). Ya generados por el usuario, pendientes de copiar aquí.
├── audio/                   Archivos .wav por sitio (mismos 5 nombres que drawings/). FALTAN LOS REALES.
├── fluidnc/                 Config de referencia de FluidNC (config_ejemplo.yaml). Se sube UNA VEZ al ESP32.
├── models/                  Modelo Vosk (vosk-model-small-es-0.42). Se descarga aparte, no versionado.
└── venv/                    Entorno virtual, no versionado.
```

## Qué es real y qué es stub/pendiente

**Ya funciona de verdad, cubierto por la suite automatizada (`pytest`, 43 tests) sin hardware:**
- Máquina de estados, interpretación de comandos, normalizador, catálogo de lugares, gramática de Vosk.
- `Ejecutor` completo (los 3 flujos de confirmación + caso de error al enviar gcode).
- `ReproductorAudio` (reproduce audio real si el `.wav` existe; modo bloqueante y no bloqueante).
- `ESP32Serial.enviar_gcode()` — protocolo real probado con un transporte falso en memoria (envío línea por línea, filtrado de comentarios, `error`, timeout). Sigue sin probarse contra la ESP32 física porque no hay hardware disponible ahora mismo.
- Fallback automático: si `main.py` no logra conectar con la ESP32, cae solo a `SerialConsola` (modo simulado) sin crashear, para poder seguir probando el resto del sistema sin hardware.
- `herramientas/simular_conversacion.py` permite probar el flujo conversacional completo escribiendo texto, sin mic/Vosk/ESP32.
- `herramientas/validar_gcode.py` revisa `drawings/` contra el catálogo real (`core/lugares.py`) y avisa qué archivos faltan o tienen señales de alerta (sin G21/G90, paréntesis desbalanceados, etc.), sin necesitar la ESP32.

**Pendiente / requiere hardware o contenido (nada de esto cambió con la reestructuración):**
1. **Probar `ESP32Serial` con la ESP32 física real** — no se ha podido validar el streaming de gcode contra FluidNC de verdad (sin hardware disponible en este momento). Es la prioridad #1 en cuanto haya acceso al hardware.
2. Completar `fluidnc/config_ejemplo.yaml` con los pines reales (steps_per_mm, STEP/DIR de cada A4988, límites) y subirlo al ESP32.
3. Confirmar el puerto Serial real en la Raspberry (`ls /dev/tty*` con la ESP32 conectada) y setear `CULTUBOT_PUERTO_ESP32` (ver `config.py`; ya no hace falta editar código).
4. **Copiar los `.gcode` reales a `drawings/`** — ya están generados (en otra computadora), pendiente pasarlos a este proyecto con los nombres exactos del catálogo (`biblioteca.gcode`, `cerro_tasajero.gcode`, `templo_historico.gcode`, `ferrocarril.gcode`, `cafe.gcode`). Usar `python herramientas/validar_gcode.py` apenas se copien, para revisarlos sin necesitar la ESP32.
5. Grabar y colocar los `.wav` reales en `audio/` (mismos 5 nombres, extensión `.wav`).
6. Validar en la Raspberry Pi 5 real que `pip install -r requirements.txt` funciona y que PortAudio está instalado (`sudo apt install portaudio19-dev` si hace falta).

## Limitaciones conocidas / mejoras futuras (no bloqueantes)

- `ESP32Serial.enviar_gcode()` usa streaming simple "send-and-wait" (una
  línea, espera `ok`, siguiente línea). Es confiable pero no el método
  más rápido posible; si el dibujo resulta muy lento en la práctica, se
  puede migrar a streaming con buffer (character counting), pero probar
  primero si hace falta.
- El modo no bloqueante de `ReproductorAudio` está disponible
  (`reproducir(..., bloqueante=False)`) pero `Ejecutor` (`core/acciones.py`)
  todavía llama todo de forma secuencial — dibujo y narración no corren
  en paralelo automáticamente todavía; sería el siguiente paso si se
  necesita en la práctica.

## Sugerencia de por dónde seguir en Claude Code

1. Con la ESP32 física disponible: probar `interface/esp32_serial.py`
   contra hardware real usando `drawings/prueba_cuadrado.gcode` (correr
   `main.py` con `CULTUBOT_PUERTO_ESP32` apuntando al puerto real).
2. Si el streaming falla o se comporta raro, revisar baudrate, timeout,
   y si FluidNC espera un handshake distinto al asumido aquí (confirmar
   contra la documentación de FluidNC de la versión que estén usando).
3. Mientras tanto (sin hardware): generar los gcode reales de los sitios
   turísticos y probarlos con `herramientas/simular_conversacion.py` +
   `pytest`.
4. Opcional: usar `reproducir(..., bloqueante=False)` en `core/acciones.py`
   para que dibujo y narración corran en paralelo de verdad.
