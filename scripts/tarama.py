#!/usr/bin/env python3
"""Durulaç kalıp taraması: düzyazıda SKILL.md kalıplarını satır satır arar (yalnız standart kütüphane).

Amaç, düzenlemeyi "aklımdaki kalıplara göre" değil sistemli yapmak: okurken gözden kaçan kalıbı
makine yakalar. Bu bir KARAR değil kontrol listesidir; bulgu, kalıbın bağlamda doğru olduğu
yerlerde (tür kapısı, yerleşik terim, kasıtlı vurgu) yok sayılabilir. Skor ya da "yapay mı"
kararı vermez.

Kullanım:
  python3 tarama.py README.tr.md                      # bulgular + özet
  python3 tarama.py yeni.md --onceki eski.md          # kalıp başına önce → sonra sayıları
  python3 tarama.py metin.md --tur resmi              # korumalı tür: tarama devre dışı
  python3 tarama.py - < metin.md                      # standart girdi
Seçenekler:
  --onceki DOSYA       karşılaştırma için eski sürüm
  --tur TÜR            resmi | akademik | hukuk → "kalıp taraması devre dışı" der (tür kapısı)
  --ingilizce-terim    sözlükteki "İngilizce terim" bölümünü de tara (varsayılan: kapalı, teknik metin)
  --ozet               yalnız özet
Yok sayılanlar: ``` kod çitleri, `satır içi kod`, URL'ler, markdown bağlantı hedefleri, HTML etiketleri,
tablo ayraç satırları. Tablo hücrelerindeki düzyazı taranır.
Çıkış kodu: 0 (bulgu varlığı hata sayılmaz); 2 kullanım hatası.
"""
import os
import re
import sys
from collections import Counter, OrderedDict

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
SOZLUK = os.path.join(HERE, os.pardir, "references", "degistirme-sozlugu.md")
KORUMALI = {"resmi", "resmî", "akademik", "hukuk"}

