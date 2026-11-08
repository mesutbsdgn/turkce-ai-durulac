"""Kenar durum ve özellik tabanlı testler: tarama.py (kalıp taraması) ve
okunabilirlik.py (Ateşman / Bezirci-Yılmaz).

Yalnız standart kütüphane + pytest. Ağ yok, model çağrısı yok. Kaynak dosyalar
DEĞİŞTİRİLMEZ; bu test dosyası yalnızca gözlenen davranışı yoklar.

Kaynak okuması (girdi/çıktı biçimleri):
  tarama.py
    - tara(metin, kurallar) -> [(satır, sütun, kalıp_no, ad, alıntı, öneri), ...]
      satır 1 tabanlı, sütun dizi içinde 1 tabanlı (tarama.py:182-189).
    - temizle(metin) -> satır listesi; kod çiti/satır içi kod/URL/bağlantı
      hedefi/HTML/tablo ayraç satırları boşlukla örtülür (tarama.py:85-101).
    - derle() -> KURALLAR (re.IGNORECASE) + sözlük kuralları (tarama.py:140-143).
    - uzun_cumleler(satirlar, esik=35): >esik sözcüklü cümle (tarama.py:146-155).
    - main(arg) -> 0 bulgu olsa da 0; kullanım hatası 2 (tarama.py:209-259).
  okunabilirlik.py
    - olc(metin) -> {"cumle","sozcuk","ort_sozcuk","ort_hece","atesman","by"}.
    - hece(sozcuk): ünlü sayısı, en az 1 (okunabilirlik.py:55-56).
    - cumleler(metin): kısaltma/sıra sayısı birleştirme (okunabilirlik.py:65-75).
    - main(arg) -> 0 tamam / 1 sayı koruma sorunu / 2 kullanım hatası.
"""
import io
import pathlib
import sys
import time
import unicodedata

import pytest

KOK = pathlib.Path(__file__).resolve().parent.parent
if str(KOK) not in sys.path:
    sys.path.insert(0, str(KOK))

import okunabilirlik as ok  # noqa: E402
import tarama as tr  # noqa: E402


@pytest.fixture(autouse=True)
def _cekirdek_kurallar(monkeypatch, request):
    """Testler yalnız yerleşik KURALLAR'ı sınar (sözlük bağımsız, hermetik).

    Sözlük (references/degistirme-sozlugu.md) ayrı ve gerçek düzende test edilir:
    test_varsayilan_sozluk_yolu_kurallari_yukler.
    """
    if request.node.name != "test_varsayilan_sozluk_yolu_kurallari_yukler":
        monkeypatch.setattr(tr, "SOZLUK", "/olmayan/degistirme-sozlugu.md")


# --------------------------------------------------------------------- yardımcılar
def _tara(metin, ingilizce=False):
    return tr.tara(metin, tr.derle(ingilizce))


def _tarama_main(argv, capsys, monkeypatch=None, stdin=None):
    if stdin is not None:
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    kod = tr.main(argv)
    kap = capsys.readouterr()
    return kod, kap.out, kap.err


def _ok_main(argv, capsys, monkeypatch=None, stdin=None):
    if stdin is not None:
        monkeypatch.setattr(sys, "stdin", io.StringIO(stdin))
    kod = ok.main(argv)
    kap = capsys.readouterr()
    return kod, kap.out, kap.err


def _dosya(tmp_path, ad, icerik, encoding="utf-8"):
    p = tmp_path / ad
    p.write_text(icerik, encoding=encoding)
    return p


# =========================================================== A. Türkçe büyük/küçük harf
def test_kucult_noktali_I_i_olur():
    assert tr.kucult("İSTANBUL") == "istanbul"


def test_kucult_noktasiz_I_noktasiz_i_olur():
    assert tr.kucult("ISPARTA") == "ısparta"
    assert tr.kucult("İI") == "iı"


