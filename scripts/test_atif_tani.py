#!/usr/bin/env python3
"""atif_tani.py testleri (uydurma veriyle): python3 -B test_atif_tani.py"""
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import atif_tani as at  # noqa: E402
import tez_analiz as ta  # noqa: E402

KAYNAKCA = [
    "BERMAN, Jay (2019), Kitap Bir, Ankara.",
    "KAYA, Mehmet (2009), Kitap İki, İstanbul.",
    "EVANS, John and SMITH, Paul (1967), Kitap Üç, London.",
    "DEMİR, Veli (2015), Kitap Dört, İzmir.",
    "FAZLALIK, Zeynep (2010), Kitap Beş, Ankara.",
    "COŞKUN, Ali (2003), Kitap Altı, Ankara.",
]
METIN = (
    "Birinci (Bernan, 2019) iddia. İkinci (Kaya, 2008: 4) iddia. Üçüncü (Smith, 1967) iddia. "
    "Dördüncü (Yok, 2020) iddia. Beşinci (Demir, 2015) iddia. Altıncı (Coşkum, 2003) iddia."
)


class AtifTaniTesti(unittest.TestCase):
    def setUp(self):
        self.ak = ta.atif_kaynakca_denetimi(METIN, KAYNAKCA)
        self.t = at.tani(self.ak["kaynakcada_eksik_atiflar"], self.ak["metinde_eksik_kaynaklar"],
                         KAYNAKCA, self.ak["metin_atiflari"])

    def test_metin_atiflari_listesi_doner(self):
        self.assertIn("Bernan (2019)", self.ak["metin_atiflari"])

    def test_yazim_farki_iki_yonde_eslesir(self):
        yok = {k: [x["atif"] for x in v] for k, v in self.t["atif_kaynakcada_yok"].items()}
        self.assertIn("Bernan (2019)", yok["yazim_farki"])
        self.assertIn("Coşkum (2003)", yok["yazim_farki"])
        atifsiz = {k: [x["kaynakca"] for x in v] for k, v in self.t["kaynakca_atifsiz"].items()}
        self.assertIn("BERMAN (2019)", atifsiz["yazim_farki"])

    def test_yil_farki(self):
        yok = {k: [x["atif"] for x in v] for k, v in self.t["atif_kaynakcada_yok"].items()}
        self.assertIn("Kaya (2008)", yok["yil_farki"])
        self.assertEqual(self.t["atif_kaynakcada_yok"]["yil_farki"][0]["kaynakca"], "KAYA (2009)")

    def test_gercek_eksik_ve_gercek_atifsiz(self):
        yok = {k: [x["atif"] for x in v] for k, v in self.t["atif_kaynakcada_yok"].items()}
        self.assertEqual(yok["gercek_eksik"], ["Yok (2020)"])
        atifsiz = {k: [x["kaynakca"] for x in v] for k, v in self.t["kaynakca_atifsiz"].items()}
        self.assertEqual(atifsiz["gercek_atifsiz"], ["FAZLALIK (2010)"])
        # EVANS ve SMITH ortak kaynak; metinde yalnız ikinci yazar (Smith) atıf almış
        self.assertEqual(self.t["kaynakca_atifsiz"]["ikinci_yazar_olasi"][0]["kaynakca"], "EVANS (1967)")

    def test_kisa_adlar_yazim_farki_sayilmaz(self):
        self.assertFalse(at.yakin("un", "lin"))
        self.assertFalse(at.yakin("segal", "senol"))
        self.assertTrue(at.yakin("bernan", "berman"))

    def test_kucuk_harfli_sozcuk_yazar_sayilmaz(self):
        ak = ta.atif_kaynakca_denetimi("Bu olay ancak (ancak 1940, sonra) ve (Yılmaz, 2020).", ["YILMAZ, A. (2020), Kitap, Ankara."])
        self.assertNotIn("ancak (1940)", ak["kaynakcada_eksik_atiflar"])

    def test_ozet_sayilari(self):
        self.assertEqual(self.t["ozet"]["atif_kaynakcada_yok"]["gercek_eksik"], 1)

    def test_uzaklik_ve_katlama(self):
        self.assertEqual(at.uzaklik("bernan", "berman"), 1)
        self.assertEqual(at.katla("IŞIK"), at.katla("ışık"))
        self.assertEqual(at.katla("Işık"), "isik")


if __name__ == "__main__":
    unittest.main(verbosity=1)
