"""Preguntas 1-3: validar la captura, crear SQLite y comparar con el respaldo.

Uso: python pipeline.py
Los archivos se resuelven respecto de este script, no del directorio de la terminal.
"""

import argparse
from collections import Counter
import json
import math
from pathlib import Path
import re
import sqlite3


BASE = Path(__file__).resolve().parent
CAUSAS = ("basura", "truncada", "checksum", "formato")
ESQUEMA = (
    """CREATE TABLE tramas (
      id INTEGER PRIMARY KEY, ts TEXT NOT NULL, seq INTEGER, t_ms INTEGER,
      t_mcu REAL, a0 INTEGER, pulsos INTEGER, boton INTEGER)""",
    """CREATE TABLE rechazos (
      id INTEGER PRIMARY KEY, ts TEXT NOT NULL, linea TEXT, causa TEXT)""",
)
COLUMNAS = "ts, seq, t_ms, t_mcu, a0, pulsos, boton"


def validar(linea):
    """Retorna (campos, causa); campos es None si la trama se rechaza.

    campos contiene (seq, t_ms, t_mcu, a0, pulsos, boton).
    Valida sintaxis e integridad; no impone coherencia física o antirreplay.
    """
    if not linea.startswith("$"):
        return None, "basura"

    if "*" not in linea:
        return None, "truncada"
    cuerpo, cs = linea[1:].split("*", 1)
    if re.fullmatch(r"[0-9A-Fa-f]{2}", cs) is None:
        return None, "truncada"

    calculado = 0
    for caracter in cuerpo:
        calculado ^= ord(caracter)
    if calculado != int(cs, 16):
        return None, "checksum"

    partes = cuerpo.split(",")
    if len(partes) != 7 or partes[0] != "CPS":
        return None, "formato"
    try:
        campos = (
            int(partes[1]), int(partes[2]), float(partes[3]),
            int(partes[4]), int(partes[5]), int(partes[6]),
        )
    except (ValueError, OverflowError):
        return None, "formato"
    if not math.isfinite(campos[2]):
        return None, "formato"
    return campos, "ok"


def leer_captura(ruta):
    validas, rechazos, textos_validos = [], [], []
    with Path(ruta).open(encoding="utf-8") as archivo:
        for numero_linea, linea in enumerate(archivo, start=1):
            if linea.startswith("#"):
                continue
            # Quita solamente el fin de línea; no normaliza el texto recibido.
            registro = linea.rstrip("\r\n")
            if ";" not in registro:
                raise ValueError(f"Registro sin separador en la línea {numero_linea}")
            ts, texto = registro.split(";", 1)
            campos, causa = validar(texto)
            if causa == "ok":
                validas.append((ts, *campos))
                textos_validos.append((ts, texto))
            else:
                rechazos.append((ts, texto, causa))
    return validas, rechazos, textos_validos


def crear_base(ruta, validas, rechazos):
    con = sqlite3.connect(ruta)
    try:
        # DDL y las dos cargas comparten una transacción explícita.
        con.execute("BEGIN")
        con.execute("DROP TABLE IF EXISTS tramas")
        con.execute("DROP TABLE IF EXISTS rechazos")
        for sentencia in ESQUEMA:
            con.execute(sentencia)
        con.executemany(
            "INSERT INTO tramas (ts,seq,t_ms,t_mcu,a0,pulsos,boton) VALUES (?,?,?,?,?,?,?)",
            validas,
        )
        con.executemany(
            "INSERT INTO rechazos (ts,linea,causa) VALUES (?,?,?)", rechazos,
        )
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def resumen_base(con, esquema):
    # esquema solo se invoca con los alias internos main y ref.
    n, suma_seq, suma_a0 = con.execute(
        f"SELECT COUNT(*), SUM(seq), SUM(a0) FROM {esquema}.tramas"
    ).fetchone()
    conteos = dict(con.execute(
        f"SELECT causa, COUNT(*) FROM {esquema}.rechazos GROUP BY causa"
    ))
    return {
        "tramas": n, "suma_seq": suma_seq, "suma_a0": suma_a0,
        "rechazos": {causa: conteos.get(causa, 0) for causa in CAUSAS},
    }


def verificar_respaldo(base, respaldo):
    if not Path(respaldo).is_file():
        raise FileNotFoundError(respaldo)
    con = sqlite3.connect(base)
    try:
        con.execute("ATTACH DATABASE ? AS ref", (str(respaldo),))
        resumen = {alias: resumen_base(con, alias) for alias in ("main", "ref")}
        diferencias = {}
        for tabla, columnas in (("tramas", COLUMNAS), ("rechazos", "ts,linea,causa")):
            for origen, destino in (("main", "ref"), ("ref", "main")):
                clave = f"{tabla}_{origen}_menos_{destino}"
                diferencias[clave] = con.execute(
                    f"SELECT {columnas} FROM {origen}.{tabla} EXCEPT "
                    f"SELECT {columnas} FROM {destino}.{tabla}"
                ).fetchall()
        # EXCEPT compara conjuntos: esta comprobación adicional incluye multiplicidad,
        # ids y orden, para asegurar igualdad completa de ambas tablas.
        igualdad_ordenada = {
            tabla: con.execute(f"SELECT * FROM main.{tabla} ORDER BY id").fetchall()
            == con.execute(f"SELECT * FROM ref.{tabla} ORDER BY id").fetchall()
            for tabla in ("tramas", "rechazos")
        }
        if resumen["main"] != resumen["ref"] or any(diferencias.values()) or not all(igualdad_ordenada.values()):
            raise AssertionError(f"La base no coincide con el respaldo: {resumen}; {diferencias}")
        return {"resumen": resumen, "diferencias": diferencias,
                "igualdad_completa_por_id": igualdad_ordenada}
    finally:
        con.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--captura", type=Path, default=BASE / "captura_nodo.txt")
    parser.add_argument("--respaldo", type=Path, default=BASE / "cps_lab3_respaldo.db")
    parser.add_argument("--base", type=Path, default=BASE / "cps_lab3.db")
    args = parser.parse_args()
    validas, rechazos, _ = leer_captura(args.captura)
    crear_base(args.base, validas, rechazos)
    verificacion = verificar_respaldo(args.base, args.respaldo)
    conteos = Counter(fila[2] for fila in rechazos)
    resultado = {
        "lineas_datos": len(validas) + len(rechazos), "validas": len(validas),
        "rechazos": {c: conteos[c] for c in CAUSAS}, "verificacion": verificacion,
    }
    salida = BASE / "resultados"
    salida.mkdir(exist_ok=True)
    (salida / "pipeline.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8",
    )
    print(json.dumps(resultado, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
