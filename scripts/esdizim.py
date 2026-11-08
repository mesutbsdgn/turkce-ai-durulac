#!/usr/bin/env python3
"""Türkçe akademik eş dizim ve kelime mantığı denetleyicisi (yalnız standart kütüphane).

Sondan eklemeli Türkçe çekimlerde (çoğul, iyelik, hal ekleri, edilgen çatı, zarf-fiil/sıfat-fiil)
ve nesne ile yüklem arasına zarf/sıfat girdiğinde bozuk fiil-nesne birlikteliklerini yakalar.

Kullanım:
  python3 esdizim.py tez.md                       # metindeki eş dizim hatalarını listeler
  python3 esdizim.py tez.md --pencere 4           # nesne-fiil arası kelime penceresi (varsayılan: 4)
  python3 esdizim.py tez.md --alan guvenlik_ir    # yalnız seçili alan kurallarını çalıştırır
  python3 esdizim.py tez.md --json                # JSON çıktı üretir
  python3 esdizim.py - < tez.md                   # standart girdi
"""
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
VERI_YOLU = os.path.join(HERE, os.pardir, "references", "akademik-esdizim.json")

# Kasten bozma ve birim testi kontrol bayrağı: True iken Türkçe çekim eklerini soyar/eşleştirir
CEKIM_EKLERI_ACIK = True

ISIM_EK_DESENI = re.compile(
    r"^(?:ler|lar)?"
    r"(?:ım|im|um|üm|ın|in|un|ün|ı|i|u|ü|sı|si|su|sü|ımız|imiz|umuz|ümüz|nız|niz|nuz|nüz|ları|leri)?"
    r"(?:ı|i|u|ü|yı|yi|yu|yü|nı|ni|nu|nü|a|e|ya|ye|na|ne)?$"
)

FIIL_DEGIL_ISIMLER = {
    "yapı", "yapısı", "yapısını", "yapısına", "yapısında", "yapısından", "yapılar", "yapıları", "yapıların",
    "üretim", "üretimi", "üretimini", "üretimler",
}

ARA_HAFIF_ISIMLER = {
    "uyum", "koruma", "korunma", "destek", "vurgu", "katkı", "katkılar", "fayda", "yarar",
    "imkan", "imkân", "olanak", "fırsat", "zemin", "ortam", "koordinasyon", "işbirliği",
    "avantaj", "üstünlük", "direnç", "yetenek", "kabiliyet", "tarif", "tarifi", "tarifinin",
    "inceleme", "incelemesi", "hedef", "hedeflerinin", "ayrım", "ayrımı", "koordine",
}

FIIL_EK_DESENI = re.compile(
    r"^(?:n|l|ıl|il|ul|ül|in|ın|un|ün|nıl|nil|nul|nül|ş|ış|iş|uş|üş|t|d|dır|dir|dur|dür|tır|tir|tur|tür)?"
    r"(?:eme|ama|yama|yeme|ebil|abil|yebil|yabil)?"
    r"(?:me|ma)?"
    r"(?:mekte|makta|iyor|ıyor|uyor|üyor|yor|ecek|acak|yecek|yacak|"
    r"di|dı|du|dü|ti|tı|tu|tü|miş|mış|muş|müş|ir|ır|ur|ür|er|ar|r|"
    r"meli|malı|se|sa|dik|dık|duk|dük|tik|tık|tuk|tük|diği|dığı|duğu|düğü|tiği|tığı|tuğu|tüğü|"
    r"en|an|yen|yan|erek|arak|yerek|yarak|ip|ıp|up|üp|yip|yıp|yup|yüp|mek|mak|mesi|ması)"
    r"(?:dir|dır|dur|dür|tir|tır|tur|tür|ler|lar|iz|ız|uz|üz|im|ım|um|üm|sin|sın|sun|sün|"
    r"ini|ını|unu|ünü|i|ı|u|ü|de|da|den|dan|e|a)?$"
)