# (kalıp no, ad, regex, öneri)  — no, SKILL.md "Kalıplar" numaralarıdır; 55+ "Çeviri kokusu" bölümüdür.
KURALLAR = [
    (28, "uzun çizgi (—)", r"\s—\s|—", "ara söz için virgül/ayraç; konuşma çizgisi değilse kısa çizgi ya da iki nokta"),
    (29, "ve/veya", r"\bve/veya\b", "“veya” kapsayıcıdır"),
    (15, "tarafından", r"\btarafından\b", "edilgeni çöz, faili öne al"),
    (3, "-mekte/-makta", r"\b\w+(?:mekte|makta)\w*\b", "günlük/teknik anlatımda geniş zaman (“yapıyor”)"),
    (31, "ile ilgili/hakkında/-e yönelik/-e ilişkin", r"\b(?:ile ilgili|hakkında|\w+[ae] yönelik|\w+[ae] ilişkin|ilişkin)\b",
     "doğrudan tamlama kur"),
    (35, "şekilde", r"\bşekilde\b", "“-la/-le” ya da tek zarf yeter"),
    (33, "gerçekleştir-/sağla- jeneriği", r"\b(?:gerçekleştir\w*|sağlan\w*|sağlar\w*|sağlıyor\w*)\b", "öz fiil kullan"),
    (6, "dolgu geçişi", r"\b(?:bu bağlamda|bu doğrultuda|sonuç olarak|bu çerçevede)\b", "paragrafı ilerletmiyorsa çıkar"),
    (7, "boğaz temizleme", r"\b(?:belirtmek gerekir ki|bilindiği üzere|unutulmamalıdır ki)\b", "doğrudan söyle"),
    (5, "bürokratik edat", r"\b(?:hususunda|nezdinde|noktasında|bağlamında)\b", "konusunda/-de"),
    (44, "amacıyla/kapsamında sarmalı", r"\b(?:amacıyla|kapsamında|çerçevesinde)\b", "eylemi öne al"),
    (54, "söz konusu/bahse konu", r"\b(?:söz konusu|bahse konu|mevzubahis)\b", "göndergeyi adıyla an"),
    (4, "önem arz etmek", r"\bönem arz\w*", "gerekçe ver ya da çıkar"),
    (46, "önemli adım/katkı", r"\bönemli (?:bir )?(?:adım|katkı)\b", "gerekçeyi söyle"),
    (39, "hayata geçirmek", r"\bhayata geçir\w*", "tarih/eylemle değiştir"),
    (40, "değer katmak/katma değer", r"\b(?:değer kat\w*|katma değer\w*)\b", "ne yapıldığını söyle"),
    (41, "fark yaratmak", r"\bfark yarat\w*", "ölçüyle değiştir"),
    (17, "reklam sıfatı", r"\b(?:kusursuz|eşsiz|benzersiz|devrim niteliğinde|çığır açan|vazgeçilmez|sorunsuz|yenilikçi|çözüm odaklı)\b",
     "kanıtla ya da çıkar"),
    (21, "jenerik çağ açılışı", r"\b(?:günümüzün|bilgi çağında|hızlı tempolu)\b", "somut girişle değiştir"),
    (49, "sahte-içgörü girişi", r"\b(?:işte tam bu noktada|asıl mesele şu ki)\b", "doğrudan söyle"),
    (12, "kendi kendine soru", r"\bpeki ya\b", "gerçek soru yoksa kaldır"),
    (9, "sadece… değil, aynı zamanda", r"\b(?:sadece|yalnızca|yalnız)\b[^.]{0,60}\bdeğil\b[^.]{0,40}\baynı zamanda\b", "“hem… hem…”"),
    (38, "ISO tarih düzyazıda", r"\b20\d\d-\d\d-\d\d\b", "düzyazıda “8 Ekim 2026” (log/komutta ISO kalır)"),
    (38, "binlik ayırıcı virgül", r"\b\d{1,3}(?:,\d{3})+\b(?!\d)", "Türkçede binlik nokta: 1.000.000"),
    (38, "ondalık nokta (yüzde)", r"%\d+\.\d+|\d+\.\d+\s?%", "ondalık virgül: %5,5"),
    # Çeviri kokusu (SKILL.md kalıp 55-60)
    (55, "atıf yapılan/atıf yapmak", r"\batıf yap\w*", "“kaynak gösterilen / gösterilen” (atıf akademiktir)"),
    (55, "buluşsal (heuristic)", r"\bbuluşsal\w*", "“sezgisel”"),
    (55, "koşu/koşturmak (run)", r"\b(?:koşturun|koşturmak|koşturur\w*|koşular\w*|koşuda|koşu)\b", "“çalıştırma/deneme/çalışma”, “başlatın”"),
    (55, "tolere etmek", r"\btolere\w*", "“kabul etmek / yok saymak”"),
    (55, "örnekleme/örnekle (spot-check)", r"\börnekle\w*", "istatistik değilse “kontrol et / göz at”"),
    (55, "kapalı-varsayılan (fail-closed)", r"\bkapalı-varsayılan\w*", "“varsayılanı yasak olan / güvenli tarafta kalan”"),
    (55, "kapı (gate)", r"\bkapı olarak\b", "“denetim noktası / engel”"),
    (55, "hoş görmek (tolerate çevirisi)", r"\bhoş görül\w*", "“kabul edilir / yok sayılır”"),
    (56, "çalışan (worker)", r"\bçalışan\w*", "worker anlamındaysa Türkçede insan çalışan çağrışımı var: “alt ajan”/tanımlı terim; ilk geçişte tanımla"),
]

# Sözlükte taranacak bölümler (başlık içinde geçen ifadeler). İngilizce terim bölümü varsayılan kapalı.
SOZLUK_ACIK = ("Yardımcı fiil", "Bürokratik edat", "-mekte", "Arkaik", "Plaza", "Eş dizim", "Reklam sıfatı")  # "Çeviri kokusu" bölümü KURALLAR'da
SOZLUK_KAPALI_VARSAYILAN = ("İngilizce terim",)
SOZLUK_SATIR = re.compile(r"^-\s+`([^`]+)`\s*→\s*(.+?)\s*$")


def kucult(s):
    return s.replace("İ", "i").replace("I", "ı").lower()


