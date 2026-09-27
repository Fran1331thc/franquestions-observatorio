# Historial automático de pruebas en sombra

`bccr_exchange_rate_shadow.jsonl` será creado por GitHub Actions. Cada línea
representa una ejecución de solo lectura y contiene la huella de la entrada
anterior. El flujo nunca modifica `franquestions.db`.

Una prueba solo cuenta como independiente cuando fue satisfactoria y ocurrió en
una fecha distinta de Costa Rica. El paso a escritura supervisada requiere tres
días satisfactorios, cero errores y revisión humana.
