import type { Brief } from './types';

// Örnek brifingler: güncel haber değil, her zaman geçerli pratik bilgiler.
// Gerçek günlük haberler uzak içerik dosyasından (app.json > extra.contentUrl) gelecek
// ve her haber maddesi doğrulanmış kaynak bağlantısı taşıyacak.
export const briefs: Brief[] = [
  {
    id: 'b-2026-10-09',
    date: '2026-10-09',
    title: 'Yapay zekâya iyi soru sormanın 3 kuralı',
    items: [
      {
        title: 'Rol ver',
        what: 'Modele kim gibi düşünmesi gerektiğini söyle: "Deneyimli bir e-ticaret pazarlamacısı gibi davran."',
        why: 'Rol, cevabın dilini, derinliğini ve bakış açısını belirler. Genel sorular genel cevaplar getirir.',
        howTo: 'Bir sonraki sorunun başına tek cümlelik bir rol ekle ve iki cevabı karşılaştır.',
      },
      {
        title: 'Bağlam ver',
        what: 'Hedef kitleni, amacını ve kısıtlarını yaz: kime, ne için, hangi uzunlukta.',
        why: 'Model senin durumunu bilmez. Eksik bağlamı tahminle doldurur, bu da isabeti düşürür.',
        howTo: '"Bağlam:" diye bir satır aç ve 2–3 madde ekle: kitle, amaç, kısıt.',
      },
      {
        title: 'Çıktı formatını iste',
        what: 'Cevabın nasıl görüneceğini belirt: tablo, 5 madde, 100 kelime, e-posta taslağı.',
        why: 'Format belirtmek düzeltme turlarını azaltır ve sonucu doğrudan kullanılabilir yapar.',
        howTo: 'Sorunun sonuna "Cevabı … formatında ver" ekle.',
      },
    ],
  },
  {
    id: 'b-2026-10-08',
    date: '2026-10-08',
    title: 'AI ile güvenli çalışmak',
    items: [
      {
        title: 'Hassas veriyi yapıştırma',
        what: 'Kimlik numarası, şifre, müşteri listesi veya gizli şirket belgeleri sohbet kutusuna girilmemeli.',
        why: 'Girdiğin metin, kullandığın servisin veri politikasına göre saklanabilir veya işlenebilir.',
        howTo: 'Paylaşmadan önce isimleri ve numaraları "[MÜŞTERİ]" gibi yer tutucularla değiştir.',
      },
      {
        title: 'Çıktıyı doğrula',
        what: 'Dil modelleri bazen gerçek olmayan bilgi, kaynak veya rakam üretebilir.',
        why: 'Kontrol edilmeden yayımlanan yanlış bilgi itibar ve güven kaybettirir.',
        howTo: 'Rakam, tarih ve alıntıları her zaman resmi kaynaktan kontrol et.',
      },
      {
        title: 'Kullanım koşullarını oku',
        what: 'Üretilen metin ve görsellerin ticari kullanım hakları servisten servise değişir.',
        why: 'Reklamda veya üründe kullanacağın içerik için hakların net olması gerekir.',
        howTo: 'Kullandığın aracın "Terms of Use" sayfasında ticari kullanım bölümüne bak.',
      },
    ],
  },
  {
    id: 'b-2026-10-07',
    date: '2026-10-07',
    title: 'Haftada saatler kazandıran 3 kullanım',
    items: [
      {
        title: 'Toplantı notunu özetle',
        what: 'Dağınık notları yapıştırıp kararları, sorumluları ve tarihleri ayrı ayrı listelemesini iste.',
        why: 'Toplantı sonrası e-postası dakikalar yerine saniyeler sürer.',
        howTo: 'Promptlar sekmesindeki "Toplantı notundan aksiyon listesi" kartını kullan.',
      },
      {
        title: 'Zor e-postaya taslak',
        what: 'Durumu ve istediğin tonu anlat, 2 farklı taslak iste.',
        why: 'Boş sayfa yerine düzenlenecek bir metinle başlamak işi hızlandırır.',
        howTo: 'Taslağı kendi cümlelerinle son kez gözden geçirmeden gönderme.',
      },
      {
        title: 'Excel formülünü açıklat',
        what: 'Anlamadığın formülü yapıştırıp adım adım açıklamasını iste.',
        why: 'Başkasından devraldığın tabloları hızlıca anlarsın.',
        howTo: 'Formülün hangi sütunlara baktığını da yazarsan açıklama netleşir.',
      },
    ],
  },
];
