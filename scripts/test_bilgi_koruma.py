"""bilgi_koruma.py: sadeleştirmede kaybolan sayı, alıntı, ad ve atıf yakalanır."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bilgi_koruma as bk  # noqa: E402

BETIK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bilgi_koruma.py")

# 30 sözcük sınırı için kısaltılan haber maddelerinin kurgusal (gerçek kişi/kurum içermeyen) örnekleri.
GAZZE_ONCE = ("Ajansa göre Örnekova'daki sel dört kişinin ölümüne yol açtı, Afet Kurumu "
              "geçen aydan bu yana en az 1.538 kişinin tahliye edildiğini bildirdi; AYV'nin "
              "desteği azaltmasıyla 500 bin kişinin etkilendiği belirtildi.")
GAZZE_SONRA = "Ajansa göre Örnekova'daki sel dört kişinin ölümüne yol açtı."
HURMUZ_ONCE = ("Örnek Grup yedi geminin hasar gördüğünü açıkladı; Bölge "
               "Komutanlığı iddiayı reddedip gemilerin %95'inin geçtiğini söyledi.")
HURMUZ_SONRA = "Örnek Grup yedi geminin hasar gördüğünü açıkladı."


class BilgiKoruma(unittest.TestCase):
    def test_kumulatif_sayi_ve_kurum_kaybi(self):
        k = bk.kayiplar(GAZZE_ONCE, GAZZE_SONRA)
        self.assertIn("1.538", k["sayı"])
        self.assertIn("500bin", k["sayı"])
        self.assertIn("AYV", k["ad"])

    def test_karsi_aciklama_kaybi(self):
        k = bk.kayiplar(HURMUZ_ONCE, HURMUZ_SONRA)
        self.assertIn("ret", k["atıf"])
        self.assertIn("Bölge", k["ad"])
        self.assertIn("%95", k["sayı"])

    def test_alinti_kaybi_ve_alinti_ici_ad_sayilmaz(self):
        once = 'Başkan Yılmaz "Belki biraz daha ileri gidebiliriz" dedi.'
        k = bk.kayiplar(once, "Başkan Yılmaz konuştu.")
        self.assertEqual(k["alıntı"], ["belki biraz daha ileri gidebiliriz"])
        self.assertNotIn("ad", k)

    def test_sadelestirme_kayipsiz(self):
        once = "Bakanlık, 12 ilde 340 okulun onarımının gerçekleştirildiğini Haber Ajansı'na göre açıkladı."
        sonra = "Haber Ajansı'na göre Bakanlık 12 ilde 340 okulu onardı."
        self.assertEqual(bk.kayiplar(once, sonra), {})

    def test_ay_adi_ad_sayilmaz(self):
        self.assertNotIn("ad", bk.kayiplar("Toplantı 27 Ekim'de yapılacak.", "Toplantı 27'sinde."))

    def test_json_kipi_cikis_kodu(self):
        with tempfile.TemporaryDirectory() as d:
            once, sonra = os.path.join(d, "o.json"), os.path.join(d, "s.json")
            json.dump({"olaylar": [{"id": "a", "ozet": GAZZE_ONCE}]}, open(once, "w"))
            json.dump([{"id": "a", "ozet": GAZZE_SONRA}], open(sonra, "w"))
            r = subprocess.run([sys.executable, BETIK, "--json", once, sonra],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 1)
            self.assertIn("1 öğede kayıp", r.stdout)
            json.dump([{"id": "a", "ozet": GAZZE_ONCE}], open(sonra, "w"))
            r = subprocess.run([sys.executable, BETIK, "--json", once, sonra],
                               capture_output=True, text=True)
            self.assertEqual(r.returncode, 0)


if __name__ == "__main__":
    unittest.main()