def test_kucult_str_lower_tuzagini_asar():
    # str.lower(): 'İ'.lower() -> 'i' + U+0307 (birleşik nokta) üretir; kucult değil.
    assert "İ".lower() != "i"
    assert tr.kucult("İ").lower() == "i"
    assert len("İ".lower()) == 2


def test_regex_ignorecase_turkce_buyuk_harfi_yakalar():
    # KURALLAR re.IGNORECASE ile derlenir; Türkçe büyük harf de yakalanmalı.
    for metin, no in [("ŞEKİLDE yaptım", 35), ("TARAFINDAN geldi", 15),
                      ("GERÇEKLEŞTİRMEK istiyorum", 33)]:
        nolar = [f[2] for f in _tara(metin)]
        assert no in nolar, (metin, nolar)


def test_kucult_resmi_tur_kapisi_buyuk_harfle():
    assert tr.kucult("RESMÎ") == "resmî"
    assert tr.kucult("Akademik") in tr.KORUMALI


# ==================================================== B. birleşik/ayrık Unicode (ş ç ğ ö ü)
def test_ayrik_ve_birlesik_unicode_farkli():
    assert unicodedata.normalize("NFC", "s\u0327") == "ş"
    assert unicodedata.normalize("NFD", "ş") == "s\u0327"
    assert unicodedata.normalize("NFD", "ş") != "ş"


def test_ayrik_sekil_kaliclar_tanmaz_bilinen_sinir():
    # Normalizasyon yapılmaz: "şekilde" kalıbı ayrık yazımla eşleşmez (bilinen sınır).
    ayrik = "s\u0327ekilde yaptım"
    assert _tara(ayrik) == []
    assert [f[2] for f in _tara("şekilde yaptım")] == [35]


def test_ayrik_sekil_sozcuk_boler():
    # SOZCUK harf sınıfı birleşik karakterleri içermez: ayrık "ş" kelimeyi böler.
    assert ok.SOZCUK.findall("s\u0327ehir") == ["s", "ehir"]
    assert ok.SOZCUK.findall("şehir") == ["şehir"]


def test_birlesik_olmayan_turkce_harfler_normal():
    # str.lower() "İ" için birleşik nokta üretir; kucult() Türkçe doğru küçültür.
    for h in "şçğıöüŞÇĞİÖÜ":
        kelime = h + "abc"
        kv = tr.kucult(kelime)
        assert ok.SOZCUK.findall(kv) == [kv], (kelime, kv)


# ============================================ C. boş / boşluk / tek kelime / çok uzun
def test_tara_bos_metin_bulgu_yok():
    assert _tara("") == []
    assert _tara("", ingilizce=True) == []


def test_tara_yalniz_bosluk_bulgu_yok():
    assert _tara("   \n\t\n  ") == []


def test_tara_tek_kelime_bulgu_var():
    assert _tara("tarafından") == [(1, 1, 15, "tarafından", "tarafından",
                                    "edilgeni çöz, faili öne al")]


def test_tara_cok_uzun_tek_satir_kokmaz():
    bulgu = _tara("tarafından " + "x" * 100000)
    assert len(bulgu) == 1 and bulgu[0][2] == 15


def test_olc_bos_metin_none():
    assert ok.olc("")["atesman"] is None
    assert ok.olc("   ")["atesman"] is None


def test_olc_yalniz_sayi_sozcuk_saymaz():
    r = ok.olc("123 456 789")
    assert r["sozcuk"] == 0 and r["atesman"] is None


def test_tara_200kb_metin_sure_siniri():
    metin = "Bu iş tarafından yapıldı ve/veya sağlanmaktadır. " * 4800
    assert len(metin.encode("utf-8")) > 200_000
    bas = time.monotonic()
    bulgu = _tara(metin)
    sure = time.monotonic() - bas
    assert sure < 5.0, f"tarama 200 KB için {sure:.2f}s"
    assert bulgu


