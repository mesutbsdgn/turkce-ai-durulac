#!/usr/bin/env python3
"""benzerlik.py testleri (uydurma belgeyle, model yok): python3 -B test_benzerlik.py"""
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import benzerlik as bz  # noqa: E402
import test_tez_onar as tt  # noqa: E402
import tez_onar as to  # noqa: E402

ESKI = "Uydurma kurum siber olaylara karşı yeni bir koordinasyon modeli geliştirmiş ve bunu 2025 yılında uygulamaya koymuştur (Örnek, 2020)."
YENI = "Bu kurum 2025 yılında, siber olaylara karşı geliştirdiği yeni koordinasyon yapısını yürürlüğe koymuştur (Örnek, 2020)."
ESL = "siber olaylara karşı yeni bir koordinasyon modeli geliştirmiş ve bunu 2025".split()


class DogrulamaTesti(unittest.TestCase):
    def test_gecerli(self):
        self.assertIsNone(bz.dogrula_cumle(ESKI, YENI, ESL))

    def test_sayi_degisirse_reddedilir(self):
        self.assertEqual(bz.dogrula_cumle(ESKI, YENI.replace("2025", "2026"), ESL), "sayi")

    def test_atif_degisirse_reddedilir(self):
        self.assertEqual(bz.dogrula_cumle(ESKI, YENI.replace("Örnek", "Yılmaz"), ESL), "atif")

    def test_yeni_ozel_ad_reddedilir(self):
        self.assertEqual(bz.dogrula_cumle(ESKI, YENI.replace("Bu kurum", "Bu kurum Interpol"), ESL), "ozel_ad")

    def test_eslesme_kalirsa_reddedilir(self):
        yeni = "Kurum, siber olaylara karşı yeni bir koordinasyon modeli geliştirdi; 2025 yılında yürürlüğe koymuştur (Örnek, 2020)."
        self.assertEqual(bz.dogrula_cumle(ESKI, yeni, ESL), "eslesme_kaldi")

    def test_uzunluk_ve_noktalama(self):
        self.assertEqual(bz.dogrula_cumle(ESKI, "Kısa 2025 (Örnek, 2020).", ESL), "uzunluk")
        self.assertEqual(bz.dogrula_cumle(ESKI, YENI.rstrip(".") + "!", ESL), "noktalama")

    def test_temizle(self):
        self.assertEqual(bz.temizle('Yeni cümle: "Merhaba dünya."\nAçıklama'), "Merhaba dünya.")


class EkKuralTesti(unittest.TestCase):
    def test_terim_birligi(self):
        self.assertEqual(bz.dogrula_cumle("Bu kanun siber uzayda geçerlidir (Örnek, 2020).", "Bu yasa siber uzayda uygulanır (Örnek, 2020).", [], 6), "terim_birligi")

    def test_birinci_sahis_ve_tablo(self):
        e = "Veriler analiz edilmiş ve sonuçlar sunulmuştur (Örnek, 2020)."
        self.assertEqual(bz.dogrula_cumle(e, "Verileri inceledik ve sonuçları sunduk (Örnek, 2020).", [], 6), "birinci_sahis")
        self.assertEqual(bz.dogrula_cumle("Sonuçlar Çizelge 3 içinde sunulmuştur (Örnek, 2020).", "Bulgular Tablo 3 içinde verilmiştir (Örnek, 2020).", [], 6), "tablo_cizelge")


class SozcukFarkiTesti(unittest.TestCase):
    def _uygula(self, eski, yeni):
        p = bz.sozcuk_farki(eski, yeni)
        out, k = "", 0
        for b, e, y in sorted(p):
            out += eski[k:b] + y
            k = e
        return out + eski[k:], p

    def test_yalniz_degisen_sozcukler(self):
        eski = "Bu durum kritik altyapıları siber saldırılara karşı daha savunmasız hale gelmesine neden olmaktadır."
        yeni = "Bu durum kritik altyapıları siber saldırılara karşı daha savunmasız bırakmaktadır."
        kur, p = self._uygula(eski, yeni)
        self.assertEqual(kur, yeni)
        self.assertEqual(len(p), 1)
        self.assertNotIn("siber", " ".join(x[2] for x in p))

    def test_ekleme_ve_silme(self):
        for eski, yeni in (("Bu saldırılar e-postalarla yapılır.", "Bu tür saldırılar e-postalarla yapılır."),
                           ("Bu tür saldırılar e-postalarla yapılır.", "Bu saldırılar e-postalarla yapılır."),
                           ("Alfa beta gama delta.", "Delta gama beta alfa.")):
            self.assertEqual(self._uygula(eski, yeni)[0], yeni)


