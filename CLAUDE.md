# Durulaç — bu depoda çalışan ajanlar için kurallar

Durulaç bir Claude becerisidir (skill): Türkçe metni anlamını bozmadan ve bilgi uydurmadan sadeleştirir. Kullanıcıya
dönük açıklama `README.md`'de, ajanın uyduğu kurallar `SKILL.md`'dedir. Bu dosya depoyu **geliştiren** ajan içindir.

## Yapı: iş × tür + ek (değiştirirken üçünü birlikte güncelle: `SKILL.md` "Üç seçim", `README.md` "Nasıl çalışır", `eval.md`)

| Eksen | Seçenek | Zorunlu okuma | Denetçi betik |
|---|---|---|---|
| İş | Temizle (varsayılan) | `SKILL.md`, `references/kaliplar.md` | `scripts/tarama.py`, `scripts/bilgi_koruma.py` |
| İş | Tespit | `SKILL.md` | `scripts/tarama.py` |
| İş | Özet | `SKILL.md` | `scripts/bilgi_koruma.py` |
| İş | İstem iyileştir | `references/istem-iyilestirme.md` | — |
| Tür (derin) | Finans | `references/finans.md`, `references/finans-terimleri.md` | `scripts/okunabilirlik.py` |
| Tür (derin) | Tez (`--tur tez`) | `references/tez-modu.md` | `scripts/tez_analiz.py`, `scripts/tez_onar.py` … |
| Tür (genel) | resmî, hukuk, akademik, haber, sohbet… | `references/tur-kapisi.md` | `scripts/tarama.py --tur` |
| Ek | +seo | `references/seo.md` | `scripts/seo_denetim.py` |

Yeni bir yetenek eklemeden önce sor: metne yapılan yeni bir **iş** mi, yeni bir **tür** mü, yoksa bir **ek** mi? Hiçbiri
değilse (ör. içerik kalite denetimi, alan bilgisi doğrulaması) ayrı beceri olmalı. Öğretim kalitesi denetimi bu yüzden
v2.0'da `ogretim-denetci` becerisine taşındı.

## Değişmez kurallar

- Betikler yalnız Python standart kütüphanesiyle çalışır (≥ 3.9); ağ, anahtar, dış paket zorunluluğu eklenmez. PDF
  ölçümü (`pdftotext`, `pdfimages`) isteğe bağlıdır; yoksa betik "ölçülmedi" der, puan uydurmaz.
- Metne ya da kurala kaynağında olmayan olgu, sayı, kaynak eklenmez. Kalıp, eşik ya da alan kuralı eklerken dayanağı
  yazılır; kaynağı doğrulanamayan kural en çok **UYARI** ya da elle madde olur, **HATA** olamaz.
- Korumalı türlerde (resmî, hukuk belgesi, akademik, edebî) kalıp listesi kapalıdır; `references/tur-kapisi.md`.
- Kişisel veri, gerçek hasta bilgisi, özel sunucu adı ya da yerel dosya yolu depoya girmez (depo herkese açıktır).
- `YOL_HARITASI.md` yerel kalır (`.git/info/exclude`); tikleri `yol-haritasi.py` atar.

## Test

```bash
for t in scripts/test_*.py; do python3 -B "$t" || echo "KIRMIZI: $t"; done
(cd scripts && python3 -I -m pytest -q tests)
```

Her yeni kontrol için olumlu ve olumsuz test yaz; testi kasten bozup (eşiği kapat, deseni boşalt) kırmızıya döndüğünü
gör, geri al. README'deki test sayısını güncelle.

## Sürüm

`SKILL.md` `version` alanı, `README.md` sürüm geçmişi ve git etiketi aynı numarayı taşır. Commit iletisi Türkçe ve
kısa: `2.0.0: …`.
