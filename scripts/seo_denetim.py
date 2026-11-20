#!/usr/bin/env python3
"""Durulaç `+seo` denetimi: bir metnin SEO kontrol listesini çıkarır (yalnız standart kütüphane, ağ yok).

Bu bir KARAR değil kontrol listesidir. SEO önerisi anlamı bozuyor, bilgi uyduruyor ya da
registerı saptırıyorsa uygulanmaz; Durulaç ilkeleri SEO'nun önündedir. Google resmî karakter
sınırı ya da anahtar sözcük yoğunluğu hedefi yayımlamaz; 60/155 gibi eşikler sektör sezgisidir.

Kullanım:
  python3 seo_denetim.py metin.md --anahtar "ana sorgu" [--ikincil "a,b"] \\
      [--baslik "Title"] [--aciklama "Meta"] [--slug "url-slug"] [--onceki once.md] [--json]
Seçenekler:
  --anahtar TERİM     ana sorgu (anahtar sözcük); verilmezse sorguya bağlı kurallar atlanır
  --ikincil "a,b"     ikincil terimler (yalnız ölçüm olarak raporlanır)
  --baslik METİN      title önerisi/mevcut title (S06, S15, S19)
  --aciklama METİN    meta açıklama (S07, S19)
  --slug METİN        mevcut URL slug'ı (S12)
  --onceki DOSYA      önceki sürüm; her kod için önce → sonra sayısı
  --json              bulguları ve ölçümleri JSON ver
Çıkış kodu: 0 hata yok, 1 en az bir `hata`, 2 kullanım hatası.
Markdown tanınır: ``` kod çitleri ve tek/çift ters tırnaklı `satır içi kod` taranmaz
(tarama.temizle ile aynı yaklaşım, çift ters tırnak burada ayrıca maskelenir);
başlıklar (#), görseller (![alt](url)) ve bağlantılar ([çapa](url)) ayrıca çözümlenir.
"""
from __future__ import annotations

import json
import os
import re
import sys
import unicodedata

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tarama import kucult, temizle  # noqa: E402

# Kasten bozma düğmesi: False yapılınca yalnız tam sözcük eşleşir, ek toleransı kapanır.
EK_TOLERANSI = True
AZAMI_EK = 6
KISA_SOZCUK = 4
AZAMI_EK_BICIMI = 3
AZAMI_EK_KISA = 9   # kısa sözcükte ek, morfemlere bölünebildiği sürece daha uzun olabilir (botlarımız)
EK_SINIFLARI = {
    "lar": 1, "ler": 1,
    "i": 2, "u": 2, "yi": 2, "yu": 2, "si": 2, "su": 2, "ni": 2, "nu": 2,
    "m": 2, "n": 2, "k": 2, "im": 2, "um": 2, "iz": 2, "uz": 2, "in": 2, "un": 2,
    "nin": 2, "nun": 2,
    "imiz": 2, "umuz": 2, "iniz": 2, "unuz": 2, "miz": 2, "muz": 2, "niz": 2, "nuz": 2,
    "a": 3, "e": 3, "ya": 3, "ye": 3, "na": 3, "ne": 3,
    "da": 3, "de": 3, "ta": 3, "te": 3,
    "dan": 3, "den": 3, "tan": 3, "ten": 3,
    "la": 3, "le": 3, "yla": 3, "yle": 3,
    "li": 4, "lu": 4, "siz": 4, "suz": 4, "ci": 4, "cu": 4, "ca": 4, "ce": 4,
    "ki": 4, "dir": 4, "dur": 4, "tir": 4, "tur": 4, "sin": 4,
}
YUMUSAMA = {"p": "b", "c": "c", "t": "d", "k": "g"}
UNLULER = set("aeiou")
AKSAN = str.maketrans("ışçğöüâîû", "iscgouaiu")
TURKCE_HARF = set("çğıöşüâîû")

TITLE_UST, TITLE_ALT = 60, 25
META_UST, META_ALT = 160, 70
ALT_UST = 155
SLUG_UST = 75
ICERIK_ESIK = 300
PARAGRAF_ESIK = 150
YOGUNLUK_ESIK = 3.0
YOGUNLUK_EN_AZ_SOZCUK = 200   # bunun altında S04 uyarı değil bilgi
SSS_ALT, SSS_UST = 25, 80
AZAMI_ARA_SOZCUK = 3

