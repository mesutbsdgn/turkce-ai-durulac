#!/usr/bin/env python3
"""tarama.py birim testleri (yalnız standart kütüphane): python3 scripts/test_tarama.py"""
import contextlib
import io
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tarama as t  # noqa: E402

KURALLAR = t.derle()


def bul(metin):
    return t.tara(metin, KURALLAR)


def adlar(metin):
    return {b[3] for b in bul(metin)}


def calistir(*arg):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = t.main(list(arg))
    return kod, cikti.getvalue(), hata.getvalue()


def dosya(icerik):
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write(icerik)
    f.close()
    return f.name


class Yoksayma(unittest.TestCase):
    def test_kod_citi_taranmaz(self):
        self.assertEqual(bul("```\nBu — kod ve/veya komut tarafından\n```\n"), [])

    def test_satir_ici_kod_url_ve_baglanti_hedefi_taranmaz(self):
        m = "Bkz. `a — b` ve https://ornek.org/ve/veya ve [bağlantı](https://x.org/koşu) tamam."
        self.assertEqual(bul(m), [])

    def test_tablo_ayrac_satiri_taranmaz_hucre_taranir(self):
        m = "| A | B |\n|---|---|\n| bu şekilde | x |\n"
        self.assertIn("şekilde", adlar(m))

    def test_bos_metin(self):
        self.assertEqual(bul(""), [])


class Kaliplar(unittest.TestCase):
    def test_uzun_cizgi(self):
        self.assertIn("uzun çizgi (—)", adlar("Sistem — beklendiği gibi — çöktü."))

    def test_ve_veya(self):
        self.assertIn("ve/veya", adlar("Dosyayı silin ve/veya taşıyın."))

    def test_tarafindan_ve_mekte(self):
        a = adlar("Rapor komisyon tarafından incelenmektedir.")
        self.assertIn("tarafından", a)
        self.assertIn("-mekte/-makta", a)

    def test_ceviri_kokusu_atif_busulsal_kosu_tolere(self):
        a = adlar("Atıf yapılan sayfada buluşsal yöntemle koşturun; bunu tolere eder.")
        self.assertTrue({"atıf yapılan/atıf yapmak", "buluşsal (heuristic)", "koşu/koşturmak (run)", "tolere etmek"} <= a)

    def test_worker_cakismasi(self):
        self.assertIn("çalışan (worker)", adlar("Çalışan notu yazar."))

    def test_iso_tarih_ve_sayi_bicimi(self):
        a = adlar("Rapor 2026-10-08 tarihli; tutar 1,000,000 TL, artış %5.5.")
        self.assertTrue({"ISO tarih düzyazıda", "binlik ayırıcı virgül", "ondalık nokta (yüzde)"} <= a)

    def test_turkce_sayi_bicimi_temiz(self):
        self.assertEqual(adlar("Tutar 1.000.000 TL, artış %5,5, tarih 8 Ekim 2026."), set())

    def test_sozluk_eslemesi_plaza_fiil(self):
        self.assertTrue(any(a.startswith("sözlük: ") for a in adlar("Dalı merge edip deploy ettik.")))

    def test_sozlukte_ingilizce_terim_varsayilan_kapali(self):
        self.assertFalse(any("sözlük: server" in a for a in adlar("The server restart.")))
        acik = t.tara("Server yeniden başladı.", t.derle(ingilizce_terim=True))
        self.assertTrue(any(b[3] == "sözlük: server" for b in acik))

    def test_uzun_cumle(self):
        cumle = " ".join(["kelime"] * 40) + "."
        self.assertTrue(any("uzun cümle" in a for a in adlar(cumle)))

    def test_ayni_baglacla_paragraf_acma(self):
        m = "Ayrıca bir.\n\nAyrıca iki.\n\nAyrıca üç.\n"
        self.assertIn("aynı bağlaçla paragraf açma", adlar(m))

    def test_sahis_karisimi_temiz_sozcuk_yanlis_alarm_vermez(self):
        self.assertNotIn("şahıs karışımı olabilir", adlar("Yazar temiz kod yazdı. Yazarın notu temiz."))

    def test_sahis_karisimi_gercek(self):
        self.assertIn("şahıs karışımı olabilir", adlar("Koşularımızda hızlıydı. Yazarın kendi notu."))


class Komut(unittest.TestCase):
    def test_help(self):
        kod, cikti, _ = calistir("--help")
        self.assertEqual(kod, 0)
        self.assertIn("Kullanım", cikti)

    def test_arguman_yok_ve_bilinmeyen_secenek(self):
        self.assertEqual(calistir()[0], 2)
        kod, _, hata = calistir("--foo")
        self.assertEqual(kod, 2)
        self.assertIn("bilinmeyen seçenek", hata)

    def test_olmayan_dosya(self):
        kod, _, hata = calistir("/yok/dosya.md")
        self.assertEqual(kod, 2)
        self.assertIn("dosya bulunamadı", hata)

    def test_korumali_tur_devre_disi(self):
        d = dosya("Gereğini arz ederim — tarafından.")
        try:
            for tur in ("resmi", "Resmî", "akademik", "hukuk"):
                kod, cikti, _ = calistir(d, "--tur", tur)
                self.assertEqual(kod, 0)
                self.assertIn("devre dışı", cikti)
                self.assertNotIn("Toplam", cikti)
        finally:
            os.unlink(d)

    def test_onceki_karsilastirma(self):
        eski = dosya("Sistem — çöktü; bu şekilde ve/veya kapandı.")
        yeni = dosya("Sistem çöktü ve kapandı.")
        try:
            kod, cikti, _ = calistir(yeni, "--onceki", eski)
        finally:
            os.unlink(eski); os.unlink(yeni)
        self.assertEqual(kod, 0)
        self.assertIn("önce → sonra", cikti)
        self.assertIn("TOPLAM", cikti)
        self.assertIn("↓", cikti)

    def test_ozet_modu_satir_basmaz(self):
        d = dosya("Bu şekilde.")
        try:
            _, cikti, _ = calistir(d, "--ozet")
        finally:
            os.unlink(d)
        self.assertNotIn("[kalıp", cikti)
        self.assertIn("Toplam 1 bulgu", cikti)


if __name__ == "__main__":
    unittest.main(verbosity=1)
