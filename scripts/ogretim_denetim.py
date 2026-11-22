#!/usr/bin/env python3
"""Durulaç `+ogretim` denetimi: alanını tanıyan öğretim materyali ölçeği (8 boyut × 0–2 = 16). 0 jeton, ağ yok.

Belgenin ALANINI (dil, tıp, diş hekimliği, matematik, fen, tarih, coğrafya, sosyal bilgiler, genel) ve BİÇİMİNİ
(sözel / görsel) tespit eder; her alanda çalışan ortak çekirdeğe o alanın kontrollerini ekler. Profiller:
references/ogretim-alanlari.json · ölçek ve gerekçeler: references/ogretim.md. Doğruluk ve hedef uyumu ELLE kalır.

Kullanım:
  python3 ogretim_denetim.py BELGE.md [--pdf BELGE.pdf] [--alan AD] [--dil KOD] [--json] [--duzelt]
Seçenekler:
  --pdf DOSYA   ölçülecek PDF (verilmezse aynı adlı .pdf aranır; yoksa yazı boyu ve sayfa ölçülmez)
  --alan AD     tespiti geç: genel|dil|tip|dis|matematik|fen|tarih|cografya|sosyal (frontmatter `alan:` da olur)
  --dil KOD     yalnız dil alanında: öğretilen dil fr|en|de|es|it (verilmezse metinden tahmin edilir)
  --json        sonucu JSON ver
  --duzelt      yalnız anlamı değiştirmeyen düzeltmeler (.md'ye yazar): karışık yazılı sözcükte Kiril/Yunan
                benzer harf → Latin; html/body font-size 8,5 pt altı → 9 pt. Sonra yeniden denetler
Çıkış kodu: 0 yayınlanabilir (temiz ya da yalnız uyarı), 1 en az bir HATA (yayınlanamaz), 2 dosya/kullanım hatası.
PDF ölçümü için poppler `pdftotext` ve `pdfimages` gerekir; yoksa PDF boyutları "ölçülmedi" olur (puan uydurulmaz).
"""
from __future__ import annotations

import json
import re
import shutil
import statistics
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.dont_write_bytecode = True

BOYUTLAR = ["Doğruluk", "Hedefle uyum", "Seviye", "Ezber ve kavrama",
            "Okunaklılık", "Sıra ve akış", "Kendini sınama", "Verimlilik"]
PDF_BOYUTLARI = ("Okunaklılık", "Verimlilik")
PROFIL_DOSYASI = Path(__file__).resolve().parents[1] / "references" / "ogretim-alanlari.json"

# ── Eşikler (gerekçeleri references/ogretim.md; ikisi birlikte değişir) ──
YAZI_HATA, YAZI_UYARI = 8.0, 9.0       # ortanca kelime kutusu yüksekliği (pt ≈ yazı boyu)
ALT_BILGI = 0.93                       # sayfa yüksekliğinin bu oranından aşağısı alt bilgi sayılır
BOS_SAYFA = 0.06                       # metin doluluğu bundan azsa ve görsel yoksa: boş sayfa
YARIM_SAYFA, YARIM_ORAN = 0.40, 0.20   # %40'tan az dolu sayfaların oranı %20'yi aşarsa (son sayfa hariç)
SAYFA_UYARI = 16                       # sayfa_tavan yoksa: 16+ sayfa gerekçe ister
TERIM_ESIK = 12                        # dil: dil bilgisi terimi sayısı
HEDEF_DISI_ESIK = 8                    # dil: hedef dışı açıklama dili sözcüğü
OKUNUS_UZUN, OKUNUS_UZUN_ORAN = 16, 0.15
YABANCI_ESIK = 3                       # dil: hedef dilden en az bu kadar sık sözcük varsa "yabancı metin var"
KISALTMA_ESIK = 3                      # tanımsız kısaltma (≥2 kez kullanılan) sayısı
VERI_YILSIZ_ESIK = 2                   # yılsız sayısal veri cümlesi
# Alan tespiti
ALAN_EN_AZ = 4                         # en yüksek alan puanı bundan azsa: genel
ALAN_SOZCUK_TAVAN = 3                  # tek sözcük puana en çok 3 kez katkı verir
ALT_ALAN_ORAN = 0.5                    # alt alan puanı üst alanın yarısına ulaşırsa alt alan seçilir
GUVEN_YUKSEK_KAT, GUVEN_ORTA_KAT = 2.0, 1.3
GORSEL_KELIME = 120                    # md'de görsel başına 120 kelimeden az metin → görsel ağırlıklı
GORSEL_SAYFA_ORAN = 0.5                # PDF sayfalarının yarısı ya da fazlası görselli ve az metinli (<120 kelime) → görsel
DUZELT_PUNTO_ALT, DUZELT_PUNTO = 8.5, "9"
BU_YIL = date.today().year
KILAVUZ_YAS = 5                        # NHMRC: kılavuzlar genelde 5 yılda bir gözden geçirilir → daha eskisi uyarı

DIL = {
    "fr": {"terim": ["participe", "imparfait", "subjonctif", "conditionnel", "auxiliaire", "infinitif", "gérondif",
                     "complément d'objet", "pronom relatif", "pronom personnel", "adjectif possessif", "déterminant",
                     "plus-que-parfait", "COD", "COI", "partitif", "passé simple", "voix passive"],
           "sik": r"je|tu|il|elle|nous|vous|ils|est|suis|sont|le|la|les|une?|des|du|et|avec|pour|dans|mon|ma|mes|pas",
           "aksan": r"[àâçéèêëîïôûùœ]"},
    "en": {"terim": ["present perfect", "past participle", "gerund", "infinitive", "auxiliary", "modal verb",
                     "passive voice", "relative clause", "conditional", "determiner", "phrasal verb"],
           "sik": r"the|and|is|are|you|this|that|with|have|has|do|does|my|your|it|of|to",
           "aksan": None},
    "de": {"terim": ["Akkusativ", "Dativ", "Genitiv", "Nominativ", "Partizip", "Konjunktiv", "Präteritum",
                     "Perfekt", "Hilfsverb", "Infinitiv", "Relativpronomen", "Passiv", "trennbare"],
           "sik": r"der|die|das|und|ist|ich|du|nicht|mit|ein|eine|sie|wir|bin|haben|zu|auf",
           "aksan": r"[ßä]"},
    "es": {"terim": ["subjuntivo", "pretérito", "imperfecto", "participio", "gerundio", "infinitivo", "auxiliar",
                     "pronombre", "complemento directo", "condicional"],
           "sik": r"el|la|los|las|y|es|soy|está|un|una|con|para|por|yo|tú|que|de|en|no",
           "aksan": r"[áéíóúñ¿¡]"},
    "it": {"terim": ["congiuntivo", "passato prossimo", "imperfetto", "participio", "gerundio", "infinito",
                     "ausiliare", "pronome", "complemento oggetto", "condizionale"],
           "sik": r"il|la|lo|gli|le|e|è|sono|un|una|con|per|io|tu|che|di|non|ho",
           "aksan": r"[àèéìòù]"},
}
TR_TERIMLER = ["nesne zamiri", "yüklem", "tümleç", "edilgen", "ortaç", "ulaç", "dolaylı tümleç", "belirteç"]
INGILIZCE = re.compile(r"\b(the|and|with|which|you|this|that|from|should|would|because)\b")

KIRIL = re.compile(r"[Ѐ-ӿ]")
YUNAN = re.compile(r"[Ͱ-Ͽ]")
BENZER = {"е": "e", "а": "a", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y", "і": "i", "ј": "j", "ѕ": "s",
          "Е": "E", "А": "A", "О": "O", "Р": "P", "С": "C", "Т": "T", "М": "M", "Н": "H", "К": "K", "В": "B",
          "Х": "X", "І": "I",
          "ο": "o", "α": "a", "ε": "e", "ι": "i", "ν": "v", "ρ": "p", "τ": "t", "υ": "u", "κ": "k",
          "Ο": "O", "Α": "A", "Ε": "E", "Ι": "I", "Ν": "N", "Ρ": "P", "Τ": "T", "Κ": "K", "Μ": "M", "Β": "B",
          "Η": "H", "Χ": "X", "Ζ": "Z"}
LATIN = re.compile(r"[A-Za-zÀ-ɏ]")
SOZCUK = re.compile(r"[^\W\d_]+(?:['’][^\W\d_]+)?")
MIKRO_BIRIM = re.compile(r"^[μµ][a-zA-Z]{1,3}$")          # μg, μm, μL: Yunan μ + Latin birim, karışık sayılmaz
YER_TUTUCU = re.compile(r"\b(TODO|FIXME)\b|\?\?\?")
SINAMA = re.compile(r"kendini\s+(dene|sına|test)|\bprova|alıştırma|soru\s*[–-]\s*cevap|cevap\s+anahtar|\btest"
                    r"|boşluğ|bakmadan|\bsına[vy]?\b|✅|\bquiz\b|\bexercise|\bsorular\b|\bsoru\s*\d|vaka\s+sorusu"
                    r"|dilsiz\s+harita|\bproblemler\b", re.I)
