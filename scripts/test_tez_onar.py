#!/usr/bin/env python3
"""tez_onar.py ve tez_ajan.py testleri: yalnız UYDURMA .docx ile. python3 -B test_tez_onar.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DURULAC = os.environ.get("TEZ_AJAN_DURULAC") or os.path.expanduser("~/.agents/skills/turkce-ai-durulac/scripts")
if os.path.isdir(DURULAC):
    sys.path.insert(0, DURULAC)

import tez_onar as to  # noqa: E402

KOK_ETIKET = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
    '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
    'xmlns:w14="http://schemas.microsoft.com/office/word/2010/wordml" '
    'xmlns:mc="http://schemas.openxmlformats.org/markup-compatibility/2006" mc:Ignorable="w14"><w:body>'
)
SON = '<w:sectPr><w:pgMar w:top="1701" w:right="1417" w:bottom="1701" w:left="2268" w:header="709" w:footer="709" w:gutter="0"/></w:sectPr></w:body></w:document>'


def kosu(t, kalin=False):
    rpr = '<w:rPr><w:b/></w:rPr>' if kalin else ""
    return f'<w:r w:rsidR="00A1">{rpr}<w:t xml:space="preserve">{t}</w:t></w:r>'


def par(*govde, stil=None):
    ppr = f'<w:pPr><w:pStyle w:val="{stil}"/></w:pPr>' if stil else ""
    return f"<w:p>{ppr}{''.join(govde)}</w:p>"


P_NOTA = par(kosu("Teröre karşı Facebook'"),
             '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteReference w:id="2"/></w:r>',
             kosu("da paylaşım yapıldı."))
P_IZLI = par(kosu("Önceki: "), '<w:ins w:id="7" w:author="x" w:date="2026-01-01T00:00:00Z">' + kosu("Kitap'da") + "</w:ins>")
P_TOC = par(kosu("IX.SONUÇ 45"), stil="T1")
P_KISALTMA = par(kosu("TSK'da ve ABD'de Paris'de görüldü."))
P_NUMARIK = par(kosu("Kaya &amp; Çetin (2019, s. 5) ve 2015&#39;de oldu."))
PARAGRAFLAR = [
    par(kosu("IX.SONUÇ"), stil="Balk1"),
    par(kosu("III. Siber "), kosu("Güvenlik ve Strateji", kalin=True), stil="Balk1"),
    par(kosu("Bu bulgu (Bıçakçı, 2014, s."), kosu("102) önemlidir. Kitap'"), kosu("da yer alır ve 1960'da başladı.")),
    P_NOTA, P_IZLI, P_TOC, P_KISALTMA, P_NUMARIK,
]
BELGE = KOK_ETIKET + "".join(PARAGRAFLAR) + SON


def docx_yaz(yol, belge_xml=BELGE):
    with zipfile.ZipFile(yol, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("[Content_Types].xml", "<Types/>")
        z.writestr("word/document.xml", belge_xml)
        z.writestr("word/styles.xml", "<w:styles xmlns:w='http://schemas.openxmlformats.org/wordprocessingml/2006/main'/>")


class OnarTesti(unittest.TestCase):
    def setUp(self):
        self.yeni_xml, self.gunluk, self.sayac, self.atlanan = to.belge_onar(BELGE, kenar=True)

    def test_kural_sayilari(self):
        self.assertEqual(self.sayac.get("ATIF_SAYFA"), 1)
        self.assertEqual(self.sayac.get("BENZESME"), 3)       # Kitap'da, 1960'da, Paris'de
        self.assertEqual(self.sayac.get("BASLIK_BOSLUK"), 1)  # IX.SONUÇ
        self.assertEqual(self.sayac.get("BASLIK_BUYUK"), 1)   # III. Siber ...
        self.assertEqual(self.sayac.get("reddedildi_degisken", 0), 0)

    def test_hepsini_kabul_edince_beklenen_metin(self):
        metinler = to._metin(to.hepsini_kabul(self.yeni_xml))
        self.assertEqual(metinler[0], "IX. SONUÇ")
        self.assertEqual(metinler[1], "III. SİBER GÜVENLİK VE STRATEJİ")
        self.assertEqual(metinler[2], "Bu bulgu (Bıçakçı, 2014: 102) önemlidir. Kitap'ta yer alır ve 1960'ta başladı.")
        self.assertEqual(metinler[6], "TSK'da ve ABD'de Paris'te görüldü.")

    def test_hepsini_reddedince_orijinal_metin(self):
        self.assertEqual(to._metin(to.hepsini_reddet(self.yeni_xml)), to._metin(to.hepsini_reddet(BELGE)))
        self.assertEqual(to.dogrula(BELGE, self.yeni_xml), [])

    def test_dokunulmayan_paragraflar_bayt_bayt_ayni(self):
        for p in (P_NOTA, P_IZLI, P_TOC, P_NUMARIK):
            self.assertIn(p, self.yeni_xml)
        self.assertGreaterEqual(self.atlanan.get("izli_degisiklik_var", 0), 1)

    def test_kisaltma_buyuk_harf_atlanir_ve_sayisal_varlik_opak(self):
        self.assertIn("TSK'", self.yeni_xml)
        self.assertNotIn("TSK'ta", to._metin(to.hepsini_kabul(self.yeni_xml))[6])

    def test_ad_alani_ve_izli_degisiklik_etiketleri(self):
        self.assertIn('w:author="Durulaç-Ajan"', self.yeni_xml)
        self.assertGreaterEqual(self.yeni_xml.count("<w:ins "), 6)
        self.assertIn("<w:delText", self.yeni_xml)

    def test_kok_etiketi_ve_isim_alanlari_degismez(self):
        self.assertTrue(self.yeni_xml.startswith(KOK_ETIKET))
        self.assertIn('mc:Ignorable="w14"', self.yeni_xml)

    def test_w_id_benzersiz(self):
        import re
        idler = re.findall(r'<w:(?:ins|del) w:id="(\d+)"', self.yeni_xml)
        self.assertEqual(len(idler), len(set(idler)))

    def test_kenar_izsiz_duzeltilir_ve_gunluge_yazilir(self):
        self.assertIn('w:top="1417"', self.yeni_xml)
        self.assertIn('w:bottom="1417"', self.yeni_xml)
        self.assertIn('w:left="2268"', self.yeni_xml)  # sol/iç dokunulmaz
        self.assertEqual(sum(1 for g in self.gunluk if g["kural"] == "KENAR"), 2)

    def test_gunluk_metin_icermez(self):
        for g in self.gunluk:
            self.assertTrue(set(g.keys()) <= {"kural", "paragraf", "eski", "yeni"})
            self.assertTrue(len(str(g.get("eski", ""))) <= 8)

    def test_dosya_yaz_ve_zip_butunlugu(self):
        with tempfile.TemporaryDirectory() as d:
            g, c = os.path.join(d, "g.docx"), os.path.join(d, "c.docx")
            docx_yaz(g)
            s = to.onar_dosya(g, c, kenar=True)
            self.assertEqual(s["hatalar"], [])
            with zipfile.ZipFile(c) as z:
                self.assertIsNone(z.testzip())
                self.assertEqual(z.namelist(), ["[Content_Types].xml", "word/document.xml", "word/styles.xml"])
                self.assertEqual(z.read("word/styles.xml"), zipfile.ZipFile(g).read("word/styles.xml"))
            # orijinal dokunulmadı
            self.assertEqual(zipfile.ZipFile(g).read("word/document.xml").decode(), BELGE)

    def test_teshis_yalniz_stil_adi_ve_sayi_icerir(self):
        t = to.SON_TESHIS
        self.assertEqual(t["baslik_duzeltilen"], 2)
        self.assertEqual(t["atif_adayi"], 2)
        self.assertEqual(t["atif_duzeltilen"], 1)
        self.assertEqual(t["baslik_atlanma_nedenleri"], {"stil_baslik1_degil:T1": 1})
        dump = json.dumps(t, ensure_ascii=False)
        for sizinti in ("Bıçakçı", "Kitap", "Siber", "Strateji", "SONUÇ"):
            self.assertNotIn(sizinti, dump)

    def test_kasten_bozma_degisken_kapisi(self):
        orijinal = to.degisiklik_gecerli
        to.degisiklik_gecerli = lambda *a: False
        try:
            yeni, gunluk, sayac, _ = to.belge_onar(BELGE)
        finally:
            to.degisiklik_gecerli = orijinal
        self.assertEqual(yeni, BELGE)
        self.assertGreaterEqual(sayac.get("reddedildi_degisken", 0), 5)

    def test_dogrulama_bozuk_cikti_yakalar(self):
        bozuk = self.yeni_xml.replace("önemlidir", "önemsizdir")
        self.assertTrue(to.dogrula(BELGE, bozuk))
        self.assertTrue(to.dogrula(BELGE, self.yeni_xml.replace("</w:body>", "")))


OPAK = '<w:r><w:rPr><w:vertAlign w:val="superscript"/></w:rPr><w:footnoteReference w:id="3"/></w:r>'
BELGE_BOLUNMUS = KOK_ETIKET + "".join([
    par(kosu("III. Siber "), OPAK, kosu("Güvenlik ve Strateji"), stil="Balk1"),
    par(kosu("Bu görüş (Stallings, 2008"), OPAK, kosu(", p. 249) ile uyumludur.")),
]) + SON


class BolunmusYapiTesti(unittest.TestCase):
    def setUp(self):
        self.yeni, self.gunluk, self.sayac, _ = to.belge_onar(BELGE_BOLUNMUS)

    def test_opak_calisma_ile_bolunmus_baslik_buyutulur(self):
        m = to._metin(to.hepsini_kabul(self.yeni))
        self.assertEqual(m[0], "III. SİBER GÜVENLİK VE STRATEJİ")
        self.assertEqual(self.sayac.get("BASLIK_BUYUK"), 2)

    def test_opak_calisma_sonrasi_atif_sayfasi_baglamdan_taninir(self):
        m = to._metin(to.hepsini_kabul(self.yeni))
        self.assertEqual(m[1], "Bu görüş (Stallings, 2008: 249) ile uyumludur.")
        self.assertEqual(self.sayac.get("ATIF_SAYFA"), 1)

    def test_bolunmus_yapida_da_hepsini_reddet_orijinal(self):
        self.assertEqual(to.dogrula(BELGE_BOLUNMUS, self.yeni), [])
        self.assertIn(OPAK, self.yeni)


SAYFA_IPUCU = '<w:r w:rsidR="00B2"><w:lastRenderedPageBreak/><w:t xml:space="preserve">'
BELGE_IPUCLU = KOK_ETIKET + "".join([
    "<w:p><w:pPr><w:pStyle w:val=\"Balk1\"/></w:pPr><w:bookmarkStart w:id=\"1\" w:name=\"_Toc1\"/>"
    + SAYFA_IPUCU + "III. Siber </w:t></w:r>" + kosu("Güvenlik ve Strateji") + "<w:bookmarkEnd w:id=\"1\"/></w:p>",
    "<w:p>" + kosu("Bu görüş (Stallings, 2008, p.") + SAYFA_IPUCU + " 249) ile uyumludur.</w:t></w:r></w:p>",
]) + SON


class SayfaIpucuTesti(unittest.TestCase):
    def test_lastRenderedPageBreak_olan_calismalar_islenir(self):
        yeni, _, sayac, _ = to.belge_onar(BELGE_IPUCLU)
        m = to._metin(to.hepsini_kabul(yeni))
        self.assertEqual(m[0], "III. SİBER GÜVENLİK VE STRATEJİ")
        self.assertEqual(m[1], "Bu görüş (Stallings, 2008: 249) ile uyumludur.")
        self.assertEqual(to.dogrula(BELGE_IPUCLU, yeni), [])
        self.assertIn('<w:bookmarkStart w:id="1" w:name="_Toc1"/>', yeni)


BELGE_ONAYLI = KOK_ETIKET + "".join([
    par(kosu("Bu iddia (Bernan, 2019) ve Bernan (2019) ile Bernanke ve Bernan yazar.")),
    par(kosu("TEWART, Ian (1997), Kitap; TEWART burada gövdede.")),
    par(kosu("Görüş (Brenner, 2012: 45) ve Brenner ("), kosu("2012) ile (Brenner, 2011) ve (Brennerx, 2012).")),
]) + SON
DUZELTMELER = {
    "ad": [{"eski": "Bernan", "yeni": "Berman"}, {"eski": "TEWART", "yeni": "STEWART", "kapsam": "kaynakca_basi"}],
    "yil": [{"soyad": "Brenner", "eski": "2012", "yeni": "2011"}],
}


class OnayliDuzeltmeTesti(unittest.TestCase):
    def setUp(self):
        self.yeni, self.gunluk, self.sayac, _ = to.belge_onar(BELGE_ONAYLI, duzeltmeler=DUZELTMELER)
        self.m = to._metin(to.hepsini_kabul(self.yeni))

    def test_ad_duzeltmesi_tam_sozcuk_ve_her_yerde(self):
        self.assertEqual(self.m[0], "Bu iddia (Berman, 2019) ve Berman (2019) ile Bernanke ve Berman yazar.")
        self.assertEqual(self.sayac["AD_DUZELT[Bernan→Berman]"], 3)

    def test_kaynakca_basi_kapsami_yalniz_paragraf_basi(self):
        self.assertEqual(self.m[1], "STEWART, Ian (1997), Kitap; TEWART burada gövdede.")
        self.assertEqual(self.sayac["AD_DUZELT[TEWART→STEWART]"], 1)

    def test_yil_duzeltmesi_parantezli_anlatisal_ve_parcali_calisma(self):
        self.assertEqual(self.m[2], "Görüş (Brenner, 2011: 45) ve Brenner (2011) ile (Brenner, 2011) ve (Brennerx, 2012).")
        self.assertEqual(self.sayac["YIL_DUZELT[2012→2011]"], 2)

    def test_hepsini_reddet_orijinal_ve_dogrulama_temiz(self):
        self.assertEqual(to._metin(to.hepsini_reddet(self.yeni)), to._metin(BELGE_ONAYLI))
        self.assertEqual(to.dogrula(BELGE_ONAYLI, self.yeni), [])

    def test_onaysiz_cift_gecersiz_ve_liste_olmadan_hicbir_sey_olmaz(self):
        to.IZINLI_AD.clear()
        self.assertFalse(to.degisiklik_gecerli("AD_DUZELT", "Bernan", "Berman"))
        self.assertFalse(to.degisiklik_gecerli("YIL_DUZELT", "2012", "ABCD"))
        yeni, _, sayac, _ = to.belge_onar(BELGE_ONAYLI)
        self.assertEqual(yeni, BELGE_ONAYLI)
        self.assertNotIn("AD_DUZELT", sayac)


class AjanTesti(unittest.TestCase):
    def setUp(self):
        import importlib
        self.d = tempfile.TemporaryDirectory()
        for alt in ("gelen", "calisma", "cikti", "gunluk"):
            os.makedirs(os.path.join(self.d.name, alt))
        os.environ["TEZ_AJAN_KOK"] = self.d.name
        import tez_ajan
        importlib.reload(tez_ajan)
        self.aj = tez_ajan
        docx_yaz(os.path.join(self.d.name, "gelen", "Tez.docx"))
        docx_yaz(os.path.join(self.d.name, "gelen", "Tez.orijinal.docx"))

    def tearDown(self):
        self.d.cleanup()
        os.environ.pop("TEZ_AJAN_KOK", None)

    def _calistir(self, gorev):
        c, h = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(c), contextlib.redirect_stderr(h):
            kod = self.aj.main([gorev])
        return kod, c.getvalue(), h.getvalue()

    def _ayar(self, **kw):
        with open(os.path.join(self.d.name, "calisma", "ayar.json"), "w") as f:
            json.dump(kw, f)

    def test_orijinal_reddedilir(self):
        self._ayar(girdi="Tez.orijinal.docx")
        kod, _, hata = self._calistir("denetle")
        self.assertEqual(kod, 5)
        self.assertIn("orijinal", hata)

    def test_yol_gezintisi_reddedilir(self):
        self._ayar(girdi="../calisma/ayar.json")
        self.assertEqual(self._calistir("denetle")[0], 2)

    def test_onar_kural_varsayilan_kuru_dosya_yazmaz(self):
        kod, cikti, _ = self._calistir("onar-kural")
        self.assertEqual(kod, 0)
        self.assertEqual(json.loads(cikti)["kip"], "kuru")
        self.assertEqual(os.listdir(os.path.join(self.d.name, "cikti")), ["onar-ozet.json"])

    def test_onar_kural_uygula_yazar_ve_gunluk_hash_icerir(self):
        self._ayar(girdi="Tez.docx", uygula=True, kenar=True)
        kod, cikti, _ = self._calistir("onar-kural")
        self.assertEqual(kod, 0)
        self.assertTrue(os.path.isfile(os.path.join(self.d.name, "cikti", "Tez.ajan.docx")))
        with open(os.path.join(self.d.name, "gunluk", "ajan.jsonl"), encoding="utf-8") as f:
            satirlar = f.read()
        self.assertIn('"girdi_sha256"', satirlar)
        self.assertNotIn("Bıçakçı", satirlar)
        self.assertNotIn("Kitap", satirlar)

    def test_denetle_iki_rapor_uretir_ve_cumlesiz_temizdir(self):
        kod, _, _ = self._calistir("denetle")
        self.assertEqual(kod, 0)
        with open(os.path.join(self.d.name, "cikti", "rapor-cumlesiz.md"), encoding="utf-8") as f:
            cum = f.read()
        tam = os.path.join(self.d.name, "cikti", "rapor-tam.md")
        self.assertTrue(os.path.isfile(tam))
        self.assertIn("Cümlesiz rapor", cum)
        self.assertEqual(oct(os.stat(tam).st_mode & 0o777), "0o600")

    def test_onar_model_henuz_yok(self):
        self.assertEqual(self._calistir("onar-model")[0], 6)


if __name__ == "__main__":
    unittest.main(verbosity=1)
