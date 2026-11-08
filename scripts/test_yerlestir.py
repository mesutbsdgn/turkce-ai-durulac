#!/usr/bin/env python3
"""yerlestir.py testleri (uydurma belge, sahte gömme): python3 -B test_yerlestir.py"""
import os
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import test_tez_onar as tt  # noqa: E402
import tez_onar as to  # noqa: E402
import yerlestir as yz  # noqa: E402

KELIMELER = " ".join(["kelime%d" % i for i in range(45)])
SIBER = " ".join(["siber güvenlik kurumu başkanlık kanun kritik altyapı saldırı"] * 7)
TERR = " ".join(["terör örgütü silahlı cebir şiddet propaganda ceza hapis"] * 7)


def p(metin, stil=None):
    pstil = f'<w:pPr><w:pStyle w:val="{stil}"/></w:pPr>' if stil else "<w:pPr><w:jc w:val=\"both\"/></w:pPr>"
    return f'<w:p>{pstil}<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">{metin}</w:t></w:r></w:p>'


BELGE = tt.KOK_ETIKET + "".join([
    p("İÇİNDEKİLER"), p("I. GİRİŞ"), p("II. KAVRAM"), p(KELIMELER), p("I. GİRİŞ"), p(KELIMELER, "Normal"), p(SIBER),
    p("II. TERÖR"), p(TERR), p("Kısa paragraf."), p("KAYNAKÇA"), p(SIBER)]) + tt.SON


def gom(metinler):
    sozluk = {}
    out = []
    for m in metinler:
        v = [0.0] * 6
        for s in m.lower().split():
            i = {"siber": 0, "güvenlik": 1, "terör": 2, "örgütü": 3, "kelime0": 4}.get(s, 5 if s.startswith("kelime") else None)
            if i is not None:
                v[i] += 1
        out.append(v)
    return out


METINLER = [{"id": "K2", "paragraflar": ["Siber güvenlik başkanlık kanun siber güvenlik kurumu kritik altyapı saldırı siber."]},
            {"id": "K3", "paragraflar": ["Terör örgütü terör örgütü silahlı propaganda terör.", "İkinci paragraf terör örgütü."]}]


class YerlestirTesti(unittest.TestCase):
    def test_aday_secimi_kaynakca_ve_baslik_disinda(self):
        a = yz.aday_paragraflar(BELGE)
        metinler = [x[2] for x in a]
        self.assertTrue(all(len(t.split()) >= 40 for t in metinler))
        self.assertEqual(len(a), 3)  # gerçek başlıktan sonra: KELIMELER, SIBER, TERR; içindekiler ve kaynakça dışarıda

    def test_yer_secimi_anlamca(self):
        a = yz.aday_paragraflar(BELGE)
        s = yz.yer_sec(a, METINLER, gom, esik=0.3)
        par = dict((x[0], x[2]) for x in a)
        self.assertIn("siber", par[s[0]["par_no"]])
        self.assertIn("terör", par[s[1]["par_no"]])
        self.assertTrue(all(x["durum"] == "yerlestirildi" for x in s))

    def test_dusuk_benzerlik_atlanir(self):
        a = yz.aday_paragraflar(BELGE)
        s = yz.yer_sec(a, METINLER, gom, esik=1.01)
        self.assertTrue(all(x["durum"] == "atlandi:dusuk_benzerlik" for x in s))

    def test_izli_ekleme_ve_geri_alma(self):
        a = yz.aday_paragraflar(BELGE)
        s = yz.yer_sec(a, METINLER, gom, esik=0.3)
        yeni = yz.ekle(BELGE, s, METINLER, "2026-11-02T00:00:00Z")
        self.assertEqual(to.dogrula(BELGE, yeni), [])
        self.assertEqual(to._metin(to.hepsini_reddet(yeni)), to._metin(BELGE))
        kabul = to._metin(to.hepsini_kabul(yeni))
        self.assertEqual(len(kabul), len(to._metin(BELGE)) + 3)
        self.assertIn(METINLER[1]["paragraflar"][1], kabul)
        self.assertIn("<w:b/>", yeni)  # çalışma biçimi bağlanmış paragraftan alındı
        self.assertIn('w:jc w:val="both"', yeni)

    def test_ekleme_xml_iyi_bicimli(self):
        import xml.etree.ElementTree as ET
        a = yz.aday_paragraflar(BELGE)
        s = yz.yer_sec(a, METINLER, gom, esik=0.3)
        ET.fromstring(yz.ekle(BELGE, s, METINLER, "2026-11-02T00:00:00Z"))


if __name__ == "__main__":
    unittest.main()
