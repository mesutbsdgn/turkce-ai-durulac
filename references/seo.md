# `+seo` kipi — Google aramasına uygun metin

`+seo` ek bir kiptir. Temizle kurallarını (gerekirse Finans kurallarını da) aynen uygular, üstüne metni Google aramasına uygun hâle getirir. **Durulaç ilkeleri her zaman SEO'nun önündedir:** anlamı bozan, bilgi uyduran ya da registerı saptıran SEO önerisi uygulanmaz.

Dayanak: 20 Kasım 2026 araştırması (quoteproof, 203 bulgunun 165'i otomatik doğrulandı, kritik olanlar kaynağında açıldı). Ayrıntılı rapor Durulaç deposunun dışında tutulur; aşağıdaki alıntılar Google'ın resmî sayfalarından ve Google temsilcilerinin kayda geçmiş sözlerinden alınmıştır.

## Kullanıcıya doğru söylenecekler

- **Sıralama vaadi verme.** Google üretim yöntemine değil değere bakar: "Using automation—including AI—to generate content with the primary purpose of manipulating ranking in search results is a violation of our spam policies" ([Google](https://developers.google.com/search/blog/2023/02/google-search-and-ai-content)). AI kokusunu gidermek tek başına sıralama getirmez; Ahrefs'in 600 bin sayfalık ölçümünde AI oranıyla sıra arasındaki ilişki için "The correlation was 0.011, effectively zero." deniyor ([Ahrefs](https://ahrefs.com/blog/ai-generated-content-does-not-hurt-your-google-rankings/)).
- **Yoğunluk hedefi yoktur.** "no, Google does not have a notion of optimal keyword density" ve "Keyword density does not matter, but being explicit does matter" (John Mueller, [Search Engine Roundtable](https://www.seroundtable.com/google-search-optimal-keyword-density-34826.html)). Yoast %0,5–3, Rank Math %1–1,5 der; bunlar eklentinin kendi eşikleridir, Google kuralı değildir.
- **Karakter sınırı resmî değildir.** "while there's no limit on how long a <title> element can be, the title link is truncated in Google Search results as needed, typically to fit the device width" ([Google](https://developers.google.com/search/docs/appearance/title-link)). Meta açıklama için de aynısı geçerlidir ([Google](https://developers.google.com/search/docs/appearance/snippet)). 60 / 155 karakter sektör sezgisidir; böyle etiketle.
- **AI Overviews / AI Modu için özel kural yoktur:** "There are no additional requirements to appear in AI Overviews or AI Mode, nor other special optimizations necessary." ([Google](https://developers.google.com/search/docs/appearance/ai-features)). AI Modu ve AI Bakışı Türkiye'de 18 Şubat 2026'da açıldı ([Google Türkiye](https://blog.google/intl/tr-tr/urun-duyurulari/turkiyede-ai-modu-ve-ai-bakisi-donemi-basliyor/)).
- **Okunabilirlik puanı doğrudan sıralama etkeni değildir** (Mueller: "we don't have kind of these basic algorithms that just count words and try to figure out what the reading level is", [SEJ](https://www.searchenginejournal.com/ranking-factors/reading-level/)); okur için yararlıdır, o yüzden korunur.

## Ne zaman uygulanır

Açık: pazarlama/kurumsal blog, kişisel blog, haber, teknik doküman, ürün/hizmet sayfası, finans müşteri bilgilendirmesi (finans kuralları önce gelir; yasal ibare ve zorunlu uyarı SEO için kısaltılmaz).

Türü dosya adına ya da uyarı cümlesinin varlığına göre değil, metnin işlevine göre seç: "Geçmiş getiriler…", "yatırım tavsiyesi değildir" gibi zorunlu uyarı taşıyan bir bilgilendirme yazısı **finans müşteri bilgilendirmesidir**, SEO açıktır. Uyarı cümleleri tek harf değişmeden kalır ve SEO paketine kısaltılarak taşınmaz.

Kapalı: resmî yazı/dilekçe, hukuk, akademik/tez, edebî metin, altyazı, sohbet/mesaj, sosyal medya gönderisi. Bu türlerde `+seo` istenirse nedenini bir cümleyle söyle, yalnız ilgili Durulaç kipini uygula.

Girdi: metin + isteğe bağlı **ana sorgu** (kullanıcının hedeflediği arama ifadesi) + ikincil terimler. Ana sorgu verilmezse metnin konusundan bir aday çıkar ve "ana sorguyu X varsaydım" de; kullanıcının ürün/marka adını sorgu yerine koyma.

## Yapılacaklar (yalnız bunlar)

1. **Konuyu açıkça adlandır.** Ana sorgu H1'de (ya da başlıkta) ve ilk paragrafta doğal biçimde geçsin. Türkçede çekimli biçim yeterlidir ("ev kredisi" → "ev kredisinde"); zorla tam eşleşme kurma. Google çekimli biçimleri büyük ölçüde eşler; her çekim için ayrı ifade serpiştirme.
2. **Jenerik açılışı (kalıp 21) konuya giren cümleyle değiştir.** Metnin ilk cümlesi okurun aradığı şeyi söylesin.
3. **Soruya yanıt veren metinde yanıtı başa al.** Girdideki bilgiyle 40–60 sözcüklük, tek başına okunabilen bir yanıt paragrafı kur. Bu paragrafa yeni olgu girmez; girdi yanıtı vermiyorsa kurma, bilgi kazancı sorusu olarak sor.
4. **Yapı:** 300 sözcüğü aşan ve ara başlığı olmayan metne, metnin kendi bölümlerine göre H2 koy. Metin zaten soruları yanıtlıyorsa soru biçimli ara başlık ("… nasıl hesaplanır?") kullanabilirsin. Düzyazıda zaten sıralanmış adımları numaralı listeye, karşılaştırmayı tabloya çevirebilirsin; olmayan madde, satır ya da sütun ekleme. Başlık hiyerarşisi (tek H1, seviye atlamama) Google kuralı değildir; erişilebilirlik için tercih edilir.
5. **Uzun paragrafı böl** (150 sözcük üstü), ama Durulaç'ın "kopuk cümle bırakma" kuralı geçerli.
6. **Çapa metni** tek başına anlamlı olsun ("buraya tıklayın" → bağlantının hedefini anlatan ifade). Hedef metinde ya da URL'de belli değilse sayfa adı uydurma; nötr bir ifade kullan ("ayrıntılı bilgi için ürün sayfasına bakın") ve hedefi kullanıcıya sor.
7. **Teknik dokümanda** okurun arayacağı yerleşik terimler (branch, main, pull request, pipeline, staging, production, commit, issue) korunur; Türkçe karşılık gerekiyorsa ilk geçişte parantezde verilir. Türkçeleşen yalnız "İngilizce fiil + etmek" (merge etmek → birleştirmek) ve çıplak süreç adıdır (SKILL.md tür kapısı).
8. **Terim tutarlılığı:** aynı kavrama metin boyunca tek ad ver (kalıp 59). Eşanlamlı çeşitlemesini SEO için artırma.
9. **Ana sorgu olguyu değiştiremez.** Sorgu ifadesi metnin söylediğinden farklı bir kesinlik, kip ya da zaman taşıyorsa (girdi: "önerge kabul edildi, 1 Aralık'ta başlayacak"; sorgu: "trafiğe kapatılan caddeler") sorguyu metne ya da title'a olduğu gibi sokma. Olguya uyan biçimi kullan ("kapatılacak caddeler") ve bunu "Ne değiştirdim"de not et.
10. **Haber:** spot (ilk cümle: kim, ne, ne zaman) haber kurallarına göre korunur; ana sorgu için spotu yeniden kurma, sorguyu başlıkta ve meta açıklamada kullan. Kaynak atfı, karşı görüş ve "yorum yapmadı" bilgisi gövdede kalır.
11. **Yanıt-önce paragrafı kurarken bilgiyi taşı, kopyalama.** Başa aldığın bilgiyi aşağıda tekrar etme. Taşıdığın cümleye bağlı göndermeleri ("bu işleme besleme denir", "bu noktada") yeniden bağla; boşta kalan "bu/şu" bırakma.
12. **Aranan terimi silme:** Sadeleştirme okurun arayacağı bir terimi değiştiriyorsa ("akdi faiz" → "sözleşme faizi", "dönem borcu" → "bu ayki borcunuz") ilk geçişte özgün terimi parantez içinde bir kez koru: "sözleşme faizi (akdi faiz)". Ana sorgu ve ikincil terimler bu kuralın kapsamındadır; sade karşılık onların yerine geçmez.

## SEO paketi (metnin sonunda, ayrı blok)

Hepsi YALNIZ metindeki bilgiden üretilir; metinde olmayan iddia, sayı, kampanya, "en iyi/ücretsiz/2026 güncel" gibi ifade eklenmez.

**Koşul ve kip kuralı:** title ve meta açıklamada gövdenin koşulları, sınırlayıcıları ve zaman kipi aynen kalır. Kısaltırken "üst üste üç kez" → "üç kez", "değişebilir" → "değişir", "başlayacak" → "başladı" yapılmaz; sığmıyorsa koşulu taşıyan bilgiyi pakete hiç alma. Kapsam da korunur: yalnız bir öğeye ait ölçü ("French press için 92-96 derece") pakette bütün öğelere yayılmaz ("üç yöntemin su sıcaklığı"). Pakette gövdede olmayan sayı bulunamaz (denetçi S19).

**Vaat kuralı:** title, meta açıklama ve SSS yalnız gövdenin GERÇEKTEN yanıtladığı soruyu sorar. Girdinin girişi "nasıl hesaplandığını anlatacağız" diyor ama gövde anlatmıyorsa bu vaadi pakete taşıma; gövdedeki vaadi de çıkar ya da eksik bilgiyi bilgi kazancı sorusu olarak sor.

- **Title:** konuyu ilk sözcüklerde söyleyen, ana sorguyu bir kez içeren başlık. Yaklaşık 50–60 karakter (sektör sezgisi). Aynı sözcüğü iki kez kullanma: "title text like foobar, foo bar, foobars, foo bars doesn't help the user" ([Google](https://developers.google.com/search/docs/appearance/title-link)). Marka adını kullanıcı verdiyse sona ekle.
- **Meta açıklama:** sayfanın ne verdiğini söyleyen 1–2 cümle, yaklaşık 120–155 karakter (sektör sezgisi). Google bunu gösterme garantisi vermez.
- **Slug:** küçük harf, sözcükler arası tire ("we recommend using hyphens", [Google](https://developers.google.com/search/docs/crawling-indexing/url-structure)), Türkçe karakter ASCII'ye çevrilir (ş→s, ğ→g, ı→i, ç→c, ö→o, ü→u). Türkçe karakterli slug teknik olarak geçerlidir ama paylaşımda yüzde kodlanır; asıl ölçüt site boyu tutarlılıktır. Yayınlanmış sayfanın slug'ını değiştirmeyi önerme (301 gerekir).
- **Alt metin** (metinde görsel varsa): görselin ne gösterdiğini söyleyen kısa ifade; "görsel/resim/fotoğraf" ile başlatma, anahtar sözcük yığma. Dekoratif görselde boş bırakılabilir.
- **SSS taslağı** (yalnız metin zaten soru-yanıt içeriyorsa): metindeki yanıtlardan en çok 4 soru; yalnız soru listesi, yanıtları yeniden yazma. Sayfa zaten soru biçimli ara başlıklarla yanıt veriyorsa ayrıca yanıt-önce özet ekleme; her yanıt sayfada bir kez bulunur (denetçi S20). Yapılandırılmış veri (schema) kodu yazma; kullanıcı isterse ayrıca sor.

## Bilgi kazancı soruları (en çok 3)

Google'ın değer verdiği ama metinde olmayan öğeleri **uydurma, sor**: özgün sayı/ölçüm, tarih ("ne zaman güncellendi?"), yazar ve uzmanlığı, birinci elden deneyim ("bunu kendiniz denediniz mi, sonuç neydi?"), kaynak. Gerekçe: Google'ın kendi değerlendirme soruları "original information, reporting, research, or analysis" arar ([Google](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)); uydurma deneyim ve sahte yazar ise aldatmadır. YMYL konularda (sağlık, finans, hukuk) yazar/inceleme bilgisini özellikle sor.

## Yasaklar

- Anahtar sözcük doldurma: "Repeating the same words or phrases so often that it sounds unnatural" ([Google spam politikaları](https://developers.google.com/search/docs/essentials/spam-policies)). Aynı cümlede ana sorgu iki kez, title'da aynı ifade iki kez, şehir/varyant listesi yok.
- Yoğunluk hedefine göre sözcük ekleme ya da çıkarma.
- Eşanlamlı çevirme (spinning), aynı metnin varyantlarını üretme. Google'ın ölçekli içerik kuralı üretim biçimine bakmaz: "no matter how it's created" ([Google](https://developers.google.com/search/docs/essentials/spam-policies)).
- Gövdeye karaktersiz yazım serpiştirme ("kislik bot" diye arayanlar için). Google yazım farkını kendisi düzeltir; okur için özensiz, anlam için risklidir (ılık/ilik).
- Uydurma deneyim, vaka, müşteri, ölçüm, tarih ya da yazar.
- "Sıralamada yükselirsiniz", "Google şunu ister" gibi kaynaksız vaat ya da iddia.
- Kelime sayısını artırmak için dolgu: uzunluk hedefi Google'ın olumsuz saydığı taktiklerdendir ([Google](https://developers.google.com/search/docs/fundamentals/creating-helpful-content)).

## İş akışı (Temizle'ye eklenen adımlar)

1. Türü belirle; kapalı türse dur ve söyle.
2. Ana sorguyu al ya da varsay.
3. `python3 scripts/seo_denetim.py once.md --anahtar "SORGU"` ile başlangıç durumunu gör.
4. Temizle adımlarını uygula; sonra yukarıdaki "Yapılacaklar"ı yalnız gereken yerde uygula.
5. Denetle: `python3 scripts/seo_denetim.py sonra.md --anahtar "SORGU" --baslik "TITLE" --aciklama "META" --slug SLUG --onceki once.md` (çıkış 1 = doldurma; düzelt), ardından `tarama.py --onceki` ve `bilgi_koruma.py` (SEO yapısı bilgi düşürmemeli). Eklediğin her cümleyi girdide karşılığıyla eşle (sessiz ekleme denetimi).
6. Teslim: tam metin → SEO paketi → bilgi kazancı soruları → Ne değiştirdim (SEO müdahalelerini ayrı satırlarla) → denetçi özeti (hata/uyarı sayısı, kalan uyarıların gerekçesi).
