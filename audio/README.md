# audio/

Archivos `.wav` pregrabados. No usamos Piper ni ningún TTS: todo esto ya
viene grabado de antemano.

## Narración por sitio

El nombre de archivo debe coincidir exactamente con `archivo_audio` en
`core/lugares.py`:

- `biblioteca.wav`
- `cerro_tasajero.wav`
- `ferrocarril.wav`
- `templo_historico.wav`
- `cafe.wav`

Si agregas un lugar nuevo en `core/lugares.py`, agrega aquí su `.wav`
correspondiente con el mismo nombre.

## Mensajes fijos de la conversación

Ver `core/mensajes.py` — se reproducen en puntos concretos del flujo
(activación, elección de sitio, pregunta de opción, salida):

- `bienvenida.wav` — al activarse ("cultura"/"culto").
- `dibujo_con_audio_o_sin_audio.wav` — pregunta de qué opción quiere.
- `eleccion_biblioteca.wav`, `eleccion_cerro.wav`, `eleccion_ferrocarril.wav`,
  `eleccion_templo.wav`, `eleccion_cafe.wav` — confirmación de qué sitio se eligió.
- `despedida.wav` — al decir "salir".
