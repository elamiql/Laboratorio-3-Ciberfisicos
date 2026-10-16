# Laboratorio Evaluado 3: solución completa

Entregables: Informe_Laboratorio_3.pdf, código Python y cps_lab3.db.
El informe responde las preguntas 1-11, incluye gráficos, tablas y SQL.
Agregar los nombres de los integrantes al informe antes de entregar, si la plataforma los requiere. No se han supuesto nombres.

## Reproducir en Windows

Desde esta carpeta, con Python 3.9 o superior:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe pipeline.py
.\.venv\Scripts\python.exe analisis_enlace.py
.\.venv\Scripts\python.exe analisis_fallas.py
.\.venv\Scripts\python.exe -m unittest -v test_pipeline.py
```

En Linux/macOS usar python3 y .venv/bin/python.
Los scripts resuelven las rutas respecto a su ubicación. pipeline.py recrea las tablas de cps_lab3.db y comprueba su igualdad con el respaldo. El registro y el respaldo no se modifican. Las consultas SQL con ATTACH deben ejecutarse desde esta carpeta.

## Contenido

- pipeline.py: validación, carga atómica y comparación con respaldo.
- analisis_enlace.py: preguntas 4-5, métricas e histograma.
- analisis_fallas.py: preguntas 6-9, métricas de P10, gráficos y evidencia CSV.
- consultas.sql: consultas SQL utilizadas.
- informe.md: versión editable completa del texto del informe.
- respuestas_parte1.md y respuestas_parte2.md: texto de desarrollo por partes.
- resultados/: gráficos, JSON de métricas y CSV de evidencia, incluido JOIN completo.
- captura_nodo.txt y cps_lab3_respaldo.db: entradas originales.
- cps_lab3.db: base generada, 850 tramas y 16 rechazos.

## Límites de interpretación

El detector flotante es retrospectivo, marca 27 muestras, omite tres dentro del tramo fluctuante y marca una muestra de recuperación. La prueba de tasa produce cuatro alarmas de transición, no un conteo completo de FDI. La cuantización ADC identifica 48 tramas; el JOIN y la continuidad identifican 30 copias. D corregida elimina replay, pero sigue incluyendo FDI y datos físicamente defectuosos.

El ZIP no incluye el entorno virtual de Windows: las dependencias se reinstalan con requirements.txt.