NOT = ("Not: SEO önerileri kontrol listesidir; Google resmî karakter sınırı ya da "
       "yoğunluk hedefi yayımlamaz.")

DURAK = {"ve", "bir", "bu", "da", "de", "ki", "ile", "icin", "gibi", "daha", "cok", "en",
         "her", "ama", "veya", "ya", "mi", "mu", "ne", "olan", "olarak", "kadar", "sonra",
         "once", "su", "o", "the", "and", "for", "with"}

ANLAMSIZ_CAPA = {"buraya tiklayin", "tiklayin", "bu baglanti", "devami", "link",
                 "buraya tikla", "tikla"}
ALT_BASLANGIC = {"gorsel", "resim", "fotograf", "image"}

BASLIK = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
TABLO_AYRAC = re.compile(r"^\s*\|?[\s:\-|]+\|?\s*$")
LISTE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
GORSEL = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)")
BAGLANTI = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)]*)\)")
SAYI = re.compile(r"\d+(?:[.,]\d+)*")
TEKRAR_ESIK = 8   # S20: en az bu kadar sözcüklük cümle iki kez geçerse
TOKEN = re.compile(r"[a-z]+|\d+(?:[.,]\d+)*")
RAW_TOKEN = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+")

KISALTMA = {"dr", "prof", "doc", "av", "sn", "vb", "vs", "orn", "bkz"}
GERCEK_CIFTLER = {
    frozenset(("ılık", "ilik")),
    frozenset(("kır", "kir")),
    frozenset(("sınır", "sinir")),
    frozenset(("ısı", "isi")),
    frozenset(("kaşar", "kasar")),
}


def nfc(s: str | None) -> str | None:
    """Unicode'u NFC'ye çevirir: ayrıştırılmış Türkçe harfler tek kod noktasına gelir."""
    return unicodedata.normalize("NFC", s) if s is not None else None


def katla(s: str) -> str:
    """Harf katlama (İ→i, I→ı, küçük harf) + aksan katlama; yalnız karşılaştırma için."""
    return kucult(s).translate(AKSAN)


def _stemler(kelime: str) -> list[str]:
    """Sözcük, yumuşama (p→b, ç→c, t→d, k→ğ) ve son ünlü düşmesi varyantları (uzundan kısaya)."""
    stemler = {kelime}
    if kelime and kelime[-1] in YUMUSAMA:
        stemler.add(kelime[:-1] + YUMUSAMA[kelime[-1]])
    if len(kelime) >= KISA_SOZCUK:
        for i in range(len(kelime) - 1, -1, -1):
            if kelime[i] in UNLULER:
                dusen = kelime[:i] + kelime[i + 1:]
                if len(dusen) >= 3:
                    stemler.add(dusen)
                break
    return sorted(stemler, key=len, reverse=True)


def _ek_bolunur(ek: str, konum: int = 0, adet: int = 0, sinif: int = 0) -> bool:
    """Ek, Türkçe ek biçimlerinden en çok 3 tanesine sırayı bozmadan bölünebiliyor mu."""
    if konum == len(ek):
        return adet > 0
    if adet >= AZAMI_EK_BICIMI:
        return False
    for uzunluk in (4, 3, 2, 1):
        parca = ek[konum:konum + uzunluk]
        yeni_sinif = EK_SINIFLARI.get(parca)
        if yeni_sinif is None or yeni_sinif < sinif:
            continue
        if _ek_bolunur(ek, konum + uzunluk, adet + 1, yeni_sinif):
            return True
    return False


def _eslesir(token: str, kelime: str) -> bool:
    """Sözcük başı + ek toleransı: kelime ya da kelime + en çok 6 harflik ek."""
    kelime = katla(kelime)
    if token[:1].isdigit() or kelime[:1].isdigit():
        return token == kelime
    for stem in _stemler(kelime):
        if token == stem:
            return True
        if not EK_TOLERANSI or not token.startswith(stem):
            continue
        ek = token[len(stem):]
        if not ek or len(ek) > (AZAMI_EK if len(kelime) >= KISA_SOZCUK else AZAMI_EK_KISA):
            continue
        if len(kelime) < KISA_SOZCUK and not _ek_bolunur(ek):
            continue
        return True
    return False


def _tokenla(metin: str) -> list[str]:
    return TOKEN.findall(metin)