class SurumDenetimTesti(unittest.TestCase):
    def test_degisen_ve_ihlal(self):
        eski = ["Başlık", "Veriler 2020 yılında toplandı (Örnek, 2020). Kanun siber uzayı kapsar.", "Sabit paragraf."]
        yeni = ["Başlık", "Veriler 2021 yılında toplandı (Örnek, 2020). Yasa siber uzayı kapsar.", "Sabit paragraf."]
        s = bz.surum_denetle(eski, yeni)
        self.assertEqual(s["degisen_paragraf"], 1)
        self.assertEqual(sorted(s["degisenler"][0]["ihlal"]), ["sayi", "terim_birligi"])
        md = bz.surum_rapor(s)
        self.assertNotIn("Veriler", md)

    def test_temiz_degisiklik(self):
        s = bz.surum_denetle(["Bu durum savunmasız hale gelmesine neden olur (Kaya, 2019)."], ["Bu durum savunmasız bırakır (Kaya, 2019)."])
        self.assertEqual(s["degisenler"][0]["ihlal"], [])


class MetinDenetimTesti(unittest.TestCase):
    def _p(self, m, numpr=False):
        return {"metin": m, "numpr": numpr, "stil": ""}

    def test_ekleme_baslangic_ve_uzunluk(self):
        uzun = " ".join(["kelime"] * 45) + "."
        niyet = [{"id": "K9", "paragraflar": ["Bu bir deneme paragrafıdır ve yeterince uzundur. İkinci cümle de burada yer alır. Uzun " + uzun]}]
        eski = [self._p("Başlık"), self._p("Sabit.")]
        yeni = [self._p("Başlık"), self._p("a/ Bu bir deneme paragrafıdır ve yeterince uzundur. İkinci cümle de burada yer alır. " + "Uzun " + uzun), self._p("Sabit.")]
        s = bz.metin_denetimi(eski, yeni, niyet)
        e = s["eklenenler"][0]
        self.assertEqual(e["metin_kodu"], "K9.1")
        self.assertEqual(e["baslangic"], "supheli")
        self.assertEqual(e["uzun_cumle_sayisi"], 1)
        self.assertEqual(e["ilk3"], "a/ ")
        self.assertEqual(len(s["belge_geneli_supheli_baslangic"]), 1)

    def test_temiz_ekleme(self):
        niyet = [{"id": "K9", "paragraflar": ["Temiz bir paragraf burada yer alır."]}]
        s = bz.metin_denetimi([self._p("A")], [self._p("A"), self._p("Temiz bir paragraf burada yer alır.")], niyet)
        self.assertEqual(s["eklenenler"][0]["baslangic"], "normal")
        self.assertEqual(s["bulunamayan_metin"], [])
        self.assertFalse(s["eklenenler"][0]["kullanici_duzenledi"])


class MetinGuncelleTesti(unittest.TestCase):
    ESKI = "Uzun bir cümle burada yer alır ve bir türlü bitmez, ikinci kısım da buna eklenir (Örnek, 2020: 5)."
    YENI = "Uzun bir cümle burada yer alır. İkinci kısım da buna eklenir (Örnek, 2020: 5)."

    def test_izli_guncelleme_ve_geri_alma(self):
        belge = tt.KOK_ETIKET + tt.par(f'<w:r><w:t xml:space="preserve">{self.ESKI}</w:t></w:r>') + tt.SON
        g = bz.MetinGuncelle([{"id": "K1", "paragraflar": [self.ESKI]}], [{"id": "K1", "paragraflar": [self.YENI]}])
        yeni, _, sayac, _ = to.belge_onar(belge, ek_oneri=g)
        self.assertGreaterEqual(sayac.get("YENIDEN_KUR", 0), 1)
        self.assertEqual(g.durum["K1.1"]["durum"], "uygulandi")
        self.assertEqual(to._metin(to.hepsini_kabul(yeni)), [self.YENI])
        self.assertEqual(to._metin(to.hepsini_reddet(yeni)), [self.ESKI])
        self.assertEqual(to.dogrula(belge, yeni), [])

    def test_sozcuk_ortasindan_kesilmez(self):
        eski = "Eylemler girişilen ve sonra bitti."
        yeni = "Eylemler gerçekleştirilir ve sonra bitti."
        belge = tt.KOK_ETIKET + tt.par(f'<w:r><w:t xml:space="preserve">{eski}</w:t></w:r>') + tt.SON
        g = bz.MetinGuncelle([{"id": "K1", "paragraflar": [eski]}], [{"id": "K1", "paragraflar": [yeni]}])
        xml, _, _, _ = to.belge_onar(belge, ek_oneri=g)
        self.assertIn("<w:delText xml:space=\"preserve\">girişilen</w:delText>", xml)
        self.assertIn("<w:t xml:space=\"preserve\">gerçekleştirilir</w:t>", xml)

    def test_atif_degisirse_yapilmaz(self):
        belge = tt.KOK_ETIKET + tt.par(f'<w:r><w:t xml:space="preserve">{self.ESKI}</w:t></w:r>') + tt.SON
        g = bz.MetinGuncelle([{"id": "K1", "paragraflar": [self.ESKI]}], [{"id": "K1", "paragraflar": [self.YENI.replace("2020", "2021")]}])
        yeni, _, sayac, _ = to.belge_onar(belge, ek_oneri=g)
        self.assertIsNone(sayac.get("YENIDEN_KUR"))
        self.assertTrue(g.durum["K1.1"]["durum"].startswith("reddedildi"))


