# CultuBot — Contexto para continuar en Claude Code

Este documento resume todo lo decidido y construido hasta ahora, para que
puedas retomar el proyecto en Claude Code sin perder contexto de la
conversación anterior.

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

Usuario: "Dibuja el malecón"
Robot:   "Encontré Malecón de Cúcuta. ¿Quieres el dibujo,
          dibujo con audio, o solo audio?"         [-> CONFIRMANDO]

Usuario: "Dibujo con audio"
Robot:   "Preparando el dibujo..." -> envía gcode por Serial
Robot:   "Este es el Malecón de Cúcuta." -> reproduce audio/malecon.wav
                                                    [-> DIBUJANDO -> NARRANDO -> FINALIZADO -> ESPERANDO_ORDEN]

Usuario: "Salir"
Robot:   "Hasta luego."                            [-> DORMIDO]
```

Máquina de estados completa en `core/estados.py` (`Estado` enum +
`MaquinaEstados`, transiciones validadas explícitamente).

## Estructura de carpetas y qué va en cada una

```
CULTUBOT/
├── main.py              Composition root: arma todas las dependencias e inicia el loop.
├── escuchar.py           Clase Escuchador: captura mic -> Vosk -> normaliza -> interpreta -> ejecuta.
├── probar_microfono.py   Utilidad de diagnóstico de audio (sin cambios).
├── core/
│   ├── estados.py         Enum Estado + clase MaquinaEstados (máquina de estados real y validada).
│   ├── comandos.py        Interpreta texto -> Accion/Opcion. Puro, no muta estado.
│   ├── acciones.py         Ejecutor: aplica transiciones + dispara efectos (voz, serial, audio).
│   ├── lugares.py           Catálogo de sitios turísticos (Lugar dataclass).
│   ├── normalizador.py      Corrige errores típicos de STT antes de interpretar.
│   ├── audio.py             ReproductorAudio: reproduce los .wav con sounddevice. REAL, no stub.
│   └── vocabulario.py       Gramática restringida para Vosk (mejora precisión).
├── interface/
│   └── esp32_serial.py      ESP32Serial: streaming real de gcode por USB. REAL, no stub.
├── drawings/                Archivos .gcode por sitio (drawings/malecon.gcode, etc.). FALTAN LOS REALES.
├── audio/                   Archivos .wav por sitio (audio/malecon.wav, etc.). FALTAN LOS REALES.
├── fluidnc/                 Config de referencia de FluidNC (config_ejemplo.yaml). Se sube UNA VEZ al ESP32.
├── models/                  Modelo Vosk (vosk-model-small-es-0.42). Ya lo tenían.
└── venv/                    Entorno virtual, sin cambios.
```

## Qué es real y qué es stub/pendiente

**Ya funciona de verdad, probado en este sandbox sin hardware:**
- Máquina de estados, interpretación de comandos, normalizador, catálogo de lugares.
- `ReproductorAudio` (reproduce audio real si el `.wav` existe).
- `ESP32Serial.enviar_gcode()` (implementación real del protocolo, no probada con hardware físico todavía porque no hay ESP32 disponible ahora mismo).
- Fallback automático: si `main.py` no logra conectar con la ESP32, cae solo a `SerialConsola` (modo simulado) sin crashear, para poder seguir probando el resto del sistema sin hardware.

**Pendiente / requiere hardware o contenido:**
1. **Probar `ESP32Serial` con la ESP32 física real** — no se ha podido validar el streaming de gcode contra FluidNC de verdad (sin hardware disponible en este momento). Es la prioridad #1 en cuanto haya acceso al hardware.
2. Completar `fluidnc/config_ejemplo.yaml` con los pines reales (steps_per_mm, STEP/DIR de cada A4988, límites) y subirlo al ESP32.
3. Confirmar el puerto Serial real en la Raspberry (`ls /dev/tty*` con la ESP32 conectada) y actualizar `PUERTO_ESP32` en `main.py` (ahora mismo asume `/dev/ttyUSB0`).
4. Generar los `.gcode` reales de cada sitio turístico (hoy solo existe `drawings/prueba_cuadrado.gcode` de prueba).
5. Grabar y colocar los `.wav` reales en `audio/`.
6. Validar en la Raspberry Pi 5 real que `pip install vosk sounddevice pyserial numpy` funciona y que PortAudio está instalado (`sudo apt install portaudio19-dev` si hace falta).

## Limitaciones conocidas / mejoras futuras (no bloqueantes)

- `ReproductorAudio.reproducir()` es **bloqueante** (`sd.wait()`): si se
  quiere que el dibujo y la narración corran en paralelo de verdad (no
  solo uno después del otro), hay que moverlo a un hilo aparte.
- `ESP32Serial.enviar_gcode()` usa streaming simple "send-and-wait" (una
  línea, espera `ok`, siguiente línea). Es confiable pero no el método
  más rápido posible; si el dibujo resulta muy lento en la práctica, se
  puede migrar a streaming con buffer (character counting), pero probar
  primero si hace falta.
- El archivo `prueba` en la raíz del proyecto no se identificó — revisar
  si sigue siendo necesario.

## Sugerencia de por dónde seguir en Claude Code

1. Con la ESP32 física disponible: probar `interface/esp32_serial.py`
   contra hardware real usando `drawings/prueba_cuadrado.gcode`.
2. Si el streaming falla o se comporta raro, revisar baudrate, timeout,
   y si FluidNC espera un handshake distinto al asumido aquí (confirmar
   contra la documentación de FluidNC de la versión que estén usando).
3. Después, generar los gcode reales de los sitios turísticos y probar
   dibujos completos.
4. Opcional: audio no bloqueante (hilo aparte) para dibujo+narración en paralelo.
