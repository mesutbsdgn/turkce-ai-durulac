#!/usr/bin/env python3
"""ogretim_denetim.py birim testleri (yalnız standart kütüphane, ağ yok): python3 scripts/test_ogretim_denetim.py"""
import contextlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ogretim_denetim as o  # noqa: E402

TEMIZ = """---
tur: rehber
baslik: Kendini tanıtma
denetim: 2026-11-22 sonnet
hedef: DELF-A1 yazma · tanıtma mesajı
---
# 1 Kalıp

| Fransızca | Okunuş | Türkçe |
|---|---|---|
| Je m'appelle Ali. | /jö mapel ali/ | Adım Ali. |
| J'habite à Paris. | /jabit a pari/ | Paris'te oturuyorum. |

# 2 Kur

Önce adını, sonra şehrini söyle.

# 3 Kendini dene

Türkçesine bak, Fransızcasını bakmadan yaz.
"""

# Olcum taklitleri: (sayfa no, doluluk oranı, görsel var mı)
IYI_PDF = {"sayfa": 3, "yazi": 11.2, "doluluk": [(1, 0.9, False), (2, 0.85, False), (3, 0.3, False)]}


def sonuc(metin, olcum=IYI_PDF, dil="fr", alan=None):
    return o.denetle(metin, olcum, alan, dil)


def boyutlar(s, duzey=None):
    return [b["boyut"] for b in s["bulgular"] if duzey is None or b["duzey"] == duzey]


def calistir(*arg):
    cikti, hata = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(cikti), contextlib.redirect_stderr(hata):
        kod = o.main(list(arg))
    return kod, cikti.getvalue(), hata.getvalue()


class Temiz(unittest.TestCase):
    def test_temiz_belge_16(self):
        s = sonuc(TEMIZ)
        self.assertEqual(s["bulgular"], [])
        self.assertEqual((s["toplam"], s["azami"]), (16, 16))
        self.assertEqual(s["karar"], "yayınlanabilir")

    def test_pdfsiz_olculmedi_puan_uydurulmaz(self):
        s = sonuc(TEMIZ, olcum=None)
        self.assertIsNone(s["puan"]["Okunaklılık"])
        self.assertIsNone(s["puan"]["Verimlilik"])
        self.assertEqual((s["toplam"], s["azami"]), (12, 12))


class Dogruluk(unittest.TestCase):
    def test_kiril_harf_hata(self):
        s = sonuc(TEMIZ.replace("Je m'appelle", "Jе m'appelle"))      # е = Kiril
        self.assertIn("Doğruluk", boyutlar(s, "HATA"))
        self.assertEqual(s["puan"]["Doğruluk"], 0)
        self.assertEqual(s["karar"], "yayınlanamaz")

    def test_yer_tutucu_hata(self):
        s = sonuc(TEMIZ + "\nTODO: örnek ekle\n")
        self.assertIn("Doğruluk", boyutlar(s, "HATA"))

    def test_kod_blogundaki_todo_sayilmaz(self):
        s = sonuc(TEMIZ + "\n```\n# TODO iç not\n```\n")
        self.assertNotIn("Doğruluk", boyutlar(s))

    def test_duzelt_kiril_latin(self):
        yeni, yapilan = o.duzelt("Jе m'аppelle. Мама")                 # karışık sözcükler + saf Kiril sözcük
        self.assertEqual(yeni, "Je m'appelle. Мама")
        self.assertTrue(yapilan)

    def test_duzelt_kucuk_punto(self):
        yeni, yapilan = o.duzelt("<style>html { font-size: 7.5pt; }</style>")
        self.assertIn("font-size: 9pt", yeni)
        yeni2, yapilan2 = o.duzelt("<style>html { font-size: 10pt; }</style>")
        self.assertEqual(yapilan2, [])


class SiraAkis(unittest.TestCase):
    def test_ek_numara_uyari(self):
        s = sonuc(TEMIZ.replace("# 3 Kendini dene", "# 2.5+ Ek\n\nek\n\n# 3 Kendini dene"))
        self.assertIn("Sıra ve akış", boyutlar(s, "UYARI"))
        self.assertEqual(s["puan"]["Sıra ve akış"], 1)

    def test_geri_giden_numara(self):
        s = sonuc(TEMIZ.replace("# 3 Kendini dene", "# 1 Tekrar\n\n# 3 Kendini dene"))
        self.assertTrue(any("geriye" in b["mesaj"] or "iki kez" in b["mesaj"] for b in s["bulgular"]))

    def test_sayfa_gondermesi(self):
        s = sonuc(TEMIZ + "\ns. 6'daki tabloya bak.\n")
        self.assertIn("Sıra ve akış", boyutlar(s, "UYARI"))