def test_olc_cok_uzun_metin_sure_siniri():
    metin = "Bu güzel bir cümledir ve anlaşılırdır. " * 6000
    assert len(metin.encode("utf-8")) > 200_000
    bas = time.monotonic()
    r = ok.olc(metin)
    sure = time.monotonic() - bas
    assert sure < 5.0, f"okunabilirlik 200 KB için {sure:.2f}s"
    assert r["cumle"] == 6000


# ======================================================= D. sayı / tarih / yüzde
def test_tara_iso_tarih_düzyazıda():
    bulgu = _tara("Toplantı 2026-10-18 günü yapıldı.")
    assert any(f[2] == 38 and f[3] == "ISO tarih düzyazıda" for f in bulgu)


def test_tara_binlik_ayirici_virgul():
    bulgu = _tara("Sonuç 1,000 kişiye ulaştı.")
    assert any(f[3] == "binlik ayırıcı virgül" and f[4] == "1,000" for f in bulgu)


def test_tara_ondalik_nokta_yuzde():
    for metin, alinti in [("%4.5 artış", "%4.5"), ("5.5% oran", "5.5%")]:
        assert any(f[3] == "ondalık nokta (yüzde)" and f[4] == alinti
                   for f in _tara(metin)), metin


def test_tara_turkce_binlik_nokta_temiz():
    assert _tara("Bütçe 1.500.000 TL oldu.") == []


def test_sayi_regex_birim_ve_olcek_yakalar():
    degerler = ok.SAYI.findall(
        "Fiyat 1.250,00 TL, %4,25 artış, tarih 18.10.2026, 1,5 milyon TL, -$3.5")
    assert "1.250,00 TL" in degerler
    assert "%4,25" in degerler
    assert "18.10.2026" in degerler
    assert "1,5 milyon TL" in degerler


def test_sayi_koruma_tamam_kod_0(tmp_path, capsys):
    a = _dosya(tmp_path, "a.txt", "Fiyat 1.250,00 TL idi.")
    b = _dosya(tmp_path, "b.txt", "Fiyat yine 1.250,00 TL idi.")
    kod, out, _ = _ok_main([str(a), str(b)], capsys)
    assert kod == 0
    assert "Sayı koruma: tamam" in out


def test_sayi_koruma_kayip_kod_1(tmp_path, capsys):
    a = _dosya(tmp_path, "a.txt", "Fiyat 1.250,00 TL idi.")
    b = _dosya(tmp_path, "b.txt", "Fiyat 1.250 TL idi.")
    kod, out, _ = _ok_main([str(a), str(b)], capsys)
    assert kod == 1
    assert "Sayı koruma: SORUN" in out
    assert "kayboldu/değişti" in out


def test_sayi_koruma_olcek_degisimi_yakalanir(tmp_path, capsys):
    a = _dosya(tmp_path, "a.txt", "Gelir 1,5 milyon TL oldu.")
    b = _dosya(tmp_path, "b.txt", "Gelir 1,5 TL oldu.")
    kod, out, _ = _ok_main([str(a), str(b)], capsys)
    assert kod == 1
    assert "yeni çıktı" in out


def test_sayi_koruma_bicim_farki_yakalanir(tmp_path, capsys):
    a = _dosya(tmp_path, "a.txt", "Tutar 1.250,00 TL.")
    b = _dosya(tmp_path, "b.txt", "Tutar 1.250 TL.")
    kod, _out, _ = _ok_main([str(a), str(b)], capsys)
    assert kod == 1


def test_normal_isaret_ve_bosluk_sadeleştirir():
    assert ok.normal("  1.250,00 ") == "1.250,00"
    assert ok.normal("−5") == "-5"


# ======================================================= E. noktalama / tırnak türleri
@pytest.mark.parametrize("tirnak", ["“tarafından”", "«tarafından»", "'tarafından'",
                                    '"tarafından"', "‘tarafından’"])
