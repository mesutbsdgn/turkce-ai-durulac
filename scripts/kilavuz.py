#!/usr/bin/env python3
"""kilavuz.py — tez yazım profili yükleyicisi (yalnız standart kütüphane).

VARSAYILAN profil, bu beceriyi yazan kişinin tezinde uygulanan yazım kılavuzunun değerlerini taşır (kurum adı yok).
Başka bir kılavuza uyarlamak için üç yol (öncelik sırasıyla):
  1. `yukle(yol)` ile açık bir JSON yolu,
  2. `DURULAC_TEZ_PROFIL` ortam değişkeni (kendi JSON dosyanız),
  3. `references/tez-yazim-kilavuzu.json` dosyasını düzenlemek.
Eksik anahtarlar aşağıdaki varsayılanlarla tamamlanır. Hangi anahtarın neyi etkilediği: README.md >
"Tez profilini kendi kılavuzuna uyarlama".

Atıf sayfa biçimi (`atif.sayfa_bicimi`):
  "iki_nokta"  (Soyad, 2014: 102)     Türkçe akademik yazında yaygın
  "apa7"       (Soyad, 2014, s. 102)  APA 7
"""
import copy
import json
import os

ORTAM_DEGISKENI = "DURULAC_TEZ_PROFIL"

HERE = os.path.dirname(os.path.abspath(__file__))
VARSAYILAN_YOL = os.path.join(HERE, os.pardir, "references", "tez-yazim-kilavuzu.json")

VARSAYILAN = {
    "profil": "yazar-tezi",
    "sayfa_duzeni": {"ust_kenar_cm": 2.5, "alt_kenar_cm": 2.5, "dis_kenar_cm": 2.5, "ic_kenar_cm": 4.0, "kenar_toleransi_cm": 0.15},
    "baslik": {"duzey1_buyuk_harf": True, "alt_duzey_baglac_kucuk": True, "numara_sonrasi_bosluk": True},
    "terim_birligi_ciftleri": [
        {"id": "TRM-01", "terim_a": "kanun", "terim_b": "yasa"},
        {"id": "TRM-02", "terim_a": "teori", "terim_b": "kuram"},
        {"id": "TRM-03", "terim_a": "tabiat", "terim_b": "doğa"},
        {"id": "TRM-04", "terim_a": "yöntem", "terim_b": "metot"},
        {"id": "TRM-05", "terim_a": "olanak", "terim_b": "imkân"},
        {"id": "TRM-06", "terim_a": "koşul", "terim_b": "şart"},
        {"id": "TRM-07", "terim_a": "siber uzay", "terim_b": "siber alan"},
        {"id": "TRM-08", "terim_a": "uluslararası", "terim_b": "milletlerarası"},
    ],
    "ozet": {"min_kelime": 250, "maks_kelime": 400, "min_anahtar_kelime": 3, "maks_anahtar_kelime": 5},
    "sekil_tablo": {"tablo_adi": "Çizelge", "sekil_adi": "Şekil", "karisik_ad_uyar": True, "bolum_numarali_uyar": True},
    "atif": {"sayfa_bicimi": "iki_nokta", "ampersand_uyar": True, "ve_digerleri_uyar": True},
    "kaynakca": {"alt_baslik_zorunlu": True, "alt_basliklar": ["KİTAPLAR", "MAKALELER", "ELEKTRONİK KAYNAKLAR"]},
}


def _birlestir(taban, ustune):
    for anahtar, deger in ustune.items():
        if isinstance(deger, dict) and isinstance(taban.get(anahtar), dict):
            _birlestir(taban[anahtar], deger)
        else:
            taban[anahtar] = deger
    return taban


def yukle(yol=None):
    """Profili döner: varsayılanlar + (varsa) JSON dosyası. Bozuk/eksik dosyada varsayılanlara düşer."""
    profil = copy.deepcopy(VARSAYILAN)
    yol = yol or os.environ.get(ORTAM_DEGISKENI) or VARSAYILAN_YOL
    try:
        with open(yol, encoding="utf-8") as f:
            veri = json.load(f)
        if isinstance(veri, dict):
            _birlestir(profil, veri)
    except (OSError, ValueError):
        pass
    return profil


def genel_profil():
    """Daha gevşek, APA benzeri genel profil (references/tez-yazim-kilavuzu.ornek-genel.json ile aynı değerler):
    iç kenar 3,5 cm, özet 150-300 kelime, 'Tablo' adı, bölüm numaralı şekil serbest, kaynakça alt başlığı zorunlu değil."""
    p = copy.deepcopy(VARSAYILAN)
    _birlestir(p, {
        "sayfa_duzeni": {"ic_kenar_cm": 3.5},
        "ozet": {"min_kelime": 150, "maks_kelime": 300},
        "sekil_tablo": {"tablo_adi": "Tablo", "bolum_numarali_uyar": False},
        "kaynakca": {"alt_baslik_zorunlu": False},
    })
    return p
