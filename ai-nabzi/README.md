# AI Nabzı

Dijitalle uğraşan herkes için Türkçe yapay zekâ uygulaması (iOS, Expo / React Native).

- **Bugün:** günlük 3 maddelik brifing (Ne? → Neden önemli? → Sen nasıl kullanırsın?) + günün promptu
- **Promptlar:** kategorili, aranabilir, kopyala-yapıştır prompt kütüphanesi
- **Kaydedilenler:** favori promptlar (cihazda saklanır)
- **Hesap / Pro:** ücretsiz plan + abonelik ekranı (Pro: tüm promptlar, brifing arşivi)

## Telefonda denemek (iPhone)

1. iPhone'a App Store'dan **Expo Go** uygulamasını kur.
2. Bilgisayarda (Node.js 20+ kurulu olmalı) bu klasörde:
   ```bash
   npm install
   npx expo start
   ```
3. Ekranda çıkan QR kodu iPhone kamerasıyla okut; uygulama Expo Go içinde açılır.

## Durum

| Parça | Durum |
|---|---|
| Ekranlar, navigasyon, açık/koyu tema | Hazır |
| 22 prompt (8 ücretsiz), 3 örnek brifing | Hazır (brifingler örnek içerik) |
| Uzak içerik (günlük brifing JSON'u) | Kod hazır: `app.json > extra.contentUrl` boş |
| Gerçek abonelik (App Store) | Yapılacak: şu an demo, "Devam et" Pro'yu yalnızca cihazda açar |
| App Store yayını | Yapılacak: Apple Developer hesabı (yıllık $99) + EAS build |

## Klasörler

- `src/app/`: ekranlar (her dosya bir ekran, Expo Router)
- `src/content/`: prompt ve brifing içerikleri
- `src/state/AppState.tsx`: favoriler, Pro durumu, uzak içerik yükleme
- `src/components/`: ortak arayüz parçaları

Kontrol: `npx tsc --noEmit`
