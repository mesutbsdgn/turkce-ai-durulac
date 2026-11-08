#!/usr/bin/env python3
"""tez_analiz.py birim testleri (yalnız standart kütüphane): python3 scripts/test_tez_analiz.py"""
import contextlib
import io
import json
import os
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kilavuz  # noqa: E402
import tez_analiz as ta  # noqa: E402


ORNEK_TEZ = """# 1. Giriş
Araştırmacılara göre siber saldırılar ulusal güvenliğe ciddi bir tehdit sergilemektedir.
Tezimizde bu sorunu adreslemek için üç temel hipotez gerçekleştirdik.

# 2. Kavramsal Çerçeve
Uluslararası sistemin aktörlerinin güvenlik stratejilerinin dönüşümünün etkileri (Yılmaz, 2020: 44) incelenmiştir.
Devletler siber uzayda yeni güvenlik politikaları inşa etmektedir [12].
"""


class TezAnalizTesti(unittest.TestCase):
    def test_bolumlere_ayir(self):
        bolumler = ta.bolumlere_ayir(ORNEK_TEZ)
        self.assertEqual(len(bolumler), 2)
        self.assertEqual(bolumler[0][0], "1. Giriş")
        self.assertEqual(bolumler[1][0], "2. Kavramsal Çerçeve")

    def test_metin_analiz_et_tum_juri_risklerini_yakalar(self):
        analiz = ta.metin_analiz_et(ORNEK_TEZ)
        self.assertEqual(analiz["atif_sayisi"], 2)
        self.assertGreaterEqual(len(analiz["esdizim_bulgulari"]), 3)
        self.assertEqual(len(analiz["kaynaksiz_otorite"]), 1)
        self.assertEqual(len(analiz["tamlama_zincirleri"]), 1)
        self.assertGreaterEqual(len(analiz["sahis_sizintilari"]), 1)
        self.assertTrue(any("Kaynaksız otorite" in r for r in analiz["juri_riskleri"]))

    def test_onceki_metinle_bilgi_kaybi_tespiti(self):
        eski = "Siber operasyonlar (Kaya, 2019) %64,5 oranında artış göstermiştir."
        yeni = "Siber operasyonlar artış göstermiştir."
        analiz = ta.metin_analiz_et(yeni, onceki_metin=eski)
        self.assertIn("sayı", analiz["bilgi_kaybi"])
        self.assertIn("ad", analiz["bilgi_kaybi"])

    def test_markdown_rapor_ve_cli_json(self):
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(ORNEK_TEZ)
        f.close()
        try:
            cikti_md = io.StringIO()
            with contextlib.redirect_stdout(cikti_md):
                kod1 = ta.main([f.name])
            self.assertEqual(kod1, 0)
            self.assertIn("# Tez Jüri ve Üslup Denetim Raporu", cikti_md.getvalue())
            self.assertIn("Kaynaksız Otorite İfadeleri", cikti_md.getvalue())

            cikti_json = io.StringIO()
            with contextlib.redirect_stdout(cikti_json):
                kod2 = ta.main([f.name, "--json"])
            self.assertEqual(kod2, 0)
            veri = json.loads(cikti_json.getvalue())
            self.assertEqual(len(veri["bolumler"]), 2)
        finally:
            os.unlink(f.name)

    def test_unsuz_benzesmesi_ve_atif_kaynakca_capraz_denetim(self):
        metin = "Siber saldırılar 2015'de ve İnternet'de (Yılmaz, 2020: 12; Demir, 2018: 44) incelenmiştir."
        kaynakca = [
            "Yılmaz, Ahmet (2020), Siber Güvenlik Stratejileri, Ankara.",
            "Kaya, Mehmet (2019), Ulusal Güvenlik ve Caydırıcılık, İstanbul.",
        ]
        analiz = ta.metin_analiz_et(metin, kaynakca_satirlari=kaynakca)
        self.assertEqual(len(analiz["benzesme_hatalari"]), 2)
        ak = analiz["atif_kaynakca_denetimi"]
        self.assertIn("Demir (2018)", ak["kaynakcada_eksik_atiflar"])
        self.assertIn("Kaya (2019)", ak["metinde_eksik_kaynaklar"])

    def test_docx_ayristir_icindekiler_kaynakca_ve_yorum_ayrimi(self):
        import zipfile
        doc_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:body>
            <w:p><w:pPr><w:pStyle w:val="T1"/></w:pPr><w:r><w:t>I. GİRİŞ 1</w:t></w:r></w:p>
            <w:p><w:pPr><w:pStyle w:val="Balk1"/></w:pPr><w:r><w:t>I. GİRİŞ</w:t></w:r></w:p>
            <w:p><w:r><w:t>Siber saldırılar (Yılmaz, 2020: 15) ciddi bir tehdit sergilemektedir.</w:t></w:r></w:p>
            <w:p><w:pPr><w:pStyle w:val="Balk1"/></w:pPr><w:r><w:t>II. KAYNAKÇA</w:t></w:r></w:p>
            <w:p><w:r><w:t>YILMAZ, A., (2020), Siber Güvenlik, Ankara.</w:t></w:r></w:p>
          </w:body>
        </w:document>"""
        comments_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <w:comments xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
          <w:comment w:id="1" w:author="danisman" w:date="2026-01-01T00:00:00Z">
            <w:p><w:r><w:t>Kontrol edilecek not</w:t></w:r></w:p>
          </w:comment>
        </w:comments>"""
        f = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        f.close()
        try:
            with zipfile.ZipFile(f.name, "w") as zf:
                zf.writestr("word/document.xml", doc_xml)
                zf.writestr("word/comments.xml", comments_xml)
            ayri = ta.docx_ayristir(f.name)
            self.assertIn("# I. GİRİŞ", ayri["ana_metin"])
            self.assertNotIn("I. GİRİŞ 1", ayri["ana_metin"])
            self.assertEqual(len(ayri["kaynakca_satirlari"]), 1)
            self.assertEqual(len(ayri["yorumlar"]), 1)
        finally:
            os.unlink(f.name)

    METIN_KILAVUZ = (
        "# I. GİRİŞ\n"
        "# II. Siber Güvenlik ve Ulusal Strateji\n"
        "Realist teori ve kuram çerçevesinde 5651 sayılı kanun ve yasa hükümleri "
        "Tablo 2 ve Şekil 1.2 içinde (Evans & Smith, 2019, s. 45) incelenmiştir.\n"
    )

    def _kilavuz_cagri(self, metin, profil):
        return ta.kilavuz_denetimi(
            metin,
            on_sayfalar=["ÖZET", " ".join(["kelime"] * 120)],
            kaynakca_ham_satirlar=["YILMAZ, A. (2020). Siber Güvenlik, Ankara."],
            ozgecmis_satirlari=["E-posta: ornek@example.com", "Doğum Tarihi: 01.01.1990"],
            kenar_bosluklari={"ust_cm": 2.5, "alt_cm": 2.5, "sol_ic_cm": 3.0, "sag_dis_cm": 2.5},
            profil=profil,
        )

    def test_kilavuz_denetimi_varsayilan_profil_terim_baslik_tablo_ve_kvkk(self):
        denetim = self._kilavuz_cagri(self.METIN_KILAVUZ, kilavuz.yukle())
        self.assertGreaterEqual(len(denetim["terim_ikilikleri"]), 2)
        self.assertGreaterEqual(len(denetim["baslik_ihlalleri"]), 1)
        self.assertGreaterEqual(len(denetim["sekil_cizelge_ihlalleri"]), 2)
        self.assertGreaterEqual(len(denetim["atif_bicim_ihlalleri"]), 2)
        self.assertFalse(denetim["ozet_denetimi"]["ozet_uygun"])
        self.assertEqual(denetim["ozet_denetimi"]["sinir"], [250, 400])
        self.assertGreaterEqual(len(denetim["kenar_ihlalleri"]), 1)
        self.assertGreaterEqual(len(denetim["kvkk_ihlalleri"]), 2)
        self.assertTrue(denetim["kaynakca_bicim_uyarilari"], "varsayılan profil kaynakça alt başlığı ister")

    def test_genel_profil_tablo_ve_bolum_numarasini_sorun_saymaz(self):
        denetim = self._kilavuz_cagri(self.METIN_KILAVUZ, kilavuz.genel_profil())
        self.assertEqual(denetim["sekil_cizelge_ihlalleri"], [], "genel profil 'Tablo 2' ve 'Şekil 1.2' için uyarı vermez")
        self.assertEqual(denetim["kaynakca_bicim_uyarilari"], [])
        self.assertEqual(denetim["ozet_denetimi"]["sinir"], [150, 300])
        self.assertGreaterEqual(len(denetim["terim_ikilikleri"]), 2)   # terim birliği her profilde aranır
        self.assertGreaterEqual(len(denetim["kvkk_ihlalleri"]), 2)

    def test_tablo_ve_cizelge_karisik_kullanimi_uyarilir(self):
        denetim = self._kilavuz_cagri("Tablo 1 ve Çizelge 2 incelendi.", kilavuz.genel_profil())
        self.assertEqual(len(denetim["sekil_cizelge_ihlalleri"]), 1)

    def test_atif_sayfa_bicimi_profile_gore_denetlenir(self):
        iki_nokta = kilavuz.yukle()
        apa = kilavuz.yukle(); apa["atif"]["sayfa_bicimi"] = "apa7"
        a = self._kilavuz_cagri("Bu sonuç (Kaya, 2020, s. 12) ve (Demir, 2019: 7) görülmüştür.", iki_nokta)["atif_bicim_ihlalleri"]
        b = self._kilavuz_cagri("Bu sonuç (Kaya, 2020, s. 12) ve (Demir, 2019: 7) görülmüştür.", apa)["atif_bicim_ihlalleri"]
        self.assertEqual(len(a), 1); self.assertIn("s. 12", a[0])
        self.assertEqual(len(b), 1); self.assertIn("2019: 7", b[0])

    def test_profil_dosyalari_kurumdan_bagimsizdir(self):
        profil = kilavuz.yukle()
        self.assertEqual(profil["profil"], "yazar-tezi")
        for yol in (kilavuz.VARSAYILAN_YOL, os.path.join(os.path.dirname(kilavuz.VARSAYILAN_YOL), "tez-yazim-kilavuzu.ornek-genel.json")):
            ham = open(yol, encoding="utf-8").read().lower()
            for yasak in ("aydın", "iaü", "iau", "aydin.edu", "madde "):
                self.assertNotIn(yasak, ham, yol)

    def test_varsayilan_json_ile_kod_varsayilanlari_ayni(self):
        """JSON silinse bile aynı değerlerle çalışılır: iki kaynak birbirinden ayrışmamalı."""
        ham = json.load(open(kilavuz.VARSAYILAN_YOL, encoding="utf-8"))
        kod = kilavuz.VARSAYILAN
        for bolum in ("sayfa_duzeni", "baslik", "ozet", "sekil_tablo", "atif", "kaynakca"):
            for anahtar, deger in kod[bolum].items():
                self.assertEqual(ham[bolum][anahtar], deger, f"{bolum}.{anahtar}")
        self.assertEqual(ham["terim_birligi_ciftleri"], kod["terim_birligi_ciftleri"])

    def test_ornek_genel_json_genel_profille_ayni(self):
        yol = os.path.join(os.path.dirname(kilavuz.VARSAYILAN_YOL), "tez-yazim-kilavuzu.ornek-genel.json")
        yuklenen = kilavuz.yukle(yol); genel = kilavuz.genel_profil()
        for bolum in ("sayfa_duzeni", "ozet", "sekil_tablo", "kaynakca", "atif", "baslik"):
            for anahtar, deger in genel[bolum].items():
                self.assertEqual(yuklenen[bolum][anahtar], deger, f"{bolum}.{anahtar}")

    def test_ortam_degiskeni_ozel_profili_secer(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            json.dump({"profil": "benim", "ozet": {"min_kelime": 100, "maks_kelime": 120}}, f); yol = f.name
        eski = os.environ.get(kilavuz.ORTAM_DEGISKENI)
        os.environ[kilavuz.ORTAM_DEGISKENI] = yol
        try:
            p = kilavuz.yukle()
            self.assertEqual(p["profil"], "benim")
            self.assertEqual(p["ozet"]["maks_kelime"], 120)
            self.assertEqual(p["sayfa_duzeni"]["ic_kenar_cm"], 4.0, "eksik anahtarlar varsayılandan tamamlanır")
        finally:
            if eski is None: os.environ.pop(kilavuz.ORTAM_DEGISKENI, None)
            else: os.environ[kilavuz.ORTAM_DEGISKENI] = eski
            os.unlink(yol)

    def test_bozuk_profil_dosyasi_varsayilana_duser(self):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as f:
            f.write("{bozuk"); yol = f.name
        try:
            self.assertEqual(kilavuz.yukle(yol)["profil"], "yazar-tezi")
        finally:
            os.unlink(yol)


KANARYA_TEZ = """# I. GİRİŞ
Tehditler kanaryaalfa yararlanarak üretilen sonuçlar yaratmaktadır.
Tezimizde kanaryabeta hipotezini inceledik ve değerlendirdik.
Araştırmacılara göre kanaryagama saldırılar hızla artmaktadır.
Saldırganların kullanıcıların kanaryadelta bilgisayarlarının veya ağlarının güvenliği önemlidir.
Olaylar 2015'de başladı ve Kanaryakitap'da ayrıntılı biçimde anlatıldı.
"""
KANARYA_RE = r"kanarya\w+"


def _calistir(args):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = ta.main(args)
    return kod, cikti.getvalue(), hata.getvalue()


class AtifEslestiriciTesti(unittest.TestCase):
    METIN = (
        "Birinci (Bıçakcı, 2012) iddia. İkinci (Kaya vd., 2008: 61) iddia. Üçüncü (DSÖ, 2024) iddia.\n"
        "Dördüncü (Evans and Smith, 1967: 150; Çetin, 2019a) iddia. Beşinci (Aktaran: Demir, 2015) iddia.\n"
        "Altıncı (Stallings & Brown, 2008, p. 249) iddia. Sekizinci (Öztürk, 2019) iddia. Dokuzuncu (Işık, 2021) iddia.\n"
        "Düz metinde Fazlalık adı geçer ama atıf değildir.\n"
    )
    KAYNAKCA = [
        "BIÇAKCI, Salih (2012), Siber Güvenlik Üzerine, Ankara.",
        "KAYA, Mehmet, ÇETİN, Ali (2008), Ulusal Güvenlik, İstanbul.",
        "DSÖ (2024), Dünya Sağlık Örgütü Raporu, Cenevre.",
        "EVANS, John and SMITH, Paul (1967), Strategy, London.",
        "ÇETİN, Ali (2019a), Caydırıcılık Kuramı, Ankara.",
        "DEMİR, Veli (2015), Terör ve Siber, İstanbul.",
        "STALLINGS, William and BROWN, Lawrie (2008), Computer Security, Boston.",
        "ÖZTÜRK, Ayşe (2019), Hukuk, Ankara.",
        "ISIK, Hasan (2021), Kriz, İzmir.",
        "FAZLALIK, Zeynep (2010), Atıfsız Kitap, Ankara.",
    ]

    def setUp(self):
        self.sonuc = ta.atif_kaynakca_denetimi(self.METIN, self.KAYNAKCA)

    def test_buyuk_harf_kaynakca_vd_kurum_ve_yil_eki_eslesir(self):
        self.assertEqual(self.sonuc["kaynakcada_eksik_atiflar"], [])

    def test_turkce_harf_katlama_isik_ISIK_eslesir(self):
        self.assertNotIn("Işık (2021)", self.sonuc["kaynakcada_eksik_atiflar"])
        self.assertNotIn("ISIK (2021)", self.sonuc["metinde_eksik_kaynaklar"])

    def test_duz_metinde_gecen_yazar_atif_sayilmaz(self):
        self.assertEqual(self.sonuc["metinde_eksik_kaynaklar"], ["FAZLALIK (2010)"])

    def test_ikinci_yazar_atifta_gecerse_kaynak_atifli_sayilir(self):
        ak = ta.atif_kaynakca_denetimi("Bu iddia (Kaya ve Çetin, 2008: 61) desteklenir.", ["ÇETİN, Ali (2008), Kitap, Ankara."])
        self.assertEqual(ak["metinde_eksik_kaynaklar"], [])

    def test_gercek_eksik_atif_ve_soyad_yazim_farki_yakalanir(self):
        ak = ta.atif_kaynakca_denetimi("İddia (Bernan, 2019) ve (Yok, 2020).", ["BERMAN, Jay (2019), Kitap, Ankara."])
        self.assertIn("Bernan (2019)", ak["kaynakcada_eksik_atiflar"])
        self.assertIn("Yok (2020)", ak["kaynakcada_eksik_atiflar"])
        self.assertIn("BERMAN (2019)", ak["metinde_eksik_kaynaklar"])


class CumlesizRaporTesti(unittest.TestCase):
    def setUp(self):
        import re
        self.re = re
        f = tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8")
        f.write(KANARYA_TEZ)
        f.close()
        self.yol = f.name

    def tearDown(self):
        os.unlink(self.yol)

    def _kanaryalar(self, metin):
        return set(self.re.findall(KANARYA_RE, ta.kucult_tr(metin)))

    def test_tam_rapor_kanaryalari_yakalar_testin_bos_olmadigini_kanitlar(self):
        _, tam, _ = _calistir([self.yol, "--tam"])
        # esdizim, tamlama zinciri ve ünsüz benzeşmesi ifadeleri kanarya taşır (kaynaksız otorite/şahıs ifadeleri taşımaz)
        self.assertGreaterEqual(len(self._kanaryalar(tam)), 3, "tam raporda en az 3 kanarya görünmeli")

    def test_varsayilan_rapor_markdown_kanarya_icermez(self):
        kod, cikti, _ = _calistir([self.yol])
        self.assertEqual(kod, 0)
        self.assertEqual(self._kanaryalar(cikti), set())
        self.assertIn("Cümlesiz rapor", cikti)
        self.assertIn("`#", cikti)

    def test_varsayilan_rapor_json_kanarya_icermez_ve_sema_yazar(self):
        kod, cikti, _ = _calistir([self.yol, "--json"])
        self.assertEqual(kod, 0)
        self.assertEqual(self._kanaryalar(cikti), set())
        veri = json.loads(cikti)
        self.assertEqual(veri["rapor_sema"], "cumlesiz-v1")
        self.assertFalse(veri["cumle_icerir"])
        self.assertGreaterEqual(len(veri["esdizim_bulgulari"]), 1)
        self.assertGreaterEqual(len(veri["kaynaksiz_otorite"]), 1)
        self.assertGreaterEqual(len(veri["sahis_sizintilari"]), 1)
        self.assertGreaterEqual(len(veri["tamlama_zincirleri"]), 1)
        self.assertGreaterEqual(len(veri["benzesme_hatalari"]), 2)
        self.assertIn("ifade_ozet", veri["esdizim_bulgulari"][0])
        self.assertNotIn("ifade", veri["esdizim_bulgulari"][0])
        self.assertNotIn("nesne", veri["esdizim_bulgulari"][0])

    def test_yorum_ve_bilgi_kaybi_degerleri_cikarilir(self):
        analiz = ta.metin_analiz_et(
            "Sonuç %12,5 oranındadır.",
            onceki_metin="Sonuç Kanaryayazar tarafından %64,5 oranında belirtildi (Kanaryayazar, 2019).",
            yorumlar=[{"yazar": "danisman", "tarih": "2026-01-01", "metin": "kanaryayorum burayı düzelt"}],
        )
        temiz = ta.cumlesizlestir(analiz)
        dump = json.dumps(temiz, ensure_ascii=False)
        self.assertEqual(self._kanaryalar(dump), set())
        self.assertEqual(temiz["yorumlar"][0]["metin_uzunluk"], len("kanaryayorum burayı düzelt"))
        self.assertTrue(all(isinstance(v, int) for v in temiz["bilgi_kaybi"].values()))
        self.assertGreaterEqual(len(temiz["bilgi_kaybi"]), 1)

    def test_sizinti_bekcisi_5_sozcuklu_parcayi_yakalar(self):
        ana = "# Başlık\nKanaryaalfa beta gama delta epsilon zeta sonucu ortaya çıkmıştır.\n"
        self.assertGreater(ta.sizinti_denetle("rapor: kanaryaalfa beta gama delta epsilon burada", ana), 0)
        self.assertEqual(ta.sizinti_denetle("rapor: kanaryaalfa beta gama delta", ana), 0)

    def test_baslik_ve_atif_parcalari_bekciyi_tetiklemez(self):
        ana = "# III. Siber Güvenlik Unsurları, Tehditler ve Savunma Stratejileri\nDüz cümle (Yılmaz, 2020: 44) burada.\n"
        cikti = "başlık: III. Siber Güvenlik Unsurları, Tehditler ve Savunma Stratejileri ; atıf (Yılmaz, 2020: 44) ok"
        self.assertEqual(ta.sizinti_denetle(cikti, ana), 0)

    def test_govdede_tekrarlanan_baslik_metni_sizinti_sayilmaz(self):
        ana = "# I. SİBER GÜVENLİK UNSURLARI VE SAVUNMA STRATEJİLERİ\nSiber Güvenlik Unsurları ve Savunma Stratejileri\nDüz bir gövde cümlesi burada yer almaktadır.\n"
        cikti = "| I. SİBER GÜVENLİK UNSURLARI VE SAVUNMA STRATEJİLERİ | 12 |"
        self.assertEqual(ta.sizinti_denetle(cikti, ana), 0)
        self.assertGreater(ta.sizinti_denetle("alıntı: Düz bir gövde cümlesi burada yer", ana), 0)
        self.assertEqual(ta.sizinti_bolumleri("## 3. Bölüm\nDüz bir gövde cümlesi burada yer", ana), {"3. Bölüm": 2})

    def test_basligin_ortak_sozcuk_dizisi_govdede_gecse_de_sizinti_sayilmaz(self):
        ana = "# IV. SİBER TERÖRİZM VE ULUSAL GÜVENLİK UYGULAMALARI\nBu çalışmada siber terörizm ve ulusal güvenlik meselesi ele alınır.\n"
        cikti = "| IV. SİBER TERÖRİZM VE ULUSAL GÜVENLİK UYGULAMALARI | 3 |"
        self.assertEqual(ta.sizinti_denetle(cikti, ana), 0)
        self.assertGreater(ta.sizinti_denetle("alıntı: siber terörizm ve ulusal güvenlik meselesi", ana), 0)

    def test_bekci_sizinti_olursa_cikti_yazilmaz(self):
        orijinal = ta.cumlesizlestir
        ta.cumlesizlestir = lambda analiz: analiz  # kasten sızdıran hâl
        try:
            kod, cikti, hata = _calistir([self.yol, "--json"])
        finally:
            ta.cumlesizlestir = orijinal
        self.assertEqual(kod, 3)
        self.assertEqual(cikti, "")
        self.assertIn("SIZINTI BEKÇİSİ", hata)

    def test_kasten_bozma_bekci_kapaliyken_sizinti_gecer(self):
        orijinal_f, orijinal_b = ta.cumlesizlestir, ta.SIZINTI_BEKCISI_AKTIF
        ta.cumlesizlestir = lambda analiz: analiz
        ta.SIZINTI_BEKCISI_AKTIF = False
        try:
            kod, cikti, _ = _calistir([self.yol, "--json"])
        finally:
            ta.cumlesizlestir, ta.SIZINTI_BEKCISI_AKTIF = orijinal_f, orijinal_b
        self.assertEqual(kod, 0)
        self.assertGreaterEqual(len(self._kanaryalar(cikti)), 1)


if __name__ == "__main__":
    unittest.main(verbosity=1)