class Sinama(unittest.TestCase):
    def test_sinamasiz_uyari(self):
        s = sonuc(TEMIZ.replace("# 3 Kendini dene\n\nTürkçesine bak, Fransızcasını bakmadan yaz.", "# 3 Son\n\nBitti."))
        self.assertIn("Kendini sınama", boyutlar(s, "UYARI"))
        self.assertEqual(s["karar"], "yayınlanabilir")               # uyarı yayını durdurmaz


class Verimlilik(unittest.TestCase):
    def test_sayfa_tavani_asildi_hata(self):
        metin = TEMIZ.replace("tur: rehber", "tur: rehber\nsayfa_tavan: 2")
        s = sonuc(metin)
        self.assertIn("Verimlilik", boyutlar(s, "HATA"))
        self.assertEqual(s["karar"], "yayınlanamaz")

    def test_tavansiz_uzun_belge_uyari(self):
        olcum = {"sayfa": 20, "yazi": 11, "doluluk": [(i, 0.9, False) for i in range(1, 21)]}
        self.assertIn("Verimlilik", boyutlar(sonuc(TEMIZ, olcum), "UYARI"))

    def test_yarim_sayfa_orani(self):
        olcum = {"sayfa": 5, "yazi": 11, "doluluk": [(1, 0.2, False), (2, 0.3, False), (3, 0.9, False),
                                                     (4, 0.9, False), (5, 0.1, False)]}
        self.assertIn("Verimlilik", boyutlar(sonuc(TEMIZ, olcum), "UYARI"))


class Okunaklilik(unittest.TestCase):
    def test_kucuk_yazi_hata_ve_uyari(self):
        self.assertIn("Okunaklılık", boyutlar(sonuc(TEMIZ, dict(IYI_PDF, yazi=7.5)), "HATA"))
        self.assertIn("Okunaklılık", boyutlar(sonuc(TEMIZ, dict(IYI_PDF, yazi=8.6)), "UYARI"))

    def test_bos_sayfa_hata(self):
        olcum = dict(IYI_PDF, doluluk=[(1, 0.9, False), (2, 0.01, False), (3, 0.9, False)])
        self.assertIn("Okunaklılık", boyutlar(sonuc(TEMIZ, olcum), "HATA"))

    def test_gorselli_sayfa_bos_sayilmaz(self):
        olcum = dict(IYI_PDF, doluluk=[(1, 0.9, False), (2, 0.01, True), (3, 0.9, False)])
        self.assertNotIn("Okunaklılık", boyutlar(sonuc(TEMIZ, olcum)))


class SeviyeEzber(unittest.TestCase):
    def test_hedef_disi_ingilizce(self):
        ek = "\nThe rule is that you should use this form with the verb, and that is because it would be fine.\n"
        self.assertIn("Seviye", boyutlar(sonuc(TEMIZ + ek), "UYARI"))

    def test_ingilizce_hedef_dilse_sayilmaz(self):
        ek = "\nThe rule is that you should use this form with the verb, and that is because it would be fine.\n"
        self.assertNotIn("Seviye", boyutlar(sonuc(TEMIZ + ek, dil="en")))

    def test_okunussuz_yabanci_metin(self):
        metin = TEMIZ.replace("/jö mapel ali/", "").replace("/jabit a pari/", "")
        self.assertIn("Ezber ve kavrama", boyutlar(sonuc(metin), "UYARI"))


class Komut(unittest.TestCase):
    def setUp(self):
        self.dizin = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.dizin)

    def yaz(self, ad, icerik):
        yol = os.path.join(self.dizin, ad)
        with open(yol, "w", encoding="utf-8") as f:
            f.write(icerik)
        return yol

    def test_cikis_kodlari_ve_json(self):
        kod, cikti, _ = calistir(self.yaz("temiz.md", TEMIZ), "--json")
        self.assertEqual(kod, 0)
        self.assertEqual(json.loads(cikti)["puan"]["Okunaklılık"], None)
        kod, _, _ = calistir(self.yaz("kiril.md", TEMIZ.replace("Paris.", "Pаris.")))
        self.assertEqual(kod, 1)
        self.assertEqual(calistir(os.path.join(self.dizin, "yok.md"))[0], 2)
        self.assertEqual(calistir(self.yaz("x.md", TEMIZ), "--dil", "xx")[0], 2)

    def test_duzelt_dosyaya_yazar_ve_hatayi_giderir(self):
        yol = self.yaz("kiril.md", TEMIZ.replace("Paris.", "Pаris."))
        kod, cikti, _ = calistir(yol, "--duzelt")
        self.assertEqual(kod, 0)
        self.assertIn("🔧", cikti)
        with open(yol, encoding="utf-8") as f:
            self.assertNotRegex(f.read(), r"[Ѐ-ӿ]")