def _zincir_say(tokenlar: list[str], kelimeler: list[str]) -> int:
    """Sorgu sözcükleri sırayla, aralarında en çok 3 sözcük kalacak biçimde kaç kez geçiyor."""
    if not kelimeler or not tokenlar:
        return 0
    poz = []
    for k in kelimeler:
        p = [i for i, t in enumerate(tokenlar) if _eslesir(t, k)]
        if not p:
            return 0
        poz.append(p)
    dp = [1] * len(poz[0])
    for i in range(1, len(poz)):
        yeni = []
        for p in poz[i]:
            toplam = 0
            for j, q in enumerate(poz[i - 1]):
                if q < p and p - q - 1 <= AZAMI_ARA_SOZCUK:
                    toplam += dp[j]
            yeni.append(toplam)
        dp = yeni
    return sum(dp)


def _cumleler(metin: str) -> list[str]:
    """Cümlelere böler; kısaltma noktası ve sayı içindeki nokta sınır sayılmaz."""
    koru = re.sub(r"(?<=\d)\.(?=\d)", "\x00", metin)
    koru = re.sub(r"\b([a-z]+)\.",
                  lambda m: m.group(1) + "\x00" if m.group(1) in KISALTMA else m.group(0), koru)
    return [c.replace("\x00", ".") for c in re.split(r"(?<=[.!?…])\s+|\n+", koru) if c.strip()]


def _cift_tik_maskele(metin: str) -> str:
    """Çift (ve daha fazla) ters tırnaklı satır içi kodu boşlukla örter; kod çitlerine dokunmaz."""
    satirlar, kodda = [], False
    for ham in metin.split("\n"):
        if re.match(r"^\s*(```|~~~)", ham):
            kodda = not kodda
            satirlar.append(ham)
            continue
        if kodda:
            satirlar.append(ham)
        else:
            satirlar.append(re.sub(r"`{2,}[^`\n]*`{2,}",
                                    lambda m: " " * len(m.group(0)), ham))
    return "\n".join(satirlar)


def _kodsuz_satirlar(metin: str) -> list[str]:
    """Kod çitlerini boşaltır, satır içi kodu boşlukla örter; bağlantı/görsel sözdizimi kalır."""
    satirlar, kodda = [], False
    for ham in metin.split("\n"):
        if re.match(r"^\s*(```|~~~)", ham):
            kodda = not kodda
            satirlar.append("")
            continue
        if kodda:
            satirlar.append("")
        else:
            satirlar.append(re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), ham))
    return satirlar


def _gorsel_temizle(s: str) -> str:
    return re.sub(r"!\[[^\]]*\]", "", s)


def _bloklar(satirlar: list[str]) -> list[dict]:
    bloklar, buf, bas = [], [], None

    def kapat():
        nonlocal buf, bas
        if buf:
            bloklar.append({"tur": "paragraf", "satir": bas, "metin": " ".join(buf)})
        buf, bas = [], None

    for i, satir in enumerate(satirlar, 1):
        m = BASLIK.match(satir)
        if m:
            kapat()
            bloklar.append({"tur": "baslik", "satir": i, "seviye": len(m.group(1)),
                            "metin": m.group(2).strip()})
            continue
        if not satir.strip():
            kapat()
            continue
        if TABLO_AYRAC.match(satir) and "|" in satir:
            kapat()
            continue
        temiz = _gorsel_temizle(satir).strip()
        if not temiz:
            kapat()
            continue
        if LISTE.match(satir):
            kapat()
            bloklar.append({"tur": "paragraf", "satir": i, "metin": LISTE.sub("", temiz)})
            continue
        if not buf:
            bas = i
        buf.append(temiz)
    kapat()
    return bloklar


def slug_oner(baslik: str, azami: int = SLUG_UST) -> str:
    """Türkçe başlığı ASCII URL slug'ına çevirir; 75 karakterde sözcük sınırından keser."""
    s = kucult(nfc(baslik)).translate(AKSAN)
    s = re.sub(r"['\u2019\u2018`]", "", s)   # kesme işareti tire olmaz: "Savaşı'nı" → "savasini"
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    if len(s) > azami:
        s = s[:azami]
        if "-" in s:
            s = s.rsplit("-", 1)[0]
        s = s.strip("-")
    return s


def _bulgu(kod, duzey, mesaj, oneri, dayanak):
    return {"kod": kod, "duzey": duzey, "mesaj": mesaj, "oneri": oneri, "dayanak": dayanak}


