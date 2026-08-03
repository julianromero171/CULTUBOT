; prueba_cuadrado.gcode
; Dibuja un cuadrado pequeño. Úsalo para probar la conexión Serial
; Raspberry <-> ESP32 antes de tener los gcode reales de cada sitio.
G21 ; unidades en milímetros
G90 ; coordenadas absolutas
G0 X0 Y0
G1 X20 Y0 F800
G1 X20 Y20 F800
G1 X0 Y20 F800
G1 X0 Y0 F800
