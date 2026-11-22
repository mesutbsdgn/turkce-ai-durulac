# Durulaç — bu depoda çalışan ajanlar için kurallar

Durulaç bir Claude becerisidir (skill): Türkçe metni anlamını bozmadan ve bilgi uydurmadan sadeleştirir. Kullanıcıya
dönük açıklama `README.md`'de, ajanın uyduğu kurallar `SKILL.md`'dedir. Bu dosya depoyu **geliştiren** ajan içindir.

## Sekiz kip (değiştirirken üçünü birlikte güncelle: `SKILL.md` tablosu, `README.md` "Sekiz kip", `eval.md`)

| Kip | Türü | Zorunlu okuma | Denetçi betik |
|---|---|---|---|
| Temizle | ana, varsayılan | `SKILL.md`, `references/kaliplar.md` | `scripts/tarama.py`, `scripts/bilgi_koruma.py` |
| Tespit | ana | `SKILL.md` | `scripts/tarama.py` |
| İstem iyileştir | ana | `references/istem-iyilestirme.md` | — |
| Özet | ana | `SKILL.md` | `scripts/bilgi_koruma.py` |
| Finans | ek | `references/finans.md`, `references/finans-terimleri.md` | `scripts/okunabilirlik.py` |
| Tez (`--tur tez`) | ek | `references/tez-modu.md` | `scripts/tez_analiz.py`, `scripts/tez_onar.py` … |
| +seo | ek | `references/seo.md` | `scripts/seo_denetim.py` |
| +ogretim | ek | `references/ogretim.md` | `scripts/ogretim_denetim.py` + `references/ogretim-alanlari.json` |

## Değişmez kurallar

- Betikler yalnız Python standart kütüphanesiyle çalışır (≥ 3.9); ağ, anahtar, dış paket zorunluluğu eklenmez. PDF
  ölçümü (`pdftotext`, `pdfimages`) isteğe bağlıdır; yoksa betik "ölçülmedi" der, puan uydurmaz.
- Metne ya da kurala kaynağında olmayan olgu, sayı, kaynak eklenmez. Kalıp, eşik ya da alan kuralı eklerken dayanağı
  yazılır; kaynağı doğrulanamayan kural en çok **UYARI** ya da elle madde olur, **HATA** olamaz.
- `+ogretim` sağlık kuralları en sıkı kısımdır: HATA olanlar (doz yazımı, hasta kimliği, TC kimlik no) ancak birincil
  kaynakla (ISMP, FDA, yönetmelik) değiştirilir. Betik dozun klinik doğruluğunu denetlemez; bunu iddia eden metin yazma.
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

## Yeni `+ogretim` alanı eklemek

1. `references/ogretim-alanlari.json`: `ad`, `sozcukler` (4 harf ve kısası yalnız tam sözcük eşleşir; genel sözcük
   koyma: "plan", "baz", "tür" başka alanları çalar), isteğe bağlı `ust`, `kontroller` (`@saglik`, `@fen`, `@kaynak`,
   `@sayisal` grupları), `elle`, `sinama_oneri`.
2. Yeni kontrol gerekiyorsa `scripts/ogretim_denetim.py` içinde `k_…` işlevi + `KONTROLLER` kaydı; eşik dosya başında sabit.
3. `references/ogretim.md` alan tablosuna satır ve dayanak; kanıtı `docs/ogretim-alan-kanitlari.md`'ye.
4. `scripts/test_ogretim_denetim.py`: tespit testi (`ALAN_ORNEKLERI`) ve kontrol testi.

## Sürüm

`SKILL.md` `version` alanı, `README.md` sürüm geçmişi ve git etiketi aynı numarayı taşır. Commit iletisi Türkçe ve
kısa: `1.9.0: …`.
