"""Preguntas 4-5. Ejecutar después de pipeline.py: python analisis_enlace.py."""

import json
from pathlib import Path
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from pipeline import leer_captura


BASE = Path(__file__).resolve().parent
SESIONES_SQL = """WITH numeradas AS (
  SELECT *,
    SUM(CASE WHEN seq = 1 THEN 1 ELSE 0 END)
      OVER (ORDER BY id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS sesion
  FROM tramas
)
SELECT sesion, COUNT(*) AS n_validas, MAX(seq) AS max_seq,
       MIN(ts) AS primera_ts, MAX(ts) AS ultima_ts
FROM numeradas
GROUP BY sesion
ORDER BY sesion;"""


def main():
    salida = BASE / "resultados"
    salida.mkdir(exist_ok=True)
    ruta_base = BASE / "cps_lab3.db"
    if not ruta_base.is_file():
        raise FileNotFoundError("Ejecute primero: python pipeline.py")
    con = sqlite3.connect(ruta_base)
    try:
        df = pd.read_sql_query("SELECT * FROM tramas ORDER BY id", con)
        sesiones = pd.read_sql_query(SESIONES_SQL, con)
        n_corr = con.execute(
            "SELECT COUNT(*) FROM rechazos WHERE causa IN ('checksum','truncada')"
        ).fetchone()[0]
    finally:
        con.close()
    if df.empty or sesiones.empty:
        raise ValueError("Se necesitan tramas válidas para calcular las métricas")

    df["ts"] = pd.to_datetime(df["ts"])
    df["minuto"] = (df["ts"] - pd.Timestamp("2026-10-08 15:00:00")).dt.total_seconds() / 60
    df["dt"] = df["ts"].diff().dt.total_seconds()
    df["sesion"] = (df["seq"] == 1).cumsum()
    df["dseq"] = df["seq"].diff()
    dt = df["dt"].dropna()
    if (dt <= 0).any():
        raise ValueError("Se esperaba orden temporal estrictamente creciente")

    # El largo se mide sobre las líneas originales, nunca reconstruyendo desde
    # SQLite: así no se pierde el formato decimal original de los números.
    validas, _, textos_validos = leer_captura(BASE / "captura_nodo.txt")
    filas_base = list(df[["seq", "t_ms", "t_mcu", "a0", "pulsos", "boton"]].itertuples(index=False, name=None))
    if len(validas) != len(df) or [fila[1:] for fila in validas] != filas_base:
        raise AssertionError("La captura y la base no corresponden")
    if [fila[0] for fila in validas] != df["ts"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3].tolist():
        raise AssertionError("Las marcas temporales no corresponden")

    longitudes = [len(texto.encode("utf-8")) + 2 for _, texto in textos_validos]
    n_val = len(df)
    n_esp = int(sesiones["max_seq"].sum())
    t = (df["ts"].iloc[-1] - df["ts"].iloc[0]).total_seconds()
    x = n_val / t
    largo = sum(longitudes) / n_val
    r = 10 * largo * x
    categorias = {
        "dt < 3 s": int((dt < 3).sum()),
        "3 <= dt < 5 s": int(((dt >= 3) & (dt < 5)).sum()),
        "5 <= dt <= 10 s": int(((dt >= 5) & (dt <= 10)).sum()),
        "dt > 10 s": int((dt > 10).sum()),
    }
    if sum(categorias.values()) != n_val - 1:
        raise AssertionError("Las categorías no cubren todos los intervalos")
    resultados = {
        "n_sesiones": len(sesiones), "Nesp": n_esp, "Nval": n_val,
        "Ncorr": n_corr, "Nperd": n_esp - n_val - n_corr,
        "D_porcentaje": 100 * n_val / n_esp,
        "primera_ts": df["ts"].iloc[0].isoformat(sep=" "),
        "ultima_ts": df["ts"].iloc[-1].isoformat(sep=" "),
        "T_s": t, "X_tramas_s": x, "L_bytes": largo,
        "bytes_totales_validas_con_CRLF": sum(longitudes),
        "R_bit_s": r, "rho_porcentaje": 100 * r / 115200,
        "longitud_min_bytes": min(longitudes), "longitud_max_bytes": max(longitudes),
        "intervalos": categorias,
        "sesiones": json.loads(sesiones.to_json(orient="records")),
    }
    (salida / "metricas_enlace.json").write_text(
        json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    sesiones.to_csv(salida / "sesiones.csv", index=False, encoding="utf-8")
    pd.DataFrame(categorias.items(), columns=["categoria", "cantidad"]).to_csv(
        salida / "categorias_intervalos.csv", index=False, encoding="utf-8",
    )
    df.to_csv(salida / "tramas_analisis.csv", index=False, encoding="utf-8")
    df.loc[df["dt"] >= 3, ["id", "ts", "seq", "sesion", "dseq", "dt"]].to_csv(
        salida / "intervalos_mayores_3s.csv", index=False, encoding="utf-8",
    )

    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 11})
    fig, ax = plt.subplots(figsize=(10, 5.2), constrained_layout=True)
    bins = np.arange(0, np.ceil(dt.max()) + 0.25, 0.25)
    ax.hist(dt, bins=bins, color="#227a9c", edgecolor="#15506b", linewidth=0.4)
    ax.set_yscale("log")
    ax.set_xlabel("Intervalo entre tramas válidas consecutivas [s]")
    ax.set_ylabel("Cantidad de intervalos (escala logarítmica)")
    ax.set_title(f"Temporización del enlace USB · {len(dt)} intervalos")
    for limite in (3, 5, 10):
        ax.axvline(limite, color="#ba5727", linestyle="--", linewidth=1)
    ax.set_xlim(0, np.ceil(dt.max()) + 0.5)
    ax.set_ylim(0.7, 1500)
    ax.grid(axis="y", which="major", alpha=0.2)
    resumen = "\n".join(f"{cat}: {n}" for cat, n in categorias.items())
    ax.text(0.98, 0.95, resumen, transform=ax.transAxes, ha="right", va="top",
            bbox={"facecolor": "white", "alpha": 0.94, "edgecolor": "#cccccc"})
    fig.savefig(salida / "histograma_intervalos.png", dpi=180)
    plt.close(fig)
    print(json.dumps(resultados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
