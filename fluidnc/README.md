# fluidnc/

Esta carpeta guarda una **copia de referencia** de la configuración de FluidNC,
no código que se ejecute desde la Raspberry.

## Flujo de configuración (se hace una sola vez, no en cada dibujo)

1. Completa los pines reales en `config_ejemplo.yaml` (steps_per_mm, pines de
   STEP/DIR de los A4988, pines de los finales de carrera, etc.).
2. Renómbralo a `config.yaml`.
3. Conéctate al portal web/captive portal de FluidNC (WiFi) y súbelo ahí,
   o cópialo directo a la SPIFFS/SD de la ESP32 según cómo tengas flasheado
   FluidNC.
4. Reinicia la ESP32. FluidNC debería levantar los ejes según ese archivo.
5. Prueba manualmente desde el portal web que los motores respondan a
   comandos básicos ($H para homing, jog manual) ANTES de conectar la
   Raspberry.

## En tiempo de ejecución (durante la competencia)

La Raspberry ya NO usa el portal web ni WiFi. Habla con la ESP32 por
**USB Serial** (ver `interface/esp32_serial.py`), mandando el gcode de
`drawings/` línea por línea, tal como lo haría cualquier programa
"gcode sender" de Grbl.