def temizle(metin):
    """Kod, satır içi kod, URL, bağlantı hedefi, HTML etiketi ve tablo ayraç satırlarını boşlukla örter (sütun/satır korunur)."""
    satirlar, kodda = [], False
    for ham in metin.split("\n"):
        if re.match(r"^\s*(```|~~~)", ham):
            kodda = not kodda
            satirlar.append("")
            continue
        if kodda or re.match(r"^\s*\|?[\s:\-|]+\|?\s*$", ham) and "|" in ham:
            satirlar.append("")
            continue
        s = re.sub(r"`[^`]*`", lambda m: " " * len(m.group(0)), ham)
        s = re.sub(r"\]\([^)]*\)", lambda m: "]" + " " * (len(m.group(0)) - 1), s)
        s = re.sub(r"https?://\S+", lambda m: " " * len(m.group(0)), s)
        s = re.sub(r"<[^>]+>", lambda m: " " * len(m.group(0)), s)
        satirlar.append(s)
    return satirlar


def sozluk_kurallari(ingilizce_terim=False):
    """references/degistirme-sozlugu.md → (ad, regex, öneri) listesi."""
    kurallar, acik = [], False
    try:
        with open(SOZLUK, encoding="utf-8") as f:
            satirlar = f.read().split("\n")
    except OSError:
        return kurallar
    kapali = SOZLUK_KAPALI_VARSAYILAN if not ingilizce_terim else ()
    for l in satirlar:
        if l.startswith("## "):
            baslik = l[3:]
            acik = any(a in baslik for a in SOZLUK_ACIK) or (ingilizce_terim and any(k in baslik for k in SOZLUK_KAPALI_VARSAYILAN))
            if any(k in baslik for k in kapali):
                acik = False
            continue
        m = SOZLUK_SATIR.match(l)
        if not (acik and m):
            continue
        anahtar, oneri = m.group(1).strip(), re.sub(r"\s*\*\*\[.*", "", m.group(2)).strip()
        if len(anahtar) < 3 or "(" in anahtar:
            continue
        k = kucult(anahtar)
        if k.endswith("etmek") and len(k) > 6:
            desen = re.escape(k[:-5].rstrip()) + r"\s+(?:et|ed)\w*"
        elif k.endswith(("mek", "mak")) and len(k) > 5:
            desen = re.escape(k[:-3]) + r"\w*"
        else:
            desen = re.escape(k)
        try:
            kurallar.append((0, f"sözlük: {anahtar}", re.compile(r"(?<![\wçğıöşü])" + desen + r"(?![\wçğıöşü])", re.IGNORECASE), oneri))
        except re.error:
            continue
    return kurallar


def derle(ingilizce_terim=False):
    kurallar = [(no, ad, re.compile(rx, re.IGNORECASE), oneri) for no, ad, rx, oneri in KURALLAR]
    kurallar += sozluk_kurallari(ingilizce_terim)
    return kurallar


def uzun_cumleler(satirlar, esik=35):
    bulgu = []
    for n, s in enumerate(satirlar, 1):
        if not s.strip() or s.lstrip().startswith("#"):
            continue
        for cumle in re.split(r"(?<=[.!?…])\s+", s):
            sozcuk = re.findall(r"[A-Za-zÇĞİÖŞÜçğıöşüÂÎÛâîû]+", cumle)
            if len(sozcuk) > esik:
                bulgu.append((n, 1, 36, f"uzun cümle ({len(sozcuk)} sözcük)", cumle.strip()[:70], "böl; ana bilgiyi öne al"))
    return bulgu


def sahis_karisimi(metin_temiz):
    gövde = " ".join(metin_temiz)
    # "temiz", "yeniz" gibi sözcükleri saymamak için iyelik/fiil ekleri en az iki harflik gövdeye bağlı aranır
    ben_biz = re.findall(r"\b\w{2,}(?:ımız|imiz|umuz|ümüz)\w*\b|\b\w{2,}(?:ıyoruz|iyoruz|uyoruz|üyoruz)\b|\bbiz(?:im)?\b", gövde, re.I)
    ucuncu = re.findall(r"\byazar(?:ın|a|ı)?\b|\bgeliştirici(?:ler)?(?:in)?\b", gövde, re.I)
    if ben_biz and ucuncu:
        return [(1, 1, 60, "şahıs karışımı olabilir", f"1. çoğul: {len(ben_biz)}× (örn. {ben_biz[0]}) · 3. kişi/yazar: {len(ucuncu)}×",
                 "tek şahıs seç: ya “biz” ya “yazar”; okura “siz”")]
    return []