OKUNUS = re.compile(r"(?<![\w/])/([a-zçğıöşüâêîôû' ·‿\-]{3,})/(?![\w/])")
BASLIK_MD = re.compile(r"^#{1,4}\s+(\d+(?:\.\d+)*)(\+*)[\s.)]", re.M)
BASLIK_HTML = re.compile(r"<h[1-4][^>]*>\s*(\d+(?:\.\d+)*)(\+*)[\s.)]", re.I)
SAYFA_GONDERME = re.compile(r"(?:\bs\.|\bsayfa)\s*\d+\s*['’][a-zçğıöşü]+", re.I)
PUNTO = re.compile(r"(?:html|body)\s*\{[^}]*?font-size:\s*([\d.]+)\s*pt", re.I)
GORSEL_MD = re.compile(r"!\[([^\]]*)\]\(([^)]*)\)|<img\b[^>]*>|<svg\b|<figure\b", re.I)
SEKIL_BASLIGI = re.compile(r"\b(şekil|görsel|resim|figure|fig\.|harita|tablo)\s*\d+", re.I)
YIL = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
CUMLE = re.compile(r"[^.!?\n]+[.!?]?")
SINAMA_ISTEYEN = ("konu-anlatimi", "pano", "rehber", "ders-notu", "")
OKUNUS_ISTEMEYEN = ("indeks", "yonetim")


def profiller() -> dict:
    return json.loads(PROFIL_DOSYASI.read_text(encoding="utf-8"))


def kontrol_listesi(profil: dict, alan: str) -> list[str]:
    """Profilin kontrolleri; '@grup' adları `_gruplar`dan açılır, tekrarlar atılır (sıra korunur)."""
    cikti = []
    for ad in profil[alan]["kontroller"]:
        for k in (profil["_gruplar"][ad[1:]] if ad.startswith("@") else [ad]):
            if k not in cikti:
                cikti.append(k)
    return cikti


def elle_listesi(profil: dict, alan: str) -> list[str]:
    cikti = []
    for g in profil[alan].get("elle_gruplar", []):
        cikti += profil["_elle_gruplar"][g]
    return cikti + profil[alan]["elle"]


# ── Metin hazırlığı ──
def on_bilgi(metin: str) -> tuple[dict, str]:
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", metin, re.S)
    if not m:
        return {}, metin
    meta = {}
    for satir in m.group(1).splitlines():
        if ":" in satir and not satir.lstrip().startswith("#"):
            a, b = satir.split(":", 1)
            meta[a.strip()] = b.strip().strip('"').strip("'")
    return meta, metin[m.end():]


def gorunur(govde: str) -> str:
    """Öğrencinin gördüğü metin: stil, betik, yorum, kod, bağlantı adresi ve etiketler atılır."""
    g = re.sub(r"<(style|script)\b.*?</\1>", " ", govde, flags=re.S | re.I)
    g = re.sub(r"<!--.*?-->", " ", g, flags=re.S)
    g = re.sub(r"^```.*?^```", " ", g, flags=re.S | re.M)
    g = re.sub(r"`[^`\n]*`", " ", g)
    g = re.sub(r"\]\([^)]*\)", "]", g)
    g = re.sub(r"https?://\S+", " ", g)
    return re.sub(r"<[^>]+>", " ", g)


def karisik_sozcukler(metin: str) -> list[str]:
    """Latin harfle karışık yazılmış Kiril/Yunan harfli sözcükler (görsel olarak ayırt edilemez)."""
    return [s for s in SOZCUK.findall(metin)
            if (KIRIL.search(s) or YUNAN.search(s)) and LATIN.search(s) and not MIKRO_BIRIM.match(s)]


def say(desen: str, metin: str) -> int:
    return len(re.findall(desen, metin))


# ── PDF ölçümü ──
def pdf_olc(pdf: Path) -> dict | None:
    if not (shutil.which("pdftotext") and shutil.which("pdfimages")):
        return None
    cikti = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True)
    if cikti.returncode != 0:
        return None
    sayfalar = re.split(r"<page ", cikti.stdout)[1:]
    gorselli = set()
    liste = subprocess.run(["pdfimages", "-list", str(pdf)], capture_output=True, text=True).stdout
    for satir in liste.splitlines()[2:]:
        p = satir.split()
        if p and p[0].isdigit():
            gorselli.add(int(p[0]))
    yukseklik, doluluk, kelime = [], [], []
    for i, pg in enumerate(sayfalar, 1):
        h = re.search(r'height="([\d.]+)"', pg)
        H = float(h.group(1)) if h else 842.0
        kutular = [(float(a), float(b)) for a, b in re.findall(r'yMin="([\d.]+)" xMax="[\d.]+" yMax="([\d.]+)"', pg)]
        govde = [(a, b) for a, b in kutular if b < ALT_BILGI * H]
        yukseklik += [b - a for a, b in govde]
        doluluk.append((i, max((b for _, b in govde), default=0) / H, i in gorselli))
        kelime.append(len(govde))
    return {"sayfa": len(sayfalar), "yazi": round(statistics.median(yukseklik), 2) if yukseklik else 0.0,
            "doluluk": doluluk, "kelime": kelime}


# ── Alan ve biçim tespiti ──
def dil_tahmin(kucuk: str) -> tuple[str, int]:
    temiz = OKUNUS.sub(" ", kucuk)
    puan = {k: say(r"(?<!\w)(?:" + v["sik"] + r")(?!\w)", temiz) for k, v in DIL.items()}
    en = max(puan, key=puan.get)
    return en, puan[en]


KISA_EK = r"(?:ler|lar|i|ı|u|ü|in|ın|un|ün|e|a|de|da|te|ta|den|dan|ten|tan|si|sı|leri|ları)?"


def sozcuk_deseni(s: str) -> str:
    """Uzun anahtar kök olarak (ekli biçimler de) eşleşir; 4 harf ve kısası yalnız kısa ekle (gen ≠ genel)."""
    e = r"(?<!\w)" + re.escape(s.strip())
    if len(s.strip()) <= 4 and s.strip()[-1:].isalpha():
        return e + KISA_EK + r"(?![\w])"
    return e