TIP = """# 1 Hipertansiyon
Tanı ofis ölçümüyle konur. Hasta anamnezi, fizik muayene ve klinik bulgular değerlendirilir.
Tedavi: enalapril 5 mg günde bir. Komplikasyon: inme. Kontrendikasyon: gebelik. İlaç dozu böbrekte ayarlanır.
Örnek vaka: 60 yaşında hasta, 160/100 mmHg. Çözüm: yaşam tarzı ve ilaç.
# 2 Sorular
Soru 1: Gebede hangi ilaç kontrendikedir? Cevap: ACE inhibitörü (anjiyotensin dönüştürücü enzim inhibitörü).
"""
TARIH = """# 1 Tanzimat
Tanzimat Fermanı 1839'da ilan edildi (İnalcık, 1964). Osmanlı İmparatorluğu XIX. yüzyılda ıslahat yaptı.
Padişah Abdülmecid dönemi; antlaşma ve savaş sonrası meclis tartışıldı.
# 2 Sorular
Soru 1: Ferman hangi yıl ilan edildi? Cevap: 1839.
Kaynakça: İnalcık, H. (1964).
"""
COG = """# 1 Türkiye iklimi
Akdeniz ikliminde yazlar kuraktır, yağış kışın düşer. Ova, plato ve akarsu yer şekilleri; erozyon toprak kaybıdır.
Karadeniz'de yıllık yağış 2200 mm'yi bulur. İç Anadolu'da nüfus yoğunluğu 40 kişi/km² civarındadır.
# 2 Dilsiz harita
Dilsiz haritada Akdeniz bölgesini bul.
"""
MAT = """# 1 Türev
Tanım: f fonksiyonunun türevi limit ile tanımlanır. Teorem: türevlenebilir fonksiyon süreklidir; ispat kitapta.
Polinom, logaritma, integral ve denklem çözümü konularıyla ilişkilidir.
# 2 Alıştırma
Soru 1: x² türevini bul. Soru 2: ln x türevini bul.
"""
DIS = """# 1 Kanal tedavisi
36 numaralı diş için periapikal radyografi alınır. Pulpa ve dentin değerlendirilir; molar dişte mezial ve distal kanal var.
Restorasyon, oklüzyon ve gingiva kontrolü yapılır. Daha sonra #19 diş kontrol edilir.
## Kendini dene
Kanal sayısı kaçtır? Cevap: 3.
"""


def tespit(metin, **kw):
    return o.denetle(metin, None, **kw)


class AlanTespiti(unittest.TestCase):
    def test_her_alan_dogru_tespit(self):
        for metin, beklenen in [(TEMIZ, "dil"), (TIP, "tip"), (TARIH, "tarih"), (COG, "cografya"), (MAT, "matematik"),
                                (DIS, "dis")]:
            with self.subTest(beklenen=beklenen):
                self.assertEqual(tespit(metin)["alan"], beklenen)

    def test_az_ipucu_genel(self):
        s = tespit("# 1 Zaman\n\nPlanlı çalış.\n\n# 2 Kendini dene\n\nSoru 1: Neden?\n")
        self.assertEqual(s["alan"], "genel")

    def test_frontmatter_ve_bayrak_tespiti_gecer(self):
        self.assertEqual(tespit("---\nalan: tarih\n---\n" + TIP)["alan"], "tarih")
        self.assertEqual(tespit(TIP, alan="matematik")["tespit"]["kaynak"], "--alan")
        with self.assertRaises(ValueError):
            tespit(TIP, alan="astroloji")

    def test_ingilizce_tip_notu_dil_sayilmaz(self):
        metin = ("# 1 Hypertension\nThe diagnosis is made in the clinic. Treatment of the patient: drug dose is 5 mg. "
                 "Tanı, tedavi, hasta, klinik, ilaç, doz, komplikasyon, kontrendikasyon. "
                 "This is the case and you have to do it with the guideline of the society.\n")
        self.assertEqual(tespit(metin)["alan"], "tip")

    def test_kisa_kok_genel_ile_eslesmez(self):
        self.assertNotRegex("genel genellikle", o.sozcuk_deseni("gen"))
        self.assertRegex("genler", o.sozcuk_deseni("gen"))