def ayni_baglac(metin):
    acilis = Counter()
    for par in re.split(r"\n\s*\n", metin):
        ilk = re.match(r"\s*(Ayrıca|Bununla birlikte|Ek olarak|Dolayısıyla|Ancak|Öte yandan)\b", par)
        if ilk:
            acilis[ilk.group(1)] += 1
    return [(1, 1, 52, "aynı bağlaçla paragraf açma", f"“{b}” {n} paragrafı açıyor", "bağlacı değiştir ya da at")
            for b, n in acilis.items() if n >= 3]


def tara(metin, kurallar):
    satirlar = temizle(metin)
    bulgu = []
    for n, s in enumerate(satirlar, 1):
        if not s.strip():
            continue
        for no, ad, rx, oneri in kurallar:
            for m in rx.finditer(s):
                bulgu.append((n, m.start() + 1, no, ad, m.group(0).strip(), oneri))
    bulgu += uzun_cumleler(satirlar) + sahis_karisimi(satirlar) + ayni_baglac(metin)
    bulgu.sort(key=lambda b: (b[0], b[1]))
    return bulgu


def ozet_sayilari(bulgu):
    c = OrderedDict()
    for _, _, no, ad, _, _ in bulgu:
        ad = "sözlük eşlemesi" if ad.startswith("sözlük: ") else re.sub(r"\s*\(\d+ sözcük\)", "", ad)
        anahtar = (no, ad)
        c[anahtar] = c.get(anahtar, 0) + 1
    return c


def oku(yol):
    if yol == "-":
        return sys.stdin.read()
    with open(yol, encoding="utf-8") as f:
        return f.read()


def main(arg):
    if not arg or any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0 if arg else 2
    dosya = onceki = tur = None
    ingilizce, sadece_ozet = False, False
    i = 0
    while i < len(arg):
        a = arg[i]
        if a == "--onceki" and i + 1 < len(arg):
            onceki = arg[i + 1]; i += 2
        elif a == "--tur" and i + 1 < len(arg):
            tur = kucult(arg[i + 1]); i += 2
        elif a == "--ingilizce-terim":
            ingilizce = True; i += 1
        elif a == "--ozet":
            sadece_ozet = True; i += 1
        elif a.startswith("-") and a != "-":
            print(f"tarama: bilinmeyen seçenek {a!r} (yardım için --help)", file=sys.stderr)
            return 2
        else:
            dosya = a; i += 1
    if dosya is None:
        print("tarama: dosya verilmedi", file=sys.stderr)
        return 2
    for yol in (dosya, onceki):
        if yol and yol != "-" and not os.path.isfile(yol):
            print(f"tarama: dosya bulunamadı: {yol}", file=sys.stderr)
            return 2
    if tur in KORUMALI:
        print(f"Korumalı tür ({tur}): kalıp taraması devre dışı. Varsayılan 0 değişiklik; yalnız açık yazım/noktalama hatası düzeltilir.")
        return 0
    kurallar = derle(ingilizce)
    yeni = tara(oku(dosya), kurallar)
    if not sadece_ozet:
        for n, s, no, ad, alinti, oneri in yeni:
            etiket = f"kalıp {no}" if no else "sözlük"
            print(f"{n}:{s} [{etiket} · {ad}] «{alinti}» → {oneri}")
    sy = ozet_sayilari(yeni)
    print(f"\nToplam {len(yeni)} bulgu · {len(sy)} kalıp türü")
    if onceki:
        eski = ozet_sayilari(tara(oku(onceki), kurallar))
        print("\nKalıp                                         önce → sonra")
        for anahtar in sorted(set(eski) | set(sy), key=lambda k: (k[0], k[1])):
            e, y = eski.get(anahtar, 0), sy.get(anahtar, 0)
            isaret = "  ↓" if y < e else "  ↑ (YENİ SORUN?)" if y > e else ""
            print(f"  [{anahtar[0] or 'söz'}] {anahtar[1][:38]:<38} {e:>3} → {y:<3}{isaret}")
        te, ty = sum(eski.values()), sum(sy.values())
        print(f"  {'TOPLAM':<45} {te:>3} → {ty:<3}")
    print("\nNot: bu bir kontrol listesidir, hüküm değil. Tür kapısına bak; yerleşik terim, kasıtlı vurgu ve resmî kalıbı yok say.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
