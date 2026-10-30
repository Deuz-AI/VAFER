# vafer-research v0.0.5: neyi değiştirmeliyiz

Tarih: 2026-10-30. Hız ve kalite tasarımcılarının önerileri ve eleştirmenin sıralaması; kaynaklar 9. bölümde.

Terimler: ana ajan = lead; boşluk bulucu = gap-finder; makbuz = receipt (sayfadan birebir alıntı); sayfa kopyası = snapshot; bayrak = `check` uyarısı. Manşet: cevap cümlesi, "bir bakışta" satırı ya da anlaşmazlık hükmü. B hücresi: anlaşmazlık tablosunda reddedilen taraf. İsabet: gerçek bayrak ÷ tüm bayraklar. Çıplak model: skill'siz model. Efor: S bir günden az, M 1–2 gün, L daha uzun.

## 1. Kısa sonuç

v0.0.4 çıplak modelden açıkça iyi ama yavaş: tek kör testte 8,6'ya 5,8 aldı ve 22:53 sürdü, çıplak modelin 4,6 katı (README; run-evidence F12). Sürenin yalnız %45'i araştırma; ana ajan 10:25 bilerek bekledi, ikinci dalga seri çalıştı, rapor elle iki kez yazıldı (run-evidence F1, F6). Kör hakemin bulduğu üç hatanın üçü de olumsuz hükümdü ve hiçbirinde hükmü verecek sayfa açılmamıştı: 4,80 m'nin sayfası açılmadan reddedildi, "27 köy"de Wikipedia'nın gösterdiği kaynak izlenmedi, 1533 sayılı kanun 6 aramada bulunamadı (skill-audit F15; run-evidence F9). Check ilk ikisini işaretledi; ama 13 bayraktan yalnız birinin gerçek olduğu gürültülü listede ana ajan ikisini de yanlış alarm sayıp kapattı (run-evidence F10). v0.0.5 özellik eklemek yerine adım silmeli: tek araştırma dalgası, her cevaba anında takip ajanı, raporu script birleştirsin, editör kalksın. Doğrudan kanıtı olan tek kalite kuralı "hüküm vermeden önce sayfayı aç"; sessiz bir check, Yalova izinin silinmesi, host düzeltmeleri ve toplu araç çağrısıyla sekiz şart tamamlanıyor (critique). Beklenti, Yalova boyutunda 10–13 dakika ve 7–8 alt ajan: çıplak modelin 2–2,5 katı; 1,5 kat çıtası tutmuyor (critique). Önce ücretsiz çevrimdışı kontroller, sonra 2–3 soruluk hafif bir yan yana test; "5×" iddiası ve brainstorm sonra.

## 2. Bugün neredeyiz

Tek ölçüm: "Yalova'nın tarihi", Claude Code, 2026-10-29. Kör hakem 26 sayfa açtı, rapor başına 10–12 iddia kontrol etti. Puanlar README'den, süre ve sayımlar run-evidence F3'ten (README süreleri yuvarlar).