class AlanKontrolleri(unittest.TestCase):
    def test_dil_kurali_dil_disinda_calismaz(self):
        s = tespit(TARIH)
        self.assertFalse(any("okunuş" in b["mesaj"] for b in s["bulgular"]))

    def test_temiz_tip_ve_tarih(self):
        self.assertEqual(tespit(TIP)["bulgular"], [])
        self.assertEqual(tespit(TARIH)["bulgular"], [])

    def test_tip_doz_hatasi(self):
        s = tespit(TIP.replace("5 mg", "5,0 mg ve ,5 mg"))
        self.assertEqual(s["karar"], "yayınlanamaz")
        self.assertEqual(len([b for b in s["bulgular"] if b["duzey"] == "HATA"]), 2)

    def test_lab_degeri_ve_mikrogram_dogru_yorumlanir(self):
        s = tespit(TIP + "\nHb 12,0 g/dL normaldir. B12 250 μg verilir.\n")
        self.assertNotIn("HATA", [b["duzey"] for b in s["bulgular"]])
        self.assertTrue(any("μg" in b["mesaj"] for b in s["bulgular"]))      # ISMP: mcg yaz (uyarı)

    def test_tip_tehlikeli_kisaltma_ve_tanimsiz(self):
        s = tespit(TIP + "\nİnsülin 10 U. KBH ve KKY, AF; KBH, KKY ve AF birlikte.\n")
        mesaj = " ".join(b["mesaj"] for b in s["bulgular"])
        self.assertIn("U/IU", mesaj)
        self.assertIn("Tanımsız kısaltma", mesaj)

    def test_kilavuz_yilsiz(self):
        self.assertIn("Doğruluk", boyutlar(tespit(TIP + "\nESC kılavuzuna göre hedef 130 mmHg.\n")))
        self.assertNotIn("Doğruluk", boyutlar(tespit(TIP + "\nESC 2024 kılavuzuna göre hedef 130 mmHg.\n")))

    def test_dis_numara_karisik(self):
        self.assertTrue(any("numaralama" in b["mesaj"] for b in tespit(DIS)["bulgular"]))
        self.assertFalse(any("numaralama" in b["mesaj"] for b in tespit(DIS.replace("#19", "46 numaralı"))["bulgular"]))

    def test_matematik_ornek_ve_cevap(self):
        s = tespit(MAT)
        self.assertIn("Sıra ve akış", boyutlar(s))
        self.assertIn("Kendini sınama", boyutlar(s))
        tamam = MAT.replace("# 2 Alıştırma", "Örnek 1: x³ türevi 3x². Çözüm: kuvvet kuralı.\n# 2 Alıştırma") + "## Cevaplar\n1) 2x 2) 1/x\n"
        self.assertEqual(tespit(tamam)["bulgular"], [])

    def test_tarih_otorite_kaynak_yuzyil(self):
        s = tespit(TARIH.replace("Kaynakça: İnalcık, H. (1964).", "").replace(" (İnalcık, 1964)", "")
                   + "Tarihçilere göre bu ferman bir dönüm noktasıdır. 18. yüzyıl Lale Devri ile kıyaslanır.\n")
        mesaj = " ".join(b["mesaj"] for b in s["bulgular"])
        for parca in ("belirsiz otorite", "kaynak gösterilmemiş", "Yüzyıl yazımı"):
            self.assertIn(parca, mesaj)

    def test_cografya_veri_ve_harita(self):
        s = tespit(COG + "\n![Türkiye iklim haritası](iklim.png)\nLejant: renkler iklim tipini gösterir.\n")
        mesaj = " ".join(b["mesaj"] for b in s["bulgular"])
        self.assertIn("Yılı ve kaynağı olmayan", mesaj)
        self.assertIn("ölçek", mesaj)
        self.assertNotIn("lejant", mesaj.split("Haritada")[1])

    def test_gorsel_bicim_ek_elle_listesi(self):
        gorsel = DIS + "".join(f"\n![Şekil {i}: diş](d{i}.png)" for i in range(4))
        s = tespit(gorsel)
        self.assertEqual(s["bicim"], "gorsel")
        self.assertTrue(any("WCAG 1.4.1" in m for m in s["elle_liste"]))
        self.assertEqual(tespit(TARIH)["bicim"], "sozel")

    def test_profil_dosyasi_gecerli(self):
        p = o.profiller()
        for ad, prof in p.items():
            if ad.startswith("_"):
                continue
            with self.subTest(alan=ad):
                for k in o.kontrol_listesi(p, ad):
                    self.assertIn(k, o.KONTROLLER)
                for g in prof.get("elle_gruplar", []):
                    self.assertIn(g, p["_elle_gruplar"])
                if prof.get("ust"):
                    self.assertIn(prof["ust"], p)
                self.assertTrue(prof["sinama_oneri"])


