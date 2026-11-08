#!/usr/bin/env python3
"""icerik.py testleri (uydurma metinle): python3 -B test_icerik.py"""
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import icerik as ic  # noqa: E402


def ayir(metin):
    bolumler, baslik, satirlar = [], "Giriş", []
    for s in metin.split("\n"):
        if s.startswith("# "):
            if "".join(satirlar).strip():
                bolumler.append((baslik, "\n".join(satirlar)))
            baslik, satirlar = s[2:], []
        else:
            satirlar.append(s)
    if "".join(satirlar).strip():
        bolumler.append((baslik, "\n".join(satirlar)))
    return bolumler


METIN = ("# Bir\nUydurma paragraf: 7545 sayılı kanun anıldı. Yapay Zekâ'nın etkisi yazıldı.\n"
         "# İki\nBaşka paragraf; Siber  Güvenlik Kanunu'nda hüküm var. 75450 sayısı sayılmaz.\n")
BRIF = {"konular": [
    {"id": "C1", "ad": "Kanun", "terimler": ["7545", "siber güvenlik kanunu"], "en_az": 2},
    {"id": "D1", "ad": "YZ", "terimler": ["yapay zeka", "deepfake"]},
    {"id": "X1", "ad": "Yok", "terimler": ["colonial pipeline"]},
]}


class IcerikTesti(unittest.TestCase):
    def setUp(self):
        self.s = ic.tara(METIN, BRIF, ayir)
        self.k = {x["id"]: x for x in self.s["konular"]}

    def test_katlama_ve_ek_kabul(self):
        self.assertEqual(self.k["D1"]["durum"], "var")
        self.assertEqual(self.k["D1"]["bolumler"], [1])

    def test_sayi_sozcuk_basinda_tam_eslesir(self):
        t = {x["terim"]: x["gecis"] for x in self.k["C1"]["terimler"]}
        self.assertEqual(t["7545"], 1)
        self.assertEqual(self.k["C1"]["bolumler"], [1, 2])

    def test_en_az_esigi_ve_bosluk(self):
        self.assertEqual(self.k["C1"]["durum"], "var")
        self.assertEqual(self.k["X1"]["durum"], "yok")
        self.assertEqual(self.s["ozet"], {"var": 2, "zayif": 0, "yok": 1})
        self.assertEqual(self.k["C1"]["oncelik"], "destek")

    def test_katlanmis_ayni_terim_bir_kez_sayilir(self):
        b = {"konular": [{"id": "Y", "terimler": ["yapay zekâ", "yapay zeka"]}]}
        k = ic.tara(METIN, b, ayir)["konular"][0]
        self.assertEqual((len(k["terimler"]), k["toplam_gecis"]), (1, 1))

    def test_zayif(self):
        b = {"konular": [{"id": "Z", "terimler": ["7545"], "en_az": 3}]}
        self.assertEqual(ic.tara(METIN, b, ayir)["konular"][0]["durum"], "zayif")

    def test_rapor_cumle_icermez(self):
        md = ic.markdown(self.s)
        self.assertNotIn("Uydurma paragraf", md)
        self.assertNotIn("Başka paragraf", md)
        self.assertIn("C1 Kanun", md)

    def test_brif_dogrulama(self):
        self.assertEqual(ic.brif_dogrula(BRIF), [])
        self.assertTrue(ic.brif_dogrula({}))
        self.assertTrue(ic.brif_dogrula({"konular": [{"id": "A", "terimler": []}]}))
        self.assertTrue(ic.brif_dogrula({"konular": [{"id": "A", "terimler": ["x"]}, {"id": "A", "terimler": ["y"]}]}))


if __name__ == "__main__":
    unittest.main()
