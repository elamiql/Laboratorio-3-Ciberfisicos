"""Pruebas de las categorías y, especialmente, de su precedencia."""
import unittest

from pipeline import validar


def trama(cuerpo):
    checksum = 0
    for caracter in cuerpo:
        checksum ^= ord(caracter)
    return f"${cuerpo}*{checksum:02X}"


class TestValidar(unittest.TestCase):
    def test_trama_correcta(self):
        self.assertEqual(validar("$CPS,1,2001,30.9,513,0,0*51"),
                         ((1, 2001, 30.9, 513, 0, 0), "ok"))

    def test_categorias_y_precedencia(self):
        casos = [
            ("ruido", "basura"),
            ("ruido*GG", "basura"),
            ("$ABC,xyz", "truncada"),
            ("$CPS,1*5", "truncada"),
            ("$CPS,1*GG", "truncada"),
            ("$CPS,1*511", "truncada"),
            ("$CPS,1,2001,30.9,513,0,0*50", "checksum"),
            ("$ABC,x*00", "checksum"),
            (trama("ABC,1,2001,30.9,513,0,0"), "formato"),
            (trama("CPS,1,2001,30.9,513,0"), "formato"),
            (trama("CPS,1,2001,abc,513,0,0"), "formato"),
            (trama("CPS,1,2001,nan,513,0,0"), "formato"),
            (trama("CPS,1.5,2001,30.9,513,0,0"), "formato"),
        ]
        for texto, causa in casos:
            with self.subTest(texto=texto):
                self.assertEqual(validar(texto), (None, causa))

    def test_no_impone_validacion_fisica(self):
        self.assertEqual(validar(trama("CPS,1,2001,90.9,513,99,0"))[1], "ok")


if __name__ == "__main__":
    unittest.main()
