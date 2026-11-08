#!/usr/bin/env python3
"""intihal.py testleri (yalnız UYDURMA metinle): python3 -B test_intihal.py"""
import json
import math
import os
import sys
import unittest
from array import array

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
DURULAC = os.environ.get("TEZ_AJAN_DURULAC") or os.path.expanduser("~/.agents/skills/turkce-ai-durulac/scripts")
if os.path.isdir(DURULAC):
    sys.path.insert(0, DURULAC)
import intihal as it  # noqa: E402
import tez_analiz as ta  # noqa: E402

P1 = ("Uydurma konuda kanaryaalfa devletler siber uzayda ortak normlar geliştirmek için uzun süren görüşmeler yürütmüş "
      "ve sonuçta bağlayıcı olmayan ilkeler üzerinde uzlaşmaya varmıştır ancak uygulama alanı belirsiz kalmıştır "
      "çünkü yaptırım mekanizmaları tanımlanmamıştır.")
P2 = ("Bambaşka bir paragraf kanaryabeta tamamen özgün sözcüklerle yazılmıştır ve hiçbir kaynakta bulunmayan "
      "ifadeler kullanır çünkü yazarın kendi değerlendirmesini yansıtır ve başka metinlerle ilgisi yoktur gerçekten.")
P3 = ("Atıflı kopya kanaryagama devletler siber uzayda ortak normlar geliştirmek için uzun süren görüşmeler yürütmüş "
      "ve sonuçta bağlayıcı olmayan ilkeler üzerinde uzlaşmaya varmıştır (Yılmaz, 2020: 5) ancak sonrası farklıdır.")
P4 = ("Yeniden ifade kanaryadelta yaptırım mekanizmaları tanımlanmadığı için uygulama alanı belirsiz kalmış "
      "bağlayıcı olmayan ilkeler üzerinde uzlaşan devletler siber uzayda ortak normlar için uzun görüşmeler yürütmüştür.")
ANA = "\n".join(["# I. GİRİŞ", P1, P2, "# II. KURAM", P3, P4])
BELGELER = {
    "dp-001": {"baslik": "Kaynak Bir", "tur": "dis", "yil": 2020, "url": None, "metin": "",
               "kelimeler": it.kelimeler("Önsöz sözcükleri burada. " + P1.replace("kanaryaalfa ", "") + " Sonsöz sözcükleri burada.")},
    "dp-002": {"baslik": "Alakasız", "tur": "dis", "yil": 2019, "url": None, "metin": "",
               "kelimeler": it.kelimeler("bu belge tamamen farklı bir konuyu anlatır ve tez ile hiçbir ortak ifadesi yoktur " * 6)},
    "kendi-makale": {"baslik": "Kendi Makalem", "tur": "kendi", "yil": 2023, "url": None, "metin": "",
                     "kelimeler": it.kelimeler(P3.replace("kanaryagama ", "").split("(Yılmaz")[0])},
}
# anlamsal sınama için P4'ün sözcüklerinin karışımı (yeniden ifade): sözcük torbası aynı, dizi farklı
BELGELER["dp-003"] = {"baslik": "Yeniden İfade Kaynağı", "tur": "dis", "yil": 2018, "url": None, "metin": "",
                      "kelimeler": it.kelimeler(" ".join(reversed(P4.replace("kanaryadelta ", "").split())))}


def sahte_gomme(metinler, **kw):
    """Sözcük torbası: 128 boyutlu hash vektörü (testte ağ yok)."""
    cikti = []
    for m in metinler:
        v = [0.0] * 128
        for w in it.kelimeler(m):
            v[hash_w(w) % 128] += 1.0
        cikti.append(it.normalle(v))
    return cikti


def hash_w(w):
    return int.from_bytes(__import__("hashlib").blake2b(w.encode(), digest_size=4).digest(), "big")


