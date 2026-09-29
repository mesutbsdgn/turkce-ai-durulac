<div align="center">

<img src="assets/durulac-logo.svg" width="120" alt="Durulaç logosu">

# Durulaç

**Türkçe metinden yapay zekâ ve bürokrasi kokusunu damıtan Claude skill'i.**

Bulanık, yapay, plaza Türkçesini alır; **anlamı ve yazarın sesini bozmadan** duru bir Türkçeye çevirir. İsterseniz yeniden yazmadan yalnızca "bu metin yapay mı?" diye kalıpları da işaretler.

![Lisans](https://img.shields.io/badge/lisans-MIT-blue) ![Claude](https://img.shields.io/badge/Claude-skill-8A63D2) ![Dil](https://img.shields.io/badge/dil-T%C3%BCrk%C3%A7e-e30a17) ![TDK](https://img.shields.io/badge/kurallar-TDK-informational)

</div>

---

## İçindekiler

- [Neden Durulaç?](#neden-durulaç)
- [Bir bakışta örnek](#bir-bakışta-örnek)
- [İki mod](#i̇ki-mod)
- [Öne çıkan özellikler](#öne-çıkan-özellikler)
- [Kurulum](#kurulum)
- [Kullanım](#kullanım)
- [Neyi değiştirmez](#neyi-değiştirmez)
- [Nasıl doğrulandı](#nasıl-doğrulandı)
- [Sınırlar](#sınırlar-dürüst-bölüm)
- [Katkı](#katkı)
- [Lisans ve teşekkür](#lisans-ve-teşekkür)

---

## Neden Durulaç?

Hazır "humanizer" araçları İngilizceye göre yazılmıştır: em dash aşırılığı, "X is the Y of Z" kalıbı, belirli İngilizce dolgu sözcükleri. Türkçede yapay dil **başka** kalıplardan gelir:

- İsimleştirme + yardımcı fiil: *"iyileştirilmesi amacıyla optimizasyonlar gerçekleştirilmiştir"*
- Bürokratik edatlar: *"hususunda", "nezdinde", "bu bağlamda"*
- Boş güçlendirici sıfatlar: *"yenilikçi, güçlü ve katma değerli çözümler"*
- Klişe açılışlar: *"Günümüzün hızlı tempolu dünyasında…"*
- Edilgen yığını ve failsiz vaatler: *"hedeflenmektedir", "sağlanmış olup"*

Durulaç bu kalıpları **Türkçeye özgü** olarak, TDK kurallarına dayanarak temizler; İngilizce bir listeyi çevirmez.

## Bir bakışta örnek

**Önce (yapay/kurumsal):**
> Günümüzün hızlı tempolu dünyasında, dijital dönüşüm süreçleri işletmeler açısından büyük önem arz etmektedir. Şirketimiz, müşteri memnuniyetini en üst düzeye çıkarmak amacıyla yenilikçi, güçlü ve katma değerli çözümler sunmaktadır. Bu bağlamda, geçtiğimiz dönemde birçok proje hayata geçirilmiş — ki bu projeler sektörde fark yaratmıştır — ve olumlu geri dönüşler alınmıştır.

**Sonra (Durulaç):**
> Müşteri memnuniyeti bizim için öncelikli, çünkü işimizin sürekliliği ona bağlı. Geçtiğimiz dönemde birçok projeyi tamamladık ve kullanıcılardan olumlu dönüşler aldık.

> **Ne değiştirdim:** jenerik açılış, "önem arz etmektedir", boş sıfat üçlüsü ve "bu bağlamda" çıkarıldı; edilgen çatı tutarlı bir "biz" sesine döndü; cümleler bağlaçla akıtıldı. **Uydurulan sayı/olgu yok** — "fark yaratma" iddiası veri olmadığı için silindi. Uzunluk: 62 → 21 kelime.

## İki mod

| Mod | Ne yapar |
|-----|----------|
| **Temizle** (varsayılan) | Metni en az müdahaleyle yeniden yazar, tam metni + kısa "Ne değiştirdim" listesi verir. |
| **Tespit et** | Yeniden yazmaz; bulduğu kalıbın adını, kısa alıntıyı ve düzeltme yönünü bildirir. "AI mı yazdı?" sorusunda **yazarlık tahmini yapmaz**, yalnızca gözlenebilir kalıpları gösterir. |

## Öne çıkan özellikler

- **46 Türkçe kalıp** — teşhis ipucu, kör yasak listesi değil; bağlama göre uygulanır.
- **Metin türü kapısı** — resmî yazı, akademik, hukuk ve teknik metinde *kasıtlı* kalıpları (edilgen çatı, "arz ederim", "işbu") kırmaz.
- **Register/ton koruması** — sohbeti rapor ağzına çevirmez; devrik cümle, eksilti, doğrudan hitap, retorik soru ve günlük dolgu korunur.
- **Uydurma yasağı** — metinde olmayan sayı, tarih, fail veya kaynağı asla eklemez; kanıtsız iddiayı işaretler ya da çıkarır.
- **Sil ve yeniden bağla** — dolgu/bağlaç silince telgraf tonuna düşmez; akışı bağlaçla geri kurar.
- **TDK kuralları** — kesme işareti, özne–yüklem virgülü, noktalı virgül, sayı/tarih yazımı.
- **Şeffaflık** — "Ne değiştirdim" listesi ve zorunlu uzunluk (X→Y kelime) satırı.

## Kurulum

Claude Code / Claude Desktop için skill klasörüne klonlayın:

```bash
git clone https://github.com/mesutbsdgn/turkce-ai-durulac.git ~/.claude/skills/turkce-ai-durulac
```

Skill dizininiz farklıysa (örn. `~/.agents/skills/`) oraya klonlayın. Claude oturumu skili otomatik tanır.

## Kullanım

Doğal dille çağırın ya da açıkça:

```
/turkce-ai-durulac
Şu metni sadeleştir: <metin>
```

**Örnekler:**

- *"Bu duyuruyu insanlaştır, kurumsal kokusunu al"* → Temizle modu.
- *"Bu paragraf yapay mı, kalıpları göster"* → Tespit modu (yeniden yazmaz).
- *"Şu sohbet mesajını sadeleştir"* → sohbet tonu korunur, rapor ağzına çevrilmez.
- *"Bu teknik dokümanı düzelt"* → kod, komut ve terimlere dokunmaz; yalnız düzyazıyı düzenler.

## Neyi değiştirmez

- Kod bloklarına, komutlara, tablolara ve teknik tanımlayıcılara **dokunmaz**.
- Kavram adlarını (a commit, pull request, host) korur — yalnız "merge etmek → birleştirmek" gibi plaza **fiillerini** Türkçeleştirir.
- Yazarın sözcük seçimini, mizahını, ritmini ve gündelik dilini korur.
- Güçlü, doğal cümlelere dokunmaz ("en az değişiklik" ilkesi).

## Nasıl doğrulandı

Durulaç kör kabul edilmedi; **kontrollü deneylerle** ölçüldü. İki uygulayıcı model (DeepSeek, GPT-6 Luna) aynı metinleri hem skilsiz hem skille temizledi; bağımsız bir model (Claude Sonnet) körlemesine puanladı. Özet bulgular:

- Skilin ölçülen asıl değeri **aşırı düzeltmeyi frenlemek**: güçlü modelin teknik terimi ve sohbet tonunu bozmasını engeller (teknik +10, sohbet +6 puan).
- Kurumsal/yapay metinde zayıf uygulayıcının kaçırdığı boş sıfatları ve klişeleri yakalatır.
- "Uydurma yasağı" hem model hem değerlendirici tarafından teyit edildi — üslup güçlense de olgu eklenmedi.

Ayrıntılı deney kayıtları: [`docs/deneyler.md`](docs/deneyler.md). *(Tek örneklik hücreler ve öznel puan içerdiğinden sonuçlar yön gösterir; büyüklük iddiası değildir.)*

## Sınırlar (dürüst bölüm)

- Etki **modele bağlıdır**: güçlü bir uygulayıcı (ör. DeepSeek) skilsiz de iyi olabilir; kurumsal metin temizliğinde güçlü uygulayıcı önerilir.
- Skil bir **korkuluktur**, sihirli değnek değil: ölçtüğü hatayı temizler, üslup zevkini garanti etmez.
- Son karar sizde: "Ne değiştirdim" listesini okuyup onaylayın.

## Katkı

Yeni kalıp, sözlük eşlemesi veya karşı-örnek (yanlış düzeltme) önerileri için **issue** veya **pull request** açın. Her kalıp için "sorun + kötü örnek + iyi örnek" üçlüsü ve TDK dayanağı beklenir. Olgu uyduran örnek kabul edilmez.

## Lisans ve teşekkür

- Kod ve içerik **MIT** lisanslıdır ([LICENSE](LICENSE)).
- Yapı [petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop) (MIT) esinlidir; İngilizce içerik kopyalanmadı, Türkçeye özgün yazıldı.
- Mekanik eşleme sözlüğü [Denomas/Turkce-yazim-denetimi](https://github.com/Denomas/Turkce-yazim-denetimi) (MIT) kurallarından seçilip uyarlandı.
- Dil bilgisi ve noktalama kuralları [TDK Yazım Kılavuzu](https://tdk.gov.tr/) temellidir.

Ayrıntılı kaynak notları: [LICENSE-NOTES.md](LICENSE-NOTES.md).