ALAN_ORNEKLERI = {
 "hemsirelik": "# 1 Bası yarası\nHemşirelik süreci: veri toplama, hemşirelik tanısı (NANDA), amaç, hemşirelik girişimi, değerlendirme. Bakım planı yazılır. Hasta düşme riski ve bası yarası açısından izlenir; vital bulgular ve yaşam bulguları kaydedilir. Aseptik teknikle enjeksiyon ve ilaç uygulama yapılır. Hemşire sıvı-elektrolit dengesini izler.\n",
 "eczacilik": "# 1 Farmakokinetik\nEtken madde emilim, dağılım hacmi ve eliminasyon ile tanımlanır. Yarılanma ömrü ve biyoyararlanım farmasötik dozaj formuna bağlıdır. İlaç etkileşimi farmakodinami ile birlikte değerlendirilir; jenerik müstahzar ve süspansiyon, kapsül farkı. Eczacı prospektüsü okur.\n",
 "veteriner": "# 1 Mastitis\nSığır ve koyunda mastitis sürü sağlığını etkiler. Veteriner hekim köpek ve kedi hastalıklarından farklı olarak buzağı ve ruminant izler. Zoonoz hastalıklar ve kuduz, şap bildirimi; arınma süresi ve hayvan sağlığı kuralları. Hayvancılık işletmesi.\n",
 "beslenme": "# 1 Enerji gereksinimi\nBeslenme planında makro besin ve mikro besin dengesi; protein alımı, karbonhidrat, yağ asidi, vitamin ve mineral. Diyetisyen öğün ve porsiyon belirler; beden kitle indeksi ve antropometri ölçülür; glisemik indeks ve besin öğesi tabloları kullanılır. Günlük 2000 kcal.\n",
 "fizyoterapi": "# 1 Diz rehabilitasyonu\nFizyoterapi programında eklem hareket açıklığı ve kas kuvveti değerlendirilir. Germe, denge, postür ve propriosepsiyon egzersizleri; manuel terapi ve elektroterapi. İzometrik kuvvetlendirme egzersizi günde 2 kez, 3 set 10 tekrar. Rehabilitasyon fonksiyonel hedeflidir.\n",
 "acil": "# 1 Resüsitasyon\nAcil serviste triyaj ve ABCDE yaklaşımı uygulanır. KPR ve defibrilasyon, hava yolu yönetimi ve entübasyon; şok ve travma hastası, Glasgow koma skalası (GKS), anafilaksi. Paramedik olay yerinde ambulansta acil müdahale yapar.\n",
 "psikoloji": "# 1 Bellek\nBilişsel psikoloji bellek ve algıyı inceler. Kişilik kuramları, bağlanma, gelişim psikolojisi; psikopatoloji ve depresyon, anksiyete. Deney grubu ve kontrol grubu karşılaştırılır; örneklem seçilir. Psikoterapi ve davranışçı terapi yaklaşımları.\n",
 "istatistik": "# 1 Hipotez testi\nİstatistik derste p değeri, anlamlılık ve güven aralığı. Regresyon ve korelasyon; varyans, standart sapma, örneklem dağılım. t testi, ki-kare ve anova; etki büyüklüğü. Olasılık dağılımı ve veri seti.\n",
 "fizik": "# 1 Dinamik\nFizik dersinde kuvvet, ivme ve momentum; newton yasaları, joule ve enerji korunumu. Serbest cisim diyagramı ve sürtünme; elektrik alan, manyetik alan, dalga, optik ve termodinamik.\n",
 "kimya": "# 1 Asit-baz\nKimya: mol ve molarite, tepkime ve reaksiyon denklemleri. Asit çözelti pH değeri; iyon, stokiyometri, titrasyon, katalizör, oksidasyon ve indirgenme. Organik bileşik ve periyodik tablo.\n",
 "biyoloji": "# 1 Hücre\nBiyoloji: hücre ve organel, doku. DNA, gen ve protein; enzim ve metabolizma. Mitoz ve mayoz, kromozom, mutasyon. Fotosentez ve solunum; evrim, ekosistem ve popülasyon.\n",
 "yer_bilimleri": "# 1 Kayaçlar\nJeoloji: magmatik, tortul ve metamorfik kayaç; mineral. Fay ve levha hareketleri, deprem ve volkan. Stratigrafi ve jeolojik zaman; fosil kayıtları.\n",
 "ziraat": "# 1 Buğday\nZiraat: toprak hazırlığı, ekim ve tohum. Sulama ve gübre; bitki koruma, zararlı ve hastalık etmeni, pestisit ilaçlama. Hasat ve verim, dekar başına üretim; sera ve çeşit seçimi.\n",
 "bilgisayar": "# 1 Döngüler\nAlgoritma ve veri yapısı; karmaşıklık. Python ve java ile yazılım; sınıf, nesne, döngü. Derleyici, veritabanı ve sql; api ve github, hata ayıklama.\n```python\nfor i in range(3):\n    print(i)\n```\n",
 "muhendislik": "# 1 Mukavemet\nMühendislik: gerilme, moment ve mukavemet hesabı. Statik ve dinamik; akışkan ve ısı transferi. Devre, akım, gerilim ve direnç; kontrol sistemi ve tolerans.\n",
 "mimarlik": "# 1 Konut\nMimarlık stüdyosu: vaziyet planı, kat planı, kesit ve görünüş. Rölöve ve restorasyon; cephe tasarımı. İmar, şehircilik ve peyzaj; maket ve mimar.\n",
 "hukuk": "# 1 Haksız fiil\n6098 sayılı Türk Borçlar Kanunu'nun 49. maddesi haksız fiili düzenler; fıkra ve bent. Yargıtay ve Danıştay içtihat; davacı ve davalı, tazminat. Mevzuat Resmî Gazete'de yayımlanır; mülga hükümler ayrılır. Sözleşme ve borçlar hukuku.\n",
 "iktisat": "# 1 Piyasa\nİktisat: arz ve talep, enflasyon ve GSYH. Faiz ve marjinal fayda; muhasebe bilanço ve gelir tablosu, hesap planı ve yevmiye. İşletme pazarlama ve finansman; ekonomi.\n",
 "ilahiyat": "# 1 Tefsir\nİlahiyat: âyet ve sure, tefsir ve fıkıh; kelam ve siyer. Hadis, sünnet ve rivayet; sahabe. Akaid, usul ve mezhep; ibadet, namaz, oruç ve zekât.\n",
 "edebiyat": "# 1 Tanzimat\nEdebiyat: şiir, roman ve hikâye; şair ve yazar. Nazım biçimleri, aruz ve hece ölçüsü; divan şiiri, Tanzimat edebiyatı ve Servet-i Fünun, edebi akım; metafor ve mazmun; tiyatro.\n",
 "felsefe": "# 1 Bilgi\nFelsefe: ontoloji ve epistemoloji; etik ve metafizik. Mantık, önerme ve akıl yürütme; varlık, bilgi kuramı ve fenomenoloji. Kant, Platon ve Aristoteles; filozof.\n",
 "sanat": "# 1 Rönesans\nSanat tarihi: ressam ve heykel, resim ve üslup; Rönesans, barok ve empresyonizm; müze. Müzik: nota, makam, armoni, beste ve besteci; tını; sanatçı.\n",
 "egitim": "# 1 Ders planı\nÖğretmen ders planı hazırlar; kazanım ve müfredat, öğretim programı. Ölçme ve değerlendirme; öğrenme kuramı ve sınıf yönetimi, rehberlik, özel eğitim. Pedagoji, Bloom taksonomisi, yapılandırmacı yaklaşım.\n",
}