def alan_tespit(meta: dict, gor: str, profil: dict, alan: str | None = None) -> dict:
    """Önce --alan, sonra frontmatter `alan:`, sonra sözcük puanı. Kanıtı ve güveni döndürür."""
    secilen = alan or meta.get("alan", "").strip().lower()
    if secilen:
        if secilen not in profil or secilen.startswith("_"):
            raise ValueError(f"bilinmeyen alan: {secilen} ({', '.join(k for k in profil if not k.startswith('_'))})")
        return {"alan": secilen, "kaynak": "--alan" if alan else "frontmatter", "guven": "kesin",
                "kanit": [], "ikinci": None, "puanlar": {}}
    kucuk = gor.lower()
    puanlar, kanit = {}, {}
    for ad, p in profil.items():
        if ad.startswith("_") or not isinstance(p, dict) or not p.get("sozcukler"):
            continue
        toplam, ip = 0, []
        for s in p["sozcukler"]:
            n = min(say(sozcuk_deseni(s), kucuk), ALAN_SOZCUK_TAVAN)
            if n:
                toplam += n
                ip.append(s.strip())
        puanlar[ad], kanit[ad] = toplam, ip
    okunus = len(OKUNUS.findall(gor))
    _, sik = dil_tahmin(kucuk)
    dil_puan = 3 * okunus + (6 if re.search(r"\bokunuş", kucuk) else 0) + (min(sik, 30) // 3 if okunus else 0)
    puanlar["dil"], kanit["dil"] = dil_puan, ([f"{okunus} okunuş /…/"] if okunus else [])
    sira = sorted(puanlar.items(), key=lambda x: -x[1])
    (en, p1), (iki, p2) = sira[0], sira[1]
    # Alt alan önceliği: kazanan bir üst alansa (tıp, fen, matematik) ve alt alanlardan biri yeterince güçlüyse
    # daha özel olanı seç (hemşirelik notu tıp sözcüğü de taşır).
    ust = en
    altlar = [(a, puanlar.get(a, 0)) for a, pr in profil.items()
              if isinstance(pr, dict) and pr.get("ust") == en and not a.startswith("_")]
    if altlar:
        alt, pa = max(altlar, key=lambda x: x[1])
        if pa >= ALAN_EN_AZ and pa >= ALT_ALAN_ORAN * p1:
            en, iki, p2 = alt, ust, p1
            p1 = max(pa, p1)
    if p1 < ALAN_EN_AZ:
        return {"alan": "genel", "kaynak": "tespit", "guven": "düşük", "kanit": [], "ikinci": en if p1 else None,
                "puanlar": puanlar}
    guven = ("yüksek" if p1 >= GUVEN_YUKSEK_KAT * max(p2, 1) and p1 >= 2 * ALAN_EN_AZ
             else "orta" if p1 >= GUVEN_ORTA_KAT * max(p2, 1) else "düşük")
    return {"alan": en, "kaynak": "tespit", "guven": guven, "kanit": kanit[en][:6],
            "ikinci": iki if p2 >= ALAN_EN_AZ else None, "puanlar": puanlar}


def bicim_tespit(meta: dict, govde: str, gor: str, olcum: dict | None) -> str:
    if meta.get("bicim") in ("gorsel", "sozel"):
        return meta["bicim"]
    gorsel = len(GORSEL_MD.findall(govde))
    kelime = len(SOZCUK.findall(gor))
    if gorsel and kelime / gorsel < GORSEL_KELIME:
        return "gorsel"
    if olcum and olcum["sayfa"]:
        kelimeler = olcum.get("kelime") or [0] * olcum["sayfa"]
        oran = sum(1 for (_, _, g), k in zip(olcum["doluluk"], kelimeler) if g and k < GORSEL_KELIME) / olcum["sayfa"]
        if oran >= GORSEL_SAYFA_ORAN:
            return "gorsel"
    return "sozel"


# ── Kontroller: her biri (bağlam, ekle) alır ──
def k_dil_terim(c, ekle):
    terim = sum(say(r"(?<!\w)" + re.escape(t) + r"(?!\w)", c["kucuk"]) for t in
                [x.lower() for x in DIL[c["dil"]]["terim"] + TR_TERIMLER])
    if terim > TERIM_ESIK:
        ekle("Seviye", "UYARI", f"Dil bilgisi terimi {terim} kez (eşik {TERIM_ESIK})",
             "Acemide terim yerine KİM–FİİL–GERİSİ şeması ve Türkçe açıklama kullan")


def k_dil_hedef_disi(c, ekle):
    if c["dil"] != "en":
        ing = INGILIZCE.findall(c["kucuk"])
        if len(ing) > HEDEF_DISI_ESIK:
            ekle("Seviye", "UYARI", f"Hedef dışı dil (İngilizce) sözcükleri: {len(ing)} (eşik {HEDEF_DISI_ESIK})",
                 "Açıklama Türkçe olmalı; hedef dışı dil öğrenciye gitmez")


def k_dil_okunus_uzun(c, ekle):
    oku = c["okunuslar"]
    uzun = [o for o in oku if len(o.replace("·", " ").split()) > OKUNUS_UZUN]
    if oku and len(uzun) / len(oku) > OKUNUS_UZUN_ORAN:
        ekle("Ezber ve kavrama", "UYARI", f"Uzun cümle oranı yüksek: {len(uzun)}/{len(oku)} okunuş {OKUNUS_UZUN}+ kelime",
             "Ezber için cümleyi böl; tekrar eden iskelet kullan")


def k_dil_okunussuz(c, ekle):
    ayar = DIL[c["dil"]]
    sik = say(r"(?<!\w)(?:" + ayar["sik"] + r")(?!\w)", OKUNUS.sub(" ", c["kucuk"]))
    yabanci = sik >= YABANCI_ESIK or bool(ayar["aksan"] and re.search(ayar["aksan"], c["gor"]))
    if not c["okunuslar"] and yabanci and c["tur"] not in OKUNUS_ISTEMEYEN:
        ekle("Ezber ve kavrama", "UYARI", "Yabancı dilde metin var ama Türkçe harfli okunuş (/…/) yok",
             "Her yabancı cümlenin yanına okunuş ve Türkçe karşılık koy (Yabancı · Okunuş · Türkçe)")


DOZ_BIRIM = r"(?:mg|mcg|µg|μg|g|ml|mL|ünite|IU|U|mEq|mmol)"
SONDAKI_SIFIR = re.compile(r"(?<![\d.,])\d+[.,]0+\s*" + DOZ_BIRIM + r"(?![\w/])")
CIPLAK_ONDALIK = re.compile(r"(?<![\d\w.,])[.,]\d+\s*" + DOZ_BIRIM + r"(?!\w)")


def k_tip_doz_yazimi(c, ekle):
    sifir, ciplak = SONDAKI_SIFIR.findall(c["gor"]), CIPLAK_ONDALIK.findall(c["gor"])
    if sifir:
        ekle("Doğruluk", "HATA", f"Dozda sondaki sıfır ({', '.join(sorted(set(sifir))[:3])}): virgül görülmezse 10 kat hata",
             "5,0 mg → 5 mg (ISMP)")
    if ciplak:
        ekle("Doğruluk", "HATA", f"Dozda baştaki sıfırsız ondalık ({', '.join(sorted(set(ciplak))[:3])})",
             ",5 mg → 0,5 mg (ISMP)")


TEHLIKELI = [(re.compile(r"\b\d+\s*(?:U|IU|cc)\b"), "ünite için U/IU, mL için cc", "'ünite' ve 'mL' yaz"),
             (re.compile(r"(?<!\w)q\.?o?\.?d\.?(?!\w)", re.I), "q.d. / q.o.d.", "'günde bir' / 'iki günde bir' yaz"),
             (re.compile(r"\b(?:MSO4|MgSO4)\b"), "MSO4 / MgSO4", "ilacın tam adını yaz"),
             (re.compile(r"\d\s*[μµ]g\b"), "μg", "'mcg' yaz")]


def k_tip_tehlikeli_kisaltma(c, ekle):
    bulunan = [(ad, oneri) for desen, ad, oneri in TEHLIKELI if desen.search(c["gor"])]
    if bulunan:
        ekle("Doğruluk", "UYARI", "Karıştırılmaya açık tıbbi kısaltma: " + ", ".join(a for a, _ in bulunan),
             "; ".join(o for _, o in bulunan) + " (ISMP 'kullanma' listesi)")


KISALTMA = re.compile(r"(?<![\w.])([A-ZÇĞİÖŞÜ][A-ZÇĞİÖŞÜ0-9]{1,5})(?![\w.])")
ROMA = re.compile(r"^[IVXLCDM]+$")
BILINEN = {"TL", "ABD", "AB", "TC", "BM", "NATO", "DNA", "RNA", "ATP", "PDF", "SI", "OK", "TV", "MÖ", "MS", "TDK",
           "TBMM", "UYARI", "HATA", "NOT", "KİM", "FİİL", "GERİSİ"}


def k_kisaltma_tanimsiz(c, ekle):
    sayac = {}
    for k in KISALTMA.findall(c["gor"]):
        if not ROMA.match(k) and k not in BILINEN and sum(ch.isalpha() for ch in k) >= 2:
            sayac[k] = sayac.get(k, 0) + 1
    tanimsiz = []
    for k, n in sayac.items():
        if n < 2:
            continue
        e = re.escape(k)
        if re.search(r"\(\s*" + e + r"\s*[),;]|(?<!\w)" + e + r"\s*(?:\(|:|=|–|—|-\s)|^\s*[|*-]?\s*" + e + r"\s*[|:]",
                     c["gor"], re.M):
            continue
        tanimsiz.append(k)
    if len(tanimsiz) >= KISALTMA_ESIK:
        ekle("Seviye", "UYARI", f"Tanımsız kısaltma ({len(tanimsiz)}: {', '.join(sorted(tanimsiz)[:5])})",
             "İlk geçtiği yerde açılımını yaz: 'Ayırıcı tanı (AT)' ya da başa Kısaltmalar listesi koy")


def k_kilavuz_yilsiz(c, ekle):
    yilsiz = [m.group(0) for m in re.finditer(r"[^.\n]*\b(?:kılavuz|guideline|konsensüs)[^.\n]*", c["gor"], re.I)
              if not YIL.search(m.group(0))]
    if yilsiz:
        ekle("Doğruluk", "UYARI", f"Kılavuz/konsensüs anılıyor ama yılı yok ({len(yilsiz)} yer)",
             "Kılavuzun adını ve sürüm yılını yaz; güncelliğini kontrol et")


ORNEK = re.compile(r"(?:^|\n)\s*(?:#+\s*|\*\*|[-*]\s*)?(?:çözülmüş\s+)?(?:örnek|örnek vaka|vaka|çözüm|example)\s*\d*\s*[:：.)]"
                   r"|^#+[^\n]*\b(?:örnek|çözüm|vaka)|çözülmüş örnek|worked example", re.I | re.M)
CEVAP = re.compile(r"(?:cevap|çözüm|yanıt|answer)\s*\d*\s*[:：]|^#+[^\n]*\b(?:cevap|çözüm|yanıt)|cevap anahtar"
                   r"|^\s*\|?\s*(?:cevap|çözüm)\s*\|", re.I | re.M)


def k_cozulmus_ornek(c, ekle):
    if c["tur"] in SINAMA_ISTEYEN and not ORNEK.search(c["gor"]):
        ekle("Sıra ve akış", "UYARI", "Çözülmüş örnek (ya da örnek vaka) yok",
             "Kuraldan hemen sonra adım adım çözülmüş bir örnek koy; sonra yarım çözümlü, sonra çözümsüz")


def k_cevapsiz_alistirma(c, ekle):
    if re.search(r"alıştırma|\bsoru\s*\d|\bproblem\s*\d|egzersiz|\bsorular\b", c["gor"], re.I) and \
            not CEVAP.search(c["gor"]):
        ekle("Kendini sınama", "UYARI", "Alıştırma/soru var ama cevap ya da çözüm yok",
             "Cevap anahtarını ya da çözüm adımlarını ayrı bir bölüme koy")


DIS_SAYI = re.compile(r"(\d{1,2})\s*(?:numaralı|nolu|no['’]lu|no\.?)\s*diş|\bdiş\s*(?:no\.?|numarası)?\s*:?\s*#?(\d{1,2})\b"
                      r"|#(\d{1,2})\b", re.I)


def k_dis_numara_karisik(c, ekle):
    fdi, universal = set(), set()
    for m in DIS_SAYI.finditer(c["gor"]):
        no = next(g for g in m.groups() if g)
        n = int(no)
        if m.group(3) or not (10 < n < 90 and 1 <= n // 10 <= 8 and 1 <= n % 10 <= 8):
            universal.add(no)
        else:
            fdi.add(no)
    if fdi and universal:
        ekle("Doğruluk", "UYARI", f"Diş numaralama karışık: FDI gibi ({', '.join(sorted(fdi)[:3])}) ve "
             f"Universal gibi ({', '.join(sorted(universal)[:3])})",
             "Tek sistem seç (FDI/ISO 3950 ya da Universal), adını belgenin başına yaz")


OTORITE = re.compile(r"(?:tarihçilere|uzmanlara|araştırmacılara|bilim insanlarına|bazı kaynaklara|kaynaklara)\s+göre"
                     r"|bilindiği üzere|herkesçe bilin|kesin olarak bilinmektedir", re.I)
ATIF = re.compile(r"\([^()]*\d{4}[^()]*\)|\[\d+\]")


def k_kaynaksiz_otorite(c, ekle):
    n = [m.group(0) for s in CUMLE.findall(c["gor"]) for m in OTORITE.finditer(s) if not ATIF.search(s)]
    if n:
        ekle("Doğruluk", "UYARI", f"Kaynağı belirsiz otorite ({len(n)}: {', '.join(sorted(set(n))[:3])})",
             "Kimin söylediğini ve kaynağını yaz (yazar, yıl) ya da ifadeyi çıkar")


KAYNAKCA = re.compile(r"kaynak(?:ça|lar)?\s*[:：]|^#+\s*kaynak|kaynakça|bibliyografya|\breferences\b|\[\d+\]"
                      r"|\([A-ZÇĞİÖŞÜ][^()]*\d{4}\)", re.I | re.M)


def k_kaynakca_yok(c, ekle):
    if c["tur"] != "pano" and not KAYNAKCA.search(c["gor"]):
        ekle("Doğruluk", "UYARI", "Hiç kaynak gösterilmemiş", "Sonuna kaynakça ya da konu yanına (yazar, yıl) ekle")


def k_yuzyil_yazimi(c, ekle):
    roma = re.search(r"\b[XVI]+\.\s*(?:yüzyıl|yy)", c["gor"])
    arap = re.search(r"\b\d{1,2}\.\s*(?:yüzyıl|yy)", c["gor"])
    if roma and arap:
        ekle("Ezber ve kavrama", "UYARI", f"Yüzyıl yazımı karışık ({roma.group(0)} ve {arap.group(0)})",
             "Belge boyunca tek yazım kullan")


VERI = re.compile(r"\d[\d.,]*\s*(?:%|km²|km2|kişi|ton|milyon|milyar|mm\b|°c|hektar|dekar|m³)|%\s*\d|nüfus[^.\n]*\d", re.I)


def k_veri_yilsiz(c, ekle):
    yilsiz = [s.strip() for s in CUMLE.findall(c["gor"]) if VERI.search(s) and not YIL.search(s)]
    if len(yilsiz) >= VERI_YILSIZ_ESIK:
        ekle("Doğruluk", "UYARI", f"Yılı ve kaynağı olmayan sayısal veri ({len(yilsiz)} cümle; ilki: «{yilsiz[0][:60]}»)",
             "Veriyi yılı ve kaynağıyla ver (ör. TÜİK, 2024)")


HARITA_OGELERI = [("lejant", r"lejant|açıklama kutusu|legend|\bkey\b"), ("ölçek", r"ölçek|scale|1\s*:\s*\d"),
                  ("kuzey/yön", r"kuzey|yön oku|north"), ("kaynak", r"kaynak|source")]


def k_harita_ogeleri(c, ekle):
    eksik = []
    for m in re.finditer(r"!\[([^\]]*)\]\([^)]*\)", c["govde"]):
        cevre = c["govde"][max(0, m.start() - 300): m.end() + 300].lower()
        if "harita" not in m.group(1).lower() and "harita" not in c["govde"][m.end(): m.end() + 150].lower():
            continue
        yok = [ad for ad, desen in HARITA_OGELERI if not re.search(desen, cevre)]
        if yok:
            eksik.append(f"«{m.group(1)[:30] or 'adsız'}»: {', '.join(yok)}")
    if eksik:
        ekle("Okunaklılık", "UYARI", f"Haritada öğe eksik ({len(eksik)}): {'; '.join(eksik[:3])}",
             "Her haritaya başlık (konu + yer + yıl), lejant, ölçek, kuzey oku ve kaynak (kurum + veri yılı) ekle")


# ── Sağlık ortak kontrolleri (tıp, diş, hemşirelik, eczacılık, veteriner, beslenme, fizyoterapi, acil, psikoloji) ──
TEHLIKELI_EK = [
    (re.compile(r"\b\d+\s*(?:SC|SQ|sub\s?q)\b|\b(?:SC|SQ)\s+(?:yolla|uygula|enjeksiyon)", re.I), "SC/SQ (deri altı)", "'deri altı' / 'subkutan' yaz"),
    (re.compile(r"(?<!\w)(?:TIW|t\.i\.w\.|D/C)(?!\w)"), "TIW / D/C", "'haftada üç kez', 'kes' ya da 'taburcu' yaz"),
    (re.compile(r"(?<!\w)(?:AD|AS|AU|OD|OS|OU)\s+(?:damla|uygula|\d)", re.I), "AD/AS/AU, OD/OS/OU (kulak/göz)", "'sağ kulak', 'sol göz' diye yaz"),
    (re.compile(r"(?<![\w<>])[<>]\s*\d+\s*(?:mg|mcg|mL|ml|U)\b"), "doz önünde > / <", "'en çok' / 'en az' yaz"),
]


def k_saglik_kisaltma_ek(c, ekle):
    bulunan = [(ad, oneri) for desen, ad, oneri in TEHLIKELI_EK if desen.search(c["gor"])]
    if bulunan:
        ekle("Doğruluk", "UYARI", "Karıştırılmaya açık klinik kısaltma: " + ", ".join(a for a, _ in bulunan),
             "; ".join(o for _, o in bulunan) + " (ISMP)")


MGKG = re.compile(r"\d[\d.,]*\s*(?:mg|mcg|g|mL|ml|U|ünite)\s*/\s*kg(?!\s*/\s*(?:gün|doz|saat|dk|h)\b)(?!\w)(?:\s*/\s*d\b)?", re.I)


def k_doz_kg_belirsiz(c, ekle):
    belirsiz = [m.group(0) for m in MGKG.finditer(c["gor"])
                if not re.search(r"(?:günde|/gün|her\s+\d+\s*saat|doz başına|tek doz|bölünmüş)",
                                 c["gor"][m.end(): m.end() + 60], re.I)]
    if belirsiz:
        ekle("Doğruluk", "UYARI", f"Kiloya göre doz zaman birimi belirsiz ({', '.join(sorted(set(belirsiz))[:3])})",
             "'mg/kg/gün' mü 'mg/kg/doz' mu yaz; sıklığı ve en yüksek dozu ekle")


ANALIT = {"glukoz": ("mg/dl", "mmol/l"), "glikoz": ("mg/dl", "mmol/l"), "kolesterol": ("mg/dl", "mmol/l"),
          "kreatinin": ("mg/dl", "µmol/l|μmol/l|umol/l"), "üre": ("mg/dl", "mmol/l"), "kalsiyum": ("mg/dl", "mmol/l"),
          "trigliserit": ("mg/dl", "mmol/l"), "bilirubin": ("mg/dl", "µmol/l|μmol/l|umol/l"),
          "hemoglobin": ("g/dl", "g/l|mmol/l")}


def k_lab_birim_karisik(c, ekle):
    k = c["kucuk"]
    karisik = []
    for analit, (geleneksel, si) in ANALIT.items():
        if not re.search(r"(?<!\w)" + analit, k):
            continue
        cumleler = [x for x in CUMLE.findall(k) if analit in x]
        g = any(re.search(re.escape(geleneksel), x) for x in cumleler)
        si_var = any(re.search(si, x) for x in cumleler)
        donusum = re.search(r"dönüşüm|çarp|× ?\d|katsayı|=\s*\d", " ".join(cumleler))
        if g and si_var and not donusum:
            karisik.append(analit)
    if karisik:
        ekle("Doğruluk", "UYARI", f"Aynı analit iki birimle ve dönüşüm yazılmadan ({', '.join(karisik)})",
             "Tek birim kullan ya da dönüşüm katsayısını yaz (ör. glukoz mg/dL ÷ 18 = mmol/L)")


def k_referans_kaynaksiz(c, ekle):
    yok = [x.strip() for x in CUMLE.findall(c["gor"])
           if re.search(r"referans aralı|normal değer|normal aralı", x, re.I)
           and not re.search(r"kaynak|laboratuvar|\(\w[^()]*\d{4}\)|\[\d+\]|yaş|cinsiyet|erişkin|çocuk", x, re.I)]
    if len(yok) >= 2:
        ekle("Doğruluk", "UYARI", f"Referans aralığı kaynaksız ve koşulsuz ({len(yok)} yer)",
             "Aralık laboratuvara, yaşa ve cinsiyete göre değişir; kaynağını ve geçerli grubu yaz")


def k_gebelik_kategorisi(c, ekle):
    if re.search(r"gebelik\s+kategori\w*\s*[:：]?\s*[ABCDX]\b|kategori\s+[ABCDX]\b[^.\n]*gebe|pregnancy\s+category\s+[ABCDX]\b",
                 c["gor"], re.I):
        ekle("Doğruluk", "UYARI", "Harfli gebelik kategorisi (A/B/C/D/X) kullanılmış",
             "FDA bu harfleri 2015'te (PLLR) kaldırdı; hangi sistemi ve hangi yılı kullandığını yaz, ya da güncel "
             "prospektüsteki gebelik/emzirme bölümünü özetle")


# ICD-10 bilerek yok: ICD-11 2022'de yürürlüğe girdi ama ülkeler ICD-10 ile kodlamayı sürdürebiliyor (WHO).
ESKI_SURUM = [(re.compile(r"\bDSM[- ]?(?:III|IV)(?:-TR)?\b"), "DSM-IV/III", "DSM-5-TR (2022)", r"DSM[- ]?5")]


def k_tani_surumu_eski(c, ekle):
    for desen, ad, yeni, guncel in ESKI_SURUM:
        if desen.search(c["gor"]) and not re.search(guncel, c["gor"]):
            ekle("Doğruluk", "UYARI", f"Eski tanı sistemi sürümü: {ad}", f"Güncel sürüm {yeni}; tarihçe değilse güncelle")


def k_kilavuz_eski(c, ekle):
    sinir = BU_YIL - KILAVUZ_YAS
    eski = sorted({int(y) for m in re.finditer(r"[^.\n]*\b(?:kılavuz|guideline|konsensüs|AHA|ERC|ESC|GINA|GOLD|KDIGO)[^.\n]*",
                                                c["gor"], re.I)
                   for y in YIL.findall(m.group(0)) if 1990 <= int(y) < sinir})
    if eski:
        ekle("Doğruluk", "UYARI", f"{KILAVUZ_YAS} yıldan eski kılavuz anılıyor ({', '.join(map(str, eski[:3]))})",
             "Kılavuzun güncel sürümünü kontrol et; eski sürümü bilerek kullanıyorsan nedenini yaz")


HASTA_AD = re.compile(r"(?:hasta(?:nın)?\s+ad[ıi](?:\s+soyad[ıi])?|hasta)\s*[:：]\s*([A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+[A-ZÇĞİÖŞÜ][a-zçğıöşü]+)")
PROTOKOL = re.compile(r"\b(?:protokol|dosya|hasta)\s*(?:no|numarası)\s*[:：]?\s*\d{4,}", re.I)


def k_hasta_kimlik(c, ekle):
    ad = HASTA_AD.findall(c["gor"])
    proto = PROTOKOL.findall(c["gor"])
    if ad or proto:
        ekle("Doğruluk", "HATA", f"Vakada hastayı tanıtabilecek bilgi ({'ad soyad' if ad else ''}{' ' if ad and proto else ''}"
             f"{'protokol/dosya no' if proto else ''})",
             "Ad, numara, tam tarih ve fotoğrafı çıkar; yaş ve cinsiyetle anlat ('58 yaşında erkek hasta')")


BINOM = re.compile(r"\b(Escherichia|Staphylococcus|Streptococcus|Mycobacterium|Salmonella|Pseudomonas|Klebsiella|Candida|"
                   r"Plasmodium|Helicobacter|Clostridium|Bacillus|Homo|Drosophila|Saccharomyces|Arabidopsis|Enterococcus|"
                   r"Neisseria|Listeria|Treponema|Toxoplasma|Giardia|Aspergillus|Canis|Felis|Bos|Equus|Rattus|Mus)\s+([A-Za-z]+)")
BINOM_KUCUK = re.compile(r"(?<![\w.])(escherichia|staphylococcus|streptococcus|mycobacterium|salmonella|pseudomonas|"
                         r"klebsiella|candida|plasmodium|helicobacter)\s+[a-z]+")
BITISIK_KISALTMA = re.compile(r"\b([A-Z])\.(coli|aureus|pneumoniae|pylori|albicans|tuberculosis|sapiens|melanogaster)\b")


def k_tur_adi_yazimi(c, ekle):
    hatali = [f"{a} {b}" for a, b in BINOM.findall(c["gor"]) if b[:1].isupper()]
    hatali += BINOM_KUCUK.findall(c["gor"])
    hatali += [f"{a}.{b}" for a, b in BITISIK_KISALTMA.findall(c["gor"])]
    if hatali:
        ekle("Doğruluk", "UYARI", f"Tür adı yazımı ({', '.join(sorted(set(hatali))[:3])})",
             "Cins büyük, tür küçük harfle ve italik: *Escherichia coli*, kısaltırken *E. coli* (noktadan sonra boşluk)")


VET_TUR = re.compile(r"köpek|kedi|at\b|atlar|sığır|koyun|keçi|domuz|tavuk|kanatlı|tavşan|kemirgen|buzağı|kuzu|equine|canine|feline|bovine", re.I)


def k_vet_tursuz_doz(c, ekle):
    tursuz = [x.strip()[:50] for x in CUMLE.findall(c["gor"])
              if re.search(r"\d\s*(?:mg|mcg|mL|ml)\s*/\s*kg", x, re.I) and not VET_TUR.search(x)]
    if tursuz:
        ekle("Doğruluk", "UYARI", f"Türü belirtilmemiş doz ({len(tursuz)}; ilki: «{tursuz[0]}»)",
             "Doz türe göre değişir (ör. kedide parasetamol toksik); her dozun yanına hayvan türünü yaz")
    if re.search(r"\b(?:sığır|koyun|keçi|tavuk|kanatlı|domuz|süt|yumurta)\b", c["gor"], re.I) and \
            re.search(r"\d\s*(?:mg|mL|ml)\s*/\s*kg", c["gor"], re.I) and not re.search(r"arınma|bekleme süresi|withdrawal", c["gor"], re.I):
        ekle("Doğruluk", "UYARI", "Gıda hayvanında ilaç dozu var ama arınma (bekleme) süresi yok",
             "Et/süt/yumurta için arınma süresini yaz")


def k_beslenme_birim(c, ekle):
    if re.search(r"\d\s*kalori\b", c["gor"], re.I):
        ekle("Doğruluk", "UYARI", "Enerji 'kalori' diye yazılmış", "Besin enerjisi kcal (ya da kJ) ile yazılır: '2000 kcal'")


SAGLIK_BEYANI = re.compile(r"(?:kanser|diyabet|şeker hastalığı|tansiyon|hastalığ\w*|enfeksiyon)\w*\s+(?:\w+\s+){0,3}"
                           r"(?:tedavi eder|iyileştirir|önler|geçirir|yok eder|şifa)", re.I)


def k_saglik_beyani(c, ekle):
    b = SAGLIK_BEYANI.findall(c["gor"])
    if b:
        ekle("Doğruluk", "UYARI", f"Besine hastalık tedavi/önleme özelliği yükleniyor ({len(b)} yer)",
             "Gıdaya hastalığı önleme/tedavi etme özelliği atfetmek beyan mevzuatında yasak; kanıtı ve kaynağı yaz, "
             "ifadeyi 'X ile ilişkili bulundu (kaynak)' diye daralt")


def k_bakim_plani(c, ekle):
    if re.search(r"bakım planı|hemşirelik süreci", c["gor"], re.I):
        eksik = [ad for ad, d in [("tanı", r"hemşirelik tanısı|tanı\s*[:：]"), ("amaç/hedef", r"amaç|hedef|beklenen sonuç"),
                                  ("girişim", r"girişim|uygulama"), ("değerlendirme", r"değerlendirme")]
                 if not re.search(d, c["gor"], re.I)]
        if eksik:
            ekle("Sıra ve akış", "UYARI", f"Bakım planında aşama eksik: {', '.join(eksik)}",
                 "Hemşirelik süreci: veri toplama → tanı → amaç → girişim → değerlendirme")


def k_egzersiz_recetesi(c, ekle):
    recete = [x for x in CUMLE.findall(c["gor"]) if re.search(r"egzersiz|germe|kuvvetlendirme", x, re.I)
              and re.search(r"\d", x)]
    if recete:
        tum = " ".join(recete)
        eksik = [ad for ad, d in [("sıklık", r"günde|haftada|kez|gün"), ("yoğunluk", r"yoğunluk|%|rpe|borg|kg|direnç|ağırlık"),
                                  ("süre/tekrar", r"dakika|dk|saniye|sn|tekrar|set"), ("tip", r"aerobik|izometrik|germe|kuvvet|denge")]
                 if not re.search(d, tum, re.I)]
        if len(eksik) >= 2:
            ekle("Ezber ve kavrama", "UYARI", f"Egzersiz reçetesinde FITT öğesi eksik: {', '.join(eksik)}",
                 "Sıklık, yoğunluk, süre (set × tekrar) ve tipi yaz")


# ── Fen, mühendislik, sayısal alanlar ──
SI_YANLIS = re.compile(r"\d\s*(Kg|KG|Km|KM|gr|Gr|lt|Lt|LT|mt|Mt|Sn|cc|KW|Kw|kw|Mhz|MHZ|mhz|KHz|khz)\b")
SI_DOGRU = {"Kg": "kg", "KG": "kg", "Km": "km", "KM": "km", "gr": "g", "Gr": "g", "lt": "L", "Lt": "L", "LT": "L",
            "mt": "m", "Mt": "m", "Sn": "s", "cc": "mL (cm³)", "KW": "kW", "Kw": "kW", "kw": "kW", "Mhz": "MHz",
            "MHZ": "MHz", "mhz": "MHz", "KHz": "kHz", "khz": "kHz"}


def k_si_birim(c, ekle):
    yanlis = sorted(set(SI_YANLIS.findall(c["gor"])))
    if yanlis:
        ekle("Doğruluk", "UYARI", f"Birim sembolü yanlış yazılmış ({', '.join(yanlis[:5])})",
             "SI sembolleri büyük/küçük harfe duyarlıdır: " + ", ".join(f"{y} → {SI_DOGRU[y]}" for y in yanlis[:5]))


TEHLIKELI_KIMYASAL = re.compile(r"\b(?:HCl|H2SO4|HNO3|NaOH|KOH|derişik|asit|baz|aseton|eter|etanol|metanol|formaldehit|"
                                r"amonyak|klor|civa|benzen|kloroform|bek|alev|ısıt)\w*", re.I)


SI_BITISIK = re.compile(r"(?<![\w.,/])\d+(?:[.,]\d+)?(kg|km|cm|mm|mg|mL|ml|kJ|kcal|kPa|MPa|Pa|kW|kN|N|J|W|V|mA|A|Hz|kHz|MHz|mol|K)\b")


def k_si_bosluk(c, ekle):
    bitisik = sorted(set(m.group(0) for m in SI_BITISIK.finditer(c["gor"])))
    if len(bitisik) >= 2:
        ekle("Ezber ve kavrama", "UYARI", f"Sayı ile birim bitişik ({', '.join(bitisik[:4])})",
             "SI kuralı: sayı ile birim arasına boşluk (5 kg, 12 V); yalnız açı derecesi (30°) bitişik")


def k_lab_guvenlik(c, ekle):
    if re.search(r"deney|laboratuvar|föy|uygulama adımları", c["gor"], re.I) and TEHLIKELI_KIMYASAL.search(c["gor"]) and \
            not re.search(r"güvenlik|koruyucu|gözlük|eldiven|önlük|çeker ocak|GHS|H\d{3}|tehlike", c["gor"], re.I):
        ekle("Doğruluk", "UYARI", "Deneyde tehlikeli madde/ısı var ama güvenlik notu yok",
             "Kişisel koruyucu (gözlük, eldiven, önlük), çeker ocak ve GHS tehlike ifadelerini ekle")


P_SIFIR = re.compile(r"\bp\s*[=<]\s*0?[.,]000\b|\bp\s*=\s*0\b", re.I)


def k_p_degeri(c, ekle):
    if P_SIFIR.search(c["gor"]):
        ekle("Doğruluk", "UYARI", "p değeri 0,000 ya da 0 yazılmış", "p sıfır olamaz: 'p < ,001' (APA: p < .001) yaz")


def k_kod_ornegi(c, ekle):
    bloklar = re.findall(r"^```([^\n]*)\n(.*?)^```", c["govde"], re.S | re.M)
    etiketsiz = [b for dil, b in bloklar if not dil.strip()]
    if len(bloklar) >= 2 and etiketsiz:
        ekle("Okunaklılık", "UYARI", f"Dil etiketi olmayan kod bloğu ({len(etiketsiz)}/{len(bloklar)})",
             "```python gibi dil etiketi koy (renklendirme ve kopyalama için)")
    kod = "\n".join(b for _, b in bloklar)
    if re.search(r"^\s*print\s+[\"'\w]", kod, re.M) or re.search(r"\bpython\s*2(?:\.\d)?\b|\braw_input\(", c["govde"], re.I):
        ekle("Doğruluk", "UYARI", "Python 2 sözdizimi ya da sürümü", "Python 2 2020'de desteğini yitirdi; print(...) ve Python 3 kullan")
    uzun = [satir for dil, b in bloklar if dil.strip().lower() in ("python", "py") for satir in b.splitlines() if len(satir) > 99]
    if uzun:
        ekle("Okunaklılık", "UYARI", f"Python kodunda 99 karakteri aşan satır ({len(uzun)})",
             "PEP 8: satır en çok 79 karakter (ekip kararıyla 99); satırı böl")
    if bloklar and not re.search(r"python\s*3\.\d+|sürüm|versiyon|version|node\s*\d+|java\s*\d+|gcc|requirements", c["govde"], re.I):
        ekle("Ezber ve kavrama", "UYARI", "Kod örneği var ama dil/kitaplık sürümü yazılmamış",
             "Örneğin çalıştığı sürümü yaz (ör. Python 3.12)")


# ── Hukuk ──
MULGA = {"765": "5237 sayılı TCK (2005)", "818": "6098 sayılı TBK (2012)", "743": "4721 sayılı TMK (2002)",
         "1086": "6100 sayılı HMK (2011)", "6762": "6102 sayılı TTK (2012)", "1412": "5271 sayılı CMK (2005)"}


# Kaldırılma hükmü mevzuat.gov.tr'de yeni kanunun metninde doğrulananlar (6098 m. 647, 6100 m. 450, 6102 m. 1533) HATA;
# yürürlük kanunuyla kaldırılan ve metni bu denetimde açılamayanlar UYARI.
MULGA_DOGRULANAN = ("818", "1086", "6762")


def k_hukuk_mulga(c, ekle):
    bulunan = [no for no in MULGA if re.search(r"\b" + no + r"\s+sayılı", c["gor"])]
    tarihce = re.search(r"mülga|yürürlükten kalk|eski kanun|önceki düzenleme|karşılaştır", c["gor"], re.I)
    if bulunan and not tarihce:
        duzey = "HATA" if any(n in MULGA_DOGRULANAN for n in bulunan) else "UYARI"
        ekle("Doğruluk", duzey, f"Yürürlükten kalkmış kanun güncel gibi anılıyor ({', '.join(no + ' sayılı' for no in bulunan)})",
             "Yerine: " + "; ".join(MULGA[n] for n in bulunan) + ". Karşılaştırma yapıyorsan 'mülga' diye belirt")


def k_hukuk_kanun_numarasiz(c, ekle):
    adlar = set(re.findall(r"\b((?:[A-ZÇĞİÖŞÜ][a-zçğıöşü]+\s+){1,4}Kanunu)\b", c["gor"]))
    numarasiz = [a for a in adlar if not re.search(r"\d{3,4}\s+sayılı\s+" + re.escape(a.split()[0]), c["gor"])]
    if len(numarasiz) >= 2:
        ekle("Doğruluk", "UYARI", f"Kanun adı numarasız ({', '.join(sorted(numarasiz)[:3])})",
             "İlk geçtiği yerde '6098 sayılı Türk Borçlar Kanunu' gibi numarasıyla yaz")


def k_hukuk_karar_kunyesi(c, ekle):
    eksik = [x.strip()[:50] for x in CUMLE.findall(c["gor"])
             if re.search(r"Yargıtay|Danıştay|Anayasa Mahkemesi|Bölge Adliye", x) and re.search(r"karar|içtihat", x, re.I)
             and not re.search(r"E\.\s*\d|K\.\s*\d|Esas|B\.\s*No|\d{4}/\d+", x)]
    if eksik:
        ekle("Doğruluk", "UYARI", f"Mahkeme kararı künyesiz anılıyor ({len(eksik)})",
             "Daire, E. (esas), K. (karar) ve T. (tarih) yaz: 'Yarg. 4. HD, E. 2019/123, K. 2020/456, T. 12.03.2020'")


# ── Beşerî bilimler ──
def k_hadis_kaynaksiz(c, ekle):
    yok = [x.strip()[:50] for x in CUMLE.findall(c["gor"]) if re.search(r"hadis|buyurdu|rivayet", x, re.I)
           and not re.search(r"Buhâr|Buhar|Müslim|Tirmiz|Ebû Dâvûd|Ebu Davud|Nesâ|Nesai|İbn Mâce|İbn Mace|Ahmed|Mâlik|Malik|"
                             r"Dârimî|\(\w[^()]*\d+\)", x, re.I)]
    if yok:
        ekle("Doğruluk", "UYARI", f"Hadis kaynaksız ({len(yok)}; ilki: «{yok[0]}»)",
             "Kaynağını (ör. Buhârî, Îmân, 2) ve gerekiyorsa sıhhat derecesini yaz")


def k_ayet_kaynaksiz(c, ekle):
    yok = [x.strip()[:50] for x in CUMLE.findall(c["gor"]) if re.search(r"\bayet|âyet", x, re.I) and re.search(r"[\"“«]", x)
           and not re.search(r"\d+\s*[:/]\s*\d+|sûre|sure\w*\s+\d", x, re.I)]
    if yok:
        ekle("Doğruluk", "UYARI", f"Âyet meali sure:âyet numarasız ({len(yok)})", "Sure adı ve âyet numarasını yaz: (Bakara 2/255)")


ALINTI = re.compile(r"[\"“«]([^\"”»]{60,})[\"”»]")


def k_alinti_kaynaksiz(c, ekle):
    yok = []
    for m in ALINTI.finditer(c["gor"]):
        sonra = c["gor"][m.end(): m.end() + 80]
        if not re.search(r"\(\w[^()]*(?:\d{4}|s\.\s*\d|\d+\s*[:/]\s*\d+)[^()]*\)|\[\d+\]|—\s*\w", sonra):
            yok.append(m.group(1)[:40])
    if len(yok) >= 2:
        ekle("Doğruluk", "UYARI", f"Doğrudan alıntı kaynaksız ({len(yok)})",
             "Alıntının hemen ardına yazar, eser, yıl ve sayfa yaz: (Tanpınar, 1949, s. 12)")


def k_eser_kunyesi(c, ekle):
    eksik = [alt for alt in re.findall(r"!\[([^\]]+)\]\(", c["govde"]) if not YIL.search(alt) and not re.search(r"yy|yüzyıl|\d{2,4}", alt)]
    if len(eksik) >= 2:
        ekle("Okunaklılık", "UYARI", f"Eser görselinde künye eksik ({len(eksik)}: {', '.join(e[:25] for e in eksik[:2])})",
             "Her eser için sanatçı, eser adı, yıl, teknik ve bulunduğu yer yaz")


def k_cizim_olcegi(c, ekle):
    if re.search(r"\b(?:plan|kesit|görünüş|vaziyet|rölöve|detay)\b", c["gor"], re.I) and GORSEL_MD.search(c["govde"]) and \
            not re.search(r"\b1\s*[:/]\s*\d+|ölçek", c["gor"], re.I):
        ekle("Okunaklılık", "UYARI", "Teknik çizim var ama ölçek yok", "Her çizime ölçek (1:50, 1:100) ve kuzey/yön ekle")

KONTROLLER = {
    "dil_terim": k_dil_terim, "dil_hedef_disi": k_dil_hedef_disi, "dil_okunus_uzun": k_dil_okunus_uzun,
    "dil_okunussuz": k_dil_okunussuz, "tip_doz_yazimi": k_tip_doz_yazimi,
    "tip_tehlikeli_kisaltma": k_tip_tehlikeli_kisaltma, "kisaltma_tanimsiz": k_kisaltma_tanimsiz,
    "kilavuz_yilsiz": k_kilavuz_yilsiz, "cozulmus_ornek": k_cozulmus_ornek,
    "cevapsiz_alistirma": k_cevapsiz_alistirma, "dis_numara_karisik": k_dis_numara_karisik,
    "kaynaksiz_otorite": k_kaynaksiz_otorite, "kaynakca_yok": k_kaynakca_yok, "yuzyil_yazimi": k_yuzyil_yazimi,
    "veri_yilsiz": k_veri_yilsiz, "harita_ogeleri": k_harita_ogeleri,
    "saglik_kisaltma_ek": k_saglik_kisaltma_ek, "doz_kg_belirsiz": k_doz_kg_belirsiz,
    "lab_birim_karisik": k_lab_birim_karisik, "referans_kaynaksiz": k_referans_kaynaksiz,
    "gebelik_kategorisi": k_gebelik_kategorisi, "tani_surumu_eski": k_tani_surumu_eski, "kilavuz_eski": k_kilavuz_eski,
    "hasta_kimlik": k_hasta_kimlik, "tur_adi_yazimi": k_tur_adi_yazimi, "vet_tursuz_doz": k_vet_tursuz_doz,
    "beslenme_birim": k_beslenme_birim, "saglik_beyani": k_saglik_beyani, "bakim_plani": k_bakim_plani,
    "egzersiz_recetesi": k_egzersiz_recetesi, "si_birim": k_si_birim, "si_bosluk": k_si_bosluk, "lab_guvenlik": k_lab_guvenlik,
    "p_degeri": k_p_degeri, "kod_ornegi": k_kod_ornegi, "hukuk_mulga": k_hukuk_mulga,
    "hukuk_kanun_numarasiz": k_hukuk_kanun_numarasiz, "hukuk_karar_kunyesi": k_hukuk_karar_kunyesi,
    "hadis_kaynaksiz": k_hadis_kaynaksiz, "ayet_kaynaksiz": k_ayet_kaynaksiz, "alinti_kaynaksiz": k_alinti_kaynaksiz,
    "eser_kunyesi": k_eser_kunyesi, "cizim_olcegi": k_cizim_olcegi,
}


def tc_gecerli(n: str) -> bool:
    """TC kimlik numarası sağlaması: 10. hane = ((tekler×7) − çiftler) mod 10, 11. hane = ilk 10 hanenin toplamı mod 10."""
    d = [int(x) for x in n]
    return (len(d) == 11 and d[0] != 0 and ((sum(d[0:9:2]) * 7 - sum(d[1:8:2])) % 10) == d[9]
            and sum(d[:10]) % 10 == d[10])


# ── Ortak çekirdek (her alanda) ──
def cekirdek(c, ekle, profil_alan):
    gor, govde, meta, olcum = c["gor"], c["govde"], c["meta"], c["olcum"]
    karisik = karisik_sozcukler(gor)
    if karisik:
        ekle("Doğruluk", "HATA", f"Latin harfle karışık yabancı alfabe harfi ({len(karisik)} sözcük: "
             f"{', '.join(sorted(set(karisik))[:3])})", "--duzelt benzer harfleri Latin harfe çevirir")
    elif c["dil"] != "ru" and KIRIL.search(gor):
        ekle("Doğruluk", "HATA", f"Kiril harf var ({len(KIRIL.findall(gor))})", "Hedef dil Kiril değil; elle düzelt")
    if YER_TUTUCU.search(gor):
        ekle("Doğruluk", "HATA", "Bitmemiş yer işareti (TODO/FIXME/???) öğrenciye gidiyor", "Tamamla ya da sil")
    tc = [n for n in re.findall(r"(?<!\d)[1-9]\d{10}(?!\d)", gor) if tc_gecerli(n)]
    if tc:
        ekle("Doğruluk", "HATA", f"Geçerli TC kimlik numarası var ({len(tc)}): kişisel veri öğrenci materyaline girmez",
             "Numarayı sil; vakada kimlik bilgisi kullanma (KVKK)")

    basliklar = BASLIK_MD.findall(govde) + BASLIK_HTML.findall(govde)
    if any(arti for _, arti in basliklar):
        ekle("Sıra ve akış", "UYARI", "Ek numaralı başlık (3.5+)", "Düz numarala; araya giren bölümle yeniden numarala")
    gorulen, onceki = set(), None
    for no, _ in basliklar:
        if no in gorulen:
            ekle("Sıra ve akış", "UYARI", f"Aynı başlık numarası iki kez: {no}", "Yeniden numarala")
        gorulen.add(no)
        t = tuple(int(x) for x in no.split("."))
        if onceki and len(t) == len(onceki) and t[:-1] == onceki[:-1] and t[-1] < onceki[-1]:
            ekle("Sıra ve akış", "UYARI", f"Başlık numarası geriye gidiyor: {'.'.join(map(str, onceki))} → {no}",
                 "Sırayı düzelt")
        onceki = t
    gonderme = SAYFA_GONDERME.findall(gor)
    if gonderme and c["tur"] != "kilavuz":
        ekle("Sıra ve akış", "UYARI", f"Belge içi sayfa göndermesi ({', '.join(sorted(set(gonderme))[:3])})",
             "Sayfa kayar; bölüm numarası ya da adı kullan")

    if c["tur"] in SINAMA_ISTEYEN and not SINAMA.search(gor):
        ekle("Kendini sınama", "UYARI", "Test / soru / alıştırma bölümü yok", profil_alan["sinama_oneri"])

    # Görsel: alt metin ve şekil başlığı (her alanda; ağırlık görselse başlık zorunlu)
    bos_alt = len(re.findall(r"!\[\s*\]\(", govde)) + len([m for m in re.findall(r"<img\b[^>]*>", govde, re.I)
                                                           if not re.search(r"\balt\s*=\s*['\"][^'\"]+", m)])
    if bos_alt:
        ekle("Okunaklılık", "UYARI", f"Açıklamasız görsel ({bos_alt}): alt metin yok", "Her görsele ne gösterdiğini yaz")
    if c["bicim"] == "gorsel" and len(GORSEL_MD.findall(govde)) >= 3 and not SEKIL_BASLIGI.search(gor):
        ekle("Okunaklılık", "UYARI", "Görsel ağırlıklı belgede şekil başlığı/numarası yok",
             "Her görsele 'Şekil N: …' başlığı ve kısa açıklama koy; metinde numarasıyla an")

    if olcum:
        y = olcum["yazi"]
        if y and y < YAZI_HATA:
            ekle("Okunaklılık", "HATA", f"Yazı çok küçük (ortanca {y} pt < {YAZI_HATA})", "Gövdeyi ≥ 11 pt, tabloyu ≥ 9 pt yap")
        elif y and y < YAZI_UYARI:
            ekle("Okunaklılık", "UYARI", f"Yazı küçük (ortanca {y} pt < {YAZI_UYARI})", "Tabloyu ≥ 9 pt yap")
        try:
            not_say = int(meta.get("not_sayfasi", 0) or 0)
        except ValueError:
            not_say = 0
        icerik = olcum["doluluk"][: len(olcum["doluluk"]) - not_say] if not_say else olcum["doluluk"]
        bos = [i for i, d, g in icerik if d < BOS_SAYFA and not g]
        if bos:
            ekle("Okunaklılık", "HATA", f"Boş sayfa: {bos}", "Zorunlu sayfa geçişini kaldır")
        yarim = [i for i, d, g in icerik[:-1] if BOS_SAYFA <= d < YARIM_SAYFA and not g]
        if icerik and len(yarim) / len(icerik) > YARIM_ORAN:
            ekle("Verimlilik", "UYARI", f"Yarım sayfa çok ({len(yarim)}/{len(icerik)}: {yarim[:8]})",
                 "Zorunlu sayfa geçişlerini azalt; büyük tabloyu bölünebilir yap")
        tavan = meta.get("sayfa_tavan", "")
        if tavan.isdigit() and olcum["sayfa"] > int(tavan):
            ekle("Verimlilik", "HATA", f"Sayfa tavanı aşıldı: {olcum['sayfa']} > {tavan}",
                 "Tekrarı ve dolguyu at, tavanın altına indir")
        elif not tavan.isdigit() and olcum["sayfa"] >= SAYFA_UYARI:
            ekle("Verimlilik", "UYARI", f"{olcum['sayfa']} sayfa ({SAYFA_UYARI}+): gerekçe ister",
                 "Frontmatter'a sayfa_tavan yaz ya da kısalt")


# ── Denetim ──
def denetle(metin: str, olcum: dict | None = None, alan: str | None = None, dil: str | None = None) -> dict:
    """metin: .md içeriği; olcum: pdf_olc() sonucu ya da None; alan/dil: tespiti geçmek için."""
    profil = profiller()
    meta, govde = on_bilgi(metin)
    gor = gorunur(govde)
    kucuk = gor.lower()
    tespit = alan_tespit(meta, gor, profil, alan)
    a = tespit["alan"]
    if dil and dil not in DIL:
        raise ValueError(f"desteklenmeyen dil: {dil} ({', '.join(DIL)})")
    dil_kodu = dil or meta.get("dil") or (dil_tahmin(kucuk)[0] if a == "dil" else "")
    if a == "dil" and dil_kodu not in DIL:
        raise ValueError(f"desteklenmeyen dil: {dil_kodu} ({', '.join(DIL)})")
    c = {"meta": meta, "govde": govde, "gor": gor, "kucuk": kucuk, "tur": meta.get("tur", ""), "olcum": olcum,
         "dil": dil_kodu, "okunuslar": OKUNUS.findall(gor), "bicim": bicim_tespit(meta, govde, gor, olcum)}
    bulgu: list[dict] = []

    def ekle(boyut, duzey, mesaj, oneri=""):
        bulgu.append({"boyut": boyut, "duzey": duzey, "mesaj": mesaj, "oneri": oneri})

    cekirdek(c, ekle, profil[a])
    for ad in kontrol_listesi(profil, a):
        KONTROLLER[ad](c, ekle)

    puan = {}
    for b in BOYUTLAR:
        d = [x["duzey"] for x in bulgu if x["boyut"] == b]
        if not d and b in PDF_BOYUTLARI and not olcum:
            puan[b] = None
        else:
            puan[b] = 0 if "HATA" in d else 1 if "UYARI" in d else 2
    olculen = [v for v in puan.values() if v is not None]
    elle = {"Doğruluk": meta.get("denetim", ""), "Hedefle uyum": meta.get("hedef", "") or meta.get("sinav", "")}
    hata = any(x["duzey"] == "HATA" for x in bulgu)
    return {"alan": a, "alan_adi": profil[a]["ad"], "tespit": tespit, "bicim": c["bicim"], "dil": dil_kodu,
            "tur": c["tur"], "puan": puan, "toplam": sum(olculen), "azami": 2 * len(olculen),
            "bulgular": sorted(bulgu, key=lambda x: (x["duzey"] != "HATA", BOYUTLAR.index(x["boyut"]))),
            "elle": elle, "elle_liste": elle_listesi(profil, a) + (profil["_gorsel"]["elle"] if c["bicim"] == "gorsel" else []), "kontroller": kontrol_listesi(profil, a),
            "sayfa": olcum["sayfa"] if olcum else None, "yazi_pt": olcum["yazi"] if olcum else None,
            "sonuc": "HATA" if hata else ("UYARI" if bulgu else "TEMIZ"),
            "karar": "yayınlanamaz" if hata else "yayınlanabilir"}


# ── Düzeltme ──
def duzelt(metin: str) -> tuple[str, list[str]]:
    """Yalnız anlamı değiştirmeyen düzeltmeler."""
    yapilan, sayac = [], 0

    def cevir(m):
        nonlocal sayac
        s = m.group(0)
        if MIKRO_BIRIM.match(s):
            return s
        yabanci = [ch for ch in s if KIRIL.match(ch) or YUNAN.match(ch)]
        if not yabanci or not all(ch in BENZER for ch in yabanci):
            return s
        if not (LATIN.search(s) or len(s) <= 2):      # saf Kiril/Yunan sözcük anlam taşıyabilir: dokunma
            return s
        sayac += 1
        return "".join(BENZER.get(ch, ch) for ch in s)

    yeni = SOZCUK.sub(cevir, metin)
    if sayac:
        yapilan.append(f"{sayac} sözcükte Kiril/Yunan benzer harf Latin harfe çevrildi")
    m = PUNTO.search(yeni)
    if m and float(m.group(1)) < DUZELT_PUNTO_ALT:
        yapilan.append(f"Gövde yazısı {m.group(1)} pt → {DUZELT_PUNTO} pt")
        yeni = yeni[:m.start(1)] + DUZELT_PUNTO + yeni[m.end(1):]
    return yeni, yapilan


# ── Çıktı ──
def yazdir(ad: str, s: dict, notlar: list[str]) -> None:
    isaret = {"TEMIZ": "✓", "UYARI": "⚠", "HATA": "⛔"}[s["sonuc"]]
    ek = f" · {s['sayfa']} s. · yazı {s['yazi_pt']} pt" if s["sayfa"] is not None else " · PDF ölçülmedi"
    print(f"{isaret} {ad}: {s['toplam']}/{s['azami']} · {s['karar']}{ek}")
    t = s["tespit"]
    neden = f"; ipucu: {', '.join(t['kanit'])}" if t["kanit"] else ""
    ikinci = f"; ikinci aday: {t['ikinci']}" if t["ikinci"] else ""
    dil = f" ({s['dil']})" if s["alan"] == "dil" else ""
    print(f"  Alan: {s['alan_adi']}{dil} · {t['kaynak']}, güven {t['guven']}{neden}{ikinci} · biçim: {s['bicim']}")
    if t["kaynak"] == "tespit" and t["guven"] != "yüksek":
        print("  (yanlışsa frontmatter'a `alan: …` yaz ya da --alan ver)")
    for n in notlar:
        print(f"  {n}")
    print("  | Boyut | Puan |\n  |---|---|")
    for b, v in s["puan"].items():
        print(f"  | {b} | {'ölçülmedi' if v is None else v} |")
    for x in s["bulgular"]:
        print(f"  {'⛔' if x['duzey'] == 'HATA' else '⚠'} {x['boyut']}: {x['mesaj']}" + (f" → {x['oneri']}" if x["oneri"] else ""))
    eksik = [b for b, v in s["elle"].items() if not v]
    if eksik:
        print(f"  ☐ elle: {', '.join(eksik)} (frontmatter denetim: / hedef:)")
    for m in s["elle_liste"]:
        print(f"  ☐ {m}")


def main(argv: list[str]) -> int:
    arg = {"pdf": None, "dil": None, "alan": None, "json": False, "duzelt": False}
    dosyalar, i = [], 0
    while i < len(argv):
        a = argv[i]
        if a in ("--pdf", "--dil", "--alan"):
            if i + 1 >= len(argv):
                print(f"{a} değer ister", file=sys.stderr)
                return 2
            arg[a[2:]] = argv[i + 1]
            i += 2
            continue
        if a in ("--json", "--duzelt"):
            arg[a[2:]] = True
        elif a in ("-h", "--help"):
            print(__doc__)
            return 0
        elif a.startswith("--"):
            print(f"bilinmeyen seçenek: {a}", file=sys.stderr)
            return 2
        else:
            dosyalar.append(a)
        i += 1
    if len(dosyalar) != 1:
        print(__doc__, file=sys.stderr)
        return 2
    md = Path(dosyalar[0])
    if not md.is_file():
        print(f"dosya yok: {md}", file=sys.stderr)
        return 2
    metin = md.read_text(encoding="utf-8")
    notlar = []
    if arg["duzelt"]:
        metin, yapilan = duzelt(metin)
        if yapilan:
            md.write_text(metin, encoding="utf-8")
            notlar += [f"🔧 {y} (PDF'i yeniden üret)" for y in yapilan]
    pdf = Path(arg["pdf"]) if arg["pdf"] else md.with_suffix(".pdf")
    if arg["pdf"] and not pdf.is_file():
        print(f"PDF yok: {pdf}", file=sys.stderr)
        return 2
    olcum = None
    if pdf.is_file():
        olcum = pdf_olc(pdf)
        if olcum is None:
            notlar.append("PDF ölçülemedi (pdftotext/pdfimages yok ya da PDF okunamadı)")
    try:
        s = denetle(metin, olcum, arg["alan"], arg["dil"])
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 2
    s["md"], s["pdf"], s["notlar"] = str(md), str(pdf) if olcum else "", notlar
    if arg["json"]:
        print(json.dumps(s, ensure_ascii=False, indent=1))
    else:
        yazdir(md.name, s, notlar)
    return 1 if s["sonuc"] == "HATA" else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
