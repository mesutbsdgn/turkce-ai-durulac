#!/usr/bin/env python3
"""esdizim.py birim testleri (yalnız standart kütüphane): python3 scripts/test_esdizim.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import esdizim as e  # noqa: E402
import tarama as t  # noqa: E402


class VeriTabaniTesti(unittest.TestCase):
    def setUp(self):
        self.kurallar = e.kurallari_yukle()

    def test_en_az_40_kural_ve_sema_gecerliligi(self):
        self.assertGreaterEqual(len(self.kurallar), 40)
        idler = set()
        zorunlu = {"id", "alan", "nesne_kokleri", "yanlis_fiil_kokleri", "dogru_fiiller", "aciklama", "ornek_yanlis", "ornek_dogru"}
        for k in self.kurallar:
            self.assertTrue(zorunlu <= set(k.keys()), f"Eksik alan: {k.get('id')}")
            self.assertNotIn(k["id"], idler, f"Tekrarlanan ID: {k['id']}")
            idler.add(k["id"])
            self.assertTrue(len(k["nesne_kokleri"]) >= 1)
            self.assertTrue(len(k["yanlis_fiil_kokleri"]) >= 1)
            self.assertTrue(len(k["dogru_fiiller"]) >= 1)

    def test_tum_kurallarin_ornek_yanlis_ve_dogru_cumleleri(self):
        for k in self.kurallar:
            yanlis_bulgu = e.metin_tara(k["ornek_yanlis"], kurallar=[k], pencere=5)
            self.assertTrue(
                len(yanlis_bulgu) >= 1,
                f"{k['id']} kendi ornek_yanlis cümlesini yakalayamadı: {k['ornek_yanlis']}",
            )
            dogru_bulgu = e.metin_tara(k["ornek_dogru"], kurallar=[k], pencere=5)
            self.assertEqual(
                len(dogru_bulgu),
                0,
                f"{k['id']} kendi ornek_dogru cümlesinde yanlış alarm verdi: {k['ornek_dogru']}",
            )


class MorfolojiVePencereTesti(unittest.TestCase):
    def test_cekimli_fiil_ve_isim_hal_ekleri(self):
        bulgu = e.metin_tara("Devlet dışı aktörler asimetrik tehdit sergilemektedir.")
        idler = {b["id"] for b in bulgu}
        self.assertIn("ESD-001", idler)

    def test_unsuz_yumusamasi_ve_edilgen_cati(self):
        metin = (
            "Siber saldırıların ulusal güvenliğe tehdidi açıkça sergilenmiştir. "
            "Bu tez literatürdeki boşluğu doldurmaktadır."
        )
        idler = {b["id"] for b in e.metin_tara(metin)}
        self.assertIn("ESD-001", idler)
        self.assertIn("ESD-018", idler)

    def test_nesne_ve_yuklem_arasinda_zarf_sifat_penceresi(self):
        metin = "Bölgesel güçler ulusal güvenlik politikalarını hızla yeniden inşa etmektedir."
        bulgu = e.metin_tara(metin, pencere=4)
        self.assertTrue(any(b["id"] == "ESD-003" for b in bulgu))

    def test_zarf_fiil_ve_sifat_fiil_cekimleri(self):
        metin = "Araştırmada üç hipotezi gerçekleştirerek saha bulgularını üreten model incelendi."
        idler = {b["id"] for b in e.metin_tara(metin)}
        self.assertIn("ESD-005", idler)
        self.assertIn("ESD-009", idler)

    def test_yanlis_on_ek_benzerligi_alarm_vermez(self):
        metin = "Politikacılar verimli çalışarak rölanti sürecinde yapıcı davrandı."
        self.assertEqual(e.metin_tara(metin), [])

    def test_cumle_siniri_asan_kelimeler_eslesmez(self):
        metin = "Ulusal güvenlikte yeni bir tehdit ortaya çıktı. Sergilenen yaklaşım farklıydı."
        self.assertEqual(e.metin_tara(metin), [])

    def test_kod_blogu_ve_satir_ici_kod_yoksayilir(self):
        metin = "```\ntehdit sergilemektedir\n```\nBkz. `politika inşa etmek`."
        self.assertEqual(e.metin_tara(metin), [])

    def test_alan_filtresi(self):
        metin = "Aktörler tehdit sergilemektedir ve örneklem yapılmıştır."
        sadece_metod = e.metin_tara(metin, alan="metodoloji")
        idler = {b["id"] for b in sadece_metod}
        self.assertIn("ESD-012", idler)
        self.assertNotIn("ESD-001", idler)


class KomutVeTaramaEntegrasyonuTesti(unittest.TestCase):
    def test_cli_json_ve_metin_ciktisi(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write("Kritik altyapı açıkları yüksek risk üretmektedir.\n")
        f.close()
        try:
            cikti = io.StringIO()
            with contextlib.redirect_stdout(cikti):
                kod = e.main([f.name, "--json"])
            self.assertEqual(kod, 0)
            veri = json.loads(cikti.getvalue())
            self.assertEqual(veri["toplam"], 1)
            self.assertEqual(veri["bulgular"][0]["id"], "ESD-002")
        finally:
            os.unlink(f.name)

    def test_tarama_tur_tez_esdizim_entegrasyonu(self):
        metin = "Devletler siber güvenlik politikalarını bölgesel düzeyde yeniden inşa etmektedir."
        kurallar = t.derle(tur="tez")
        bulgular = t.tara(metin, kurallar, tur="tez")
        self.assertTrue(any("ESD-003" in b[3] for b in bulgular))


if __name__ == "__main__":
    unittest.main(verbosity=1)
