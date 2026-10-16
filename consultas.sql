-- P2: cantidad de filas de cada tabla.
SELECT COUNT(*) AS n_tramas FROM tramas;
SELECT COUNT(*) AS n_rechazos FROM rechazos;
SELECT causa, COUNT(*) AS cantidad FROM rechazos GROUP BY causa;

-- P3: ejecutar ATTACH una sola vez en la conexión.
ATTACH DATABASE 'cps_lab3_respaldo.db' AS ref;
SELECT COUNT(*) AS cantidad, SUM(seq) AS suma_seq, SUM(a0) AS suma_a0 FROM main.tramas;
SELECT COUNT(*) AS cantidad, SUM(seq) AS suma_seq, SUM(a0) AS suma_a0 FROM ref.tramas;
SELECT causa, COUNT(*) AS cantidad FROM main.rechazos GROUP BY causa;
SELECT causa, COUNT(*) AS cantidad FROM ref.rechazos GROUP BY causa;

-- Generada menos respaldo.
SELECT ts,seq,t_ms,t_mcu,a0,pulsos,boton FROM main.tramas
EXCEPT
SELECT ts,seq,t_ms,t_mcu,a0,pulsos,boton FROM ref.tramas;

-- Respaldo menos generada.
SELECT ts,seq,t_ms,t_mcu,a0,pulsos,boton FROM ref.tramas
EXCEPT
SELECT ts,seq,t_ms,t_mcu,a0,pulsos,boton FROM main.tramas;

-- P4: numeración por reinicios confirmados, no por cualquier caída de seq.
WITH numeradas AS (
  SELECT *, SUM(CASE WHEN seq=1 THEN 1 ELSE 0 END)
    OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS sesion
  FROM tramas
)
SELECT sesion,COUNT(*) AS n_validas,MAX(seq) AS max_seq,MIN(ts) AS primera_ts,MAX(ts) AS ultima_ts
FROM numeradas GROUP BY sesion ORDER BY sesion;

WITH numeradas AS (
  SELECT seq,SUM(CASE WHEN seq=1 THEN 1 ELSE 0 END) OVER(ORDER BY id) AS sesion FROM tramas
), maximos AS (
  SELECT sesion,MAX(seq) AS max_seq FROM numeradas GROUP BY sesion
), conteos AS (
  SELECT (SELECT SUM(max_seq) FROM maximos) AS Nesp,
         (SELECT COUNT(*) FROM tramas) AS Nval,
         (SELECT COUNT(*) FROM rechazos WHERE causa IN ('checksum','truncada')) AS Ncorr
)
SELECT Nesp,Nval,Ncorr,Nesp-Nval-Ncorr AS Nperd,100.0*Nval/Nesp AS D_porcentaje FROM conteos;

-- P5: intervalos consecutivos calculados a partir de ts.
-- Se redondea al milisegundo para compensar el error de julianday.
WITH intervalos AS (
 SELECT ROUND((julianday(ts)-julianday(LAG(ts) OVER(ORDER BY id)))*86400,3) AS dt
 FROM tramas
)
SELECT SUM(dt<3) AS menor_3,
       SUM(dt>=3 AND dt<5) AS entre_3_y_5,
       SUM(dt>=5 AND dt<=10) AS entre_5_y_10,
       SUM(dt>10) AS mayor_10
FROM intervalos WHERE dt IS NOT NULL;


-- P6-P8: series y rechazos usados por el análisis Python.
SELECT * FROM tramas ORDER BY id;
SELECT * FROM rechazos ORDER BY id;
-- P9: igualdad del contenido con mensajes anteriores.
SELECT a.id,a.ts,a.seq,b.id AS id_original,b.ts AS ts_original
FROM tramas a JOIN tramas b
ON a.seq=b.seq AND a.t_ms=b.t_ms AND a.t_mcu=b.t_mcu
AND a.a0=b.a0 AND a.pulsos=b.pulsos AND a.boton=b.boton
AND b.id<a.id ORDER BY a.id;