def mesajlar(metin, **kw):
    s = o.denetle(metin, None, **kw)
    return " ".join(b["mesaj"] for b in s["bulgular"]), s


class GenisAlanlar(unittest.TestCase):
    def test_yirmi_uc_yeni_alan_tespiti(self):
        for alan, metin in ALAN_ORNEKLERI.items():
            with self.subTest(alan=alan):
                self.assertEqual(tespit(metin)["alan"], alan)

    def test_tip_sozcugu_yogun_hemsirelik_notu_alt_alana_gider(self):
        metin = ("# 1 Diyabet\nHasta tanı ve tedavi sürecinde ilaç dozu izlenir; hasta klinik bulgular, komplikasyon ve "
                 "kontrendikasyon açısından izlenir. Hasta anamnezi alınır. Hemşirelik tanısı konur, bakım planı yazılır, "
                 "hemşirelik girişimi uygulanır.\n")
        s = tespit(metin)
        self.assertEqual(s["alan"], "hemsirelik")
        self.assertEqual(s["tespit"]["ikinci"], "tip")

    def test_saglik_grubu_alt_alanlarda_calisir(self):
        for alan in ("hemsirelik", "eczacilik", "veteriner", "beslenme", "fizyoterapi", "acil"):
            with self.subTest(alan=alan):
                self.assertIn("tip_doz_yazimi", o.kontrol_listesi(o.profiller(), alan))
                self.assertTrue(any("Yüksek riskli" in m for m in tespit("x", alan=alan)["elle_liste"]))


