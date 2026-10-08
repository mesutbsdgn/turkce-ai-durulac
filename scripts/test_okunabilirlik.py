#!/usr/bin/env python3
"""okunabilirlik.py birim testleri (yalnız standart kütüphane): python3 scripts/test_okunabilirlik.py"""
import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import okunabilirlik as o  # noqa: E402


def sayilar(metin):
    return sorted(o.normal(x) for x in o.SAYI.findall(metin))


def calistir(*arg):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = o.main(list(arg))
    return kod, cikti.getvalue(), hata.getvalue()


def dosya(icerik):
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8")
    f.write(icerik)
    f.close()
    return f.name


class Hece(unittest.TestCase):
    def test_unlu_sayisi_hece_sayisidir(self):
        self.assertEqual(o.hece("kitap"), 2)
        self.assertEqual(o.hece("okunabilirlik"), 6)
        self.assertEqual(o.hece("ağ"), 1)

    def test_unluzu_olmayan_en_az_bir_hece(self):
        self.assertEqual(o.hece("TL"), 1)


class Cumle(unittest.TestCase):
    def test_basit_bolme(self):
        self.assertEqual(len(o.cumleler("Gel. Gör. Yaz.")), 3)

    def test_binlik_nokta_bolmez(self):
        self.assertEqual(len(o.cumleler("Tutar 12.500 TL oldu. Ödendi.")), 2)

    def test_kisaltma_bolmez(self):
        self.assertEqual(len(o.cumleler("Dr. Ayşe geldi. Toplantı başladı.")), 2)

    def test_sira_sayisi_kucuk_harf_bolmez(self):
        self.assertEqual(len(o.cumleler("3. çeyrekte gelir arttı. Bu iyi.")), 2)

    def test_bos_metin(self):
        self.assertEqual(o.cumleler("   "), [])
        self.assertIsNone(o.olc("")["atesman"])


class Olcum(unittest.TestCase):
    def test_kisa_cumle_kolay_uzun_cumle_zor(self):
        kolay = o.olc("Ali geldi. Ali gitti. Ali yedi.")
        zor = o.olc("Gerçekleştirilmesi öngörülen düzenlemelerin değerlendirilmesine ilişkin "
                    "yükümlülüklerin yerine getirilebilmesi bakımından gerekli koşullar oluşturulmuştur.")
        self.assertGreater(kolay["atesman"], zor["atesman"])
        self.assertLess(kolay["by"], zor["by"])

    def test_duzey_sinirlari(self):
        self.assertEqual(o.atesman_duzey(95), "çok kolay")
        self.assertEqual(o.atesman_duzey(70), "kolay")
        self.assertEqual(o.atesman_duzey(50), "orta")
        self.assertEqual(o.atesman_duzey(30), "zor")
        self.assertEqual(o.atesman_duzey(10), "çok zor")
        self.assertIn("ölçek dışı", o.atesman_duzey(120))
        self.assertEqual(o.by_duzey(8), "ilköğretim")
        self.assertEqual(o.by_duzey(20), "akademik")


class SayiAlgilama(unittest.TestCase):
    def test_turk_tutari(self):
        self.assertEqual(sayilar("Tutar 1.250,00 TL ödenecek."), ["1.250,00tl"])

    def test_milyon_olcegi_degerin_parcasi(self):
        self.assertEqual(sayilar("Yaklaşık 1,5 milyon TL harcandı."), ["1,5milyontl"])

    def test_yuzde_onde_ve_sonda(self):
        self.assertEqual(sayilar("Oran %4,25 oldu."), ["%4,25"])
        self.assertEqual(sayilar("Oran 4,25% oldu."), ["4,25%"])

    def test_negatif_yuzde(self):
        self.assertEqual(sayilar("Değişim -%4,25 oldu."), ["-%4,25"])

    def test_isaret_kaybi_yakalanir(self):
        # "-%4,25" (düşüş) → "%4,25" (artış) sessizce geçmemeli
        a = dosya("Değişim -%4,25 oldu.")
        b = dosya("Değişim %4,25 oldu.")
        try:
            kod, _, _ = calistir(a, b)
        finally:
            os.unlink(a); os.unlink(b)
        self.assertEqual(kod, 1)

    def test_tarih(self):
        self.assertEqual(sayilar("Son gün 13.10.2026 idi."), ["13.10.2026"])

    def test_aralik_eksi_isareti_sayilmaz(self):
        self.assertEqual(sayilar("10-20 arası"), ["10", "20"])


class CikisKodu(unittest.TestCase):
    def test_help_cikmaz_ve_sifir_doner(self):
        for bayrak in ("--help", "-h"):
            kod, cikti, _ = calistir(bayrak)
            self.assertEqual(kod, 0)
            self.assertIn("Kullanım", cikti)

    def test_bilinmeyen_secenek_temiz_hata(self):
        kod, _, hata = calistir("--foo")
        self.assertEqual(kod, 2)
        self.assertIn("bilinmeyen seçenek", hata)

    def test_olmayan_dosya_temiz_hata(self):
        kod, _, hata = calistir("/yok/boyle/dosya.txt")
        self.assertEqual(kod, 2)
        self.assertIn("dosya bulunamadı", hata)

    def test_argumansiz_kullanim_ve_iki(self):
        kod, cikti, _ = calistir()
        self.assertEqual(kod, 2)
        self.assertIn("Kullanım", cikti)

    def test_sayi_korunduysa_sifir(self):
        a = dosya("Aylık %4,25 faiz ve 1.250,00 TL ödeme var. Son gün 13.10.2026.")
        b = dosya("Ödemeniz 1.250,00 TL; aylık faiz %4,25. Son gün 13.10.2026.")
        try:
            kod, cikti, _ = calistir(a, b)
        finally:
            os.unlink(a); os.unlink(b)
        self.assertEqual(kod, 0)
        self.assertIn("Sayı koruma: tamam", cikti)

    def test_sayi_kaybolursa_bir(self):
        a = dosya("Aylık %4,25 faiz ve 1.250,00 TL ödeme var.")
        b = dosya("Aylık faiz ve 1.250 TL ödeme var.")
        try:
            kod, cikti, _ = calistir(a, b)
        finally:
            os.unlink(a); os.unlink(b)
        self.assertEqual(kod, 1)
        self.assertIn("SORUN", cikti)
        self.assertIn("kayboldu/değişti", cikti)

    def test_para_birimi_degisimi_yakalanir(self):
        a = dosya("Tutar 100 TL.")
        b = dosya("Tutar 100 USD.")
        try:
            kod, _, _ = calistir(a, b)
        finally:
            os.unlink(a); os.unlink(b)
        self.assertEqual(kod, 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
