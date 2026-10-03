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

## Deney 5 — Kapsam genişletme (4 tür kapısı + 8 kalıp) ve regresyon

Araştırma turundan (kaynaklı: dergipark, TDK, no-ai-slop, Netflix altyazı kılavuzu) sonra eklenenler: altyazı, sosyal medya, haber ve edebî tür kapıları; 8 yeni kalıp (çıplak İngilizce ad/süreç, şişkin gelecek, sahte-içgörü girişi, yüzeysel analiz iskeleti, sahte-derin kapanış, paragraf-açılışı tekrarı, dramatik kesik cümle, "söz konusu" yığını); tespit modu nitel belirteçleri + perplexity dışlama ve "tespit kesin değildir" notu. **Okunabilirlik skoru bilinçli EKLENMEDİ** (LLM hece/kelime sayımı güvenilmez, sayı halüsinasyonu riski; formüller uzman görüşüyle tutarsız).

Aynı 8 metin (regresyon) + 5 yeni metin (yeni kapılar), DeepSeek+Qwen, Sonnet /10:

| Model | Önce (8 madde) | Sonra (8 madde) | Genel (13) |
|-------|---:|---:|---:|
| DeepSeek | 9.53 | 9.93 | 9.94 |
| Qwen | 9.00 | 9.53 | 9.25 |

Regresyon yok; DeepSeek yükseldi. Yeni kapılar doğrulandı (altyazı satırları birleştirilmez, sosyal medya işaretleri korunur, haberde basın-bülteni kalıpları uygulanmaz, edebî metne dokunulmaz, plaza adları Türkçeleşir). Qwen'in iki nokta hatası (geçersiz çekim, haber kapısı ihlali) model zayıflığıdır, skil kusuru değil; haber kapısı yine de "DEVRE DIŞI" sert filtresine çevrildi.

## Deney 6 — Sözlük derinleştirme (A/B)

Değiştirme sözlüğüne yeni bir **eş dizim (kalıp 27) bölümü** (12 madde, hepsi "bağlama göre" notlu) ve eksik plaza adları eklendi. Kaynak niyeti Mersin Eşdizim Sözlüğü + TDK Karşılıklar; araştırma arka ucu geçici olarak çökük olduğundan maddeler yerleşik kullanımdan elle kürasyonla derlendi (web-kaynaklı sürüm sonraya ertelendi).

A/B testi (eş dizim + plaza stresine ve yanlış-pozitif tuzağına odaklı 7 metin; uygulayıcı Codex/Luna, puan Sonnet): **A = eski sözlük, B = aday sözlük.**

| Sürüm | Ort. /10 |
|-------|---------:|
| A (eski) | 8.07 |
| B (aday) | **9.07** |

B kazandı: yeni eş dizim maddeleri "başarıya imza atmak → başarı elde etmek" ve "süreç yaşamak → süreçten geçmek" gibi düzeltmeleri yakalattı; kritik olarak "değer üretmek" ekonomi bağlamında **korundu** ([bağlama bağlı] notu yanlış-pozitifi önledi). Resmî/sohbet/temiz metinlerde regresyon yok. **Genişletilmiş sözlük son sürüm oldu.**

## Deney 7 — Finans eklentisi (v1.3)

Eklenenler: tür kapısına dört alt türlü finans türü (yasal ibare, müşteri bilgilendirmesi, yatırım/pazarlama, iç yazışma), `references/finans-terimleri.md` (AYNEN / SADE / TR sınıflı 67 terim), `references/finans-mevzuat.md`, `scripts/okunabilirlik.py` ve `eval.md`'ye 12 finans vakası. Deney 5'te okunabilirlik skoru, modelin hece ve sözcük sayımına güvenilemediği için eklenmemişti. Bu sürümde sayımı model değil betik yapıyor; model yalnız betiğin çıktısını aktarıyor.

**Tur 1 — kör uygulama ve inceleme (GPT-6 Luna).** Uygulayıcı `eval.md`'yi görmeden 15 metni işledi (10 finans, 5 gerileme: dilekçe, sohbet, teknik, kurumsal). Ayrı bir Luna koşusu betiği ve kuralları inceledi. Bulgular:

| Bulgu | Kaynak | Düzeltme |
|---|---|---|
| Sayı denetimi para birimi, eksi işareti ve "milyon" değişikliğini kaçırıyordu ("1.250,00 USD" → "TL" geçiyordu) | inceleme | Değer artık işaret, birim, yüzde ve ölçekle birlikte karşılaştırılıyor |
| Cümle bölücü "Dr.", "A.Ş.", "md. 5", "3. çeyrek" noktalarında bölüyordu (3 cümle → 6) | inceleme | Kısaltma listesi ve sıra sayısı kuralı |
| Ateşman 100'ü aşınca "çok kolay" deniyordu | inceleme | "Ölçek dışı" etiketi |
| Mevzuat notunda yanlış düzenleme adı (03.10.2014 metni BDDK ücretler yönetmeliğiydi; güncel karşılığı TCMB Tebliği 2020/7) ve fazla geniş kapsam | inceleme; Resmî Gazete'den doğrulandı | Ad, sayı ve kapsam düzeltildi |
| Bir eval vakası kendi sayı denetimini geçmiyordu | inceleme | Beklenen çıktı düzeltildi |
| Yasak vaat silinince metinde olmayan çağrı uyduruldu ("Yeni fonumuzu inceleyin") | uygulama | Kural: geriye bilgi kalmazsa özü bırak, yeni cümle ekleme |
| EBITDA → FAVÖK çevrildi | uygulama | Kural: kısaltma başka kısaltmaya çevrilmez |
| Dayanaksız "istikrarlı performans" işaretlenmedi | uygulama | Yatırım türünde zorunlu **Uyum notu** alanı |
| Bilgisiz kapanış yerine yeni dolgu konuldu ("Sizi bilgilendiriyoruz") | uygulama | Kural ve eval vakası 12 |

Gerileme metinlerinde (dilekçe, sohbet, "deploy", kurumsal slogan) davranış değişmedi.

**Tur 2–4 — yineleme (GPT-6 Luna, kör).** Sorunlu vakalar yeniden işlendi. Zorunlu uyarının ikinci cümlesinin de değiştirildiği görüldü ("ile" → "ve", "sunulmaktadır" → "sunulur"); kural "uyarı bloğu harfi harfine kalır" diye netleştirildi. Son turda: uyarı bloğu aynen kaldı, performans iddiası uyum notunda TBB gerekçesiyle işaretlendi, kart mektubu üç kısa cümleye bölündü ve sayı denetimi "tamam" verdi (Ateşman 36,6 → 71,6).

Sınır: Luna aynı vakada turdan tura farklı karar verebildi (performans iddiası bir turda işaretlendi, ötekinde işaretlenmedi). Zorunlu çıktı alanı bu oynaklığı azaltmak için eklendi; tek koşu sonucu kesin ölçü değildir.