def denetle(metin: str, anahtar: str | None = None, ikincil: str | list[str] | None = None,
            baslik: str | None = None, aciklama: str | None = None,
            slug: str | None = None) -> tuple[list[dict], dict]:
    """Metni denetler; (bulgular, ölçümler) döndürür."""
    metin = _cift_tik_maskele(nfc(metin))
    anahtar = nfc(anahtar)
    baslik = nfc(baslik)
    aciklama = nfc(aciklama)
    slug = nfc(slug)
    satirlar = temizle(metin)
    kodsuz = _kodsuz_satirlar(metin)
    bloklar = _bloklar(satirlar)
    basliklar = [b for b in bloklar if b["tur"] == "baslik"]
    paragraflar = [b for b in bloklar if b["tur"] == "paragraf"]
    h1ler = [b for b in basliklar if b["seviye"] == 1]

    gorseller, baglantilar = [], []
    for i, satir in enumerate(kodsuz, 1):
        for m in GORSEL.finditer(satir):
            gorseller.append({"alt": m.group(1), "url": m.group(2), "satir": i})
        for m in BAGLANTI.finditer(satir):
            baglantilar.append({"capa": m.group(1), "url": m.group(2), "satir": i})

    govde = "\n\n".join(p["metin"] for p in paragraflar)
    govde_f = katla(govde)
    tokenlar = _tokenla(govde_f)
    sozcuk = len(tokenlar)

    kelimeler = _tokenla(katla(anahtar)) if anahtar else []

    bulgular: list[dict] = []

    # ---- ana sorgu kuralları (S01-S05) ----
    yogunluk = 0.0
    s03 = False
    s03_yer = []
    if kelimeler:
        if h1ler:
            kaynak = "H1'de"
            uygun = any(_zincir_say(_tokenla(katla(b["metin"])), kelimeler) for b in h1ler)
        elif baslik:
            kaynak = "title'da"
            uygun = _zincir_say(_tokenla(katla(baslik)), kelimeler) > 0
        else:
            kaynak = "başlıkta"
            uygun = False
        if not uygun:
            bulgular.append(_bulgu(
                "S01", "uyari", f"Ana sorgu {kaynak} geçmiyor",
                "Ana sorguyu H1'de ve ilk paragrafta doğal biçimde geçir; çekimli biçim yeter",
                "sektor"))

        ilk100 = tokenlar[:100]
        if _zincir_say(ilk100, kelimeler) == 0:
            bulgular.append(_bulgu(
                "S02", "bilgi", "Ana sorgu ilk 100 sözcükte geçmiyor",
                "İlk paragrafta konuyu doğrudan adlandır; zorlama tekrar yapma", "sektor"))

        adet = sum(_zincir_say(_tokenla(c), kelimeler) for c in _cumleler(govde_f))
        yogunluk = (adet / sozcuk * 100) if sozcuk else 0.0
        # Kısa metinde (< YOGUNLUK_EN_AZ_SOZCUK) doğal anışlar yüzdeyi şişirir: uyarı yerine bilgi.
        if yogunluk > YOGUNLUK_ESIK and adet >= 4 and sozcuk < YOGUNLUK_EN_AZ_SOZCUK:
            bulgular.append(_bulgu(
                "S04", "bilgi", f"Ana sorgu yoğunluğu %{yogunluk:.2f} (kısa metin, {sozcuk} sözcük)".replace(".", ","),
                "Kısa metinde yüzde oynaktır; doğal anışları silme, yalnız aynı cümlede tekrarı önle", "sektor"))
        elif yogunluk > YOGUNLUK_ESIK and adet >= 4:
            bulgular.append(_bulgu(
                "S04", "uyari", f"Ana sorgu yoğunluğu %{yogunluk:.2f}".replace(".", ","),
                "Aşırı tekrar; anahtar doldurma görünümünü azalt, eşanlamlı zincir kurma", "sektor"))
        bulgular.append(_bulgu(
            "S05", "bilgi", f"Ana sorgu yoğunluğu %{yogunluk:.2f}".replace(".", ","),
            "Hedef değil; yalnız aşırı tekrarı izle", "—"))

        for c in _cumleler(govde_f):
            if _zincir_say(_tokenla(c), kelimeler) >= 2:
                s03 = True
                s03_yer.append("gövdede aynı cümlede")
                break

    # S03: aynı cümlede ≥2 ya da title'da aynı sözcük/ifade ≥2 (title tekrarı sorgudan bağımsız)
    if baslik:
        bt = [t for t in _tokenla(katla(baslik)) if len(t) >= 3 and t not in DURAK]
        if len(bt) > len(set(bt)):
            s03 = True
            s03_yer.append("title'da yinelenen sözcük: " + ", ".join(sorted({t for t in bt if bt.count(t) > 1})))
        elif kelimeler and _zincir_say(_tokenla(katla(baslik)), kelimeler) >= 2:
            s03 = True
            s03_yer.append("title'da sorgu iki kez")
    if s03:
        bulgular.append(_bulgu(
            "S03", "hata", "Anahtar doldurma şüphesi (aynı sorgu/sözcük ≥2): " + "; ".join(s03_yer),
            "Tekrarı azalt; ifadeyi doğal biçimde bir kez kur", "google"))

    # ---- title ve meta (S06, S07) ----
    if baslik:
        n = len(baslik)
        if n > TITLE_UST or n < TITLE_ALT:
            bulgular.append(_bulgu(
                "S06", "uyari", f"Title uzunluğu {n} karakter (sezgi: {TITLE_ALT}-{TITLE_UST})",
                "Kırpılma/yetersizlik sezgisi; resmî sınır yok, cihaz genişliğine göre kırpılır", "sektor"))
    if aciklama is not None:
        n = len(aciklama)
        if n > META_UST or n < META_ALT:
            bulgular.append(_bulgu(
                "S07", "uyari", f"Meta açıklama {n} karakter (sezgi: {META_ALT}-{META_UST})",
                "Açıklamayı metindeki bilgiyle {0}-{1} karakter aralığına getir".format(META_ALT, META_UST),
                "sektor"))

    # ---- yapı (S08, S09, S10, S14) ----
    if len(h1ler) != 1:
        bulgular.append(_bulgu(
            "S08", "bilgi", f"H1 sayısı {len(h1ler)}",
            "Tek H1 kullan; bu Google kuralı değil, bilgi düzeyinde bir öneridir", "sektor"))

    onceki_seviye = 1
    for b in basliklar:
        if b["seviye"] > onceki_seviye + 1:
            bulgular.append(_bulgu(
                "S09", "bilgi", f"Başlık seviyesi atlıyor (H{onceki_seviye}→H{b['seviye']})",
                "Ara seviyeyi kullan (H2→H3); erişilebilirlik bilgisi", "sektor"))
        onceki_seviye = b["seviye"]

    if sozcuk >= ICERIK_ESIK and not any(b["seviye"] >= 2 for b in basliklar):
        bulgular.append(_bulgu(
            "S10", "uyari", f"{sozcuk} sözcük ve hiç ara başlık yok",
            "Metnin kendi bölümlerine göre H2 ekle; yeni içerik uydurma", "durulac"))

    for idx, b in enumerate(bloklar):
        if b["tur"] == "baslik" and katla(b["metin"]).strip().endswith("?"):
            if idx + 1 < len(bloklar) and bloklar[idx + 1]["tur"] == "paragraf":
                n = len(_tokenla(katla(bloklar[idx + 1]["metin"])))
                if n < SSS_ALT or n > SSS_UST:
                    bulgular.append(_bulgu(
                        "S14", "bilgi", f"Soru başlığı yanıtı {n} sözcük (gözlem: {SSS_ALT}-{SSS_UST})",
                        "Kendi kendine yeten kısa yanıtı hemen başlığın altına al", "sektor"))

    # ---- görseller (S11) ----
    for g in gorseller:
        alt = g["alt"].strip()
        if not alt:
            bulgular.append(_bulgu(
                "S11", "uyari", f"Görselde alt metin yok (satır {g['satir']})",
                "Görselin ne gösterdiğini metindeki bilgiyle yaz", "google"))
            continue
        parcalar = _tokenla(katla(alt))
        if parcalar and parcalar[0] in ALT_BASLANGIC:
            bulgular.append(_bulgu(
                "S11", "uyari", f"Alt metin jenerik başlıyor: «{alt[:40]}»",
                "“Görsel/resim/fotoğraf” yerine görselin içeriğini yaz", "google"))
        elif len(alt) > ALT_UST:
            bulgular.append(_bulgu(
                "S11", "uyari", f"Alt metin {len(alt)} karakter (>{ALT_UST})",
                "Alt metni kısalt; anahtar doldurma değil, betimleme", "google"))

    # ---- slug (S12) ----
    slug_onerisi = None
    if slug:
        if re.search(r"[A-ZÇĞİÖŞÜ]", slug):
            bulgular.append(_bulgu("S12", "uyari", f"Slug büyük harf içeriyor: «{slug}»",
                                   f"Küçük harf kullan: {slug_oner(slug)}", "google"))
        if "_" in slug:
            bulgular.append(_bulgu("S12", "uyari", f"Slug alt çizgi içeriyor: «{slug}»",
                                   f"Tire kullan: {slug_oner(slug)}", "google"))
        if re.search(r"\s", slug):
            bulgular.append(_bulgu("S12", "uyari", f"Slug boşluk içeriyor: «{slug}»",
                                   f"Boşluk yerine tire: {slug_oner(slug)}", "sektor"))
        if re.search(r"[^A-Za-z0-9\-_\s]", slug):
            bulgular.append(_bulgu(
                "S12", "uyari", f"Slug ASCII dışı ya da özel karakter içeriyor: «{slug}»",
                f"Yüzde kodlama riski; ASCII transliterasyon: {slug_oner(slug)}", "google"))
        if len(slug) > SLUG_UST:
            bulgular.append(_bulgu("S12", "uyari", f"Slug {len(slug)} karakter (>{SLUG_UST})",
                                   f"Kısalt: {slug_oner(slug)}", "sektor"))
        if "--" in slug:
            bulgular.append(_bulgu("S12", "uyari", f"Slug ardışık tire içeriyor: «{slug}»",
                                   f"Tek tireye indir: {slug_oner(slug)}", "sektor"))
    else:
        kaynak_metin = baslik or (h1ler[0]["metin"] if h1ler else None)
        if kaynak_metin:
            slug_onerisi = slug_oner(kaynak_metin)

    # ---- bağlantı çapası (S13) ----
    for b in baglantilar:
        capa = re.sub(r"\s+", " ", katla(b["capa"])).strip(" .,!?:;\"'")
        if capa in ANLAMSIZ_CAPA:
            bulgular.append(_bulgu(
                "S13", "uyari", f"Anlamsız çapa metni: «{b['capa']}»",
                "Çapayı hedefin konusunu anlatan ifadeyle değiştir", "google"))

    # ---- title/H1 ortak sözcük (S15) ----
    if baslik and h1ler:
        bt = {t for t in _tokenla(katla(baslik)) if len(t) >= 3 and t not in DURAK}
        ht = {t for t in _tokenla(katla(" ".join(h["metin"] for h in h1ler)))
              if len(t) >= 3 and t not in DURAK}
        if not (bt & ht):
            bulgular.append(_bulgu(
                "S15", "uyari", "Title ile H1 ortak anlamlı sözcük içermiyor",
                "Title ile H1 aynı konuyu adlandırsın; anahtar doldurma değil", "sektor"))

    # ---- karaktersiz yazım (S16) ----
    formlar: dict[str, set[str]] = {}
    for m in RAW_TOKEN.finditer(govde):
        raw = kucult(m.group(0))
        anahtar_k = katla(raw)
        if len(anahtar_k) >= 3:
            formlar.setdefault(anahtar_k, set()).add(raw)
    for anahtar_k, kumeler in formlar.items():
        if frozenset(kumeler) in GERCEK_CIFTLER:
            continue
        if len(kumeler) > 1 and any(set(f) & TURKCE_HARF for f in kumeler) and anahtar_k in kumeler:
            bulgular.append(_bulgu(
                "S16", "bilgi",
                f"Karaktersiz yazım şüphesi: {', '.join(sorted(kumeler))}; "
                "farklı anlamlı sözcük olabilir (ılık/ilik); elle bak",
                "Gövdede tek yazım seç; karaktersiz serpiştirme yapma", "durulac"))

    # ---- paragraf uzunluğu (S17) ----
    for p in paragraflar:
        n = len(_tokenla(katla(p["metin"])))
        if n > PARAGRAF_ESIK:
            bulgular.append(_bulgu(
                "S17", "uyari", f"Uzun paragraf: {n} sözcük (>{PARAGRAF_ESIK})",
                "Paragrafı konu sınırından böl; bilgi atma", "sektor"))

    # ---- ince içerik bilgisi (S18) ----
    if sozcuk < ICERIK_ESIK:
        bulgular.append(_bulgu(
            "S18", "bilgi", f"Metin {sozcuk} sözcük (<{ICERIK_ESIK})",
            "İnce içerik riski değil, bilgi; konu gerektiriyorsa genişlet", "sektor"))

    # ---- title/meta sayıları gövdede var mı (S19) ----
    govde_sayilar = set(SAYI.findall(metin))
    for ad, deger in (("Title", baslik), ("Meta açıklama", aciklama)):
        if not deger:
            continue
        eksik = sorted({n for n in SAYI.findall(deger) if n not in govde_sayilar})
        if eksik:
            bulgular.append(_bulgu(
                "S19", "uyari", f"{ad} gövdede olmayan sayı içeriyor: {', '.join(eksik)}",
                "Pakete yalnız gövdedeki sayıyı, kapsamı ve koşuluyla taşı", "durulac"))

    # ---- aynı uzun cümle iki kez (S20) ----
    goruldu, tekrar = {}, []
    for c in _cumleler(govde_f):
        t = tuple(_tokenla(c))
        if len(t) >= TEKRAR_ESIK:
            goruldu[t] = goruldu.get(t, 0) + 1
            if goruldu[t] == 2:
                tekrar.append(" ".join(t[:6]) + " …")
    if tekrar:
        bulgular.append(_bulgu(
            "S20", "uyari", f"Aynı cümle birden çok kez geçiyor ({len(tekrar)}): {'; '.join(tekrar[:3])}",
            "Yanıtı başa taşıdıysan aşağıdaki kopyayı sil; SSS yanıtı sayfada bir kez bulunur", "durulac"))

    bulgular.sort(key=lambda b: (b["kod"], b["mesaj"]))

    ikincil_liste = []
    if ikincil:
        ikincil_liste = ([t.strip() for t in ikincil.split(",")] if isinstance(ikincil, str)
                         else list(ikincil))
        ikincil_liste = [t for t in ikincil_liste if t]

    olcumler = {
        "sozcuk_sayisi": sozcuk,
        "yogunluk": round(yogunluk, 2) if kelimeler else None,
        "baslik_agaci": [{"seviye": b["seviye"], "metin": b["metin"]} for b in basliklar],
        "title_uzunluk": len(baslik) if baslik else None,
        "aciklama_uzunluk": len(aciklama) if aciklama is not None else None,
        "h1_sayisi": len(h1ler),
        "gorsel_sayisi": len(gorseller),
        "baglanti_sayisi": len(baglantilar),
        "slug_onerisi": slug_onerisi,
        "ikincil": {t: sum(_zincir_say(_tokenla(c), _tokenla(katla(t)))
                           for c in _cumleler(govde_f)) for t in ikincil_liste},
    }
    return bulgular, olcumler


