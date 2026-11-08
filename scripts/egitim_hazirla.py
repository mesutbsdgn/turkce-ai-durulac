#!/usr/bin/env python3
"""Türkçe akademik tez ve kelime mantığı (eş dizim) eğitimi için JSONL veri seti üreticisi.

`references/akademik-esdizim.json` kurallarından ve kalıp 61–66 örneklerinden
negatif (bozuk) → pozitif (doğal akademik Türkçe) eğitim çiftleri (`instruction/input/output`)
üretir; her çifti `bilgi_koruma` (sayı, tarih, özel ad ve APA/IEEE atıf koruması) süzgecinden geçirir.

Kullanım:
  python3 egitim_hazirla.py                         # JSONL satırlarını stdout'a yazar
  python3 egitim_hazirla.py --cikti egitim.jsonl    # dosyaya yazar
  python3 egitim_hazirla.py --ozet                  # toplam çift ve alan dağılımını basar
"""
import json
import os
import re
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bilgi_koruma as bk  # noqa: E402
import esdizim as esd  # noqa: E402

# Kasten bozma ve birim testi kontrol bayrağı: True iken sayı/atıf/özel ad koruma kapısını çalıştırır
KORUMA_DOGRULAMA_AKTIF = True

SISTEM_YONERGESI = (
    "Aşağıdaki Türkçe akademik tez metnini, anlamını, APA/IEEE kaynak atıflarını, "
    "sayıları, yüzdeleri ve edilgen akademik çatıyı (-ılmıştır, -mektedir) koruyarak "
    "Türkçe kelime mantığına (doğal fiil-nesne eş dizimine) uygun biçimde düzeltin."
)

ATIF_RE = re.compile(r"\(\s*[^)]*(?:19|20)\d\d[^)]*\)|\[\d+(?:\s*[-,]\s*\d+)*\]")

YAPISAL_TEZ_CIFTLERI = [
    {
        "id": "YAP-061A",
        "alan": "ceviri_kokusu",
        "input": "Bu çalışma (Kaya, 2020: 34) siber caydırıcılık literatüründeki boşluğu doldurmak ve atfedilebilirlik sorununu adreslemek amacıyla yürütülmüştür.",
        "output": "Bu çalışma (Kaya, 2020: 34) siber caydırıcılık literatüründeki eksikliği gidermek ve atfedilebilirlik sorununu ele almak amacıyla yürütülmüştür.",
    },
    {
        "id": "YAP-061B",
        "alan": "ceviri_kokusu",
        "input": "Soğuk Savaş sonrası dönem [12] asimetrik çatışmalarla karakterize edilmekte ve yazarlar yeni argümanlar ileri sürmektedir.",
        "output": "Soğuk Savaş sonrası dönem [12] asimetrik çatışmalarla belirginleşmekte ve yazarlar yeni savlar öne sürmektedir.",
    },
    {
        "id": "YAP-063A",
        "alan": "akademik_klise",
        "input": "Ulusal siber güvenlik stratejileri (%74,5 oranında) kritik altyapıların korunmasında kritik bir rol oynamaktadır (Demir, 2019).",
        "output": "Ulusal siber güvenlik stratejileri (%74,5 oranında) kritik altyapıların korunmasında belirleyici olmaktadır (Demir, 2019).",
    },
    {
        "id": "YAP-065A",
        "alan": "tamlama_zinciri",
        "input": "Uluslararası sistemin aktörlerinin güvenlik stratejilerinin dönüşümünün etkileri 2015 yılında incelenmiştir.",
        "output": "Uluslararası sistemdeki aktörlerin güvenlik stratejilerinde 2015 yılında yaşanan dönüşümün etkileri incelenmiştir.",
    },
    {
        "id": "YAP-066A",
        "alan": "sahis_uyumu",
        "input": "Tezimizde 2018-2022 dönemindeki 48 siber operasyonu ele aldık ve kanaatimce caydırıcılık sınırları doğrulanmıştır.",
        "output": "Bu çalışmada 2018-2022 dönemindeki 48 siber operasyon ele alınmış ve caydırıcılık sınırları doğrulanmıştır.",
    },
    {
        "id": "KLV-001",
        "alan": "kilavuz",
        "input": "Realist teori çerçevesinde devletlerin siber savunma kuramları (Yılmaz, 2020: 44) karşılaştırmalı metot ve nitel yöntem ile incelenmiştir.",
        "output": "Realist kuram çerçevesinde devletlerin siber savunma kuramları (Yılmaz, 2020: 44) karşılaştırmalı ve nitel yöntem ile incelenmiştir.",
    },
    {
        "id": "KLV-002",
        "alan": "kilavuz",
        "input": "Uluslararası hukukta 5651 sayılı yasa ve ilgili kanun hükümleri (Kaya, 2019: 18) siber alanda ve siber uzayda devlet sorumluluğunu düzenlemektedir.",
        "output": "Uluslararası hukukta 5651 sayılı kanun ve ilgili kanun hükümleri (Kaya, 2019: 18) siber uzayda devlet sorumluluğunu düzenlemektedir.",
    },
    {
        "id": "KLV-003",
        "alan": "kilavuz",
        "input": "Kritik altyapılara yönelik 2018-2022 dönemi siber saldırı verileri Tablo 12 içinde ve Şekil 5 kapsamında (Demir, 2021: 63) tehdit sergilemektedir.",
        "output": "Kritik altyapılara yönelik 2018-2022 dönemi siber saldırı verileri Çizelge 12 içinde ve Şekil 5 kapsamında (Demir, 2021: 63) tehdit oluşturmaktadır.",
    },
    {
        "id": "KLV-004",
        "alan": "kilavuz",
        "input": "Araştırmamızda ele aldığımız 3 temel hipotez gerçekleştirdik ve ulaştığımız bulgular ışığında politika inşa etmek kritik bir rol oynamaktadır (Örnek, 2022: 91).",
        "output": "Bu çalışmada ele alınan 3 temel hipotez sınanmış ve ulaşılan bulgular ışığında politika geliştirmek belirleyici olmaktadır (Örnek, 2022: 91).",
    },
]

