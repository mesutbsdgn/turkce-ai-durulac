# İstem iyileştirme modu (ayrıntı)

Bu dosya SKILL.md'den taşındı; metin aynen korunmuştur.

Kaynak fikir: prompts.chat'in `improve_prompt` yaklaşımı (açık kaynak, yerelde okundu). Biz **yalnız yöntemi aldık**; hiçbir metin dışarıya gönderilmez, uzak servis çağrılmaz.

**Amaç:** İstemin ne istediğini değiştirmeden daha net, eksiksiz ve yeniden kullanılabilir yap. Dil, kullanıcının yazdığı dil kalır (Türkçe istem Türkçe kalır); çıktı dili istenmişse istemde açıkça yazılır.

**Önce kısa teşhis (yalnız eksik olanları söyle):** rol/bağlam · görev · kısıtlar · çıktı biçimi · başarı ölçütü · örnek gereksinimi · belirsiz noktalar. Basit ve kısa ama açık bir istem **geçerlidir**; şüphede dokunma, "zaten yeterli" de.

**Teknikler:**
1. **Rol** eksikse ve metin sohbet/uzmanlık istiyorsa "… olarak davran" ekle. Görsel/video/ses istemlerinde rol YAZMA; onun yerine sahne, ışık, kamera, tarz, süre, ses türü, ruh hâli gibi teknik ayrıntıyı iste/ekle.
2. **Bağlam**: istemde olmayan olguyu uydurma; eksik bağlamı `${değişken}` ya da `${değişken:varsayılan}` olarak işaretle ve kullanıcıya sor.
3. **Görev** tek ve açık cümleyle başlasın; adımlar numaralı.
4. **Kısıt** ve yasaklar madde madde; "yapma" yerine mümkünse "yap" biçiminde.
5. **Çıktı biçimi**: tablo, JSON, madde sayısı, uzunluk, ton açıkça yazılsın.
6. **Örnek**: örnek eklenebilecek yeri belirt; sahte örnek UYDURMA, `[örnek buraya]` yer tutucusu bırak.
7. **Doğrulama**: işe uygunsa "emin olmadığın yerde söyle, uydurma" ve "bitirmeden kontrol et" cümlesi ekle.

**Kurallar:** Amacı, kapsamı ve kısıtları değiştirme. İstemin içeriğine kendi görüşünü katma. İstemdeki kod, komut, yol, değişken adı ve alıntıya dokunma. Gizli bilgi (anahtar, parola) görürsen yerine yer tutucu koy ve söyle.

**Çıktı:** (1) İyileştirilmiş istem, kopyalanabilir tek blokta. (2) **Ne ekledim** listesi, en çok beş madde. (3) Varsa **Sana soru** satırı: doldurman gereken `${…}` alanları. İstemin kendisini yerine getirmeye çalışma; yalnız istemi hazırla.