KELIME_RE = re.compile(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+|[.,!?;:()\[\]]")


def kucult(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def kurallari_yukle(yol=VERI_YOLU, alan=None):
    with open(yol, encoding="utf-8") as f:
        veri = json.load(f)
    kurallar = veri.get("kurallar", [])
    if alan:
        kurallar = [k for k in kurallar if k.get("alan") == alan]
    return kurallar


def isim_eslesir_mi(kelime, nesne_kokleri):
    k = kucult(kelime)
    for kok in nesne_kokleri:
        kok_k = kucult(kok)
        if k == kok_k:
            return True
        if CEKIM_EKLERI_ACIK and k.startswith(kok_k):
            kalan = k[len(kok_k):]
            if ISIM_EK_DESENI.match(kalan):
                return True
    return False


def tek_fiil_eslesir_mi(kelime, fiil_koku):
    k = kucult(kelime)
    if k in FIIL_DEGIL_ISIMLER:
        return False
    fk = kucult(fiil_koku)
    aday_kokler = [fk]
    if fk == "et":
        aday_kokler.append("ed")
    elif fk.endswith("t") and len(fk) >= 2:
        aday_kokler.append(fk[:-1] + "d")
    for ak in aday_kokler:
        if k == ak:
            return True
        if CEKIM_EKLERI_ACIK and k.startswith(ak):
            kalan = k[len(ak):]
            if not kalan or FIIL_EK_DESENI.match(kalan):
                return True
    return False


def fiil_eslesir_mi(tokenler, idx, yanlis_fiil_kokleri):
    """tokenler[idx:] başında yanlis_fiil_kokleri'nden biri varsa kaç token kapladığını (1..3) döner, yoksa 0."""
    for fk in yanlis_fiil_kokleri:
        parcalar = fk.split()
        uzunluk = len(parcalar)
        if idx + uzunluk > len(tokenler):
            continue
        bas_uyum = True
        for p_i in range(uzunluk - 1):
            if kucult(tokenler[idx + p_i][0]) != kucult(parcalar[p_i]):
                bas_uyum = False
                break
        if not bas_uyum:
            continue
        son_kelime = tokenler[idx + uzunluk - 1][0]
        if tek_fiil_eslesir_mi(son_kelime, parcalar[-1]):
            return uzunluk
    return 0


def temizle_satirlar(metin):
    satirlar, kodda = [], False
    for ham in metin.split("\n"):
        if re.match(r"^\s*(```|~~~)", ham):
            kodda = not kodda
            satirlar.append("")
            continue
        if kodda or (re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", ham) and "|" in ham):
            satirlar.append("")
            continue
        s = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), ham)
        s = re.sub(r"\]\([^)]*\)", lambda m: "]" + " " * (len(m.group(0)) - 1), s)
        s = re.sub(r"https?://\S+", lambda m: " " * len(m.group(0)), s)
        satirlar.append(s)
    return satirlar


def satir_tara(satir, satir_no, kurallar, pencere=4):
    bulgular = []
    ham_tokenler = [(m.group(0), m.start() + 1, m.end()) for m in KELIME_RE.finditer(satir)]
    # Cümle/yan cümle sınırlarına göre grupla
    gruplar, aktif = [], []
    for tok, bas, bit in ham_tokenler:
        if tok in ".;:!?()[]":
            if aktif:
                gruplar.append(aktif)
                aktif = []
        elif tok == ",":
            continue
        else:
            aktif.append((tok, bas, bit))
    if aktif:
        gruplar.append(aktif)

    for tokenler in gruplar:
        n = len(tokenler)
        for i in range(n):
            kelime_i, bas_i, _ = tokenler[i]
            for kural in kurallar:
                if not isim_eslesir_mi(kelime_i, kural["nesne_kokleri"]):
                    continue
                ust_sinir = min(n, i + 1 + pencere)
                for j in range(i + 1, ust_sinir):
                    ara_kelimeler = {kucult(tokenler[m_i][0]) for m_i in range(i + 1, j)}
                    if ara_kelimeler & ARA_HAFIF_ISIMLER:
                        break
                    kaplanan = fiil_eslesir_mi(tokenler, j, kural["yanlis_fiil_kokleri"])
                    if kaplanan > 0:
                        son_bit = tokenler[j + kaplanan - 1][2]
                        ifade = satir[bas_i - 1:son_bit].strip()
                        fiil_ifade = " ".join(t[0] for t in tokenler[j:j + kaplanan])
                        bulgular.append({
                            "satir": satir_no,
                            "sutun": bas_i,
                            "id": kural["id"],
                            "alan": kural["alan"],
                            "ifade": ifade,
                            "nesne": kelime_i,
                            "fiil": fiil_ifade,
                            "dogru_fiiller": kural["dogru_fiiller"],
                            "aciklama": kural["aciklama"],
                        })
                        break
    return bulgular


def metin_tara(metin, kurallar=None, pencere=4, alan=None):
    if kurallar is None:
        kurallar = kurallari_yukle(alan=alan)
    satirlar = temizle_satirlar(metin) if isinstance(metin, str) else metin
    bulgular = []
    for n, s in enumerate(satirlar, 1):
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        bulgular.extend(satir_tara(s, n, kurallar, pencere=pencere))
    return bulgular


def tarama_bulgularina_donustur(metin_veya_satirlar, pencere=4):
    """tarama.py --tur tez için (satır, sütun, kalıp_no, ad, alıntı, öneri) biçiminde çıktı döner."""
    bulgular = metin_tara(metin_veya_satirlar, pencere=pencere)
    cikti = []
    for b in bulgular:
        oneriler = " / ".join(b["dogru_fiiller"][:3])
        ad = f"kelime mantığı ({b['id']}: {b['nesne']} + {b['fiil']})"
        oneri = f"{b['aciklama']} Öneri: “{oneriler}”"
        cikti.append((b["satir"], b["sutun"], 62, ad, b["ifade"], oneri))
    return cikti


def main(arg):
    if not arg or any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0 if arg else 2
    dosya = alan = None
    pencere = 4
    json_cikti = False
    i = 0
    while i < len(arg):
        a = arg[i]
        if a == "--pencere" and i + 1 < len(arg):
            pencere = int(arg[i + 1]); i += 2
        elif a == "--alan" and i + 1 < len(arg):
            alan = arg[i + 1]; i += 2
        elif a == "--json":
            json_cikti = True; i += 1
        elif a.startswith("-") and a != "-":
            print(f"esdizim: bilinmeyen seçenek {a!r}", file=sys.stderr)
            return 2
        else:
            dosya = a; i += 1
    if dosya is None:
        print("esdizim: dosya verilmedi", file=sys.stderr)
        return 2
    if dosya != "-" and not os.path.isfile(dosya):
        print(f"esdizim: dosya bulunamadı: {dosya}", file=sys.stderr)
        return 2
    if dosya == "-":
        metin = sys.stdin.read()
    else:
        with open(dosya, encoding="utf-8") as f:
            metin = f.read()
    kurallar = kurallari_yukle(alan=alan)
    bulgular = metin_tara(metin, kurallar=kurallar, pencere=pencere)
    if json_cikti:
        print(json.dumps({"toplam": len(bulgular), "bulgular": bulgular}, ensure_ascii=False, indent=2))
        return 0
    for b in bulgular:
        oneriler = ", ".join(b["dogru_fiiller"])
        print(f"{b['satir']}:{b['sutun']} [{b['id']} · {b['alan']}] «{b['ifade']}» → {oneriler} ({b['aciklama']})")
    print(f"\nToplam {len(bulgular)} akademik eş dizim bulgusu ({len(kurallar)} aktif kural tarandı)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