class SaglikKontrolleri(unittest.TestCase):
    def test_tc_kimlik_her_alanda_hata(self):
        m, s = mesajlar(TARIH + "\nÖğrenci no 10000000146.\n")
        self.assertIn("TC kimlik", m)
        self.assertEqual(s["karar"], "yayınlanamaz")
        self.assertNotIn("TC kimlik", mesajlar(TARIH + "\nSayı 12345678901.\n")[0])   # sağlama tutmuyor

    def test_hasta_adi_ve_protokol_hata(self):
        m, s = mesajlar(TIP + "\nHasta: Ayşe Yılmaz, protokol no 458812.\n")
        self.assertIn("tanıtabilecek", m)
        self.assertEqual(s["karar"], "yayınlanamaz")
        self.assertNotIn("tanıtabilecek", mesajlar(TIP + "\n58 yaşında kadın hasta.\n")[0])

    def test_kiloya_gore_doz(self):
        self.assertIn("zaman birimi", mesajlar(TIP + "\nAmoksisilin 50 mg/kg/d verilir.\n")[0])
        self.assertNotIn("zaman birimi", mesajlar(TIP + "\nAmoksisilin 50 mg/kg/gün, iki doza bölünmüş.\n")[0])

    def test_ek_kisaltmalar(self):
        m = mesajlar(TIP + "\nB12 TIW yapılır; ilaç D/C edildi. Damla OD 2 damla.\n")[0]
        self.assertIn("TIW", m)
        self.assertIn("OD/OS/OU", m)

    def test_gebelik_kategorisi_ve_dsm(self):
        self.assertIn("gebelik kategorisi", mesajlar(TIP + "\nGebelik kategorisi: X.\n")[0])
        self.assertIn("DSM-IV", mesajlar(TIP + "\nDSM-IV ölçütleri kullanılır.\n")[0])
        self.assertNotIn("DSM-IV", mesajlar(TIP + "\nDSM-IV ile DSM-5-TR karşılaştırılır.\n")[0])

    def test_lab_birim_ve_referans(self):
        self.assertIn("iki birimle", mesajlar(TIP + "\nAçlık glukoz 126 mg/dL ya da 7 mmol/L.\n")[0])
        self.assertNotIn("iki birimle", mesajlar(TIP + "\nGlukoz 126 mg/dL = 7 mmol/L (÷ 18 dönüşüm).\n")[0])
        m = mesajlar(TIP + "\nSodyum normal değer 135-145. Potasyum normal değer 3,5-5.\n")[0]
        self.assertIn("Referans aralığı", m)

    def test_kilavuz_eski(self):
        eski = o.BU_YIL - 8
        self.assertIn("eski kılavuz", mesajlar(TIP + f"\nESC {eski} kılavuzuna göre tedavi.\n")[0])
        self.assertNotIn("eski kılavuz", mesajlar(TIP + f"\nESC {o.BU_YIL - 1} kılavuzuna göre tedavi.\n")[0])

    def test_tur_adi(self):
        self.assertIn("Tür adı", mesajlar(TIP + "\nEscherichia Coli ve E.coli idrar yolunda.\n")[0])
        self.assertNotIn("Tür adı", mesajlar(TIP + "\n*Escherichia coli* (*E. coli*) idrar yolunda.\n")[0])

    def test_veteriner_tur_ve_arinma(self):
        m = mesajlar(ALAN_ORNEKLERI["veteriner"].replace("arınma süresi ve ", "") + "\nOksitetrasiklin 10 mg/kg verilir.\nSığırda süt için 20 mg/kg.\n")[0]
        self.assertIn("Türü belirtilmemiş", m)
        self.assertIn("arınma", m)

    def test_beslenme_kalori_ve_beyan(self):
        m = mesajlar(ALAN_ORNEKLERI["beslenme"] + "\nGünde 1500 kalori. Zencefil kanseri tedavi eder.\n")[0]
        self.assertIn("kalori", m)
        self.assertIn("tedavi/önleme", m)

    def test_bakim_plani_ve_fitt(self):
        self.assertIn("aşama eksik", mesajlar("# 1\nBakım planı: hemşirelik tanısı konur.\n", alan="hemsirelik")[0])
        self.assertIn("FITT", mesajlar("# 1\nGerme egzersizi 3 kez.\n", alan="fizyoterapi")[0])
        self.assertNotIn("FITT", mesajlar(ALAN_ORNEKLERI["fizyoterapi"])[0])


