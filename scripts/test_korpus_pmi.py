#!/usr/bin/env python3
"""korpus_pmi.py birim testleri (yalnız standart kütüphane): python3 scripts/test_korpus_pmi.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import korpus_pmi as kp  # noqa: E402


ORNEK_KORPUS = """
Araştırmada üç temel hipotez kurulmaktadır. İkinci bölümde yeni bir hipotez kurulmuştur.
Literatür taraması sonucunda sınanabilir bir hipotez kuruldu.
Siber saldırılar kritik altyapılara yönelik tehdit oluşturmaktadır.
Asimetrik unsurlar ulusal güvenliğe ciddi tehdit oluşturmuştur.
Bölgesel istikrarsızlık sınır güvenliğine tehdit oluşturmaktadır.
Yarı yapılandırılmış mülakat yöntemiyle saha verileri toplanmıştır.
İkincil arşiv kaynaklarından kapsamlı veriler toplanmaktadır.
Örneklem grubundan anket yoluyla birincil veriler toplandı.
Tek seferlik gürültü kelimesi rastgele yazılmıştır.
"""


class KorpusPmiTesti(unittest.TestCase):
    def test_cumlelere_ayir_atiflari_temizler(self):
        metin = "Siber caydırıcılık (Yılmaz, 2018) incelenmiştir [12]. İkinci cümle uzundur."
        cumleler = kp.cumlelere_ayir(metin)
        self.assertEqual(len(cumleler), 2)
        self.assertNotIn("2018", cumleler[0])
        self.assertNotIn("[12]", cumleler[0])

    def test_fiil_ve_isim_koku_cikarma(self):
        self.assertEqual(kp.fiil_koku_cikar("oluşturmaktadır"), "oluştur")
        self.assertEqual(kp.fiil_koku_cikar("incelenmiştir"), "incele")
        self.assertEqual(kp.isim_koku_cikar("tehdidi"), "tehdit")
        self.assertEqual(kp.isim_koku_cikar("boşluğu"), "boşluk")
        self.assertEqual(kp.isim_koku_cikar("politikalarını"), "politika")

    def test_pmi_hesapla_yerlesik_esdizimleri_bulur(self):
        sonuclar = kp.pmi_hesapla(ORNEK_KORPUS, min_frekans=2, pencere=3)
        ciftler = {(s["nesne"], s["fiil"]): s for s in sonuclar}
        self.assertIn(("hipotez", "kurmak"), ciftler)
        self.assertIn(("tehdit", "oluşturmak"), ciftler)
        self.assertIn(("veri", "toplamak"), ciftler)
        self.assertGreater(ciftler[("hipotez", "kurmak")]["pmi"], 0.5)

    def test_min_frekans_nadir_gurultu_filtresi(self):
        sonuclar = kp.pmi_hesapla(ORNEK_KORPUS, min_frekans=2, pencere=3)
        nesneler = {s["nesne"] for s in sonuclar}
        self.assertNotIn("gürültü", nesneler)
        self.assertNotIn("kelime", nesneler)
        for s in sonuclar:
            self.assertGreaterEqual(s["frekans"], 2)

    def test_dogal_fiilleri_grupla(self):
        sonuclar = kp.pmi_hesapla(ORNEK_KORPUS, min_frekans=2, pencere=3)
        gruplar = kp.dogal_fiilleri_grupla(sonuclar)
        self.assertIn("kurmak", gruplar.get("hipotez", []))
        self.assertIn("oluşturmak", gruplar.get("tehdit", []))
        self.assertIn("toplamak", gruplar.get("veri", []))

    def test_cli_json_ciktisi(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
        f.write(ORNEK_KORPUS)
        f.close()
        try:
            cikti = io.StringIO()
            with contextlib.redirect_stdout(cikti):
                kod = kp.main([f.name, "--min-frekans", "2", "--json"])
            self.assertEqual(kod, 0)
            veri = json.loads(cikti.getvalue())
            self.assertGreaterEqual(veri["toplam_cift"], 3)
            self.assertIn("hipotez", veri["dogal_fiiller"])
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