def _say(bulgular: list[dict]) -> dict[str, int]:
    sayilar: dict[str, int] = {}
    for b in bulgular:
        sayilar[b["kod"]] = sayilar.get(b["kod"], 0) + 1
    return sayilar


def _json_cikti(bulgular, olcumler, kelimeler, karsilastirma=None):
    veri = {
        "anahtar": " ".join(kelimeler) if kelimeler else None,
        "olcumler": olcumler,
        "bulgular": bulgular,
        "not": NOT,
    }
    if karsilastirma is not None:
        veri["karsilastirma"] = karsilastirma
    print(json.dumps(veri, ensure_ascii=False, indent=2))


def _metin_cikti(bulgular, olcumler):
    hata = sum(1 for b in bulgular if b["duzey"] == "hata")
    uyari = sum(1 for b in bulgular if b["duzey"] == "uyari")
    bilgi = sum(1 for b in bulgular if b["duzey"] == "bilgi")
    if bulgular:
        print(f"SEO denetimi: {len(bulgular)} bulgu ({hata} hata, {uyari} uyarı, {bilgi} bilgi)")
        for b in bulgular:
            print(f"{b['duzey']} · {b['kod']} · {b['mesaj']} · {b['oneri']} · {b['dayanak']}")
    else:
        print("SEO denetimi: bulgu yok")
    parcacik = [f"{olcumler['sozcuk_sayisi']} sözcük"]
    if olcumler["yogunluk"] is not None:
        parcacik.append(f"yoğunluk %{olcumler['yogunluk']:.2f}".replace(".", ","))
    parcacik.append(f"H1 {olcumler['h1_sayisi']}")
    if olcumler["title_uzunluk"] is not None:
        parcacik.append(f"title {olcumler['title_uzunluk']} karakter")
    if olcumler["aciklama_uzunluk"] is not None:
        parcacik.append(f"açıklama {olcumler['aciklama_uzunluk']} karakter")
    print("Ölçüm: " + " · ".join(parcacik))
    if olcumler["slug_onerisi"]:
        print(f"Önerilen slug: {olcumler['slug_onerisi']}")