def test_tara_tirnak_turlerinde_kalip_bulunur(tirnak):
    assert any(f[2] == 15 for f in _tara(tirnak)), tirnak


def test_olc_tirnak_cumleyi_bolmez():
    assert ok.cumleler("«Merhaba dedi.» Sonra gitti.") == ["«Merhaba dedi.» Sonra gitti."]


def test_olc_kivircik_tirnak_cumleyi_bolmez():
    assert ok.cumleler("“Merhaba dedi.” Sonra gitti.") == ["“Merhaba dedi.” Sonra gitti."]


def test_olc_apostrof_tek_sozcuk():
    assert ok.SOZCUK.findall("Türkiye'nin başkenti Ankara'dır.") == \
        ["Türkiye'nin", "başkenti", "Ankara'dır"]


# =========================================================== F. satır sonu varyantları
def test_tara_crlf_satiri_dogru_bildirir():
    bulgu = _tara("Birinci satır.\r\nBu iş tarafından yapıldı.\r\n")
    assert bulgu == [(2, 7, 15, "tarafından", "tarafından", "edilgeni çöz, faili öne al")]


def test_tara_lf_ve_crlf_ayni_satir_no():
    lf = _tara("a\nb\ntarafından\n")
    crlf = _tara("a\r\nb\r\ntarafından\r\n")
    assert [f[0] for f in lf] == [f[0] for f in crlf] == [3]


def test_temizle_satir_sayisi_ve_sutun_korunur():
    metin = "para `kod` devam\nhttp://x.y a\n"
    satirlar = tr.temizle(metin)
    assert len(satirlar) == len(metin.split("\n"))
    assert len(satirlar[0]) == len(metin.split("\n")[0])
    assert len(satirlar[1]) == len(metin.split("\n")[1])


# ==================================================================== G. emoji
def test_tara_emoji_kalicları_etkilemez():
    bulgu = _tara("Merhaba 😀 dünya 🌍 tarafından yapıldı.")
    assert [f[2] for f in bulgu] == [15]


def test_olc_emoji_sozcuk_saymaz():
    r = ok.olc("Merhaba 😀 dünya 🌍 güzel.")
    assert r["sozcuk"] == 3 and r["cumle"] == 1


# ============================================================ H. ikili benzeri girdi
def test_tara_kontrol_karakterleri_kokmaz():
    bulgu = _tara("veri\x00\x01\x02 tarafından işlendi.")
    assert [f[2] for f in bulgu] == [15]


def test_olc_kontrol_karakterleri_kokmaz():
    r = ok.olc("veri\x00\x01 tarafından işlendi.")
    assert r["sozcuk"] == 3


# ============================================================ I. determinizm
def test_tara_deterministik():
    metin = "Bu iş tarafından yapıldı.\n\nAyrıca bir.\n\nAyrıca iki.\n\nAyrıca üç."
    assert _tara(metin) == _tara(metin)
    assert _tara(metin, True) == _tara(metin, True)


def test_olc_deterministik():
    metin = "Kitap okumak güzel bir alışkanlıktır. Her gün biraz okumak gerekir."
    assert ok.olc(metin) == ok.olc(metin)


def test_tarama_main_cikti_deterministik(tmp_path, capsys):
    f = _dosya(tmp_path, "m.md", "Bu iş tarafından yapıldı.\n")
    ilk = _tarama_main([str(f)], capsys)
    ikinci = _tarama_main([str(f)], capsys)
    assert ilk == ikinci


# ================================================ J. skor aralıkları ve monotonluk
def test_atesman_duzey_sinirlari():
    assert ok.atesman_duzey(95) == "çok kolay"
    assert ok.atesman_duzey(90) == "çok kolay"
    assert ok.atesman_duzey(80) == "kolay"
    assert ok.atesman_duzey(60) == "orta"
    assert ok.atesman_duzey(40) == "zor"
    assert ok.atesman_duzey(10) == "çok zor"


