#!/usr/bin/env python3
"""Türkçe akademik tez korpusundan PMI (Pointwise Mutual Information) ve N-gram eş dizim madencisi.

AI öncesi doğal Türkçe akademik metinlerdeki (tez, makale) yerleşik nesne-fiil birlikteliklerini
istatistiksel olarak çıkarır ve yüksek PMI skorlu doğal eş dizimleri listeler (yalnız standart kütüphane).

Kullanım:
  python3 korpus_pmi.py korpus.txt --min-frekans 2 --min-pmi 0.5
  python3 korpus_pmi.py korpus_dizin/ --json
  python3 korpus_pmi.py - < tez_orneklemi.txt
"""
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True

# Kasten bozma ve birim testi kontrol bayrağı: True iken min_frekans eşiğini uygular
MIN_FREKANS_AKTIF = True

DURAK_KELIMELER = {
    "ve", "veya", "ile", "için", "ancak", "fakat", "ama", "lakin", "çünkü", "gibi",
    "kadar", "ಗöre", "göre", "olarak", "ise", "de", "da", "ki", "bu", "şu", "o",
    "bir", "her", "tüm", "bütün", "bazı", "hiçbir", "çok", "daha", "en", "hem",
    "ya", "ne", "kendi", "aynı", "diğer", "başka", "böyle", "şöyle", "öyle",
    "üzerine", "üzerinde", "altında", "arasında", "içinde", "dışında", "sonra", "önce",
}

YARDIMCI_EKLER = {"et", "ol", "kıl", "eyle", "bulun", "kal", "gel", "ver", "al", "yap", "koy", "tut", "sür", "aç"}

FIIL_CEKIM_SONU = re.compile(
    r"^([a-zçğıöşüâîû]{2,22}?)"
    r"(?:ebil|abil|yebil|yabil|eme|ama)?"
    r"(?:me|ma)?"
    r"(?:mektedir|maktadır|mekte|makta|ilmiştir|ılmıştır|ulmuştur|ülmüştür|"
    r"nmiştir|nmıştır|nmuştur|nmüştür|lmiştir|lmıştır|lmuştur|lmüştür|"
    r"miştir|mıştır|muştur|müştür|di|dı|du|dü|ti|tı|tu|tü|"
    r"iyor|ıyor|uyor|üyor|ecek|acak|yecek|yacak|"
    r"meli|malı|melidir|malıdır|erek|arak|yerek|yarak|"
    r"dik|dık|duk|dük|diği|dığı|duğu|düğü|mek|mak|mesi|ması)$"
)

KESIN_FIIL_SONU = re.compile(
    r"(?:mektedir|maktadır|mekte|makta|ilmiştir|ılmıştır|ulmuştur|ülmüştür|"
    r"nmiştir|nmıştır|nmuştur|nmüştür|lmiştir|lmıştır|lmuştur|lmüştür|"
    r"miştir|mıştır|muştur|müştür|iyor|ıyor|uyor|üyor|ecek|acak|"
    r"melidir|malıdır|erek|arak|mek|mak)$"
)

EDILGEN_EK = re.compile(r"^([a-zçğıöşüâîû]{2,20}?)(?:nıl|nil|nul|nül|ıl|il|ul|ül)$")
EDILGEN_UNLU_N = re.compile(r"^([a-zçğıöşüâîû]*[aeıioöuüâîû])n$")

ISIM_SON_EK = re.compile(
    r"^([a-zçğıöşüâîû]{3,20}?)"
    r"(?:ler|lar)?"
    r"(?:leri|ları|si|sı|su|sü|i|ı|u|ü|imiz|ımız|umuz|ümüz)?"
    r"(?:ni|nı|nu|nü|yi|yı|yu|yü|i|ı|u|ü|ne|na|ye|ya|e|a|nde|nda|de|da|te|ta|"
    r"nden|ndan|den|dan|ten|tan|nin|nın|nun|nün|in|ın|un|ün|yle|yla|le|la)?$"
)