def _karsilastir(yeni, eski):
    sy, se = _say(yeni), _say(eski)
    print("\nKod   önce → sonra")
    for kod in sorted(set(sy) | set(se)):
        a, b = se.get(kod, 0), sy.get(kod, 0)
        isaret = "  ↑ YENİ SORUN" if kod in ("S03", "S04") and b > a else ""
        print(f"{kod}   {a:>3} → {b:<3}{isaret}")
    print(f"TOPLAM {sum(se.values()):>3} → {sum(sy.values()):<3}")
    return {"kodlar": {k: {"once": se.get(k, 0), "sonra": sy.get(k, 0)}
                       for k in sorted(set(sy) | set(se))},
            "toplam": {"once": sum(se.values()), "sonra": sum(sy.values())}}


def oku(yol: str) -> str:
    if yol == "-":
        return sys.stdin.read()
    with open(yol, encoding="utf-8") as f:
        return f.read()


def main(arg: list[str] | None = None) -> int:
    arg = list(sys.argv[1:] if arg is None else arg)
    if not arg:
        print(__doc__, file=sys.stderr)
        return 2
    if any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0

    dosya = None
    anahtar = ikincil = baslik = aciklama = slug = onceki = None
    json_modu = False
    i = 0
    while i < len(arg):
        a = arg[i]
        if a in ("--anahtar", "--ikincil", "--baslik", "--aciklama", "--slug", "--onceki"):
            if i + 1 >= len(arg):
                print(f"seo_denetim: {a} için değer yok", file=sys.stderr)
                return 2
            if a == "--anahtar":
                anahtar = arg[i + 1]
            elif a == "--ikincil":
                ikincil = arg[i + 1]
            elif a == "--baslik":
                baslik = arg[i + 1]
            elif a == "--aciklama":
                aciklama = arg[i + 1]
            elif a == "--slug":
                slug = arg[i + 1]
            else:
                onceki = arg[i + 1]
            i += 2
        elif a == "--json":
            json_modu = True
            i += 1
        elif a.startswith("-") and a != "-":
            print(f"seo_denetim: bilinmeyen seçenek {a!r} (yardım için --help)", file=sys.stderr)
            return 2
        else:
            dosya = a
            i += 1
    if dosya is None:
        print("seo_denetim: dosya verilmedi (yardım için --help)", file=sys.stderr)
        return 2
    for yol in (dosya, onceki):
        if yol and yol != "-" and not os.path.isfile(yol):
            print(f"seo_denetim: dosya bulunamadı: {yol}", file=sys.stderr)
            return 2

    bulgular, olcumler = denetle(oku(dosya), anahtar, ikincil, baslik, aciklama, slug)
    kelimeler = _tokenla(katla(anahtar)) if anahtar else []

    karsilastirma = None
    if onceki:
        eski_bulgular, _ = denetle(oku(onceki), anahtar, ikincil, baslik, aciklama, slug)
        if json_modu:
            karsilastirma = _say_sozluk(eski_bulgular, bulgular)
        else:
            _metin_cikti(bulgular, olcumler)
            _karsilastir(bulgular, eski_bulgular)
            print("\n" + NOT)
            return 1 if any(b["duzey"] == "hata" for b in bulgular) else 0

    if json_modu:
        _json_cikti(bulgular, olcumler, kelimeler, karsilastirma)
    else:
        _metin_cikti(bulgular, olcumler)
        print("\n" + NOT)
    return 1 if any(b["duzey"] == "hata" for b in bulgular) else 0


def _say_sozluk(eski, yeni):
    se, sy = _say(eski), _say(yeni)
    return {"kodlar": {k: {"once": se.get(k, 0), "sonra": sy.get(k, 0)}
                       for k in sorted(set(se) | set(sy))},
            "toplam": {"once": sum(se.values()), "sonra": sum(sy.values())}}


if __name__ == "__main__":
    sys.exit(main())