def test_atesman_olcek_disi():
    assert "ölçek dışı" in ok.atesman_duzey(101)
    assert "ölçek dışı" in ok.atesman_duzey(-1)


def test_by_duzey_sinirlari():
    assert ok.by_duzey(8) == "ilköğretim"
    assert ok.by_duzey(9) == "lise"
    assert ok.by_duzey(13) == "lisans"
    assert ok.by_duzey(17) == "akademik"


def test_atesman_formulu_birebir():
    metin = "Ali ata bak. Ali ata bak."
    r = ok.olc(metin)
    beklenen = 198.825 - 40.175 * r["ort_hece"] - 2.610 * (r["sozcuk"] / r["cumle"])
    assert r["atesman"] == pytest.approx(beklenen)
    assert r["cumle"] == 2 and r["sozcuk"] == 6


def test_by_formulu_birebir():
    metin = "Küçük çocuk parkta oynadı. Annesi onu çağırdı. Eve birlikte döndüler."
    r = ok.olc(metin)
    # BY = sqrt(OKS * (H3*0,84 + H4*1,5 + H5*3,5 + H6*26,25)); burada heceler <=3.
    assert r["by"] == pytest.approx(2.2, abs=0.2)
    assert r["by"] >= 0


def test_monoton_daha_uzun_karmasik_cumle_daha_zor():
    basit = "Ali geldi. Ayşe gitti. O güldü. Herkes mutlu oldu."
    karmasik = ("Uluslararasılaştırma süreçlerinin karmaşıklığı, kurumsallaşmanın "
                "gerektirdiği yapısal dönüşümlerle birlikte değerlendirildiğinde, "
                "sürdürülebilirlik açısından çok boyutlu bir çerçeve sunmaktadır.")
    a, b = ok.olc(basit), ok.olc(karmasik)
    assert a["atesman"] > b["atesman"]  # daha uzun/karmaşık -> daha düşük Ateşman
    assert a["by"] < b["by"]            # daha uzun sözcükler -> daha yüksek BY


def test_kategoriler_ornek_metinlerde():
    assert ok.atesman_duzey(
        ok.olc("Küçük çocuk parkta oynadı. Annesi onu çağırdı. Eve birlikte döndüler.")["atesman"]
    ) == "kolay"
    assert ok.atesman_duzey(
        ok.olc("Kurumun yönetim kurulu, mali tabloları değerlendirerek gelecek yıla "
               "ilişkin stratejik planlamayı onayladı.")["atesman"]
    ) == "zor"


# ============================================================ K. hece sayımı
@pytest.mark.parametrize("kelime,beklenen", [("kitap", 2), ("araba", 3), ("Türkçe", 2),
                                             ("merhaba", 3), ("İSTANBUL", 3), ("ağaç", 2)])
def test_hece_bilinen_kelimeler(kelime, beklenen):
    assert ok.hece(kelime) == beklenen


def test_hece_unsuz_kelime_en_az_bir():
    assert ok.hece("krk") == 1
    assert ok.hece("") == 1


def test_hece_uzun_kelime():
    assert ok.hece("uluslararasılaştırma") == 9


# ==================================================== L. tarama özellik/CLI
def test_temizle_kod_citi_icini_ortar():
    assert _tara("```\ntarafından\n```") == []


def test_temizle_satir_ici_kod_taranmaz():
    assert _tara("Bu `tarafından` kod.") == []
    assert _tara("Bu tarafından kod.") != []


def test_temizle_url_html_link_taranmaz():
    # URL/HTML/bağlantı hedefi örtülür; kalan düzyazıda kalıp varsa bulunur.
    assert _tara("https://tarafından.example/a tarafından") != []
    assert all(f[2] == 15 for f in _tara("https://x.y/z"))