| | v0.0.4 | İlk taslak (0.2.0-alpha) | Çıplak model |
|---|---|---|---|
| Genel | **8,6** | 8,1 | 5,8 |
| Doğruluk | 8,5 | 8 | 5 |
| Kaynak kalitesi | 9 | 9 | 3,5 |
| Çelişki yönetimi | 8,5 | 9 | 5,5 |
| Okunurluk | 8,5 | 6,5 | 8 |
| Süre | 22:53 | 13:39 | 4:59 |
| Alt ajan | 11 | 5 | 0 |
| Araç çağrısı | 362 (307'si alt ajanlarda) | 206 | 25 |

**İyi yaptıkları.** Birincil kaynağa gidiyor (kaynak kalitesi 9'a 3,5). Rumi 1316 = 1900 dönüşümünü yalnız v0.0.4 doğru yaptı. Boşluk bulucu Kibotos 1096, 1915 ve 1923'ü 50 saniyede buldu (run-evidence F8, F11; skill-audit F10).

**Kötü yaptıkları.**

| Sorun | Ölçüm | Kaynak |
|---|---|---|
| Süre araştırmaya gitmiyor | Araştırma %45, sonrası 9:32; ana ajan 10:25 boşta | run-evidence F1 |
| Seri ikinci dalga | 6:20, 3 alt ajan, 128 çağrı; öğeler 3. dakikada belliydi | run-evidence F2; design-speed SPD-1 |
| Elle yapılan işler | Rapor iki kez yazıldı; scriptler doğaçlandı; ana ajan bağlamı ~210 bin token | skill-audit F11 |
| Editör | Cümle başına 12,3 → 11,0 kelime, ama 6 atıf kopardı; 2:43 seri süre | run-evidence F7 |
| Check | 13 bayraktan 1'i gerçek (isabet ~%8); "252/258" yazıyor, oysa 261 rakamın 85'i yalnız sayfanın başka yerinde eşleşiyor | run-evidence F10; design-quality Q2 |
| Olumsuz hükümler | 17'nin 3'ü tersine döndü | design-quality R2 |
| Araştırmacı verimi | 20–35 tur, %76–79'u tek çağrı; 98 kabuk okuması | design-speed M2; critique |
| Fetch | 63 indirmenin 12'si başarısız; dizinden 14 satır kayboldu | skill-audit F7, F8 |

**Sınırlar.** Tek soru, tek koşu, tek hakem; 0,5 puanlık farklar gürültü (run-evidence F8). Aynı tasarım bir koşuda 13:39, diğerinde 24:00 sürdü (F13). Ana ajan alt ajan olarak çalıştı, bu 1:31 ekledi (F6). Skill'deki Yalova örneği testi kirletti (skill-audit F17). a927973 düzeltmeleri ölçülmedi.

**Rakipler.** hyperresearch'ü kimse çalıştırmadı; "light" tahmini 30–40 dakika (prior-research F9). Claude Code'un `/deep-research`'ü bir koşuda ~13 dakika, 98 ajan ve 533 çağrı kullandı (external-sweep F1); Claude Code'da asıl çıta o.

## 3. İyi bir deep research'te olması gerekenler

İki tasarımcının listeleri birleştirildi.

| Yetenek | v0.0.4 | Not |
|---|---|---|
| Kapsam: okur, amaç, toplam uzunluk | kısmen | Okur varsayıldı; uzunluk hedefi yok (skill-audit F13) |
| Her satır kendini çözecek kaydı adlandırır | var | Ama 12 satırın hepsi `[prior]` (skill-audit F10) |
| Taze boşluk bulucu | kısmen | Seri dalgaya döndü |
| Soru şekilleri: karşılaştırma, hesap, liste, kanıt, hukuk | yok | Yalnız çelişkili bir liste varyantı (stress-test F4) |
| Arama ustalığı: çok dil, önce kayıt, dipnot takibi | kısmen | 1533 sayılı kanun 6 sorguda kaçtı |
| Verimli okuma: toplu çağrı, pasaja tek adımda | yok | Turların %76'sı tek çağrı; 98 kabuk okuması |
| Tablo, PDF, OCR (taranmış metin) okuma | kısmen | Tablo ve OCR reddediliyor (skill-audit F7) |
| Bütçe ve kanıta dayalı durma | kısmen | Sayaç yok; "There is no time limit" |
| Alana göre kaynak sıralaması | kısmen | Tarihe göre kurulmuş tek merdiven (stress-test F10) |
| Kaybeden tarafı açmadan hüküm vermemek | kısmen | 3/17 hüküm tersine döndü |
| Yargılar için karşı kanıt, kesinlik dili | kısmen | Karşı kanıt yalnız Ultra'da |
| Rakam ve makbuz kontrolü | kısmen | Rakamların %33'ü yalnız sayfanın başka yerinde eşleşiyor; makbuz kopyayla karşılaştırılmıyor (skill-audit F4) |
| Düzyazının iddia düzeyinde desteği | yok | Kontrol yok; hakem desteksiz düzyazı bulmadı |
| Önce cevap, kısa cümle, temiz tablo | var | Okunurluk 8,5 |
| Her dilde çıktı | kısmen | Başlıklar sabit Türkçe (skill-audit F17) |
| Olay güdümlü yönetim, mekanik işler kodda | yok | Ana ajan 10:25 boştaydı; mekanik işler elle |
| Rol başına model ve effort | yok | İki host da izin veriyor (hosts F1, F3) |
| Önceki koşuyu yeniden kullanma | kısmen | Hiç çalışmadı (stress-test F6) |
| Host dayanıklılığı | kısmen | Codex denenmedi (hosts F7) |
| Dürüst durum satırı | kısmen | Kontrol edilmeyen rakam sayılmıyor (skill-audit F5) |

## 4. v0.0.5 için değişiklikler

Omurga eleştirmenin sıralaması (critique.md); numaralar onu izler. Olabilir maddeleri (17–23) ve eleştirmenin eksik bulduğu E1–E2 aşağıda tek satırda; Codex denemesi ve sabit geçme ölçütleri 8. bölümde.

| # | Değişiklik | Efor | Beklenen kazanç |
|---|---|---|---|
| | **Şart** | | |
| 1 | Hüküm vermeden önce sayfayı aç | S | Hatalı olumsuz hüküm ≤ 1/17 |
| 2 | Önce boşluk bulucu, tek başlatma | S | −4–5 dk, −3 alt ajan |
| 3 | Her cevaba anında takip ajanı | S | Bilinçli bekleme biter |
| 4 | Raporu script birleştirir, editör yok | M | Son kısım ≤ 3 dk |
| 5 | Sessiz ve dürüst check | M | Açık bayrak ≤ ~5 |
| 6 | Yalova izi, sabit Türkçe iskelet gider | S | Temiz kıyas |
| 7 | Host düzeltmeleri | S | PowerShell, Codex çalışır |
| 8 | Toplu araç çağrısı, tek çağrıda pasaj | M | Araştırmacı −%15–30 |
| | **Olmalı** | | |
| 9 | Paralel fetch, PDF okuma sırası | M | İndirme ~25 sn |
| 10 | Kısa brifler, kurallar tek dosyada | S | Brif ~0:25 |
| 11 | Arama sayacı, kanıta dayalı durma | S | Daha az arama |
| 12 | Makbuz sayfayla doğrulanır | S | Uydurma makbuz geçmez |
| 13 | Alan merdiveni, kapsam kuralı | S | Tarih dışı doğru hüküm |
| 14 | Yeniden kullanım: tazele, ödünç al | S | Takipte 3–8 arama az |
| 15 | Paket ve tek sürüm etiketi | M | Tek kurulum |
| 16 | İzin kurallarını belgele | S | Daha az onay |

### Şart

**1. Hüküm vermeden önce sayfayı aç (S).**
- *Sorun:* 4,80 m'nin sayfası açılmadı (C15); "27 köy" kaynaksız sayıldı, oysa Wikipedia Gingeras'ı gösteriyordu (C12); 1533 sayılı kanun 6 sorguda bulunamadı. Atıfsız 4 B hücresinden 2'si bu hatalar (critique #1).
- *Değişiklik:* `briefs.md`: reddetmeden önce değeri veren sayfayı aç, dipnotu bir kez izle, `[prior]` değerlerini tırnakla ara. `SKILL.md`: açılmamış değer "kontrol edilmedi", hükmü "çözülmedi". Her B hücresi `[n]` ya da "(açılmadı)" taşır; yoksa `check` yüksek bayrak verir.
- *Etki:* Tersine dönen olumsuz hüküm 3/17'den ≤ 1'e; B bayrağının isabeti %50, bugünkü check'inki %8. Maliyet 5–10 sayfa, 0–1 dk.
- *Doğrulama:* C12 ve C15'i yeni brifle bir takip ajanına ver; Gingeras'a ve 4,80 m sayfasına ulaşmalı.

**2. Önce boşluk bulucu, tek başlatma (S).**
- *Sorun:* Öğeler 3. dakikada belliydi, ama boşluk dalgası bölümleri bekledi: 6:20, 3 alt ajan, 128 çağrı (run-evidence F2).
- *Değişiklik:* `SKILL.md` 1. adım: boşluk bulucuyu önce başlat, o çalışırken `plan.md`'yi yaz, öğeleri satırlara ya da tek ek bölüme kat, sonra başlat. 4. adım silinir. Boşluk bulucu 8–12 öğe ve listede öğeleri sayan kaydı verir.
- *Etki:* −4–5 dk, −3 alt ajan, ~−100 çağrı; başlatma 0–1 dk gecikir.
- *Doğrulama:* Araştırma ≤ 6 dk; ikinci dalga yok; ≤ 8 alt ajan.

**3. Her cevaba anında takip ajanı (S).**
- *Sorun:* Ana ajan Termal takvim çelişkisini gördü, uzlaştırıcıyı (adjudicator) 1:30 sonra başlattı; `SKILL.md:44` ve `hosts.md:23` dalganın tamamını beklemeyi söylüyor (critique #3).
- *Değişiklik:* 3. ve 4. adım "Cevaplar geldikçe takip et" olur: çözülemeyen manşet çelişkisi, açık manşet satırı ya da açılmadan reddedilecek değer için hemen takip ajanı (Standard en fazla 3, Deep 6). Tek takip brifi, uzlaştırıcı ve boşluk briflerinin yerini alır. Codex için `hosts.md`: `wait_agent` tüm açık ajanlarla, ilk biteni işle, `close_agent`.
- *Etki:* Bilinçli bekleme biter; geç takip en çok ~2 dk ekler.
- *Doğrulama:* Takip, tetikleyen cevaptan ≤ 30 sn sonra başlar; boşta süre < 3 dk.

**4. Raporu script birleştirir, editör yok (M, kapılı).**
- *Sorun:* Araştırma sonrası seri iş ~6:30–7:30; editör 6 atıf kopardı. Risk yapıda: düz birleşim 3.708 kelime ve 28 başlık, teslim edilen rapor 2.866 ve 13 (critique #4).
- *Değişiklik:* Yeni `vafer_check.py assemble <run>`: bölümleri ve ana ajanın yazdığı `_top.md` (cevap, bir bakışta) ile `_end.md`'yi (anlaşmazlıklar, bilinmeyenler) birleştirir, atıfları numaralar, Kaynaklar'ı okurun dilinde yazar. Editör, `report.before-edit.md` ve 6. adım silinir; bölüm bütçesi toplamdan türer.
- *Kapı:* Kodlamadan önce bir kör hakem düz birleşimi, editör öncesi ve sonrası raporu okunurlukta sıralar. Birleşim açıkça kötüyse ana ajan editörsüz yeniden yazar ve `vafer_check.py diff` çalışır; çıplak `diff` PowerShell'de bozuk düzenlemeye "başarılı" diyor (stress-test F9).
- *Etki:* Son kısım ≤ 3 dk (kapı yolunda ~2:45 kazanç); −1 alt ajan, 0 kopan atıf.
- *Doğrulama:* Okunurluk ≥ 8; gövde hedefin ±%15'i içinde.

**5. Sessiz ve dürüst check (M).**
- *Sorun:* 13 bayraktan 1'i gerçekti; gürültü önemli iki bayrağı kapattırdı. Düz birleşim 55 bayrak veriyor (critique #5).
- *Değişiklik:* `vafer_check.py`: yüzyıl (XVI. = 16. yüzyıl), saat ve tam tarih tek parça okunur; B sütunu ve bilinmeyenler eşleştirilmez; atıfsız cümle paragrafının atıfını ödünç alır; yalnız orta ve yüksek bayrak karar ister. `evidence.md` dürüst sayar; durum satırı oranı bırakır. `check --section <id>` ile araştırmacı taslağını kendisi düzeltir.
- *Etki:* Teslimde ≤ ~5 açık orta veya yüksek bayrak (bugün 13); bayrak işi 1:42'den ≤ 1 dk'ya.
- *Doğrulama:* Kayıtlı koşuda kalan her bayrak gerçek ya da adı konmuş bir sınıf; canlıda isabet ≥ %50.

**6. Yalova izi ve sabit Türkçe iskelet gider (S).**
- *Sorun:* Raporun ilk cümlesi `style.md:26`'nın tekrarı; `SKILL.md:80` "yalova" arıyor; başlıklar Türkçe sabit; check "## Fuentes" altında rakam görmüyor (skill-audit F17).
- *Değişiklik:* `SKILL.md` bölümleri işlevle ve okurun dilinde adlandırır; durum satırı da öyle. `style.md`'ye nötr örnek. Check Kaynaklar'ı `assemble` işaretiyle bulur, sızıntıyı yalnız iç belirteçlerde arar.
- *Etki:* Temiz kıyas; her dilde rapor ve check.
- *Doğrulama:* Skill'de "Yalova" kalmaz; İngilizce ve İspanyolca birim testi.

**7. Host düzeltmeleri (S).**
- *Sorun:* Yeniden kullanım araması PowerShell'de "os error 123" veriyor; script örnekleri göreli yol, `python3` yok; README'deki `codex exec --search` reddediliyor (stress-test F6; hosts F7).
- *Değişiklik:* Ana ajan script'in mutlak yolunu ve yorumlayıcıyı (`python`, `python3`, `py -3`) bir kez bulup brife yazar. Arama: `rg -i -l "<terim>" .vafer/research --glob plan.md`. Codex: `-c web_search="live"` ve `-c sandbox_workspace_write.network_access=true`. 1. adımda tek satır ön kontrol: arama modu, alt ajan, ağlı kabuk.
- *Etki:* Windows ve Codex'te yeniden kullanım; sessiz, fetch'siz koşu yok.
- *Doğrulama:* Arama PowerShell ve Git Bash'te; Codex'te tarihli bir Quick soru.

**8. Toplu araç çağrısı, tek çağrıda pasaj (M).**
- *Sorun:* Araştırmacı başına 20–35 tur, %79'u tek çağrı; 98 kabuk okuması. En yavaş araştırmacı araç bekliyordu (82 sn fetch); kazanç çoğunlukla ötekilerde (critique #8).
- *Değişiklik:* Kural: ilk mesajda 3–5 arama; sonra her mesaj aramaları, fetch'i ve pasaj sorgusunu toplar; önce geniş, sonra dar. Script: `fetch <run> --find "a|b|c" <url>...` sayfa başına en fazla 3 numaralı pasaj basar; `find` eski kopyaları sorgular. WebFetch yalnız fetch başarısızsa.
- *Etki:* Tur ~12–16, kabuk okuması ~35, WebFetch 41'den ~10; araştırmacı süresi −%15–30.
- *Doğrulama:* `speed_turns.py`: tek çağrılı tur ≤ %40; doğruluk düşmez.

### Olmalı

**9. Paralel, yarışsız fetch (M).** *Sorun:* Sıralı 82 sn'lik bir fetch dalganın sonunu belirledi; 102 URL'nin 21'i iki kez indi; eşzamanlı yazma 14 dizin satırı kaybetti; `pdftotext -layout` iki sütunlu PDF'yi karıştırıyor (critique #9). *Değişiklik:* Host başına 2 işçiyle paralel indirme; HTTP 429 (çok fazla istek) ve 503'te bekleyip tekrar; durum kopyanın başlığında; tablo satırı içerik; düz yazılı PDF okuma sırasıyla. *Doğrulama:* En uzun fetch ≤ 30 sn.

**10. Kısa brifler, kurallar tek dosyada (S).** *Sorun:* Brifler 548–596 kelime, yazımı 1:14; #2'den sonra kritik yolda. *Değişiklik:* `references/researcher.md` `style.md`'nin yerine sabit kuralları tutar; brifler ~120 kelimeye iner. *Etki:* Brif ~0:25. *Doğrulama:* İlk ve son başlatma arası ≤ 30 sn.

**11. Arama sayacı, kanıta dayalı durma (S).** *Sorun:* Süreyi en yavaş araştırmacı belirliyor (bir koşuda tek başına 10:22); ama süre sınırı b1c91b8'de bilerek kalktı. *Değişiklik:* ~8 arama (Deep 16) ve notlarda sayaç; satır kendini çözen kayıt ya da iki bağımsız kaynakla kapanır; yeni bilgi gelmeyince durulur; saat yok. *Doğrulama:* ≤ 10 arama; en uzun araştırmacı ≤ 6 dk.

**12. Makbuz sayfayla doğrulanır (S).** *Sorun:* 157 makbuzun 14'ü (%9) kopyasında yok, çoğu PDF düzeninden; 9 satır sessizce okunmadı. *Değişiklik:* `<URL>` biçimi kabul; tutmayan makbuz bayraksız düşer ve sayılır; #9'dan sonra. *Doğrulama:* Alıntıların ≥ %97'si kalır.

**13. Alan merdiveni, kapsam kuralı (S).** *Sorun:* Satıcının kendi kıyaslama testi (benchmark) birincil sayılıyor; yasa teklifi yürürlükteki yasayı geçebiliyor; kanıt masa başı test (stress-test F10). *Değişiklik:* ~80 kelimelik kural: kurumun kendisi hakkındaki iddiası basın sayılır; sağlıkta kılavuz > deney > gözlem; hukukta statü etiketi; rakam yer, dönem, birim ve tanım tutarsa geçer; yeni hüküm "ikisi de, tanıma göre". *Doğrulama:* Tarih dışı soru (8. bölüm).

**14. Yeniden kullanım: tazele, ödünç al (S).** *Sorun:* Hiç çalışmadı; `reuse.md` eski satırların hepsini komşu soruya taşır; Quick hiç kaydetmez. *Değişiklik:* Tazele (aynı soru) ve ödünç al (komşu soru, yalnız kapsamı tutan makbuzlar); Quick not yazar. *Etki:* Takipte 3–8 arama az; hyperresearch'te yeniden kullanım olmadığı için en inandırıcı 5× adayı (critique #14). *Doğrulama:* Ertesi gün takibi, boş klasöre karşı.

**15. Paket ve tek sürüm (M).** 7. bölümde; brainstorm skill'i hazır olunca yapılır.

**16. İzin kurallarını belgele (S).** *Sorun:* Manual modda WebFetch her yeni alan adı için onay ister; alt ajanların onayları ana oturuma düşer (hosts F6). *Değişiklik:* README ve `hosts.md` WebSearch, WebFetch ve `Bash(python* *vafer_check.py*)` izinlerini ya da auto modu önerir. *Doğrulama:* Manual oturumda onay sayısı.

### Olabilir

- **17. Takvim dönüştürücü (S):** `vafer_check.py convert hijri|rumi <yıl>`; 3 "derived" bayrağı gider. Test: Rumi 1316, 14 Mart 1900'de başlar.
- **18. Model ve effort deneyi (S):** şartlardan sonra araştırmacılar `effort: low` ile; belki −%20–35 süre. Doğruluk 0,5 içinde ve süre ≥ %25 düşükse benimse.
- **19. Dar sorular Quick'e (S):** belki 3–5 dakikalık cevap; önce iki dar soruda Quick'i Standard'la kıyasla.
- **20. Sayı okuma (S):** 50M, yüzde ve parantezli denklemde yanlış bayrak biter; ilk hesaplı soruyla.
- **21. Soru şekilleri (S):** karşılaştırmada ortak çerçeve; hesapta girdiyi araştırmacı, hesabı ana ajan yapar; listede çerçeveyi boşluk bulucu verir.
- **22. Üç sayım (S):** hakem brifine tersine dönen hüküm, bayrak isabeti, süre ve çağrı; karar sayıma dayanır.
- **23. Wayback ve "önce kayıt" (S):** 404 ya da 410'da arşiv kopyası; brife "önce kayda git". Test: 12 başarısız URL'yi yeniden dene.
- **E1. Dayanıklılık (S):** düşen ajanı bir kez yeniden başlat; bağlam sıkıştırmadan sonra `plan.md`'yi yeniden oku; Deep'te 200 aramalık oturum tavanını say.
- **E2. Kopyalar (efor belirsiz):** aynı anlatının kopyaları tek kaynak; araştırmacı "via [5]" diye not eder.

## 5. Yapmayacaklarımız

- Her cümleye makbuz çapası ve `support.md`: ölçülmüş hata yok; v0.0.3'ün kendi için kayıt kalıbı.
- Rapordan sonra doğrulayıcı alt ajan: yeni aşama, ölçülmüş yakalama yok.
- Kesinlik kelimeleri ve yargı satırlarına karşı kanıt: ölçülmüş hata yok; çelişki puanı 8,5.
- Plandan önce ana ajanın 3–5 araması: boşluk bulucuyu tekrarlar, 1–1,5 dk ekler.
- Yeni bayrak türleri: yalnız sayfada eşleşen rakam kayıtlı koşuda gerçek hata bulmadı; sayfada bulunmayan makbuz koşu başına ~14 yanlış alarm verir.
- 4 dakikalık sert saat: süre sınırı bilerek kaldırıldı; ~6 dakikalık bir taşma ölçülürse dönülür.
- Beşinci referans dosyası `shapes.md`: 4 dosya tavanını bozar; tarih dışı soru koşulmadı.
- Ayrı puan kartı belgesi: değerlendirme altyapısına kayar.
- WebSearch extended modu: kota maliyeti doğrulanmadı.

## 6. Brainstorm'da karar vermemiz gerekenler

1. **Hız hedefi.** Seçenekler: ~10 dk; çıplak modelin ≤ 2 katı; ≤ 1,5 katı (~7,5 dk, derinliği kesmeden zor). *Öneri:* v0.0.5 için ≤ 13 dk ve ≤ 8 alt ajan, sonra ≤ 2 kat; `/deep-research`'e karşı hız iddiası ölçmeden yok.
2. **Araştırmacı sınırı ve modeli.** Seçenekler: sınır yok (13:39–24:00 oynaması kabul); sayaç ve kanıta dayalı durma; ~8 arama ve 4 dakikalık saat. Model: oturum modeli ya da `effort: low`. *Öneri:* sayaç, saat yok; oturum modeli.
3. **Raporu kim yazar.** Seçenekler: script; ana ajan; editör yalnız Deep ve Ultra'da; editör her yerde. *Öneri:* ücretsiz 3'lü sıralama ilk ikisinden birini seçsin; editör varsayılan olmasın.
4. **Rapor uzunluğu.** Seçenekler: gövde ~1.500 ya da ~2.000 kelime; "detaylı" ~3.000, "kısa" ~1.000. *Öneri:* ~2.000; 2.406 kelimelik gövde 8,5 okunurluk aldı. CSV ilk liste sorusuyla.
5. **Bütçe tavanları.** Seçenekler: 700/700 satırla dolu script (skill-audit F19) kalır ya da ~800, ~900, ~1.000 satıra çıkar; referans 4 ya da 5 dosya. *Öneri:* bir kez ~900, her özellik ölçülmüş ajan işinin yerini alırsa; 4 dosya, `researcher.md` `style.md`'nin yerine.
6. **İlk "5×".** Seçenekler: manşetlerde desteksiz iddia; takip maliyeti; liste eksiksizliği. Her biri payda ister; hyperresearch light koşusu tahminen 30–40 dk. *Öneri:* takip maliyeti, çünkü hyperresearch'te yeniden kullanım yok; hyperresearch light, v0.0.5 testi geçince bir kez.
7. **Tarih dışı ilk soru ve doğrulayıcı ajan.** Seçenekler: teknik karşılaştırma, sağlık, hukuk, hesap, liste; rapordan sonra 1–2 dakikalık doğrulayıcı. *Öneri:* ikinci turda bir hukuk ya da hesap sorusu; doğrulayıcı yok.
8. **Eklenti ve klasör adları.** Seçenekler: `research` ve `brainstorm` (eklentide `vafer:research`); ya da `vafer-research` ve `vafer-brainstorm` (kopya kurulum ve `$vafer-research` bozulmaz). *Öneri:* ikincisi; ad değişikliği brainstorm tasarımında.

## 7. v0.0.5 paketi

- Sürüm `0.0.5` tek kaynakta: `.claude-plugin/plugin.json` (`"name": "vafer"`). Her `SKILL.md`'deki `metadata.version` buna eşit kalır; hijyen testi her skill için döner ve eşitliği doğrular. Hiçbir host `metadata.version` okumuyor (hosts F8).
- `.claude-plugin/marketplace.json` (source `"./"`): Claude Code okur; Codex kaynak koduna göre bu dosyalara geri düşer, ama canlı kurulum denenmedi (hosts F12). Sürümden önce iki hostta kurulur.
- README: iki host için eklenti ve kopya kurulumu (bulut oturumları yerel eklenti yüklemez; hosts F11), Codex için `-c web_search="live"`, izin kuralları, durum satırı v0.0.5.
- Brainstorm tasarımına kalanlar: ortak `.vafer/<module>/` klasör düzeni ve brainstorm'un araştırma kurallarını kopyalamak yerine vafer-research'ü çağırması.

## 8. Doğrulama

Yeni altyapı yok: mevcut scriptler (`runstats.py`, `speed_turns.py`, `readab.py`; geçici klasörden bu klasördeki `tools/`'a kopyalandı) ve tek kör hakem yeter.

1. Önce metin şartları: #6 (her koşudan önce), #7, #1, #2, #3.
2. Ücretsiz çevrimdışı kontroller: #4'ün 3'lü sıralaması; yeni check'in kayıtlı koşuda tekrarı (tam 4 B hücresi); C12 ve C15 için tek takip ajanı.
3. Script şartları (#5, #4, #8), birim testleriyle.
4. Yan yana test: v0.0.5, v0.0.4 ve çıplak model; ana ajan ana oturumda; bütçe yeterse her VAFER kolu iki kez.

| Soru | Tip | Ölçtüğü |
|---|---|---|
| Yeni bir Türkiye-yerel tarih sorusu ("Mudanya'nın tarihi" gibi) | Anlatı | Sekiz şart |
| Küçük bir SaaS için AB Yapay Zekâ Yasası ya da asgari ücretin gerçek değişimi | Hukuk veya hesap | #13, #20, #21 |
| İlk sorunun ertesi gün takibi, eski ve boş klasörle | Takip | #14 |

Geçme ölçütleri koşudan önce sabitlenir (critique): ≤ 13 dk ve ≤ 8 alt ajan; doğruluk ≥ v0.0.4; tersine dönen olumsuz hüküm ≤ 1; okunurluk ≥ 8; açık orta veya yüksek bayrak ≤ 5, isabet ≥ %50; araştırma sonrası ≤ 3 dk. Codex desteği iddiasından önce Codex'te bir Standard soru koşulur.

## 9. Kaynaklar

İnceleme dosyaları (`docs/research/2026-10-30-v0.0.5-review/`): `notes/run-evidence.md`, `notes/skill-audit.md`, `notes/stress-test.md`, `notes/hosts.md`, `notes/external-sweep.md`, `notes/prior-research.md`, `design-speed.md`, `design-quality.md`, `critique.md`.

Dış kaynaklar:
- hyperresearch: https://github.com/jordan-gibbs/hyperresearch
- `/deep-research` incelemesi: https://steel.dev/blog/claude-code-deep-research-autopsy
- Tur başına çok çağrı (W&D): https://arxiv.org/abs/2602.07359
- Görünür arama bütçesi: https://arxiv.org/abs/2511.17006
- Kendi yazılan cümlelerin desteği: https://arxiv.org/abs/2610.18442
- Küçük modellerde derin arama (DeepSearchQA): https://arxiv.org/abs/2601.20975
- Claude Code alt ajanları: https://code.claude.com/docs/en/sub-agents
- Codex alt ajanları: https://learn.chatgpt.com/docs/agent-configuration/subagents
- Codex web araması: https://learn.chatgpt.com/docs/web-search