class DigerAlanKontrolleri(unittest.TestCase):
    def test_si_birim_ve_bosluk(self):
        m = mesajlar(ALAN_ORNEKLERI["fizik"] + "\nKütle 5 Kg, yol 3 Km. Kuvvet 10N ve 5kg yük.\n")[0]
        self.assertIn("Birim sembolü", m)
        self.assertIn("bitişik", m)

    def test_lab_guvenlik(self):
        self.assertIn("güvenlik notu", mesajlar(ALAN_ORNEKLERI["kimya"] + "\nDeney: derişik HCl ısıtılır.\n")[0])
        self.assertNotIn("güvenlik notu", mesajlar(ALAN_ORNEKLERI["kimya"] + "\nDeney: derişik HCl çeker ocakta, gözlük ve eldivenle.\n")[0])

    def test_p_degeri(self):
        self.assertIn("p değeri", mesajlar(ALAN_ORNEKLERI["istatistik"] + "\nSonuç p = 0.000 bulundu.\n")[0])
        self.assertNotIn("p değeri 0,000", mesajlar(ALAN_ORNEKLERI["istatistik"] + "\nSonuç p < .001 bulundu.\n")[0])

    def test_kod_ornegi(self):
        m = mesajlar("# 1\nDöngü.\n```\nprint \"merhaba\"\n```\n```\nx = 1\n```\n", alan="bilgisayar")[0]
        for parca in ("Dil etiketi", "Python 2", "sürümü"):
            self.assertIn(parca, m)
        self.assertIn("99 karakter", mesajlar("# 1\n```python\n" + "x = " + "1" * 120 + "\n```\n", alan="bilgisayar")[0])

    def test_hukuk_mulga(self):
        m, s = mesajlar(ALAN_ORNEKLERI["hukuk"].replace("mülga hükümler ayrılır", "") + "\n818 sayılı Borçlar Kanunu uygulanır.\n")
        self.assertEqual(s["karar"], "yayınlanamaz")
        m2, s2 = mesajlar(ALAN_ORNEKLERI["hukuk"].replace("mülga hükümler ayrılır", "") + "\n765 sayılı Kanun uygulanır.\n")
        self.assertIn("Yürürlükten kalkmış", m2)
        self.assertEqual(s2["karar"], "yayınlanabilir")                   # 765: kaynakta açılamadı → UYARI
        self.assertNotIn("Yürürlükten kalkmış", mesajlar(ALAN_ORNEKLERI["hukuk"] + "\n818 sayılı mülga Kanun ile karşılaştır.\n")[0])

    def test_hukuk_kunye_ve_numara(self):
        m = mesajlar("# 1\nTürk Medeni Kanunu ve Türk Ticaret Kanunu. Yargıtay kararı ile içtihat oluştu.\n", alan="hukuk")[0]
        self.assertIn("numarasız", m)
        self.assertIn("künyesiz", m)
        self.assertNotIn("künyesiz", mesajlar("# 1\nYargıtay 4. HD kararı (E. 2019/1, K. 2020/2).\n", alan="hukuk")[0])

    def test_ilahiyat_kaynak(self):
        m = mesajlar("# 1\nPeygamber şöyle buyurdu: kolaylaştırın. Âyette \"Allah sabredenlerle beraberdir\" denir.\n", alan="ilahiyat")[0]
        self.assertIn("Hadis kaynaksız", m)
        self.assertIn("numarasız", m)
        temiz = mesajlar("# 1\nŞöyle buyurdu: kolaylaştırın (Buhârî, İlim, 11). Âyette \"Allah sabredenlerle beraberdir\" (Bakara 2/153).\n", alan="ilahiyat")[0]
        self.assertNotIn("Hadis kaynaksız", temiz)

    def test_alinti_eser_ve_olcek(self):
        uzun = "\"" + "Bu cümle uzun bir doğrudan alıntıdır ve kaynağı yazılmamıştır, okur nereden geldiğini bilemez." + "\""
        self.assertIn("Doğrudan alıntı", mesajlar(f"# 1\n{uzun} Sonra.\n{uzun} Yine.\n", alan="edebiyat")[0])
        self.assertIn("künye eksik", mesajlar("# 1\n![Mona Lisa](a.png)\n![Gece](b.png)\n", alan="sanat")[0])
        self.assertIn("ölçek yok", mesajlar("# 1\nZemin kat planı.\n![Plan](p.png)\n", alan="mimarlik")[0])
        self.assertNotIn("ölçek yok", mesajlar("# 1\nZemin kat planı, ölçek 1:100.\n![Plan](p.png)\n", alan="mimarlik")[0])


if __name__ == "__main__":
    unittest.main(verbosity=1)
