# Parent Wise — Otomatik Sosyal Medya İçerik Fabrikası

`Untitled.docx` sistem dokümanının birebir uyarlaması; niş: **ebeveynlik / çocuk gelişimi**, içerik dili **İngilizce**, sahip arayüzü **Türkçe**.
Referans marka: "Parent Wise" (`@parentwise__`), değiştirmek için [brand.py](brand.py).

## Durum

| Parça | Durum |
|---|---|
| news.py + sources.json (WHO, CDC, CPSC, NPR, Child Mind, Zero to Three, FDA, HN) | çalışıyor, hatasız |
| cover.py, carousel.py, temalar (adaptive, playbooks, hookcover), 19 OFL font | çalışıyor, görsel doğrulandı |
| voice.py (Kokoro), music.py, reel.py (30 fps, altyazı, daktilo, ducking) | çalışıyor, uçtan uca test edildi |
| clip.py, viral.py | yazıldı, gerçek link/API ile test edilmedi |
| publish.py, meta_token.py, yt_token.py | yazıldı, **hesap/token gerektiği için canlı test edilmedi** |
| studio.py + studio/index.html, telegram_bot.py, stt.py, metrics.py | Studio açılıyor, API + zamanlayıcı + collect düğümü çalışıyor; scout/write/qa Claude CLI gerektirir |

## Kurulum (sırayla)
1. `pip install -r requirements.txt kokoro soundfile yt-dlp` ve `python -m playwright install chromium`, `winget install Gyan.FFmpeg`
2. `python fetch_fonts.py` (bir kez), `npm i -g @anthropic-ai/claude-code` ve `claude` ile giriş
3. `python news.py` → `research/` altında JSON, `errors` boş olmalı
4. `python cover.py content/<x>.json` → `python carousel.py content/<x>.json` → `python reel.py content/<x>.json`
5. Hesaplar: Instagram Professional + Facebook Sayfası + YouTube kanalı + GitHub repo (`gh-pages` orphan dalı, Pages açık, `.nojekyll`, privacy.html / terms.html)
6. `.env.example` → `.env`; Meta uygulaması: `python meta_token.py --page "<Sayfa adı>"`; YouTube: `client_secret.json` + `python yt_token.py`
7. `python publish.py content/<x>.json --dry-run`
8. `python studio.py` (kalıcı: `powershell -File install_startup.ps1`), Telegram için `TELEGRAM_BOT_TOKEN`

## Nişe özel uyarlamalar (dokümandaki 13. bölümün karşılığı)
- **Anayasa:** [CLAUDE.md](CLAUDE.md) — tıbbi uyarı satırı, çocuk yüzü yasağı, resmi kaynak kuralı.
- **İkinci direk:** "kopyala-yapıştır prompt paketi" yerine **playbook** kartları: çocuğa söylenecek cümleler (`script` slaytı), tema `playbooks`.
- **Tarama alanları (12):** uyku, beslenme, aşı/sağlık, güvenlik/geri çağırma, ekran, erken gelişim, okul çağı, ergen, disiplin, gebelik/yenidoğan, ebeveynlik+AI, aile politikaları.
- **Kapak kişisi:** yetişkin uzman / kurum yetkilisi (Wikimedia lisanslı); çocuk fotoğrafı asla; yoksa Flux sahnesi, o da yoksa gradyan.
- **YouTube kategorisi:** 26 (Howto & Style); AI'daki 28 yerine.
- **Klip filtresi:** reşit olmayanı aşağılayan / özel anları teşhir eden klipler `hook` adımında reddedilir.

## Bilinen sınırlar
- Kokoro bu makinede CPU'da çalışıyor (video ~1,5 dk). Kelime zamanlamaları Kokoro'dan gelmezse eşit aralıkla dağıtılır.
- Flux/Forge kurulu değil; kapak fotoğrafı yoksa gradyan yedeği kullanılır.
- `sources.json`: NIH, UNICEF, AAP HealthyChildren, Harvard için çalışan RSS bulunamadı; `manual` listesinde, scout web aramasıyla kontrol eder.
