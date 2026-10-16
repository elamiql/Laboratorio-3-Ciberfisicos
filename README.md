# Laboratorio 3: parte base (preguntas 1-5)

Este paquete deja lista la base que utilizará el compañero para resolver las
preguntas 6-11. No es todavía el informe PDF final de la pareja.

## Ejecución

Descomprimir toda la carpeta. Requiere Python 3.9 o superior. Abrir una terminal
dentro de `laboratorio3_parte1`.

En Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe pipeline.py
.\.venv\Scripts\python.exe analisis_enlace.py
```

En Linux/macOS, usar `python3` para crear el entorno y `.venv/bin/python` en lugar
de `.\.venv\Scripts\python.exe`.

El pipeline vuelve a crear las tablas `tramas` y `rechazos` de `cps_lab3.db` en
cada ejecución. El archivo de respaldo y el registro crudo se conservan. Si se
agregan tablas de análisis propias a la base, evitar claves foráneas a las tablas
recreadas o guardar ese análisis en archivos separados.

Las consultas de `consultas.sql` se deben ejecutar con esta carpeta como directorio
de trabajo para que `ATTACH` localice el respaldo. El archivo usa funciones de
ventana, por lo que requiere SQLite 3.25 o superior, según el enunciado.

Pruebas opcionales:

```powershell
.\.venv\Scripts\python.exe -m unittest -v test_pipeline.py
```

## Cómo revisar tu parte

1. Leer `validar()` en `pipeline.py`: cuatro causas y su precedencia.
2. Revisar `leer_captura()`: separación de hora y texto, UTF-8 y conteos.
3. Revisar `crear_base()`: esquema, orden, `executemany` y transacción única.
4. Revisar `verificar_respaldo()`: sumas, EXCEPT e igualdad por id.
5. Leer `analisis_enlace.py`: sesiones, disponibilidad y temporización.
6. Revisar `respuestas_parte1.md` y ajustar su redacción al informe de la pareja.

## Checklist de tu parte: realizada y comprobada con los archivos proporcionados

- [x] P1: validador, orden de rechazos, procesamiento completo y explicación de UTF-8.
- [x] P2: SQLite con esquema pedido, carga en una transacción y conteos SQL.
- [x] P3: comparación de resúmenes y EXCEPT en ambos sentidos sin diferencias.
- [x] P4: sesiones mediante funciones de ventana y métricas de disponibilidad.
- [x] P5a: T, X, L, R, ocupación y discusión del margen.
- [x] P5b: histograma logarítmico, categorías y explicación de los intervalos.
- [x] Respuestas escritas, código, base y resultados preparados para compartir.
- [ ] Leer y comprender el código y la redacción antes de entregar.

## Checklist del compañero: pendiente

- [ ] P6: identificar desconexiones con al menos tres señales; tabla de reparación,
  MTTR, MTBF, disponibilidad A y comparación con D.
- [ ] P7: gráfico a0, detector automático de entrada flotante, límites, tramas
  marcadas y falsos positivos; validación sintáctica frente a física.
- [ ] P8: FDI, variable afectada, límites ts/seq, cantidad, magnitud y gráfico;
  explicación de checksum y pilar de seguridad; prueba ADC y tasa de cambio.
- [ ] P9: JOIN para replay, originales y repeticiones, coincidencias fuera de
  ventana, comparación con reconexión y D corregida.
- [ ] P10: formato HMAC y contador persistente o sesión aleatoria, reglas del
  receptor, longitudes y nueva ocupación del enlace.
- [ ] P11: cronología, cobertura de detección, eslabón débil y mejora concreta.

## Entrega conjunta: pendiente

- [ ] Incorporar respuestas 1-5 y 6-11 en un único informe PDF.
- [ ] Incorporar gráficos, tablas y todas las consultas SQL utilizadas.
- [ ] Revisar consistencia de los valores compartidos: T, Nesp, Nval, D, L y X.
- [ ] Incluir el código Python de ambas partes y `cps_lab3.db`.
- [ ] Revisar PDF y archivos finales antes de enviar por la plataforma del curso.

## Datos que necesita el compañero

| Magnitud | Valor |
|---|---:|
| Sesiones | 4 |
| Nesp | 873 |
| Nval inicial, incluidas todas las tramas válidas | 850 |
| Ncorr | 13 |
| Nperd inicial | 10 |
| D inicial | 97,36540664375715 % |
| T | 1797,872 s |
| X | 0,47278115460944936 tramas/s |
| L, con CRLF | 32,625882352941176 bytes/trama |
| R | 154,24902328975588 bit/s |
| Ocupación | 0,13389672160569085 % |

**Atención:** no eliminar tramas de `tramas` para los análisis de seguridad ni
alterar sus ids. Usar filtros o columnas derivadas. P4 incluye todas las válidas;
P9 solicita un cálculo corregido específico. Un descenso de seq por sí solo no
debe generar una nueva sesión.
"# Lab 3 " 