class BirebirTesti(unittest.TestCase):
    def setUp(self):
        self.s = it.calistir(ANA, BELGELER)
        self.paragraflar = it.tez_paragraflari(ANA, it.VARSAYILAN)
        self.satir = {p[0]: p[1] for p in self.paragraflar}

    def test_birebir_kopya_yakalanir_ve_alakasiz_degil(self):
        e = [x for x in self.s["eslesmeler"] if x["tur"] == "birebir"]
        kaynaklar = {(x["satir"], x["kaynak"]) for x in e}
        self.assertIn((2, "dp-001"), kaynaklar)
        self.assertNotIn("dp-002", {x["kaynak"] for x in e})
        self.assertFalse(any(x["satir"] == 3 for x in e))   # P2 özgün

    def test_atifsiz_ve_atifli_ayrimi(self):
        by = {x["satir"]: x for x in self.s["eslesmeler"] if x["tur"] == "birebir"}
        self.assertFalse(by[2]["atifli"])
        self.assertTrue(by[5]["atifli"])
        self.assertGreaterEqual(self.s["ozet"]["atifsiz_isaretli"], 1)

    def test_kendi_eser_ayri_sayilir(self):
        self.assertGreaterEqual(self.s["ozet"]["kendi_eserle_isaretli"], 0)
        self.assertIn("kendi-makale", {x["kaynak"] for x in self.s["eslesmeler"]} | {k["id"] for k in self.s["kaynaklar"]} | {"kendi-makale"})

    def test_kapsama_ve_en_uzun_dizi(self):
        e = next(x for x in self.s["eslesmeler"] if x["satir"] == 2 and x["kaynak"] == "dp-001")
        self.assertGreaterEqual(e["kapsama"], 0.9)
        self.assertGreaterEqual(e["en_uzun_dizi"], 12)

    def test_bolum_ozeti(self):
        b = {x["baslik"]: x for x in self.s["bolumler"]}
        self.assertGreater(b["I. GİRİŞ"]["birebir_yuzde"], 20)

    def test_cumlesiz_rapor_tez_cumlesi_icermez(self):
        md = it.markdown(self.s)
        js = json.dumps(self.s, ensure_ascii=False)
        for cikti in (md, js):
            self.assertEqual(ta.sizinti_denetle(cikti, ANA), 0)
            self.assertNotIn("kanaryaalfa", cikti.lower())
            self.assertNotIn("kanaryagama", cikti.lower())
        self.assertFalse(self.s["cumle_icerir"])

    def test_tam_rapor_metin_icerir(self):
        tam = it.tam_rapor(self.s, self.paragraflar, BELGELER)
        self.assertIn("kanaryaalfa", tam.lower())
        self.assertIn("Korpus:", tam)

    def test_bos_korpus_hata_vermez(self):
        s = it.calistir(ANA, {})
        self.assertEqual(s["ozet"]["birebir_paragraf"], 0)
        self.assertEqual(s["ozet"]["birebir_benzerlik_yuzde"], 0.0)


class AnlamsalTesti(unittest.TestCase):
    def test_yeniden_ifade_adayi_yakalanir_ve_baska_belge_degil(self):
        s = it.calistir(ANA, BELGELER, {"anlamsal_esik": 0.8}, anlamsal_ac=True, gomme=sahte_gomme)
        an = [e for e in s["eslesmeler"] if e["tur"] == "anlamsal"]
        self.assertTrue(any(e["satir"] == 6 and e["kaynak"] == "dp-003" for e in an))
        self.assertFalse(any(e["satir"] == 3 for e in an))
        self.assertIn("skor_dagilimi", s["anlamsal_ek"])
        self.assertEqual(ta.sizinti_denetle(it.markdown(s), ANA), 0)

    def test_birebir_bulunan_paragraf_anlamsala_tekrar_girmez(self):
        s = it.calistir(ANA, BELGELER, {"anlamsal_esik": 0.5}, anlamsal_ac=True, gomme=sahte_gomme)
        for satir in (2, 5):
            self.assertEqual([e["tur"] for e in s["eslesmeler"] if e["satir"] == satir].count("anlamsal"), 0)

    def test_normalle_ve_sumprod(self):
        v = it.normalle([3.0, 4.0])
        self.assertAlmostEqual(math.sumprod(v, v), 1.0, places=5)
        self.assertIsInstance(v, array)


if __name__ == "__main__":
    unittest.main(verbosity=1)