YUMUSAMA_TERS = {
    "tehdid": "tehdit",
    "boşluğ": "boşluk",
    "nedenselliğ": "nedensellik",
    "caydırıcılığ": "caydırıcılık",
    "geçerliliğ": "geçerlilik",
    "güvenilirliğ": "güvenilirlik",
    "egemenliğ": "egemenlik",
    "ölceğ": "ölçek",
    "sonuc": "sonuç",
    "amac": "amaç",
    "araç": "araç",
    "arac": "araç",
    "güc": "güç",
    "hukuğ": "hukuk",
    "ittifağ": "ittifak",
    "etkileşim": "etkileşim",
    "bağımlılığ": "bağımlılık",
    "güvenliğ": "güvenlik",
    "bütünlüğ": "bütünlük",
    "üstünlüğ": "üstünlük",
    "özgürlüğ": "özgürlük",
    "sorumluluğ": "sorumluluk",
    "yükümlülüğ": "yükümlülük",
    "yetkinliğ": "yetkinlik",
    "verimliliğ": "verimlilik",
    "tutarlılığ": "tutarlılık",
    "kapsamlılığ": "kapsamlılık",
}

UNLU_KALIN = set("aıouâû")


def kucult(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def mastar_yap(fiil_koku):
    parcalar = fiil_koku.split()
    son = parcalar[-1]
    if son == "ed":
        son = "et"
    unlu = [c for c in son if c in "aeıioöuüâîû"]
    ek = "mak" if (unlu and unlu[-1] in UNLU_KALIN) else "mek"
    parcalar[-1] = son + ek
    return " ".join(parcalar)


def cumlelere_ayir(metin):
    """Atıfları ve kod bloklarını temizleyip metni cümle listesine böler."""
    temiz = re.sub(r"```[\s\S]*?```", " ", metin)
    temiz = re.sub(r"\([^)]*\d{4}[^)]*\)", " ", temiz)
    temiz = re.sub(r"\[\d+(?:\s*[-,]\s*\d+)*\]", " ", temiz)
    cumleler = re.split(r"[.!?;:\n]+", temiz)
    return [c.strip() for c in cumleler if len(c.strip()) >= 10]


def fiil_koku_cikar(kelime):
    k = kucult(kelime)
    if k in DURAK_KELIMELER or len(k) < 4:
        return None
    m = FIIL_CEKIM_SONU.match(k)
    if not m:
        return None
    govde = m.group(1)
    m_ed = EDILGEN_EK.match(govde)
    if m_ed and len(m_ed.group(1)) >= 2:
        govde = m_ed.group(1)
    else:
        m_un = EDILGEN_UNLU_N.match(govde)
        if m_un and len(m_un.group(1)) >= 3:
            govde = m_un.group(1)
    if govde == "ed":
        govde = "et"
    elif govde.endswith("d") and govde[:-1] + "t" in {"et", "üret", "yönet", "gözet", "denet", "yarat", "kapat", "başlat"}:
        govde = govde[:-1] + "t"
    if len(govde) < 2 or govde in DURAK_KELIMELER:
        return None
    return govde


def isim_koku_cikar(kelime):
    k = kucult(kelime)
    if k in DURAK_KELIMELER or len(k) < 3:
        return None
    if KESIN_FIIL_SONU.search(k):
        return None
    m = ISIM_SON_EK.match(k)
    kok = m.group(1) if m else k
    kok = YUMUSAMA_TERS.get(kok, kok)
    if kok in DURAK_KELIMELER or len(kok) < 3:
        return None
    return kok


def ikilileri_cikar(metin, pencere=3):
    """Metindeki cümlelerden (nesne_kökü, fiil_mastar) aday ikililerini çıkarır."""
    ikililer = []
    for cumle in cumlelere_ayir(metin):
        kelimeler = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+", cumle)
        n = len(kelimeler)
        i = 0
        while i < n:
            fk = fiil_koku_cikar(kelimeler[i])
            if fk:
                fiil_bas = i
                if fk in YARDIMCI_EKLER and i >= 1:
                    onceki_k = kucult(kelimeler[i - 1])
                    if onceki_k not in DURAK_KELIMELER and not fiil_koku_cikar(kelimeler[i - 1]):
                        fk = f"{onceki_k} {fk}"
                        fiil_bas = i - 1
                fiil_mastar = mastar_yap(fk)
                alt = max(0, fiil_bas - pencere)
                for j in range(alt, fiil_bas):
                    ik = isim_koku_cikar(kelimeler[j])
                    if ik and ik != fk.split()[0]:
                        ikililer.append((ik, fiil_mastar))
            i += 1
    return ikililer


def pmi_hesapla(metin_veya_liste, min_frekans=2, min_pmi=0.0, pencere=3):
    """Metin(ler) üzerinden (nesne, fiil) ikililerinin PMI skorlarını hesaplar."""
    metin = "\n".join(metin_veya_liste) if isinstance(metin_veya_liste, (list, tuple)) else metin_veya_liste
    ikililer = ikilileri_cikar(metin, pencere=pencere)
    toplam = len(ikililer)
    if toplam == 0:
        return []
    nesne_say = Counter(ik[0] for ik in ikililer)
    fiil_say = Counter(ik[1] for ik in ikililer)
    cift_say = Counter(ikililer)

    sonuclar = []
    for (nesne, fiil), c_xy in cift_say.items():
        if MIN_FREKANS_AKTIF and c_xy < min_frekans:
            continue
        p_xy = c_xy / toplam
        p_x = nesne_say[nesne] / toplam
        p_y = fiil_say[fiil] / toplam
        pmi = math.log2(p_xy / (p_x * p_y)) if (p_x > 0 and p_y > 0) else 0.0
        if pmi < min_pmi:
            continue
        sonuclar.append({
            "nesne": nesne,
            "fiil": fiil,
            "frekans": c_xy,
            "nesne_frekans": nesne_say[nesne],
            "fiil_frekans": fiil_say[fiil],
            "pmi": round(pmi, 4),
        })
    sonuclar.sort(key=lambda r: (r["pmi"], r["frekans"]), reverse=True)
    return sonuclar


def dogal_fiilleri_grupla(pmi_sonuclari, en_fazla=5):
    """Her nesne kökü için en yüksek PMI/frekanslı doğal akademik fiilleri gruplar."""
    gruplar = defaultdict(list)
    for s in sorted(pmi_sonuclari, key=lambda r: (r["frekans"], r["pmi"]), reverse=True):
        if len(gruplar[s["nesne"]]) < en_fazla and s["fiil"] not in gruplar[s["nesne"]]:
            gruplar[s["nesne"]].append(s["fiil"])
    return dict(gruplar)


def yol_oku(yol):
    if yol == "-":
        return sys.stdin.read()
    if os.path.isdir(yol):
        parcalar = []
        for kok_d, _, dosyalar in os.walk(yol):
            for d in sorted(dosyalar):
                if d.endswith((".txt", ".md")):
                    with open(os.path.join(kok_d, d), encoding="utf-8", errors="ignore") as f:
                        parcalar.append(f.read())
        return "\n".join(parcalar)
    with open(yol, encoding="utf-8") as f:
        return f.read()


def main(arg):
    if not arg or any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0 if arg else 2
    hedef = None
    min_frekans = 2
    min_pmi = 0.0
    pencere = 3
    json_cikti = False
    i = 0
    while i < len(arg):
        a = arg[i]
        if a == "--min-frekans" and i + 1 < len(arg):
            min_frekans = int(arg[i + 1]); i += 2
        elif a == "--min-pmi" and i + 1 < len(arg):
            min_pmi = float(arg[i + 1]); i += 2
        elif a == "--pencere" and i + 1 < len(arg):
            pencere = int(arg[i + 1]); i += 2
        elif a == "--json":
            json_cikti = True; i += 1
        elif a.startswith("-") and a != "-":
            print(f"korpus_pmi: bilinmeyen seçenek {a!r}", file=sys.stderr)
            return 2
        else:
            hedef = a; i += 1
    if hedef is None:
        print("korpus_pmi: dosya veya dizin verilmedi", file=sys.stderr)
        return 2
    if hedef != "-" and not os.path.exists(hedef):
        print(f"korpus_pmi: yol bulunamadı: {hedef}", file=sys.stderr)
        return 2
    metin = yol_oku(hedef)
    sonuclar = pmi_hesapla(metin, min_frekans=min_frekans, min_pmi=min_pmi, pencere=pencere)
    if json_cikti:
        print(json.dumps({
            "toplam_cift": len(sonuclar),
            "dogal_fiiller": dogal_fiilleri_grupla(sonuclar),
            "pmi_listesi": sonuclar,
        }, ensure_ascii=False, indent=2))
        return 0
    for s in sonuclar[:50]:
        print(f"{s['nesne']:<18} + {s['fiil']:<22} frekans={s['frekans']:<4} PMI={s['pmi']:.3f}")
    print(f"\nToplam {len(sonuclar)} eş dizim çifti (min_frekans={min_frekans}, min_pmi={min_pmi})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
