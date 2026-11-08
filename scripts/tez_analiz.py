#!/usr/bin/env python3
"""Tez Jüri ve Üslup Denetim Hattı (yalnız standart kütüphane, 0-token yerel + isteğe bağlı uzak Ollama sunucusu).

Bir yüksek lisans/doktora tez taslağını (.docx, .md veya .txt) bölüm bazında tarar;
DOCX dosyalarında kapak, içindekiler tablosu (T1-T4) ve kaynakçayı otomatik ayırır;
okunabilirlik (Ateşman, Bezirci-Yılmaz), Türkçe kelime mantığı (eş dizim), kaynaksız otorite
ifadeleri, 4+ tamlayanlı ad tamlaması zincirleri, 1. şahıs sızıntıları, ünsüz benzeşmesi (de/te)
hataları, Metin İçi Atıf ↔ Kaynakça çapraz tutarlılığı ve Word yorumlarını tek raporda birleştirir.

Kullanım:
  python3 tez_analiz.py Tez.eski.docx
  python3 tez_analiz.py tez_taslak.md
  python3 tez_analiz.py tez_yeni.md --onceki tez_eski.md
  python3 tez_analiz.py Tez.eski.docx --cikti juri_raporu.md
  python3 tez_analiz.py Tez.eski.docx --json
  python3 tez_analiz.py Tez.eski.docx --uzak

Varsayılan çıktı CÜMLESİZDİR (şema cumlesiz-v1): eşleşen ifade metni yerine konum, kural kimliği, sayı ve
`#özet` yazılır; Word yorum metni, bilgi kaybı değerleri ve uzak model önerisi çıkarılır. Çıktı yazılmadan önce
sızıntı bekçisi tez gövdesinden 5 ardışık sözcük arar; bulursa çıktıyı yazmaz ve 3 koduyla çıkar.
--tam  ifadeleri aynen yazar (yalnız tezin sahibi ve yerel/sunucu ajanı içindir; raporu başka bir yapay zekâya vermeyin)
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bilgi_koruma as bk  # noqa: E402
import kilavuz  # noqa: E402
import esdizim as esd  # noqa: E402
import okunabilirlik as ok  # noqa: E402
import tarama as tr  # noqa: E402

# Kasten bozma ve birim testi kontrol bayrağı: True iken kaynaksız otorite denetimini çalıştırır
KAYNAKSIZ_OTORITE_AKTIF = True

ATIF_RE = re.compile(r"\(\s*[^)]*(?:19|20)\d\d[^)]*\)|\[\d+(?:\s*[-,]\s*\d+)*\]")
BASLIK_RE = re.compile(r"^(?:#{1,3}\s+.+|[IVX0-9]+\.\s*[A-ZÇĞİÖŞÜ]{3,}.*)$")
NS_W = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
W_VAL = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val"
W_AUTHOR = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}author"
W_DATE = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}date"
W_ID = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}id"

# Türkçede sert ünsüzle veya 3, 4, 5, 70 ile biten yıl/kısaltma/kelime sonrası -da/-de/-dan/-den hatası
BENZESME_SAYI_RE = re.compile(
    r"\b(\d*(?:[345]|70))\s*['’]\s*(da|de|dan|den)\b",
    re.IGNORECASE,
)
BENZESME_KESME_RE = re.compile(
    r"\b([A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]{2,}[fstkçşhpFSTKÇŞHP])\s*['’]\s*(da|de|dan|den)\b"
)


def kucult_tr(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def soyad_norm(s):
    """İngilizce/Türkçe BÜYÜK HARF kaynakça ile metin içi atıf eşleştirmesi için ı/i farkını eşitler."""
    s = kucult_tr(s)
    for kaynak, hedef in (("ı", "i"), ("â", "a"), ("î", "i"), ("û", "u"), ("ş", "s"), ("ç", "c"), ("ğ", "g"), ("ö", "o"), ("ü", "u")):
        s = s.replace(kaynak, hedef)
    return s


def docx_ayristir(yol):
    """DOCX dosyasını standart kütüphaneyle okuyup ana metin, kaynakça, dipnot ve yorumları ayırır."""
    with zipfile.ZipFile(yol) as z:
        isimler = set(z.namelist())
        kok = ET.fromstring(z.read("word/document.xml"))
        yorumlar = []
        if "word/comments.xml" in isimler:
            cm_kok = ET.fromstring(z.read("word/comments.xml"))
            for c in cm_kok.findall(".//w:comment", NS_W):
                yazar = c.attrib.get(W_AUTHOR, "")
                tarih = c.attrib.get(W_DATE, "")[:10]
                m = "".join(t.text or "" for t in c.findall(".//w:t", NS_W)).strip()
                if m:
                    yorumlar.append({"yazar": yazar, "tarih": tarih, "metin": m})
        dipnotlar = []
        if "word/footnotes.xml" in isimler:
            fn_kok = ET.fromstring(z.read("word/footnotes.xml"))
            for fn in fn_kok.findall(".//w:footnote", NS_W):
                fid = fn.attrib.get(W_ID, "")
                m = "".join(t.text or "" for t in fn.findall(".//w:t", NS_W)).strip()
                if m and fid not in ("-1", "0"):
                    dipnotlar.append(m)

    # Sayfa kenar boşluklarını (twips -> cm, 1 inch = 1440 twips = 2.54 cm -> 566.93 twips/cm) oku
    kenar_bosluklari = {}
    pg_mar = kok.find(".//w:sectPr/w:pgMar", NS_W)
    if pg_mar is not None:
        for yon, ad in (("top", "ust_cm"), ("bottom", "alt_cm"), ("left", "sol_ic_cm"), ("right", "sag_dis_cm")):
            deger = pg_mar.attrib.get(f"{{http://schemas.openxmlformats.org/wordprocessingml/2006/main}}{yon}")
            if deger and deger.lstrip("-").isdigit():
                kenar_bosluklari[ad] = round(int(deger) / 566.93, 2)

    ham_paragraflar = []
    for p in kok.findall(".//w:body/w:p", NS_W):
        stil_el = p.find(".//w:pStyle", NS_W)
        stil = stil_el.attrib.get(W_VAL, "") if stil_el is not None else ""
        metin = "".join(t.text or "" for t in p.findall(".//w:t", NS_W)).strip()
        if not metin:
            continue
        # İçindekiler / Çizelgeler / Şekiller listesi stillerini (T1..T5, TOC) atla
        if re.match(r"^(?:T\d+|TOC\d*|igure|able)$", stil, re.I):
            continue
        ham_paragraflar.append((stil, metin))

    # Ana metin başlangıcını (I. GİRİŞ / 1. GİRİŞ / BİRİNCİ BÖLÜM) ve KAYNAKÇA başlangıcını bul
    giris_idx = 0
    giris_bulundu = False
    kaynakca_idx = len(ham_paragraflar)
    ozgecmis_idx = len(ham_paragraflar)
    for idx, (stil, metin) in enumerate(ham_paragraflar):
        ust = metin.upper().strip()
        if not giris_bulundu and (
            re.match(r"^(?:I\.|1\.|BİRİNCİ\s+BÖLÜM)\s*GİRİŞ\b", ust)
            or (stil in ("Balk1", "Heading1") and "GİRİŞ" in ust)
        ):
            giris_idx = idx
            giris_bulundu = True
        elif giris_bulundu and kaynakca_idx == len(ham_paragraflar) and (
            re.match(r"^(?:[IVX0-9]+\.\s*)?(?:KAYNAKÇA|KAYNAKLAR)\b", ust)
        ):
            kaynakca_idx = idx
        elif kaynakca_idx < len(ham_paragraflar) and re.match(r"^(?:[IVX0-9]+\.\s*)?(?:ÖZGEÇMİŞ|EKLER)\b", ust):
            ozgecmis_idx = idx
            break

    on_sayfalar = [m for _, m in ham_paragraflar[:giris_idx]]
    ozgecmis_satirlari = [m for _, m in ham_paragraflar[ozgecmis_idx:]]
    kaynakca_ham_satirlar = [m for _, m in ham_paragraflar[kaynakca_idx + 1:ozgecmis_idx]]

    ana_satirlar = []
    for stil, metin in ham_paragraflar[giris_idx:kaynakca_idx]:
        # Şekil/Çizelge alt yazılarını başlık yapma
        if re.match(r"^(?:Şekil|Çizelge|Tablo|Kaynak\s*:)\s*\d*", metin, re.I):
            ana_satirlar.append(metin)
            continue
        if stil in ("Balk1", "Heading1") or re.match(r"^[IVX]+\.\s*[A-ZÇĞİÖŞÜ]{3,}", metin):
            ana_satirlar.append(f"# {metin}")
        elif stil in ("Balk2", "Heading2"):
            ana_satirlar.append(f"## {metin}")
        elif stil in ("Balk3", "Heading3"):
            ana_satirlar.append(f"### {metin}")
        else:
            ana_satirlar.append(metin)

    kaynakca_satirlari = [
        m for m in kaynakca_ham_satirlar
        if len(m.strip()) > 15 and not m.strip().isupper()
    ]
    return {
        "ana_metin": "\n".join(ana_satirlar),
        "kaynakca_satirlari": kaynakca_satirlari,
        "kaynakca_ham_satirlar": kaynakca_ham_satirlar,
        "on_sayfalar": on_sayfalar,
        "ozgecmis_satirlari": ozgecmis_satirlari,
        "kenar_bosluklari": kenar_bosluklari,
        "yorumlar": yorumlar,
        "dipnot_sayisi": len(dipnotlar),
    }


def unsuz_benzesmesi_denetimi(satirlar):
    """Sert ünsüz veya 3/4/5/70 rakamı sonrası -da/-de/-dan/-den yazım hatalarını yakalar."""
    bulgular = []
    ek_duzelt = {"da": "ta", "de": "te", "dan": "tan", "den": "ten"}
    for n, s in enumerate(satirlar, 1):
        if not s.strip():
            continue
        for rx in (BENZESME_SAYI_RE, BENZESME_KESME_RE):
            for m in rx.finditer(s):
                govde, ek = m.group(1), m.group(2)
                dogru_ek = ek_duzelt.get(ek.lower(), "te")
                bulgular.append({
                    "satir": n,
                    "sutun": m.start() + 1,
                    "ifade": m.group(0),
                    "oneri": f"{govde}'{dogru_ek} (ünsüz benzeşmesi / sertleşme kuralı)",
                })
    return bulgular


def atif_kaynakca_denetimi(ana_metin, kaynakca_satirlari):
    """Metin içi APA atıfları ile Kaynakça listesini çapraz denetler."""
    if not kaynakca_satirlari:
        return {"kaynakca_sayisi": 0, "kaynakcada_eksik_atiflar": [], "metinde_eksik_kaynaklar": []}

    kaynakca_birlesik = soyad_norm("\n".join(kaynakca_satirlari))
    # Metin içi (Soyad, Yıl...) veya (; Soyad, Yıl...) kalıplarını çıkar
    apa_kalip = re.compile(r"(?:\(|;)\s*([A-ZÇĞİÖŞÜa-zçğıöşüÂÎÛâîû][^(),;0-9]{1,45}?)\s*,\s*((?:19|20)\d\d[a-z]?)\b")
    metin_atiflari = set()
    for m in apa_kalip.finditer(ana_metin):
        ham_yazar, yil = m.group(1).strip(), m.group(2).strip()
        ham_yazar = re.sub(r"^(?:aktaran|akt\.?|bkz\.?|örn\.?|kaynak)\s*:?\s*", "", ham_yazar, flags=re.I).strip()
        ilk_soyad = re.split(r"\s+(?:ve|&|vd\.?|et\s+al\.?)\s+|\s+", ham_yazar)[0].strip(".,;:")
        if len(ilk_soyad) >= 2 and ilk_soyad[0].isupper():  # küçük harfle başlayan sözcük ("ancak 1940") yazar değildir
            metin_atiflari.add((ilk_soyad, yil))

    kaynakcada_eksik = []
    kaynakca_norm_satirlar = [soyad_norm(s) for s in kaynakca_satirlari]
    for soyad, yil in sorted(metin_atiflari):
        sk = soyad_norm(soyad)
        # soyad ve yıl AYNI kaynakça satırında aranır (yalnız soyad eşleşmesi yıl farkını gizlerdi)
        if not any(sk in satir and yil[:4] in satir for satir in kaynakca_norm_satirlar):
            kaynakcada_eksik.append(f"{soyad} ({yil})")

    # Kaynakçadaki yazar, yalnız parantezli atıf parçalarında (tüm yazar adlarıyla) aranır; düz metindeki
    # geçişler atıf sayılmaz.
    atif_ciftleri = set()  # (yazar sözcüğü, yıl): "(A, 2010; B, 2012)" noktalı virgülle ayrı atıflara bölünür
    for m in ATIF_RE.finditer(ana_metin):
        for parca in m.group(0).split(";"):
            yil_m = re.search(r"\b((?:19|20)\d\d)", parca)
            if not yil_m:
                continue
            for kelime in re.findall(r"[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ'-]{2,}", parca):
                atif_ciftleri.add((soyad_norm(kelime.strip("'-")), yil_m.group(1)))
    metinde_eksik = []
    for k_satir in kaynakca_satirlari:
        m_k = re.match(r"^([A-ZÇĞİÖŞÜa-zçğıöşüÂÎÛâîû'-]{2,25})\s*,", k_satir.strip())
        m_yil = re.search(r"\b((?:19|20)\d\d)\b", k_satir)
        if m_k and m_yil:
            k_soyad = m_k.group(1)
            k_yil = m_yil.group(1)
            if (soyad_norm(k_soyad), k_yil) not in atif_ciftleri:
                metinde_eksik.append(f"{k_soyad} ({k_yil})")

    return {
        "kaynakca_sayisi": len(kaynakca_satirlari),
        "tekil_metin_atfi": len(metin_atiflari),
        "metin_atiflari": [f"{soyad} ({yil})" for soyad, yil in sorted(metin_atiflari)],
        "kaynakcada_eksik_atiflar": sorted(set(kaynakcada_eksik)),
        "metinde_eksik_kaynaklar": sorted(set(metinde_eksik)),
    }


def bolumlere_ayir(metin):
    """Metni ana tez başlıklarına (# Başlık veya I. BAŞLIK) göre (başlık, içerik) listesine ayırır."""
    satirlar = metin.split("\n")
    bolumler = []
    aktif_baslik = "Giriş / Genel Metin"
    aktif_satirlar = []
    for s in satirlar:
        st = s.strip()
        ana_baslik_mi = st.startswith("# ") or (
            not st.startswith("#") and re.match(r"^[IVX]+\.\s*[A-ZÇĞİÖŞÜ]{3,}.*$", st)
        )
        if ana_baslik_mi:
            if "".join(aktif_satirlar).strip():
                bolumler.append((aktif_baslik, "\n".join(aktif_satirlar)))
            aktif_baslik = st.lstrip("#").strip()
            aktif_satirlar = []
        else:
            aktif_satirlar.append(s)
    if "".join(aktif_satirlar).strip():
        bolumler.append((aktif_baslik, "\n".join(aktif_satirlar)))
    if not bolumler and metin.strip():
        bolumler.append(("Tam Metin", metin))
    return bolumler


def kilavuz_denetimi(
    ana_metin,
    on_sayfalar=None,
    kaynakca_ham_satirlar=None,
    ozgecmis_satirlari=None,
    kenar_bosluklari=None,
    profil=None,
):
    """Tez yazım profilini (references/tez-yazim-kilavuzu.json; varsayılan: standart profil) denetler."""
    profil = profil or kilavuz.yukle()
    metin_kucuk = kucult_tr(ana_metin)

    # 1. Terim birliği: eş anlamlı terim çiftlerinde tek terim seçilmeli
    terim_ikilikleri = []
    for c in profil["terim_birligi_ciftleri"]:
        ta_str, tb_str = c["terim_a"], c["terim_b"]
        # İmkân / imkan her iki yazılışı da say
        rx_a = re.compile(rf"\b{re.escape(ta_str)}\w*\b")
        tb_norm = tb_str.replace("â", "[aâ]")
        rx_b = re.compile(rf"\b{tb_norm}\w*\b")
        say_a = len(rx_a.findall(metin_kucuk))
        say_b = len(rx_b.findall(metin_kucuk))
        if say_a > 0 and say_b > 0:
            baskin = ta_str if say_a >= say_b else tb_str
            terim_ikilikleri.append({
                "id": c["id"],
                "terim_a": ta_str,
                "adet_a": say_a,
                "terim_b": tb_str,
                "adet_b": say_b,
                "oneri": f"Terim birliği için tek terim kullanın ('{baskin}' teriminde birleştirin).",
            })

    # 2. Başlık biçimi
    bp = profil["baslik"]
    baslik_ihlalleri = []
    for n, s in enumerate(ana_metin.splitlines(), 1):
        st = s.strip()
        if st.startswith("# "):
            b_metin = st[2:].strip()
            # Numara noktasından sonra boşluk (Romen: "IX.SONUÇ", ondalık: "1.GİRİŞ")
            if bp["numara_sonrasi_bosluk"] and re.match(r"^(?:[IVX]+|\d+)\.\S", b_metin):
                baslik_ihlalleri.append({
                    "satir": n,
                    "baslik": b_metin,
                    "kural": "1. düzey başlıkta numaradan sonra 1 boşluk bırakılmalıdır.",
                })
            harfler = [ch for ch in b_metin if ch.isalpha()]
            if bp["duzey1_buyuk_harf"] and harfler and any(ch.islower() for ch in harfler):
                baslik_ihlalleri.append({
                    "satir": n,
                    "baslik": b_metin,
                    "kural": "1. düzey başlıklarda tüm kelimeler ('VE', 'VEYA', 'İLE' dâhil) BÜYÜK HARF olmalıdır.",
                })
        elif st.startswith("## ") or st.startswith("### "):
            b_metin = st.lstrip("#").strip()
            if bp["alt_duzey_baglac_kucuk"] and re.search(r"\b(?:VE|VEYA|İLE)\b", b_metin):
                baslik_ihlalleri.append({
                    "satir": n,
                    "baslik": b_metin,
                    "kural": "Alt başlıklarda 've', 'veya', 'ile' bağlaçları küçük harfle yazılmalıdır.",
                })

    # 3. Şekil / tablo adlandırma
    st_p = profil["sekil_tablo"]
    sekil_cizelge_ihlalleri = []
    beklenen = st_p["tablo_adi"]
    diger = "Çizelge" if beklenen == "Tablo" else "Tablo"
    if st_p["karisik_ad_uyar"]:
        digerleri = re.findall(rf"\b{diger}\s*\d+(?:\.\d+)?\b", ana_metin, flags=re.I)
        if digerleri:
            sekil_cizelge_ihlalleri.append(
                f"Metinde {len(digerleri)} kez '{diger}' kullanılmış ({', '.join(digerleri[:5])}); profilde tablo adı '{beklenen}' olarak tanımlı, "
                f"tek ad kullanın."
            )
    if st_p["bolum_numarali_uyar"]:
        bolumlu_sekil = re.findall(r"\b(?:Şekil|Çizelge|Tablo)\s+\d+\.\d+\b", ana_metin, flags=re.I)
        if bolumlu_sekil:
            sekil_cizelge_ihlalleri.append(
                f"Bölüm numaralı şekil/tablo ({', '.join(bolumlu_sekil[:5])}) kullanılmış; profil sıralı numaralandırma ('Şekil 1, Şekil 2') ister."
            )

    # 4. Metin içi atıf biçimi
    ap = profil["atif"]
    atif_bicim_ihlalleri = []
    for m in ATIF_RE.finditer(ana_metin):
        a_metin = m.group(0)
        if ap["ampersand_uyar"] and "&" in a_metin:
            atif_bicim_ihlalleri.append(f"{a_metin} -> '&' yerine Türkçe kaynakta 've', İngilizce kaynakta 'and' kullanılmalıdır.")
        if ap["sayfa_bicimi"] == "iki_nokta" and re.search(r"\b(?:s\.|p\.|pp\.|ss\.)\s*\d+", a_metin, flags=re.I):
            atif_bicim_ihlalleri.append(f"{a_metin} -> Profil 'Soyadı, Yıl: Sayfa' biçimini ister; 's./p.' yazılmaz.")
        if ap["sayfa_bicimi"] == "apa7" and re.search(r"(?:19|20)\d\d\s*:\s*\d+", a_metin):
            atif_bicim_ihlalleri.append(f"{a_metin} -> Profil APA 7 biçimini ister: 'Soyadı, Yıl, s. Sayfa'.")
        if ap["ve_digerleri_uyar"] and re.search(r"\bve\s+diğerleri\b", a_metin, flags=re.I):
            atif_bicim_ihlalleri.append(f"{a_metin} -> 've diğerleri' yerine 'vd.' (İngilizce kaynakta 'et al.') yazılmalıdır.")

    # 5. ÖZET / ABSTRACT kelime sınırı
    op = profil["ozet"]
    ozet_denetimi = {}
    if on_sayfalar:
        aktif_kisim = None
        ozet_kelimeler = []
        abstract_kelimeler = []
        for p_metin in on_sayfalar:
            ust = p_metin.strip().upper()
            if ust == "ÖZET":
                aktif_kisim = "ozet"; continue
            elif ust == "ABSTRACT":
                aktif_kisim = "abstract"; continue
            elif ust in ("İÇİNDEKİLER", "ÖNSÖZ", "ONUR SÖZÜ", "KISALTMALAR LİSTESİ", "ŞEKİLLER LİSTESİ", "ÇİZELGELER LİSTESİ", "TABLOLAR LİSTESİ"):
                aktif_kisim = None; continue
            if aktif_kisim == "ozet" and not ust.startswith("ANAHTAR KELİME"):
                ozet_kelimeler.extend(p_metin.split())
            elif aktif_kisim == "abstract" and not ust.startswith("KEY WORD") and not ust.startswith("KEYWORD"):
                abstract_kelimeler.extend(p_metin.split())
        if ozet_kelimeler:
            oz_say = len(ozet_kelimeler)
            ozet_denetimi["ozet_kelime"] = oz_say
            ozet_denetimi["ozet_uygun"] = (op["min_kelime"] <= oz_say <= op["maks_kelime"])
        if abstract_kelimeler:
            ab_say = len(abstract_kelimeler)
            ozet_denetimi["abstract_kelime"] = ab_say
            ozet_denetimi["abstract_uygun"] = (op["min_kelime"] <= ab_say <= op["maks_kelime"])
        if ozet_denetimi:
            ozet_denetimi["sinir"] = [op["min_kelime"], op["maks_kelime"]]

    # 6. Sayfa kenar boşlukları
    sd = profil["sayfa_duzeni"]
    kenar_ihlalleri = []
    hedefler = {"ust_cm": sd["ust_kenar_cm"], "alt_cm": sd["alt_kenar_cm"], "sol_ic_cm": sd["ic_kenar_cm"], "sag_dis_cm": sd["dis_kenar_cm"]}
    if kenar_bosluklari:
        for k_ad, hedef in hedefler.items():
            mevcut = kenar_bosluklari.get(k_ad)
            if mevcut is not None and abs(mevcut - hedef) > sd["kenar_toleransi_cm"]:
                kenar_ihlalleri.append(f"{k_ad}={mevcut} cm (profil hedefi: {hedef} cm)")

    # 7. Kaynakça alt başlıkları (yalnız profil istiyorsa)
    kp = profil["kaynakca"]
    kaynakca_bicim_uyarilari = []
    if kp["alt_baslik_zorunlu"] and kaynakca_ham_satirlar:
        ham_ust = {s.strip().upper() for s in kaynakca_ham_satirlar}
        eksik_alt = set(kp["alt_basliklar"]) - ham_ust
        if eksik_alt:
            kaynakca_bicim_uyarilari.append(
                f"Kaynakça profildeki alt başlıklara ({', '.join(kp['alt_basliklar'])}) ayrılmamış; eksik: {', '.join(sorted(eksik_alt))}."
            )

    # 8. KVKK özgeçmiş denetimi
    kvkk_ihlalleri = []
    if ozgecmis_satirlari:
        oz_metin = "\n".join(ozgecmis_satirlari)
        if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", oz_metin):
            kvkk_ihlalleri.append("Özgeçmişte e-posta adresi yer alıyor (kişisel veri; KVKK uyarısı gereği kaldırılmalıdır).")
        if re.search(r"\b(?:0?5\d{2}[\s-]?\d{3}[\s-]?\d{2}[\s-]?\d{2}|\+90\s*\d{3})\b", oz_metin):
            kvkk_ihlalleri.append("Özgeçmişte telefon numarası yer alıyor (kişisel veri; KVKK uyarısı gereği kaldırılmalıdır).")
        if re.search(r"\b(?:doğum\s+tarihi|doğum\s+yeri|t\.?c\.?\s*kimlik|orcid|adres)\b", oz_metin, flags=re.I):
            kvkk_ihlalleri.append("Özgeçmişte doğum tarihi/yeri, adres veya kimlik/ORCID alanı yer alıyor (kişisel veri; KVKK uyarısı gereği kaldırılmalıdır).")

    return {
        "terim_ikilikleri": terim_ikilikleri,
        "baslik_ihlalleri": baslik_ihlalleri,
        "sekil_cizelge_ihlalleri": sekil_cizelge_ihlalleri,
        "atif_bicim_ihlalleri": atif_bicim_ihlalleri[:25],
        "ozet_denetimi": ozet_denetimi,
        "kenar_bosluklari": kenar_bosluklari or {},
        "kenar_hedefleri": hedefler,
        "kenar_ihlalleri": kenar_ihlalleri,
        "kaynakca_bicim_uyarilari": kaynakca_bicim_uyarilari,
        "kvkk_ihlalleri": kvkk_ihlalleri,
    }


def metin_analiz_et(
    metin,
    onceki_metin=None,
    kaynakca_satirlari=None,
    yorumlar=None,
    on_sayfalar=None,
    kaynakca_ham_satirlar=None,
    ozgecmis_satirlari=None,
    kenar_bosluklari=None,
):
    """Tez metnini tüm yerel denetleyicilerle analiz edip yapılandırılmış sözlük döner."""
    temiz_satirlar = tr.temizle(metin)
    tez_kurallari = tr.derle(tur="tez")
    tarama_bulgulari = tr.tara(metin, tez_kurallari, tur="tez")
    if not KAYNAKSIZ_OTORITE_AKTIF:
        tarama_bulgulari = [b for b in tarama_bulgulari if b[2] != 64]

    esdizim_bulgulari = esd.metin_tara(metin)
    kaynaksiz = tr.kaynaksiz_otorite(temiz_satirlar) if KAYNAKSIZ_OTORITE_AKTIF else []
    zincirler = tr.tamlama_zinciri(temiz_satirlar)
    sahis_sizinti = tr.tez_sahis_uyumu(temiz_satirlar)
    benzesme_hatalari = unsuz_benzesmesi_denetimi(temiz_satirlar)
    okunabilirlik_ozet = ok.olc(metin)
    atiflar = ATIF_RE.findall(metin)
    atif_capraz = atif_kaynakca_denetimi(metin, kaynakca_satirlari or [])
    kilavuz_sonuc = kilavuz_denetimi(
        metin,
        on_sayfalar=on_sayfalar,
        kaynakca_ham_satirlar=kaynakca_ham_satirlar,
        ozgecmis_satirlari=ozgecmis_satirlari,
        kenar_bosluklari=kenar_bosluklari,
    )

    bolum_ozetleri = []
    for baslik, icerik in bolumlere_ayir(metin):
        b_ok = ok.olc(icerik)
        b_esd = esd.metin_tara(icerik)
        b_atif = ATIF_RE.findall(icerik)
        bolum_ozetleri.append({
            "baslik": baslik,
            "sozcuk": b_ok.get("sozcuk", 0),
            "cumle": b_ok.get("cumle", 0),
            "atesman": round(b_ok["atesman"], 1) if b_ok.get("atesman") is not None else None,
            "by": round(b_ok["by"], 1) if b_ok.get("by") is not None else None,
            "atif_sayisi": len(b_atif),
            "esdizim_hatasi": len(b_esd),
        })

    bilgi_kaybi = bk.kayiplar(onceki_metin, metin) if onceki_metin is not None else {}

    juri_riskleri = []
    if kaynaksiz:
        juri_riskleri.append(f"Kaynaksız otorite ifadesi ({len(kaynaksiz)} adet): Jüri 'Hangi araştırmacılar?' diye sorar; (Yazar, Yıl) atfı ekleyin.")
    if esdizim_bulgulari:
        juri_riskleri.append(f"Akademik eş dizim / kelime mantığı hatası ({len(esdizim_bulgulari)} adet): Çeviri kokusu taşıyan fiil-nesne birlikteliklerini doğal akademik fiillerle değiştirin.")
    if zincirler:
        juri_riskleri.append(f"4+ tamlayanlı ad tamlaması zinciri ({len(zincirler)} adet): Okunabilirliği düşüren tamlama zincirlerini fiilimsi veya edatla kırın.")
    if sahis_sizinti:
        juri_riskleri.append(f"1. şahıs sızıntısı ({len(sahis_sizinti)} adet): Tez üslubunda 'tezimizde/inceledik/kanaatimce' yerine 3. kişi edilgen çatı ('bu çalışmada incelenmiştir') kullanın.")
    if benzesme_hatalari:
        juri_riskleri.append(f"Ünsüz benzeşmesi (de/te, da/ta) yazım hatası ({len(benzesme_hatalari)} adet): Sert ünsüz ve 3/4/5/70 sonrası ekleri düzeltin.")
    if atif_capraz["kaynakcada_eksik_atiflar"]:
        juri_riskleri.append(f"Metinde atıf yapılıp Kaynakçada bulunmayan kaynak ({len(atif_capraz['kaynakcada_eksik_atiflar'])} adet): Savunma öncesi Kaynakçaya ekleyin.")
    if atif_capraz["metinde_eksik_kaynaklar"]:
        juri_riskleri.append(f"Kaynakçada yer alıp metinde hiç atıf yapılmayan kaynak ({len(atif_capraz['metinde_eksik_kaynaklar'])} adet): Metinde atıf verin ya da Kaynakçadan çıkarın.")
    if bilgi_kaybi:
        juri_riskleri.append(f"Bilgi/sayı/atıf kaybı ({', '.join(bilgi_kaybi.keys())}): Önceki taslağa göre düşen sayı, özel ad veya atıfları kontrol edin.")
    if kilavuz_sonuc["terim_ikilikleri"]:
        juri_riskleri.append(f"Terim birliği ihlali ({len(kilavuz_sonuc['terim_ikilikleri'])} terim çifti): kanun/yasa, teori/kuram vb. eş anlamlılarda tek terim tercih edilmelidir.")
    if kilavuz_sonuc["baslik_ihlalleri"]:
        juri_riskleri.append(f"Başlık biçimi ihlali ({len(kilavuz_sonuc['baslik_ihlalleri'])} başlık): tez yazım profiline göre 1. düzey başlık biçimini ve numara sonrası boşluğu düzeltin.")
    if kilavuz_sonuc["kvkk_ihlalleri"]:
        juri_riskleri.append(f"KVKK ihlali ({len(kilavuz_sonuc['kvkk_ihlalleri'])} bulgu): Özgeçmiş/Ekler kısmında kişisel veri (e-posta, telefon, doğum tarihi/yeri vb.) yer almamalıdır.")

    return {
        "okunabilirlik": {
            "cumle": okunabilirlik_ozet.get("cumle", 0),
            "sozcuk": okunabilirlik_ozet.get("sozcuk", 0),
            "atesman": round(okunabilirlik_ozet["atesman"], 1) if okunabilirlik_ozet.get("atesman") is not None else None,
            "by": round(okunabilirlik_ozet["by"], 1) if okunabilirlik_ozet.get("by") is not None else None,
        },
        "atif_sayisi": len(atiflar),
        "atif_kaynakca_denetimi": atif_capraz,
        "kilavuz_denetimi": kilavuz_sonuc,
        "toplam_tarama_bulgusu": len(tarama_bulgulari),
        "esdizim_bulgulari": esdizim_bulgulari,
        "kaynaksiz_otorite": [
            {"satir": b[0], "sutun": b[1], "ifade": b[4], "oneri": b[5]}
            for b in kaynaksiz
        ],
        "tamlama_zincirleri": [
            {"satir": b[0], "sutun": b[1], "ifade": b[4], "oneri": b[5]}
            for b in zincirler
        ],
        "sahis_sizintilari": [
            {"satir": b[0], "sutun": b[1], "ifade": b[4], "oneri": b[5]}
            for b in sahis_sizinti
        ],
        "benzesme_hatalari": benzesme_hatalari,
        "yorumlar": yorumlar or [],
        "bolumler": bolum_ozetleri,
        "bilgi_kaybi": bilgi_kaybi,
        "juri_riskleri": juri_riskleri,
    }


def uzak_oneri_al(cumle, zaman_asimi=30):
    """Uzak Ollama sunucusundaki modelden HTTP API ile cümle onarım önerisi alır.

    DURULAC_UZAK_SSH (ssh takma adı) tanımlı değilse hiçbir şey göndermez ve None döner.
    Model adı DURULAC_UZAK_MODEL ile seçilir (varsayılan durulac-tez:latest).
    """
    uzak = os.environ.get("DURULAC_UZAK_SSH", "").strip()
    if not uzak:
        return None
    istek = json.dumps({
        "model": os.environ.get("DURULAC_UZAK_MODEL", "durulac-tez:latest"),
        "messages": [{"role": "user", "content": cumle}],
        "stream": False,
        "options": {"num_predict": 160, "temperature": 0.1},
    }, ensure_ascii=False)
    try:
        sonuc = subprocess.run(
            ["ssh", uzak, "curl -s http://127.0.0.1:11434/api/chat -d @-"],
            input=istek,
            capture_output=True,
            text=True,
            timeout=zaman_asimi,
            check=False,
        )
        if sonuc.returncode == 0 and sonuc.stdout.strip():
            veri = json.loads(sonuc.stdout)
            return veri.get("message", {}).get("content", "").strip() or None
    except Exception:
        pass
    return None


# Cümlesiz rapor (şema cumlesiz-v1): raporu okuyan taraf (ör. Claude) tez metnini görmez.
# Kasten bozma / test bayrağı: False iken sızıntı bekçisi kapanır (yalnız test içindir).
SIZINTI_BEKCISI_AKTIF = True
CUMLESIZ_SEMA = "cumlesiz-v1"
BEKCI_N = 5

# Alan beyaz listeleri: listede olmayan hiçbir alan cümlesiz rapora girmez (kara liste değil).
_TARAMA_ANAHTARLARI = {
    "esdizim_bulgulari": ("satir", "sutun", "id", "alan", "dogru_fiiller", "aciklama"),
    "kaynaksiz_otorite": ("satir", "sutun", "oneri"),
    "tamlama_zincirleri": ("satir", "sutun", "oneri"),
    "sahis_sizintilari": ("satir", "sutun", "oneri"),
}


def ifade_ozeti(ifade):
    """İfadeyi geri döndürülemez kısa bir özete çevirir (konum aynı kalır, metin kalmaz)."""
    return {
        "ifade_ozet": hashlib.sha1(ifade.encode("utf-8")).hexdigest()[:8],
        "ifade_sozcuk": len(ifade.split()),
    }


def cumlesizlestir(analiz):
    """Analiz sözlüğünden tez cümlelerini çıkarır; yalnız konum, kural kimliği, sayı ve özet kalır.

    Korunanlar: bölüm/başlık adları, kaynakça künyeleri (Soyad (Yıl)), kural terimleri ve sayılar.
    Çıkarılanlar: eşleşen ifade metni, öneri içindeki gövde sözcüğü, Word yorum metni, uzak model önerisi,
    bilgi kaybında düşen özel ad/sayı değerleri.
    """
    temiz = {k: v for k, v in analiz.items() if k not in _TARAMA_ANAHTARLARI
             and k not in ("benzesme_hatalari", "yorumlar", "bilgi_kaybi", "uzak_ornek_oneri")}
    for alan, anahtarlar in _TARAMA_ANAHTARLARI.items():
        temiz[alan] = []
        for b in analiz.get(alan, []):
            yeni = {a: b[a] for a in anahtarlar if a in b}
            yeni.update(ifade_ozeti(b.get("ifade", "")))
            temiz[alan].append(yeni)
    temiz["benzesme_hatalari"] = []
    for b in analiz.get("benzesme_hatalari", []):
        ek = re.search(r"['’]\s*(da|de|dan|den)\s*$", b.get("ifade", ""), flags=re.I)
        yeni = {"satir": b.get("satir"), "sutun": b.get("sutun"),
                "ek_duzeltme": (ek.group(1).lower() + " → " + {"da": "ta", "de": "te", "dan": "tan", "den": "ten"}[ek.group(1).lower()]) if ek else "-"}
        yeni.update(ifade_ozeti(b.get("ifade", "")))
        temiz["benzesme_hatalari"].append(yeni)
    temiz["yorumlar"] = [
        {"yazar": y.get("yazar", ""), "tarih": y.get("tarih", ""), "metin_uzunluk": len(y.get("metin", ""))}
        for y in analiz.get("yorumlar", [])
    ]
    temiz["bilgi_kaybi"] = {tur: len(liste) for tur, liste in (analiz.get("bilgi_kaybi") or {}).items()}
    temiz["rapor_sema"] = CUMLESIZ_SEMA
    temiz["cumle_icerir"] = False
    return temiz


def _kelimeler(s):
    return re.findall(r"[\wçğıöşüÇĞİÖŞÜâîûÂÎÛ]+", kucult_tr(s))


def _basliklar(ana_metin):
    """Raporda yapı bilgisi olarak görünebilen başlık metinleri (tam dizge)."""
    cikti = []
    for satir in ana_metin.splitlines():
        st = satir.strip()
        if st.startswith("#"):
            cikti.append(st.lstrip("#").strip())
        elif re.match(r"^[IVX]+\.\s*[A-ZÇĞİÖŞÜ]{3,}", st) and len(st) < 200:
            cikti.append(st)
    return sorted({b for b in cikti if b}, key=len, reverse=True)


def _basliksiz(cikti_metni, ana_metin):
    for b in _basliklar(ana_metin):
        cikti_metni = cikti_metni.replace(b, " ")
    return cikti_metni


def _govde_kaynak_kumesi(ana_metin, n):
    """Gövde satırlarının n'li sözcük parçaları. Başlıklar ve atıf parçaları çıkarılır (yapı/künyedir);
    bölüm başlığı sayılan satırlar (# ile başlayan ya da 'IV. BÜYÜK HARF' kalıbı) ve bunların gövdede
    birebir tekrarı da başlık sayılır."""
    def norm(t):
        return re.sub(r"^(?:[ıivx]+|\d+)\s+", "", " ".join(_kelimeler(t.lstrip("#"))))

    satirlar = ana_metin.splitlines()
    baslik_norm = set()
    for s in satirlar:
        st = s.strip()
        if st.startswith("#") or (re.match(r"^[IVX]+\.\s*[A-ZÇĞİÖŞÜ]{3,}", st) and len(st) < 200):
            baslik_norm.add(norm(st))
    kaynak = set()
    for satir in satirlar:
        st = satir.strip()
        if st.startswith("#") or (re.match(r"^[IVX]+\.\s*[A-ZÇĞİÖŞÜ]{3,}", st) and len(st) < 200):
            continue
        if norm(st) in baslik_norm:
            continue
        w = _kelimeler(ATIF_RE.sub(" ", satir))
        for i in range(len(w) - n + 1):
            kaynak.add(tuple(w[i:i + n]))
    return kaynak


def sizinti_denetle(cikti_metni, ana_metin, n=BEKCI_N):
    """Çıktıda tez gövdesinden n ardışık sözcük (varsayılan 5) geçiyorsa bulunan parça sayısını döner.

    Kaynak kümesinden başlık satırları ve atıf parçaları çıkarılır (bunlar yapı/künyedir, cümle değil).
    """
    if not SIZINTI_BEKCISI_AKTIF:
        return 0
    kaynak = _govde_kaynak_kumesi(ana_metin, n)
    w = _kelimeler(_basliksiz(cikti_metni, ana_metin))
    return sum(1 for i in range(len(w) - n + 1) if tuple(w[i:i + n]) in kaynak)


def sizinti_bolumleri(cikti_metni, ana_metin, n=BEKCI_N):
    """Sızıntı hangi rapor bölümünde? {bölüm başlığı: parça sayısı}. Metin döndürmez (yalnız başlık adı ve sayı)."""
    kaynak = _govde_kaynak_kumesi(ana_metin, n)
    sonuc, bolum = {}, "(başlıksız)"
    for satir in cikti_metni.splitlines():
        if satir.startswith("## "):
            bolum = satir[3:60]
        w = _kelimeler(_basliksiz(satir, ana_metin))
        say = sum(1 for i in range(len(w) - n + 1) if tuple(w[i:i + n]) in kaynak)
        if say:
            etiket = bolum
            sonuc[etiket] = sonuc.get(etiket, 0) + say
    return sonuc


def _ifade_goster(b):
    return f"«{b['ifade']}»" if "ifade" in b else f"`#{b['ifade_ozet']}` ({b['ifade_sozcuk']} sözcük)"


def rapor_uret(analiz):
    """Analiz sözlüğünden okunabilir Markdown Tez Jüri ve Üslup Raporu üretir."""
    ok_b = analiz["okunabilirlik"]
    ak = analiz.get("atif_kaynakca_denetimi", {})
    satirlar = [
        "# Tez Jüri ve Üslup Denetim Raporu",
        "",
    ]
    if analiz.get("rapor_sema") == CUMLESIZ_SEMA:
        satirlar.extend([
            f"> Cümlesiz rapor (`{CUMLESIZ_SEMA}`): tez cümlesi içermez. İfadeler `#özet` olarak gösterilir; "
            "konum (satır/sütun) tez dosyasındaki çıkarılmış metne göredir. Başlık adları ve kaynakça künyeleri (Soyad (Yıl)) yapı bilgisi olarak kalır.",
            "",
        ])
    satirlar.extend([
        "## 1. Genel Ölçümler",
        f"- **Sözcük / Cümle:** {ok_b['sozcuk']} sözcük · {ok_b['cumle']} cümle",
        f"- **Okunabilirlik:** Ateşman `{ok_b['atesman']}` · Bezirci-Yılmaz `{ok_b['by']}`",
        f"- **Kaynak Atfı (APA/IEEE):** {analiz['atif_sayisi']} metin içi atıf"
        + (f" · {ak.get('kaynakca_sayisi', 0)} kaynakça girdisi" if ak.get("kaynakca_sayisi") else ""),
        f"- **Toplam Üslup / Kelime Mantığı Bulgusu:** {analiz['toplam_tarama_bulgusu']} adet",
        "",
        "## 2. Jüri Kritik Risk Özeti",
    ])
    if analiz["juri_riskleri"]:
        for r in analiz["juri_riskleri"]:
            satirlar.append(f"- ⚠️ {r}")
    else:
        satirlar.append("- ✅ Kritik jüri üslup riski saptanmadı.")

    satirlar.extend(["", "## 3. Bölüm Bazlı Dağılım", "| Bölüm | Sözcük | Cümle | Ateşman | Atıf | Eş Dizim Hatası |", "|---|---:|---:|---:|---:|---:|"])
    for b in analiz["bolumler"]:
        satirlar.append(
            f"| {b['baslik']} | {b['sozcuk']} | {b['cumle']} | {b['atesman'] if b['atesman'] is not None else '-'} | {b['atif_sayisi']} | {b['esdizim_hatasi']} |"
        )

    if analiz["esdizim_bulgulari"]:
        satirlar.extend(["", "## 4. Kelime Mantığı (Akademik Eş Dizim) Bulguları"])
        for e in analiz["esdizim_bulgulari"]:
            oneriler = ", ".join(e["dogru_fiiller"][:3])
            satirlar.append(f"- **Satır {e['satir']} [{e['id']}]** {_ifade_goster(e)} → Öneri: `{oneriler}` ({e['aciklama']})")

    if analiz["kaynaksiz_otorite"]:
        satirlar.extend(["", "## 5. Kaynaksız Otorite İfadeleri (Kalıp 64)"])
        for k in analiz["kaynaksiz_otorite"]:
            satirlar.append(f"- **Satır {k['satir']}** {_ifade_goster(k)} → {k['oneri']}")

    if analiz["tamlama_zincirleri"]:
        satirlar.extend(["", "## 6. Belirtili Ad Tamlaması Zincirleri (Kalıp 65)"])
        for z in analiz["tamlama_zincirleri"]:
            satirlar.append(f"- **Satır {z['satir']}** {_ifade_goster(z)} → {z['oneri']}")

    if analiz["sahis_sizintilari"]:
        satirlar.extend(["", "## 7. Tezde 1. Şahıs Sızıntıları (Kalıp 66)"])
        for s in analiz["sahis_sizintilari"]:
            satirlar.append(f"- **Satır {s['satir']}** {_ifade_goster(s)} → {s['oneri']}")

    if analiz.get("benzesme_hatalari"):
        satirlar.extend(["", "## 8. Ünsüz Benzeşmesi (-de/-te, -da/-ta) Hataları"])
        for bh in analiz["benzesme_hatalari"]:
            if "ifade" in bh:
                satirlar.append(f"- **Satır {bh['satir']}** «{bh['ifade']}» → `{bh['oneri']}`")
            else:
                satirlar.append(f"- **Satır {bh['satir']}** {_ifade_goster(bh)} → ek düzeltmesi `{bh['ek_duzeltme']}` (ünsüz benzeşmesi)")

    if ak.get("kaynakcada_eksik_atiflar") or ak.get("metinde_eksik_kaynaklar"):
        satirlar.extend(["", "## 9. Metin İçi Atıf ↔ Kaynakça Çapraz Denetimi"])
        if ak.get("kaynakcada_eksik_atiflar"):
            satirlar.append(f"- **Metinde atıf yapılıp Kaynakçada bulunmayanlar ({len(ak['kaynakcada_eksik_atiflar'])}):** {', '.join(ak['kaynakcada_eksik_atiflar'][:30])}")
        if ak.get("metinde_eksik_kaynaklar"):
            satirlar.append(f"- **Kaynakçada yer alıp metinde atıf bulunmayanlar ({len(ak['metinde_eksik_kaynaklar'])}):** {', '.join(ak['metinde_eksik_kaynaklar'][:30])}")

    if analiz.get("yorumlar"):
        satirlar.extend(["", "## 10. Dosya İçi Word Yorumları (Temizlenecek Notlar)"])
        for y in analiz["yorumlar"]:
            icerik = f"«{y['metin']}»" if "metin" in y else f"({y['metin_uzunluk']} karakterlik not)"
            satirlar.append(f"- **[{y['yazar']} · {y['tarih']}]** {icerik}")

    kd = analiz.get("kilavuz_denetimi") or {}
    if any(kd.get(k) for k in ("terim_ikilikleri", "baslik_ihlalleri", "sekil_cizelge_ihlalleri", "atif_bicim_ihlalleri", "ozet_denetimi", "kenar_ihlalleri", "kaynakca_bicim_uyarilari", "kvkk_ihlalleri")):
        satirlar.extend(["", "## 11. Tez Yazım Kılavuzu Uygunluk Denetimi"])
        oz_d = kd.get("ozet_denetimi") or {}
        if oz_d:
            lo, hi = (oz_d.get("sinir") or [0, 0])
            oz_durum = f"✅ Uygun ({lo}-{hi} sınırında)" if oz_d.get("ozet_uygun") else f"⚠️ Sınır dışı (profil: {lo}-{hi} kelime)"
            ab_durum = f"✅ Uygun ({lo}-{hi} sınırında)" if oz_d.get("abstract_uygun") else f"⚠️ Sınır dışı (profil: {lo}-{hi} kelime)"
            satirlar.append(f"- **Özet / Abstract Kelime Sayısı:** ÖZET `{oz_d.get('ozet_kelime', '-')}` kelime ({oz_durum}) · ABSTRACT `{oz_d.get('abstract_kelime', '-')}` kelime ({ab_durum})")
        kb = kd.get("kenar_bosluklari") or {}
        if kb:
            h = kd.get("kenar_hedefleri") or {}
            satirlar.append(f"- **Sayfa Kenar Boşlukları:** Sol/İç `{kb.get('sol_ic_cm')}` cm (Hedef: {h.get('sol_ic_cm')}) · Üst `{kb.get('ust_cm')}` cm · Alt `{kb.get('alt_cm')}` cm · Sağ/Dış `{kb.get('sag_dis_cm')}` cm (Hedef: {h.get('sag_dis_cm')})")
        for b_ih in kd.get("baslik_ihlalleri", []):
            satirlar.append(f"- **Başlık Kuralı İhlali (Satır {b_ih['satir']}):** «{b_ih['baslik']}» → {b_ih['kural']}")
        for sc in kd.get("sekil_cizelge_ihlalleri", []):
            satirlar.append(f"- **Şekil/Tablo Kuralı:** {sc}")
        for kb_u in kd.get("kaynakca_bicim_uyarilari", []):
            satirlar.append(f"- **Kaynakça Düzeni:** {kb_u}")
        for kv in kd.get("kvkk_ihlalleri", []):
            satirlar.append(f"- **KVKK Kişisel Veri Uyarısı:** {kv}")
        for ab_ih in kd.get("atif_bicim_ihlalleri", [])[:10]:
            satirlar.append(f"- **Metin İçi Atıf Biçimi Uyarısı:** {ab_ih}")
        if kd.get("terim_ikilikleri"):
            satirlar.append("- **Terim Birliği İkilikleri (tek terim seçilmeli):**")
            for ti in kd["terim_ikilikleri"]:
                satirlar.append(f"  - `{ti['terim_a']}` ({ti['adet_a']} kez) ↔ `{ti['terim_b']}` ({ti['adet_b']} kez) — {ti['oneri']}")

    if analiz.get("uzak_ornek_oneri"):
        satirlar.extend([
            "",
            "## 12. Uzak model (Ollama) Akademik Yeniden Yazım Önerisi",
            f"- {analiz['uzak_ornek_oneri']}",
        ])

    return "\n".join(satirlar) + "\n"


def dosya_yukle(yol):
    if yol == "-":
        return {"ana_metin": sys.stdin.read(), "kaynakca_satirlari": [], "yorumlar": []}
    if yol.lower().endswith(".docx"):
        return docx_ayristir(yol)
    with open(yol, encoding="utf-8") as f:
        return {"ana_metin": f.read(), "kaynakca_satirlari": [], "yorumlar": []}


def main(arg):
    if not arg or any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0 if arg else 2
    dosya = onceki = cikti_yolu = None
    json_cikti = False
    uzak_kullan = False
    tam_rapor = False
    i = 0
    while i < len(arg):
        a = arg[i]
        if a == "--tam":
            tam_rapor = True; i += 1
        elif a == "--onceki" and i + 1 < len(arg):
            onceki = arg[i + 1]; i += 2
        elif a == "--cikti" and i + 1 < len(arg):
            cikti_yolu = arg[i + 1]; i += 2
        elif a == "--json":
            json_cikti = True; i += 1
        elif a == "--uzak":
            uzak_kullan = True; i += 1
        elif a.startswith("-") and a != "-":
            print(f"tez_analiz: bilinmeyen seçenek {a!r}", file=sys.stderr)
            return 2
        else:
            dosya = a; i += 1
    if dosya is None:
        print("tez_analiz: dosya verilmedi", file=sys.stderr)
        return 2
    for yol in (dosya, onceki):
        if yol and yol != "-" and not os.path.isfile(yol):
            print(f"tez_analiz: dosya bulunamadı: {yol}", file=sys.stderr)
            return 2
    yuklenen = dosya_yukle(dosya)
    onceki_metin = dosya_yukle(onceki)["ana_metin"] if onceki else None
    analiz = metin_analiz_et(
        yuklenen["ana_metin"],
        onceki_metin=onceki_metin,
        kaynakca_satirlari=yuklenen["kaynakca_satirlari"],
        yorumlar=yuklenen["yorumlar"],
        on_sayfalar=yuklenen.get("on_sayfalar"),
        kaynakca_ham_satirlar=yuklenen.get("kaynakca_ham_satirlar"),
        ozgecmis_satirlari=yuklenen.get("ozgecmis_satirlari"),
        kenar_bosluklari=yuklenen.get("kenar_bosluklari"),
    )
    if tam_rapor and uzak_kullan and analiz["esdizim_bulgulari"]:
        ilk_satir_no = analiz["esdizim_bulgulari"][0]["satir"]
        satir_listesi = yuklenen["ana_metin"].splitlines()
        ornek_cumle = satir_listesi[ilk_satir_no - 1] if 1 <= ilk_satir_no <= len(satir_listesi) else analiz["esdizim_bulgulari"][0]["ifade"]
        analiz["uzak_ornek_oneri"] = uzak_oneri_al(ornek_cumle[:500])
    if not tam_rapor:
        analiz = cumlesizlestir(analiz)
    if json_cikti:
        cikti_metni = json.dumps(analiz, ensure_ascii=False, indent=2) + "\n"
    else:
        cikti_metni = rapor_uret(analiz)
    if not tam_rapor:
        sizan = sizinti_denetle(cikti_metni, yuklenen["ana_metin"])
        if sizan:
            print(f"tez_analiz: SIZINTI BEKÇİSİ: çıktıda tez gövdesinden {sizan} adet {BEKCI_N} sözcüklük parça var; çıktı yazılmadı.", file=sys.stderr)
            return 3
    if cikti_yolu:
        with open(cikti_yolu, "w", encoding="utf-8") as f:
            f.write(cikti_metni)
        print(f"Rapor yazıldı: {cikti_yolu}")
    else:
        print(cikti_metni, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
