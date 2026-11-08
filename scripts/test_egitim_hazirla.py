#!/usr/bin/env python3
"""egitim_hazirla.py birim testleri (yalnız standart kütüphane): python3 scripts/test_egitim_hazirla.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import egitim_hazirla as eh  # noqa: E402
import esdizim as esd  # noqa: E402


class EgitimHazirlaTesti(unittest.TestCase):
    def test_ciftleri_uret_boyut_ve_alanlar(self):
        ciftler = eh.ciftleri_uret()
        self.assertGreaterEqual(len(ciftler), 200)
        zorunlu = {"id", "alan", "instruction", "input", "output"}
        for c in ciftler:
            self.assertTrue(zorunlu <= set(c.keys()))
            self.assertNotEqual(c["input"], c["output"])

    def test_bozuk_sayi_ve_atif_cifti_elenir(self):
        adaylar = [
            {
                "id": "GECERLI-1",
                "input": "Siber saldırılar (Yılmaz, 2020: 15) %42,5 oranında tehdit sergilemektedir.",
                "output": "Siber saldırılar (Yılmaz, 2020: 15) %42,5 oranında tehdit oluşturmaktadır.",
            },
            {
                "id": "BOZUK-SAYI",
                "input": "Siber saldırılar %42,5 oranında tehdit sergilemektedir.",
                "output": "Siber saldırılar tehdit oluşturmaktadır.",
            },
            {
                "id": "BOZUK-ATIF",
                "input": "Siber saldırılar (Yılmaz, 2020: 15) tehdit sergilemektedir.",
                "output": "Siber saldırılar tehdit oluşturmaktadır.",
            },
            {
                "id": "BOZUK-IEEE",
                "input": "Siber saldırılar [18] tehdit sergilemektedir.",
                "output": "Siber saldırılar tehdit oluşturmaktadır.",
            },
        ]
        gecerli = eh.ciftleri_filtrele(adaylar)
        idler = [c["id"] for c in gecerli]
        self.assertEqual(idler, ["GECERLI-1"])

    def test_uretilen_cikti_cumlelerinde_esdizim_hatasi_yok(self):
        ciftler = eh.ciftleri_uret()
        kurallar = {k["id"]: k for k in esd.kurallari_yukle()}
        for c in ciftler[:40]:
            ana_id = c["id"].replace("-ATIF", "")
            if ana_id in kurallar:
                bulgu = esd.metin_tara(c["output"], kurallar=[kurallar[ana_id]])
                self.assertEqual(bulgu, [], f"{c['id']} çıktısında hâlâ eş dizim hatası var: {c['output']}")

    def test_cli_dosya_yazma_ve_ozet(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        f.close()
        try:
            cikti = io.StringIO()
            with contextlib.redirect_stdout(cikti):
                kod = eh.main(["--cikti", f.name])
            self.assertEqual(kod, 0)
            with open(f.name, encoding="utf-8") as oku:
                satirlar = [json.loads(s) for s in oku.read().strip().split("\n")]
            self.assertGreaterEqual(len(satirlar), 200)
        finally:
            os.unlink(f.name)


if __name__ == "__main__":
    unittest.main(verbosity=1)
