import type { Prompt } from './types';

export const categories = [
  'Yazı & İçerik',
  'Sosyal Medya',
  'İş & Verimlilik',
  'Öğrenme',
  'Kod',
  'Görsel AI',
] as const;

export const prompts: Prompt[] = [
  // Yazı & İçerik
  {
    id: 'blog-taslak',
    category: 'Yazı & İçerik',
    title: 'Blog yazısı iskeleti',
    description: 'Konudan başlıklar, alt başlıklar ve ana fikirler çıkarır.',
    body: 'Deneyimli bir içerik editörü gibi davran. [KONU] hakkında [HEDEF KİTLE] için bir blog yazısı iskeleti hazırla. 1 ana başlık önerisi, 5–7 alt başlık ve her alt başlık altında 2 maddelik ana fikir yaz. Sonunda okuru harekete geçiren bir kapanış cümlesi öner.',
    premium: false,
  },
  {
    id: 'metin-sadelestir',
    category: 'Yazı & İçerik',
    title: 'Metni sadeleştir',
    description: 'Karmaşık bir metni herkesin anlayacağı dile çevirir.',
    body: 'Aşağıdaki metni anlamını değiştirmeden sadeleştir. Kısa cümleler kullan, teknik terimleri açıkla, 12 yaşındaki birinin anlayacağı netlikte yaz.\n\nMetin:\n[METİN]',
    premium: false,
  },
  {
    id: 'baslik-alternatif',
    category: 'Yazı & İçerik',
    title: '10 başlık alternatifi',
    description: 'Aynı içerik için farklı tonlarda başlıklar üretir.',
    body: '[İÇERİK ÖZETİ] için 10 başlık öner. 3 tanesi merak uyandıran, 3 tanesi fayda odaklı, 2 tanesi soru şeklinde, 2 tanesi rakam içeren olsun. Abartılı vaat ve tıklama tuzağı kullanma.',
    premium: true,
  },
  {
    id: 'ton-degistir',
    category: 'Yazı & İçerik',
    title: 'Tonu değiştir',
    description: 'Metni resmi, samimi veya ikna edici tona çevirir.',
    body: 'Aşağıdaki metni [TON: resmi / samimi / ikna edici] bir tona çevir. Uzunluğu yaklaşık aynı kalsın, bilgileri değiştirme.\n\nMetin:\n[METİN]',
    premium: true,
  },

  // Sosyal Medya
  {
    id: 'carousel-plan',
    category: 'Sosyal Medya',
    title: 'Instagram carousel planı',
    description: '7–10 slaytlık bir carousel akışı çıkarır.',
    body: 'Bir sosyal medya stratejisti gibi davran. [KONU] hakkında [HEDEF KİTLE] için 8 slaytlık bir Instagram carousel planı hazırla. Slayt 1: 8–15 kelimelik dikkat çekici kapak cümlesi. Slayt 2–7: her birinde tek fikir, en fazla 25 kelime. Slayt 8: kaydet ve takip et çağrısı. Uydurma istatistik kullanma.',
    premium: false,
  },
  {
    id: 'reels-senaryo',
    category: 'Sosyal Medya',
    title: '30 saniyelik Reels senaryosu',
    description: 'İlk 3 saniyesi güçlü, kısa video metni yazar.',
    body: '[KONU] için 30 saniyelik bir Reels senaryosu yaz. İlk 3 saniye için güçlü bir giriş cümlesi, ardından 3 kısa sahne (her biri ekranda görünecek yazı + seslendirme), sonunda net bir çağrı. Toplam seslendirme 70–80 kelimeyi geçmesin.',
    premium: true,
  },
  {
    id: 'icerik-takvimi',
    category: 'Sosyal Medya',
    title: '30 günlük içerik takvimi',
    description: 'Bir ay boyunca paylaşım fikirlerini tablo halinde verir.',
    body: '[HESAP KONUSU] için 30 günlük içerik takvimi hazırla. Tablo sütunları: Gün, Format (carousel / reels / tek görsel / hikâye), Konu, Kapak cümlesi. Formatları dengeli dağıt, aynı konuyu tekrarlama.',
    premium: true,
  },
  {
    id: 'yorum-cevap',
    category: 'Sosyal Medya',
    title: 'Yorumlara cevap önerisi',
    description: 'Olumsuz yorumlara bile sakin ve profesyonel cevaplar.',
    body: 'Markamın sesi [MARKA SESİ: ör. samimi, yardımsever]. Aşağıdaki yoruma 2 farklı cevap öner. Savunmaya geçme, teşekkür et, gerekiyorsa çözüm için özel mesaja davet et. En fazla 40 kelime.\n\nYorum:\n[YORUM]',
    premium: true,
  },

  // İş & Verimlilik
  {
    id: 'toplanti-aksiyon',
    category: 'İş & Verimlilik',
    title: 'Toplantı notundan aksiyon listesi',
    description: 'Dağınık notlardan kararlar, sorumlular ve tarihler.',
    body: 'Aşağıdaki toplantı notlarını analiz et. Üç bölüm halinde yaz: 1) Alınan kararlar, 2) Aksiyonlar (görev – sorumlu – tarih tablosu), 3) Açık kalan sorular. Notlarda olmayan bilgiyi uydurma; eksikse "belirtilmemiş" yaz.\n\nNotlar:\n[NOTLAR]',
    premium: false,
  },
  {
    id: 'zor-eposta',
    category: 'İş & Verimlilik',
    title: 'Zor e-posta taslağı',
    description: 'Hassas durumlar için iki farklı tonda taslak.',
    body: 'Şu durum için bir e-posta yazmam gerekiyor: [DURUM]. Alıcı: [ALICI]. İstediğim sonuç: [AMAÇ]. Biri daha resmi, biri daha samimi iki taslak yaz. Her biri en fazla 150 kelime olsun ve net bir sonraki adım içersin.',
    premium: false,
  },
  {
    id: 'swot',
    category: 'İş & Verimlilik',
    title: 'Hızlı SWOT analizi',
    description: 'Fikir veya iş için güçlü/zayıf yönler, fırsat ve tehditler.',
    body: 'Bir iş danışmanı gibi davran. [İŞ / FİKİR] için SWOT analizi yap. Her başlıkta 3–5 madde yaz. Sonunda en kritik 3 riski ve her biri için bir önlem öner. Bilmediğin pazar verisini uydurma, varsayımlarını açıkça belirt.',
    premium: true,
  },
  {
    id: 'haftalik-plan',
    category: 'İş & Verimlilik',
    title: 'Haftalık öncelik planı',
    description: 'Görev listesini önem ve aciliyete göre sıralar.',
    body: 'Aşağıdaki görevleri Eisenhower matrisine göre (önemli/acil) dört gruba ayır. Ardından bu hafta için gün gün bir plan öner. Günde en fazla 3 ana görev olsun.\n\nGörevler:\n[GÖREVLER]',
    premium: true,
  },
  {
    id: 'cv-ilan',
    category: 'İş & Verimlilik',
    title: 'CV\'yi ilana uyarla',
    description: 'Deneyimini iş ilanındaki anahtar becerilere göre düzenler.',
    body: 'Aşağıdaki iş ilanını ve CV özetimi karşılaştır. İlandaki en önemli 5 beceriyi çıkar, CV\'mde bunlarla eşleşen deneyimleri vurgulayan 4 madde yeniden yaz. Olmayan bir deneyimi ekleme.\n\nİlan:\n[İLAN]\n\nCV özetim:\n[CV]',
    premium: true,
  },

  // Öğrenme
  {
    id: 'feynman',
    category: 'Öğrenme',
    title: 'Feynman tekniğiyle öğren',
    description: 'Bir konuyu basitçe anlatır, sonra seni test eder.',
    body: '[KONU] konusunu hiç bilmeyen birine anlatır gibi basitçe açıkla. Bir günlük hayattan benzetme kullan. Sonra anlayıp anlamadığımı ölçmek için bana 3 soru sor ve cevaplarımı bekle.',
    premium: false,
  },
  {
    id: 'calisma-plani',
    category: 'Öğrenme',
    title: '4 haftalık çalışma planı',
    description: 'Yeni bir beceri için haftalık hedefli plan.',
    body: '[BECERİ] öğrenmek istiyorum. Günde [SÜRE] dakikam var ve seviyem [SEVİYE]. 4 haftalık bir plan hazırla: her hafta için hedef, günlük çalışma konuları ve hafta sonunda yapılacak küçük bir proje.',
    premium: true,
  },
  {
    id: 'kavram-karti',
    category: 'Öğrenme',
    title: 'Tekrar kartları üret',
    description: 'Bir metinden soru-cevap kartları çıkarır.',
    body: 'Aşağıdaki metinden 10 adet soru–cevap tekrar kartı oluştur. Sorular tek bir kavramı ölçsün, cevaplar en fazla 2 cümle olsun. Metinde olmayan bilgi ekleme.\n\nMetin:\n[METİN]',
    premium: true,
  },

  // Kod
  {
    id: 'kod-acikla',
    category: 'Kod',
    title: 'Kodu satır satır açıkla',
    description: 'Anlamadığın bir kod parçasını açıklar.',
    body: 'Aşağıdaki [DİL] kodunu yeni başlayan birine satır satır açıkla. Sonunda kodun ne işe yaradığını tek cümlede özetle ve olası bir hatayı veya iyileştirmeyi belirt.\n\nKod:\n[KOD]',
    premium: false,
  },
  {
    id: 'excel-formul',
    category: 'Kod',
    title: 'Excel / Sheets formülü yaz',
    description: 'Ne istediğini anlat, formülü ve açıklamasını al.',
    body: 'Excel\'de şu işlemi yapmak istiyorum: [İSTEK]. Verilerim şu sütunlarda: [SÜTUNLAR]. Bana formülü, nasıl çalıştığını ve hangi hücreye yazmam gerektiğini anlat. Türkçe Excel kullanıyorsam fonksiyon adlarının Türkçe karşılığını da ver.',
    premium: true,
  },
  {
    id: 'hata-ayikla',
    category: 'Kod',
    title: 'Hata mesajını çöz',
    description: 'Hata mesajından olası nedenleri ve çözümü bulur.',
    body: 'Şu hatayı alıyorum:\n[HATA MESAJI]\n\nİlgili kod:\n[KOD]\n\nEn olası 3 nedeni olasılık sırasına göre yaz, her biri için nasıl kontrol edeceğimi ve düzeltmeyi göster.',
    premium: true,
  },

  // Görsel AI
  {
    id: 'gorsel-prompt',
    category: 'Görsel AI',
    title: 'Görsel üretim promptu',
    description: 'Fikrini detaylı bir görsel tarifine dönüştürür.',
    body: 'Görsel üretim modeli için İngilizce bir prompt yaz. Fikrim: [FİKİR]. Şunları belirt: ana konu, ortam, ışık, kamera açısı, stil, renk paleti. Gerçek bir kişiyi, markayı veya logoyu taklit etme. 3 farklı varyasyon ver.',
    premium: false,
  },
  {
    id: 'urun-fotografi',
    category: 'Görsel AI',
    title: 'Ürün fotoğrafı sahnesi',
    description: 'E-ticaret için arka plan ve sahne fikirleri.',
    body: '[ÜRÜN] için e-ticaret görseli hazırlayacağım. Hedef kitle: [KİTLE]. 5 farklı sahne/arka plan fikri öner ve her biri için görsel üretim modeline verilecek İngilizce prompt yaz. Ürünün kendisini değiştirme, sadece sahneyi tarif et.',
    premium: true,
  },
  {
    id: 'logo-brif',
    category: 'Görsel AI',
    title: 'Logo tasarım brifi',
    description: 'Tasarımcıya veya AI aracına verilecek net brif.',
    body: '[MARKA ADI] için logo brifi hazırla. Sektör: [SEKTÖR]. Marka kişiliği: [3 SIFAT]. Brifte: renk önerileri, kaçınılacak klişeler, simge fikirleri ve yazı karakteri yönü olsun. Var olan bir markaya benzememesi için uyarı ekle.',
    premium: true,
  },
];
