#!/usr/bin/env python3
"""denetci.py testleri (uydurma belgeyle): python3 -B test_denetci.py"""
import os
import sys
import tempfile
import unittest
import zipfile

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import denetci as dn  # noqa: E402
import test_tez_onar as tt  # noqa: E402
import tez_onar as to  # noqa: E402


class DenetciTesti(unittest.TestCase):
    def _hazirla(self, belge, duzeltmeler=None, bozucu=None):
        d = tempfile.mkdtemp()
        g, a = os.path.join(d, "g.docx"), os.path.join(d, "a.docx")
        tt.docx_yaz(g, belge)
        yeni, _, _, _ = to.belge_onar(belge, kenar=False, duzeltmeler=duzeltmeler)
        if bozucu:
            yeni = bozucu(yeni)
        tt.docx_yaz(a, yeni)
        return dn.denetle(g, a, duzeltmeler)

    def test_ajanin_tum_kurallari_temiz_gecer(self):
        belge = tt.BELGE.replace("</w:body>", "") if False else tt.BELGE
        s = self._hazirla(belge)
        self.assertEqual(s["sorunlar"], [])
        sayi = s["sayilar"]
        self.assertGreaterEqual(sayi.get("ATIF_SAYFA", 0), 1)
        self.assertGreaterEqual(sayi.get("BENZESME", 0), 3)
        self.assertGreaterEqual(sayi.get("BASLIK_BOSLUK", 0), 1)
        self.assertGreaterEqual(sayi.get("BASLIK_BUYUK", 0), 1)
        self.assertNotIn("bilinmeyen", sayi)

    def test_onayli_ad_ve_yil_duzeltmeleri_siniflanir(self):
        s = self._hazirla(tt.BELGE_ONAYLI, tt.DUZELTMELER)
        self.assertEqual(s["sorunlar"], [])
        self.assertEqual(s["sayilar"].get("AD_DUZELT"), 4)
        self.assertEqual(s["sayilar"].get("YIL_DUZELT"), 2)
        onceler = {c["once"].strip("()'’,.;:") for c in s["degisiklikler"] if c["sinif"] == "AD_DUZELT"}
        self.assertIn("Bernan", onceler)

    def test_p_nokta_bosluk_varyanti_atif_sayilir(self):
        belge = tt.KOK_ETIKET + tt.par(tt.kosu("Görüş (Stallings, 2008, p. 249) önemlidir.")) + tt.SON
        s = self._hazirla(belge)
        self.assertEqual(s["sorunlar"], [])
        self.assertEqual(s["sayilar"].get("ATIF_SAYFA"), 1)

    def test_metni_bozulmus_cikti_yakalanir(self):
        s = self._hazirla(tt.BELGE, bozucu=lambda x: x.replace("önemlidir", "önemsizdir"))
        self.assertTrue(any("hepsini reddedince" in x for x in s["sorunlar"]))

    def test_bilinmeyen_degisiklik_yakalanir(self):
        yabanci = ('<w:ins w:id="9999" w:author="Durulaç-Ajan" w:date="2026-01-01T00:00:00Z">'
                   '<w:r><w:t xml:space="preserve">GİZLİ EKLEME</w:t></w:r></w:ins>')
        s = self._hazirla(tt.BELGE, bozucu=lambda x: x.replace("<w:p>", "<w:p>" + yabanci, 1))
        self.assertIn("bilinmeyen", s["sayilar"])
        self.assertTrue(any("bilinmeyen" in x for x in s["sorunlar"]))

    def test_baska_yazarin_degisikligi_ajan_sayilmaz(self):
        s = self._hazirla(tt.BELGE)
        self.assertEqual(s["yabanci_degisiklik_sayisi"], 1)  # BELGE içindeki hazır 'x' yazarlı izli ekleme


if __name__ == "__main__":
    unittest.main(verbosity=1)