def test_temizle_tablo_ayrac_atlanir_hucre_taranir():
    metin = "| Kalıp | Açıklama |\n|---|---|\n| bu | tarafından yapıldı |\nRet tarafından geldi."
    bulgu = _tara(metin)
    assert [f[0] for f in bulgu] == [3, 4]


def test_uzun_cumle_esik_35_sinir():
    w35 = " ".join(["kelime"] * 35) + "."
    w36 = " ".join(["kelime"] * 36) + "."
    assert tr.uzun_cumleler(tr.temizle(w35)) == []
    bulgu = tr.uzun_cumleler(tr.temizle(w36))
    assert len(bulgu) == 1 and bulgu[0][3] == "uzun cümle (36 sözcük)"


def test_uzun_cumle_baslik_satiri_atlanir():
    assert tr.uzun_cumleler(tr.temizle("# " + " ".join(["k"] * 40))) == []


def test_sahis_karisimi_biz_ve_yazar():
    bulgu = tr.sahis_karisimi(tr.temizle("Biz projeyi geliştirdik. Yazar anlatıyor."))
    assert len(bulgu) == 1 and bulgu[0][2] == 60


def test_sahis_karisimi_tek_kisi_yok():
    assert tr.sahis_karisimi(tr.temizle("Biz projeyi geliştirdik.")) == []


def test_ayni_baglac_esik_3():
    p = "Ayrıca bir.\n\nAyrıca iki.\n\nAyrıca üç."
    assert len(tr.ayni_baglac(p)) == 1


def test_ayni_baglac_2_yetmez():
    assert tr.ayni_baglac("Ayrıca bir.\n\nAyrıca iki.") == []


def test_ozet_sayilari_etiketleri():
    bulgu = [(1, 1, 0, "sözlük: talep etmek", "x", "y"),
             (1, 1, 0, "sözlük: etki etmek", "x", "y"),
             (2, 1, 36, "uzun cümle (40 sözcük)", "x", "y"),
             (3, 1, 15, "tarafından", "x", "y")]
    sy = tr.ozet_sayilari(bulgu)
    assert sy[(0, "sözlük eşlemesi")] == 2
    assert sy[(36, "uzun cümle")] == 1           # "(N sözcük)" kırpılır
    assert sy[(15, "tarafından")] == 1


@pytest.mark.parametrize("tur", ["resmi", "resmî", "akademik", "hukuk"])
def test_tur_kapisi_taramayi_durdurur(tmp_path, capsys, tur):
    f = _dosya(tmp_path, "m.md", "tarafından\n")
    kod, out, _ = _tarama_main(["--tur", tur, str(f)], capsys)
    assert kod == 0 and "kalıp taraması devre dışı" in out


def test_tur_kapisi_buyuk_harf_normalize(tmp_path, capsys):
    f = _dosya(tmp_path, "m.md", "tarafından\n")
    kod, out, _ = _tarama_main(["--tur", "AKADEMİK", str(f)], capsys)
    assert kod == 0 and "akademik" in out


def test_tarama_main_cikis_kodu_bulgu_varken_0(tmp_path, capsys):
    f = _dosya(tmp_path, "m.md", "tarafından\n")
    kod, out, _ = _tarama_main([str(f)], capsys)
    assert kod == 0 and "Toplam 1 bulgu" in out


def test_tarama_main_bilinmeyen_secenek_kod_2(capsys):
    kod, _out, err = _tarama_main(["--zzz"], capsys)
    assert kod == 2 and "bilinmeyen seçenek" in err


def test_tarama_main_dosya_yok_kod_2(capsys):
    kod, _out, err = _tarama_main(["yok_dosya.md"], capsys)
    assert kod == 2 and "dosya bulunamadı" in err


def test_tarama_main_ozet_yalniz_ozet(tmp_path, capsys):
    f = _dosya(tmp_path, "m.md", "tarafından\n")
    kod, out, _ = _tarama_main([str(f), "--ozet"], capsys)
    assert kod == 0 and "Toplam 1 bulgu" in out and "[kalıp" not in out