class SinirTesti(unittest.TestCase):
    def test_et_al_cumleyi_bolmez(self):
        m = "Girdi cümle. Smith et al. (2019) bunu gösterdi ve başka bir şey ekledi. Son cümle."
        bas = m.index("bunu")
        b, s = bz.cumle_siniri(m, bas, bas + 4)
        self.assertEqual(m[b:s], "Smith et al. (2019) bunu gösterdi ve başka bir şey ekledi.")

    def test_yarim_cumle_atlanir(self):
        self.assertIsNone(bz.cumle_siniri("küçük harfle başlayan parça devam eder", 5, 10))


class UcUcaTesti(unittest.TestCase):
    def _belge(self, metin):
        return tt.KOK_ETIKET + tt.par(f"<w:r><w:t xml:space=\"preserve\">{metin}</w:t></w:r>") + "<w:p><w:r><w:t>Başka paragraf.</w:t></w:r></w:p>" + tt.SON

    def test_izli_degisiklik_ve_geri_alinabilirlik(self):
        metin = "Giriş cümlesi burada. " + ESKI + " Kapanış cümlesi."
        belge = self._belge(metin)
        hedef = [{"no": 7, "yuzde": 80, "alan": "ornek.org", "bolum": 1, "kelimeler": bz.sozcukler(" ".join(ESL)), "kelimeler_ham": ESL}]
        kanca = bz.Kanca(hedef, lambda c: YENI)
        yeni, gunluk, sayac, atlanan = to.belge_onar(belge, ek_oneri=kanca)
        self.assertGreaterEqual(sayac.get("YENIDEN_KUR"), 1)
        self.assertEqual(kanca.durum[7]["durum"], "uygulandi")
        self.assertIn("w:ins", yeni)
        self.assertEqual(to.dogrula(belge, yeni), [])
        kabul = "".join(to._metin(to.hepsini_kabul(yeni)))
        self.assertIn(YENI, kabul)
        self.assertNotIn("koordinasyon modeli", kabul)
        self.assertEqual(to._metin(to.hepsini_reddet(yeni)), to._metin(belge))

    def test_gecersiz_model_ciktisi_belgeye_yazilmaz(self):
        belge = self._belge("Giriş cümlesi burada. " + ESKI)
        hedef = [{"no": 1, "yuzde": 80, "alan": "x", "bolum": 1, "kelimeler": bz.sozcukler(" ".join(ESL)), "kelimeler_ham": ESL}]
        kanca = bz.Kanca(hedef, lambda c: c.replace("2025", "2030"))
        yeni, _, sayac, _ = to.belge_onar(belge, ek_oneri=kanca)
        self.assertIsNone(sayac.get("YENIDEN_KUR"))
        self.assertEqual(yeni, belge)
        self.assertEqual(kanca.durum[1]["durum"], "reddedildi:sayi")

    def test_geri_bildirimle_ikinci_denemede_gecer(self):
        belge = self._belge("Giriş cümlesi burada. " + ESKI)
        hedef = [{"no": 2, "yuzde": 80, "alan": "x", "bolum": 1, "kelimeler": bz.sozcukler(" ".join(ESL)), "kelimeler_ham": ESL}]
        gelen = []

        def yaz(cumle, ek="", sicaklik=0.3):
            gelen.append(ek)
            if not ek:
                return "Kurum, siber olaylara karşı yeni bir koordinasyon modeli geliştirdi; 2025 yılında yürürlüğe koymuştur (Örnek, 2020)."
            return YENI
        kanca = bz.Kanca(hedef, yaz)
        yeni, _, sayac, _ = to.belge_onar(belge, ek_oneri=kanca)
        self.assertGreaterEqual(sayac.get("YENIDEN_KUR"), 1)
        self.assertEqual(kanca.durum[2]["deneme"], 2)
        self.assertIn("KULLANMA", gelen[1])

    def test_kanca_sonra_kapanir(self):
        to.belge_onar(self._belge("Metin."), ek_oneri=lambda m: [])
        self.assertIsNone(to.EK_ONERI)

    def test_rapor_cumle_icermez(self):
        md, js = bz.rapor({3: {"durum": "uygulandi", "yuzde": 70, "alan": "a.org", "bolum": 2}})
        self.assertIn("| 3 | 70 | 2 | a.org | uygulandi |", md)
        self.assertEqual(js["sayim"], {"uygulandi": 1})


if __name__ == "__main__":
    unittest.main()