ATIF_SABLONLARI = [
    ("Yılmaz, 2018: 42", "%64,2 oranında"),
    ("Kaya ve Demir, 2020: 118", "3 temel boyutta"),
    ("Öztürk, 2019", "%18,5 düzeyinde"),
    ("Örnek, 2021: 77", "12 ülkede"),
]


def cift_gecerli_mi(girdi, cikti):
    """Girdi metnindeki sayı, özel ad ve kaynak atıflarının çıktı metninde korunduğunu doğrular."""
    if not girdi.strip() or not cikti.strip() or girdi.strip() == cikti.strip():
        return False
    if not KORUMA_DOGRULAMA_AKTIF:
        return True
    kayip = bk.kayiplar(girdi, cikti)
    if "sayı" in kayip or "ad" in kayip or "alıntı" in kayip:
        return False
    girdi_atiflar = ATIF_RE.findall(girdi)
    cikti_atiflar = ATIF_RE.findall(cikti)
    if girdi_atiflar != cikti_atiflar:
        return False
    return True


def ciftleri_uret(kurallar=None):
    """Eş dizim kurallarından ve yapısal tez kalıplarından doğrulanmış JSONL eğitim çiftleri üretir."""
    if kurallar is None:
        kurallar = esd.kurallari_yukle()
    veri_seti = []
    for idx, k in enumerate(kurallar):
        yanlis = k["ornek_yanlis"].strip()
        dogru = k["ornek_dogru"].strip()
        if cift_gecerli_mi(yanlis, dogru):
            veri_seti.append({
                "id": k["id"],
                "alan": k["alan"],
                "instruction": SISTEM_YONERGESI,
                "input": yanlis,
                "output": dogru,
            })
        # Atıf ve sayı koruma pekiştirmeli ikinci varyant
        atif, olcu = ATIF_SABLONLARI[idx % len(ATIF_SABLONLARI)]
        if yanlis.endswith(".") and dogru.endswith("."):
            yanlis_atifli = f"{yanlis[:-1]} ({atif}; {olcu})."
            dogru_atifli = f"{dogru[:-1]} ({atif}; {olcu})."
            if cift_gecerli_mi(yanlis_atifli, dogru_atifli):
                veri_seti.append({
                    "id": f"{k['id']}-ATIF",
                    "alan": k["alan"],
                    "instruction": SISTEM_YONERGESI,
                    "input": yanlis_atifli,
                    "output": dogru_atifli,
                })
    for y in YAPISAL_TEZ_CIFTLERI:
        if cift_gecerli_mi(y["input"], y["output"]):
            veri_seti.append({
                "id": y["id"],
                "alan": y["alan"],
                "instruction": SISTEM_YONERGESI,
                "input": y["input"],
                "output": y["output"],
            })
    return veri_seti


def ciftleri_filtrele(ham_ciftler):
    """Dışarıdan verilen aday çift listesinden sayı/atıf/özel ad kaybı olanları eler."""
    gecerli = []
    for c in ham_ciftler:
        if cift_gecerli_mi(c.get("input", ""), c.get("output", "")):
            gecerli.append(c)
    return gecerli


def main(arg):
    if any(a in ("-h", "--help") for a in arg):
        print(__doc__)
        return 0
    cikti_yolu = None
    sadece_ozet = False
    i = 0
    while i < len(arg):
        a = arg[i]
        if a == "--cikti" and i + 1 < len(arg):
            cikti_yolu = arg[i + 1]; i += 2
        elif a == "--ozet":
            sadece_ozet = True; i += 1
        else:
            print(f"egitim_hazirla: bilinmeyen seçenek {a!r}", file=sys.stderr)
            return 2

    ciftler = ciftleri_uret()
    if sadece_ozet:
        alan_say = Counter(c["alan"] for c in ciftler)
        print(f"Toplam {len(ciftler)} doğrulanmış eğitim çifti:")
        for alan, adet in sorted(alan_say.items()):
            print(f"  {alan:<20}: {adet}")
        return 0

    satirlar = [json.dumps(c, ensure_ascii=False) for c in ciftler]
    if cikti_yolu:
        with open(cikti_yolu, "w", encoding="utf-8") as f:
            f.write("\n".join(satirlar) + "\n")
        print(f"Yazıldı: {cikti_yolu} ({len(satirlar)} eğitim çifti)")
    else:
        print("\n".join(satirlar))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
