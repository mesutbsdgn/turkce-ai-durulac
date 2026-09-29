# Doğrulama deneyleri

Durulaç, kör kabul edilmedi; kontrollü deneylerle ölçüldü. Uygulama modelleri **DeepSeek** ve **GPT-6 Luna**, puanlama bağımsız **Claude Sonnet** ile körlemesine yapıldı.

> **Dürüstlük sınırı:** Hücre başına tek örnek, tek değerlendirici, sınırlı metin türü. Sonuçlar **yön** gösterir, büyüklük iddiası değildir.

## Deney 1 — Skilsiz vs skilli, iki model (kurumsal AI-slop metin)

Sonnet /50 körlemesine:

| Model | Skilsiz | Skilli | Δ |
|-------|--------:|-------:|--:|
| DeepSeek | 29 | 38 | **+9** |
| GPT-6 Luna | 44 | 32 | −12 |

**Bulgu:** Skil zayıf/kirli tabanı yükseltir, ama güçlü modelde agresif kesme akıcılığı düşürebilir. Bu deney, aşağıdaki iyileştirmeleri (sil-ve-yeniden-bağla, şahıs tutarlılığı, tam paragraf örneği) doğurdu.

## Deney 2 — Ablasyon (Luna, kurumsal): kütle mi, çerçeve mi?

| Kol | /50 | Jenerik açılış |
|-----|----:|----------------|
| skilsiz | 44 | ✅ kaldırdı |
| tam skil | 35 | ❌ korudu |
| 46 kural çıkarılmış (strip) | 32 | ❌ korudu |

**Bulgu:** 46 kuralı çıkarmak sorunu düzeltmedi, hatta kötüleştirdi. Yani zayıflık kural *kütlesi* değil, güçlü modelin kaynak yapısına aşırı sadakati (model sınırı).

## Deney 3 — 3 tür × 2 model grid (yeni sürüm)

| Tür | DeepSeek Δ | Luna Δ |
|-----|-----------:|-------:|
| Kurumsal | +6 (yardım) | −9 (zarar: açılış klişesi) |
| Sohbet | −1 (fark yok) | +6 (yardım) |
| Teknik | +1 (marjinal) | +10 (güçlü yardım) |

**Net örüntü:** Skilin ölçülen asıl değeri **aşırı düzeltmeyi frenlemek** — Luna skilsizken *deploy→güncelleme* (anlam kaybı), *n'aptın→ne yaptın* (sohbeti resmîleştirme) gibi fazla düzeltir; skil bunu engeller. Tek net negatif hücre kurumsal×Luna'dır ve içerikle çözülemez (bkz. ablasyon).

## Pratik sonuç

- Kurumsal/resmî metin temizliğinde **güçlü bir uygulayıcı** (ör. DeepSeek) tercih edin.
- Sohbet ve teknik metinde skil her modelde tutarlı katkı sağlar (register ve terim koruması).

## Deney 4 — Çok-modelli kırmızı-takım + iyileştirme turu

8 tuzaklı metin (kurumsal/sohbet/teknik+kod/akademik/dilekçe/deyim/temiz/tespit), iki uygulayıcı (DeepSeek, Qwen), Sonnet hakem, **Opus 4.8 kırmızı-takım**. Opus 7 sistematik kusur buldu (P1–P7); en kritiği: *"koruma kısa bir listeye, düzeltme uzun bir listeye yaslanmış; çeliştiklerinde uzun liste kazanıyor."*

Uygulanan düzeltmeler: (P1) korumalı türlerde kalıp/sözlük açıkça DEVRE DIŞI, (P2) "sadeleştirme ≠ özetleme" + cümle atma yasağı, (P3) çıplak İngilizce süreç-adı 3. kategorisi, (P4) sohbette kalıp 8/30 devre dışı + yumuşatıcı koruması, (P5) uzunluğu niteliğe çevirme, (P6) edilgende "biz" uydurma yasağı, (P7) tespit modunda kalıp-yığma yasağı.

Aynı bataryayla ikinci tur (Sonnet /10 ortalama):

| Model | Önce | Sonra | Δ |
|-------|-----:|------:|--:|
| DeepSeek | 7.98 | **9.53** | +1.55 |
| Qwen | 8.40 | **9.00** | +0.60 |

Dilekçe aşırı düzenleme, "deploy" çevirisi, aşırı sıkıştırma, "biz" uydurma ve kalıp-yığma hatalarının tümü kapandı; regresyon gözlenmedi.
