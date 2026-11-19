#!/usr/bin/env python3
"""seo_denetim.py birim testleri (yalnız standart kütüphane): python3 scripts/test_seo_denetim.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import seo_denetim as s  # noqa: E402


def bul(metin, **kw):
    return s.denetle(metin, **kw)[0]


def kodlar(metin, **kw):
    return [b["kod"] for b in bul(metin, **kw)]


def olcum(metin, **kw):
    return s.denetle(metin, **kw)[1]


def calistir(*arg):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = s.main(list(arg))
    return kod, cikti.getvalue(), hata.getvalue()


def dosya(icerik):
    f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
    f.write(icerik)
    f.close()
    return f.name


class S19S20(unittest.TestCase):
    def test_s19_meta_govdede_olmayan_sayi(self):
        b = s.denetle("# Bot\n\nBot 2.899 TL.", aciklama="Bot 1.999 TL'den başlıyor, hızlı kargo ile gelir.")[0]
        self.assertTrue(any(x["kod"] == "S19" and "1.999" in x["mesaj"] for x in b))

    def test_s19_temiz(self):
        b = s.denetle("# Bot\n\nBot 2.899 TL.", aciklama="Bot 2.899 TL, kış için su geçirmez deri üst yüzey.")[0]
        self.assertFalse(any(x["kod"] == "S19" for x in b))

    def test_s20_ayni_cumle_iki_kez(self):
        c = "Pasaport başvurusu il ve ilçe müdürlüklerinden randevu alınarak yapılır."
        b = s.denetle(f"# P\n\n{c}\n\n## Nereden?\n\n{c}")[0]
        self.assertTrue(any(x["kod"] == "S20" for x in b))

    def test_s20_kisa_cumle_sayilmaz(self):
        b = s.denetle("# P\n\nEvet doğru.\n\nEvet doğru.")[0]
        self.assertFalse(any(x["kod"] == "S20" for x in b))


class KisaSozcukUzunEk(unittest.TestCase):
    def test_uzun_iyelik_zinciri(self):
        import seo_denetim as s
        for w in ("botlarımız", "botlarınız", "evlerimiz", "evlerimizde"):
            self.assertTrue(s._eslesir(s.katla(w), s.katla(w[:3] if w.startswith("bot") else "ev")), w)
        for w in ("botanik", "evrim", "evren", "evet"):
            self.assertFalse(s._eslesir(s.katla(w), s.katla("bot" if w.startswith("bot") else "ev")), w)


class EkEsleme(unittest.TestCase):
    def test_kisa_sozcuk_bilinen_ek_baslangiclari(self):
        self.assertTrue(s._eslesir("evlerde", "ev"))
        self.assertTrue(s._eslesir("evde", "ev"))
        self.assertFalse(s._eslesir("evrim", "ev"))

    def test_uzun_sozcuk_yumusama_kitap_kitabi(self):
        self.assertTrue(s._eslesir("kitabi", "kitap"))
        self.assertTrue(s._eslesir("kitaplar", "kitap"))

    def test_ek_alti_harfi_asmaz(self):
        self.assertTrue(s._eslesir("kitapabc", "kitap"))
        self.assertFalse(s._eslesir("kitapabcdefg", "kitap"))

    def test_kisa_sozcuk_ek_bicimlerine_bolunur(self):
        self.assertTrue(s._eslesir("botlar", "bot"))
        self.assertTrue(s._eslesir("botu", "bot"))
        self.assertTrue(s._eslesir("botlarda", "bot"))
        self.assertTrue(s._eslesir("botlarim", "bot"))
        self.assertFalse(s._eslesir("botanik", "bot"))
        self.assertFalse(s._eslesir("evrim", "ev"))

    def test_buyuk_harf_katlama_istanbul(self):
        self.assertEqual(s.katla("ISTANBUL"), "istanbul")
        self.assertEqual(s.katla("İstanbul"), "istanbul")
        self.assertTrue(s._eslesir("istanbul", "İstanbul"))

    def test_cok_sozcuklu_sorgu_ara_sozcuk_siniri(self):
        self.assertEqual(s._zincir_say("kahve bir iki uc falina".split(), ["kahve", "fali"]), 1)
        self.assertEqual(s._zincir_say("kahve bir iki uc dort falina".split(), ["kahve", "fali"]), 0)

    def test_s02_ek_bicimi_ilk_paragrafta_sayilir(self):
        metin = "# Ev\n\nEvlerde yaşıyoruz."
        self.assertNotIn("S02", kodlar(metin, anahtar="ev"))

    def test_cok_sozcuklu_sorgu_ek_bicimi(self):
        self.assertEqual(s._zincir_say(s._tokenla(s.katla("kahve falına bakılır")),
                                       s._tokenla(s.katla("kahve falı"))), 1)


class S01S02(unittest.TestCase):
    def test_s01_h1de_yok(self):
        self.assertIn("S01", kodlar("# Başka Konu\n\nkahve burada.", anahtar="çay"))

    def test_s01_h1de_var(self):
        self.assertNotIn("S01", kodlar("# Çay Rehberi\n\nçay burada.", anahtar="çay"))

    def test_s01_baslik_yedegi(self):
        self.assertNotIn("S01", kodlar("metin", anahtar="çay", baslik="Çay Rehberi"))
        self.assertIn("S01", kodlar("metin", anahtar="çay", baslik="Kahve Rehberi"))

    def test_s02_ilk_yuzde_yok(self):
        metin = "# Kahve\n\n" + "dolgu " * 110 + "kahve"
        self.assertIn("S02", kodlar(metin, anahtar="kahve"))

    def test_s02_ilk_paragrafta_var(self):
        self.assertNotIn("S02", kodlar("# Kahve\n\nkahve ilk paragrafta.", anahtar="kahve"))

    def test_kod_bloku_ve_satir_ici_kod_taranmaz(self):
        metin = "# Kahve\n\n```\nkahve falı\n```\n\n`kahve` yazısı."
        self.assertIn("S02", kodlar(metin, anahtar="kahve"))

    def test_cift_ters_tikli_satir_ici_kod_taranmaz(self):
        metin = "# Kahve\n\n``kahve`` yazısı."
        self.assertIn("S02", kodlar(metin, anahtar="kahve"))
        self.assertEqual(olcum(metin, anahtar="kahve")["sozcuk_sayisi"], 1)

    def test_kisa_sozcukte_botanik_sorgu_sayilmaz(self):
        metin = "# Bot Rehberi\n\nbotanik."
        self.assertIn("S02", kodlar(metin, anahtar="bot"))
        self.assertEqual(olcum(metin, anahtar="bot")["yogunluk"], 0.0)

    def test_sayi_token_tek_parca_ve_birebir(self):
        self.assertEqual(s._tokenla("4,5 faiz ve 2.899 tl"), ["4,5", "faiz", "ve", "2.899", "tl"])
        self.assertEqual(s._zincir_say(s._tokenla("4,5 faiz"), s._tokenla("4,5 faiz")), 1)
        self.assertEqual(s._zincir_say(s._tokenla("5,5 faiz"), s._tokenla("4,5 faiz")), 0)
        metin = "# 4,5 faiz\n\n5,5 faiz uygulanır."
        self.assertIn("S02", kodlar(metin, anahtar="4,5 faiz"))
        self.assertEqual(olcum(metin, anahtar="4,5 faiz")["yogunluk"], 0.0)

    def test_yalniz_sayidan_olusan_sorgu_kurallari_calistirir(self):
        self.assertIn("S05", kodlar("# 4,5\n\n4,5 faiz.", anahtar="4,5"))


class S03S04S05(unittest.TestCase):
    def test_s03_ayni_cumlede_iki_kez(self):
        b = bul("# Konu\n\nKahve kahve demledim.", anahtar="kahve")
        self.assertTrue(any(x["kod"] == "S03" and x["duzey"] == "hata" for x in b))

    def test_s03_titleda_tekrar(self):
        self.assertIn("S03", kodlar("# Kahve\n\nBir yazı.", anahtar="kahve",
                                    baslik="Kahve Kahve Rehberi"))

    def test_s03_temiz(self):
        self.assertNotIn("S03", kodlar("# Kahve\n\nKahve demledim. Çay içtim.", anahtar="kahve"))

    def test_s03_title_tekrari_sorgusuz(self):
        self.assertIn("S03", kodlar("metin", baslik="Kahve Kahve Rehberi"))

    def test_kisaltma_noktasi_cumleyi_bolmez(self):
        metin = "# K\n\nKahve yazarı Dr. Aylin kahve tarifini paylaştı."
        self.assertIn("S03", kodlar(metin, anahtar="kahve"))
        self.assertEqual(len(s._cumleler("2.899 TL harcandı. Yeni cümle.")), 2)

    def test_s04_yogunluk_asiri(self):
        cumle = "Sabah kahve içtim ve uzun uzun yürüyüş yaptım bugün parkta. "
        metin = "# Konu\n\n" + cumle * 25 + "dolgu " * 10
        b = bul(metin, anahtar="kahve")
        self.assertTrue(any(x["kod"] == "S04" and x["duzey"] == "uyari" for x in b))

    def test_s04_kisa_metinde_bilgi(self):
        metin = "# Konu\n\nkahve bir iki. kahve üç dört. kahve beş altı. kahve yedi sekiz."
        b = bul(metin, anahtar="kahve")
        self.assertTrue(any(x["kod"] == "S04" and x["duzey"] == "bilgi" for x in b))
        self.assertFalse(any(x["kod"] == "S04" and x["duzey"] == "uyari" for x in b))

    def test_s12_ascii_slug_ascii_disi_demez(self):
        b = bul("metin", slug="Kislik_Bot")
        self.assertFalse(any("ASCII dışı" in x["mesaj"] for x in b if x["kod"] == "S12"))
        b = bul("metin", slug="kışlık-bot")
        self.assertTrue(any("ASCII dışı" in x["mesaj"] for x in b if x["kod"] == "S12"))

    def test_s04_yogunluk_normal(self):
        metin = "# Konu\n\nkahve " + "dolgu " * 99
        self.assertNotIn("S04", kodlar(metin, anahtar="kahve"))

    def test_s05_yogunluk_bilgi_ve_olcum(self):
        b = bul("# Konu\n\nkahve bir iki.", anahtar="kahve")
        self.assertTrue(any(x["kod"] == "S05" and x["duzey"] == "bilgi" for x in b))
        self.assertAlmostEqual(olcum("# Konu\n\nkahve bir iki.", anahtar="kahve")["yogunluk"],
                               33.33, places=1)

    def test_s05_anahtar_yoksa_yok(self):
        self.assertNotIn("S05", kodlar("# Konu\n\nkahve bir iki."))


class S06S07(unittest.TestCase):
    def test_s06_kisa_title(self):
        self.assertIn("S06", kodlar("metin", baslik="K" * 24))

    def test_s06_uzun_title(self):
        self.assertIn("S06", kodlar("metin", baslik="K" * 61))

    def test_s06_normal(self):
        self.assertNotIn("S06", kodlar("metin", baslik="Kahve Demleme Rehberi ve Notlar"))

    def test_s07_kisa_meta(self):
        self.assertIn("S07", kodlar("metin", aciklama="a" * 60))

    def test_s07_uzun_meta(self):
        self.assertIn("S07", kodlar("metin", aciklama="a" * 170))

    def test_s07_normal(self):
        self.assertNotIn("S07", kodlar("metin", aciklama="a" * 100))


class Yapi(unittest.TestCase):
    def test_s08_h1_yok(self):
        self.assertIn("S08", kodlar("## Alt başlık\n\nmetin"))

    def test_s08_cift_h1(self):
        self.assertIn("S08", kodlar("# Bir\n\n# İki\n\nmetin"))

    def test_s08_tek_h1(self):
        self.assertNotIn("S08", kodlar("# Bir\n\nmetin"))

    def test_s09_seviye_atlama(self):
        self.assertIn("S09", kodlar("# A\n\n## B\n\n#### C\n\nmetin"))

    def test_s09_ardisik_seviye(self):
        self.assertNotIn("S09", kodlar("# A\n\n## B\n\n### C\n\nmetin"))

    def test_s10_uzun_ve_arasiz(self):
        self.assertIn("S10", kodlar("# Başlık\n\n" + "dolgu " * 310))

    def test_s10_arabasligi_var(self):
        self.assertNotIn("S10", kodlar("# Başlık\n\n## Ara\n\n" + "dolgu " * 310))

    def test_s14_kisa_yanit(self):
        metin = "# B\n\n## Kahve nasıl demlenir?\n\nKısa bir yanıt burada duruyor işte."
        self.assertIn("S14", kodlar(metin))

    def test_s14_uygun_uzunluk(self):
        metin = "# B\n\n## Kahve nasıl demlenir?\n\n" + "dolgu " * 40
        self.assertNotIn("S14", kodlar(metin))


class GorselSlugCapa(unittest.TestCase):
    def test_s11_alt_metin_yok(self):
        self.assertIn("S11", kodlar("# B\n\n![](x.png)"))

    def test_s11_jenerik_baslangic(self):
        self.assertIn("S11", kodlar("# B\n\n![Görsel: kahve](x.png)"))

    def test_s11_uzun_alt(self):
        self.assertIn("S11", kodlar("# B\n\n![" + "a" * 156 + "](x.png)"))

    def test_s11_uygun(self):
        self.assertNotIn("S11", kodlar("# B\n\n![Kahve demleme adımları](x.png)"))

    def test_s12_buyuk_harf_alt_cizgi_bosluk(self):
        k = kodlar("# Kahve\n\nmetin", slug="Kahve_Rehberi Test")
        self.assertIn("S12", k)

    def test_s12_ascii_disi_ve_oneri(self):
        b = bul("# Kahve\n\nmetin", slug="kahve-çay")
        self.assertTrue(any(x["kod"] == "S12" and "kahve-cay" in x["oneri"] for x in b))

    def test_s12_uzun_ve_ardisik_tire(self):
        self.assertIn("S12", kodlar("metin", slug="a" * 76))
        self.assertIn("S12", kodlar("metin", slug="kahve--cay"))

    def test_s12_temiz(self):
        self.assertNotIn("S12", kodlar("metin", slug="kahve-rehberi"))

    def test_s13_anlamsiz_capa(self):
        self.assertIn("S13", kodlar("# B\n\n[buraya tıklayın](https://x.org)"))

    def test_s13_anlamli_capa(self):
        self.assertNotIn("S13", kodlar("# B\n\n[kahve demleme rehberi](https://x.org)"))


class S15S16S17S18(unittest.TestCase):
    def test_s15_ortak_sozcuk_yok(self):
        self.assertIn("S15", kodlar("# Çay Notları\n\nmetin", baslik="Kahve Rehberi"))

    def test_s15_ortak_sozcuk_var(self):
        self.assertNotIn("S15", kodlar("# Kahve Notları\n\nmetin", baslik="Kahve Rehberi"))

    def test_s16_karaktersiz_yazim(self):
        self.assertIn("S16", kodlar("# B\n\nKışlık ürün ve kislik ürün aynı."))

    def test_s16_temiz(self):
        self.assertNotIn("S16", kodlar("# B\n\nKışlık ürün."))

    def test_s16_duzey_bilgi_ve_mesaj(self):
        b = [x for x in bul("# B\n\nKışlık ürün ve kislik ürün aynı.") if x["kod"] == "S16"]
        self.assertEqual(len(b), 1)
        self.assertEqual(b[0]["duzey"], "bilgi")
        self.assertIn("farklı anlamlı sözcük olabilir (ılık/ilik); elle bak", b[0]["mesaj"])

    def test_s16_gercek_anlamli_cift_bildirilmez(self):
        for cift in ("Ilık ve ilik farklı sözcüklerdir.", "Kır ve kir ayrı sözcükler.",
                     "Sınır ile sinir ayrı.", "Isı ve isi farklı.", "Kaşar ve kasar ayrı."):
            self.assertNotIn("S16", kodlar("# B\n\n" + cift))

    def test_s17_uzun_paragraf(self):
        self.assertIn("S17", kodlar("# B\n\n" + "dolgu " * 151))

    def test_s17_normal_paragraf(self):
        self.assertNotIn("S17", kodlar("# B\n\n" + "dolgu " * 100))

    def test_s18_kisa_metin(self):
        self.assertIn("S18", kodlar("# B\n\nkısa metin"))

    def test_s18_yeterli_metin(self):
        self.assertNotIn("S18", kodlar("# B\n\n## Ara\n\n" + "dolgu " * 300))


class SlugOner(unittest.TestCase):
    def test_transliterasyon(self):
        self.assertEqual(s.slug_oner("Kışlık Çay & Kahve Rehberi"), "kislik-cay-kahve-rehberi")

    def test_75_karakter_sozcuk_siniri(self):
        slug = s.slug_oner("kelime " * 20)
        self.assertLessEqual(len(slug), 75)
        self.assertFalse(slug.endswith("-"))

    def test_bos_baslik(self):
        self.assertEqual(s.slug_oner("  &  "), "")

    def test_slug_onerisi_h1den(self):
        self.assertEqual(olcum("# Kışlık Çay Rehberi\n\nmetin")["slug_onerisi"],
                         "kislik-cay-rehberi")

    def test_nfc_ayristirilmis_harf(self):
        baslik = "Kıs\u0327lık Rehberi"
        self.assertEqual(s.slug_oner(baslik), "kislik-rehberi")
        self.assertEqual(olcum("# " + baslik + "\n\nmetin")["slug_onerisi"], "kislik-rehberi")
        b = [x for x in bul("metin", slug="kıs\u0327lık-bot") if x["kod"] == "S12"]
        self.assertEqual(len(b), 1)
        self.assertIn("«kışlık-bot»", b[0]["mesaj"])


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

    def test_deger_yok(self):
        self.assertEqual(calistir("x.md", "--anahtar")[0], 2)

    def test_cikis_sifir_uyari_bilgi(self):
        d = dosya("# Kahve\n\nkahve kısa.")
        try:
            kod, cikti, _ = calistir(d, "--anahtar", "kahve")
        finally:
            os.unlink(d)
        self.assertEqual(kod, 0)
        self.assertIn(s.NOT, cikti)

    def test_cikis_bir_hata(self):
        d = dosya("# Konu\n\nKahve kahve.")
        try:
            kod, _, _ = calistir(d, "--anahtar", "kahve")
        finally:
            os.unlink(d)
        self.assertEqual(kod, 1)

    def test_json_bicimi(self):
        d = dosya("# Kahve\n\nkahve kısa.")
        try:
            kod, cikti, _ = calistir(d, "--anahtar", "kahve", "--json")
        finally:
            os.unlink(d)
        veri = json.loads(cikti)
        self.assertEqual(kod, 0)
        self.assertEqual(veri["anahtar"], "kahve")
        self.assertIn("bulgular", veri)
        self.assertIn("sozcuk_sayisi", veri["olcumler"])
        self.assertIn("baslik_agaci", veri["olcumler"])
        self.assertIn("not", veri)

    def test_onceki_karsilastirma_ve_yeni_sorun(self):
        eski = dosya("# Kahve\n\nkahve güzel.")
        yeni = dosya("# Kahve\n\nkahve kahve güzel.")
        try:
            kod, cikti, _ = calistir(yeni, "--anahtar", "kahve", "--onceki", eski)
        finally:
            os.unlink(eski)
            os.unlink(yeni)
        self.assertEqual(kod, 1)
        self.assertIn("önce → sonra", cikti)
        self.assertIn("↑ YENİ SORUN", cikti)
        self.assertIn("TOPLAM", cikti)


if __name__ == "__main__":
    unittest.main(verbosity=1)