def test_tarama_main_onceki_karsilastirma(tmp_path, capsys):
    eski = _dosya(tmp_path, "e.md", "Bu iş yapıldı.\n")
    yeni = _dosya(tmp_path, "y.md", "Bu iş tarafından yapıldı.\n")
    kod, out, _ = _tarama_main([str(yeni), "--onceki", str(eski)], capsys)
    assert kod == 0
    assert "önce → sonra" in out and "TOPLAM" in out
    assert "YENİ SORUN" in out


def test_tarama_main_stdin(capsys, monkeypatch):
    kod, out, _ = _tarama_main(["-"], capsys, monkeypatch, stdin="Bu tarafından yapıldı.")
    assert kod == 0 and "Toplam 1 bulgu" in out


def test_tarama_main_help_kod_0(capsys):
    kod, out, _ = _tarama_main(["--help"], capsys)
    assert kod == 0 and "Kullanım" in out


def test_tarama_main_bos_arg_kod_2(capsys):
    kod, _out, _err = _tarama_main([], capsys)
    assert kod == 2


def test_okunabilirlik_main_bilinmeyen_secenek_kod_2(capsys):
    kod, _out, err = _ok_main(["--bad"], capsys)
    assert kod == 2 and "bilinmeyen seçenek" in err


def test_okunabilirlik_main_arg_sayisi_kod_2(capsys):
    kod, _out, _err = _ok_main([], capsys)
    assert kod == 2
    kod2, _out2, _err2 = _ok_main(["x", "y", "z"], capsys)
    assert kod2 == 2


def test_okunabilirlik_main_stdin(capsys, monkeypatch):
    kod, out, _ = _ok_main(["-"], capsys, monkeypatch, stdin="Merhaba dünya.")
    assert kod == 0 and out.startswith("Metin: 1 cümle")


def test_okunabilirlik_main_tek_dosya_tur_etiketi(tmp_path, capsys):
    f = _dosya(tmp_path, "m.txt", "Merhaba dünya. Bu ikinci cümle. Üçüncü cümle bu.")
    kod, out, _ = _ok_main([str(f)], capsys)
    assert kod == 0
    assert "Metin: 3 cümle" in out and "Ateşman" in out and "Bezirci-Yılmaz" in out


# ============================================================ M. sözlük yükleme
def test_sozluk_kurallari_gecici_dosyadan(tmp_path, monkeypatch):
    yol = _dosya(tmp_path, "s.md",
                 "## Yardımcı fiil şişmesi\n- `talep etmek` → `istemek`\n"
                 "## İngilizce terim\n- `worker` → `alt ajan`\n")
    monkeypatch.setattr(tr, "SOZLUK", str(yol))
    varsayilan = {ad for _, ad, _, _ in tr.sozluk_kurallari()}
    assert "sözlük: talep etmek" in varsayilan
    assert "sözlük: worker" not in varsayilan          # İngilizce terim varsayılan kapalı
    acik = {ad for _, ad, _, _ in tr.sozluk_kurallari(True)}
    assert "sözlük: worker" in acik


def test_sozluk_bulgu_kalic_no_sifir(tmp_path, monkeypatch):
    yol = _dosya(tmp_path, "s.md", "## Yardımcı fiil şişmesi\n- `talep etmek` → `istemek`\n")
    monkeypatch.setattr(tr, "SOZLUK", str(yol))
    bulgu = tr.tara("Bu işi talep etmek istiyorum.", tr.sozluk_kurallari())
    assert bulgu and bulgu[0][2] == 0 and bulgu[0][3] == "sözlük: talep etmek"


def test_varsayilan_sozluk_yolu_kurallari_yukler():
    assert tr.SOZLUK.endswith("degistirme-sozlugu.md")
    assert tr.sozluk_kurallari() != []