import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';
import { useSafeAreaInsets } from 'react-native-safe-area-context';

import { Card, PrimaryButton } from '../components/ui';
import { useAppState } from '../state/AppState';
import { useTheme } from '../theme';

// Fiyatlar taslaktır; gerçek fiyatlar App Store Connect'te belirlenip mağazadan okunacak.
const plans = [
  { id: 'yearly', title: 'Yıllık', price: '₺999,99 / yıl', note: 'Aylık ₺83 — 2 ay bedava' },
  { id: 'monthly', title: 'Aylık', price: '₺149,99 / ay', note: 'İstediğin zaman iptal' },
] as const;

const features = [
  'Tüm prompt kütüphanesi (her hafta yeni paketler)',
  'Brifing arşivinin tamamı',
  'Konu bazlı bildirimler',
  'Reklamsız deneyim',
];

export default function PaywallScreen() {
  const t = useTheme();
  const insets = useSafeAreaInsets();
  const { setPremium } = useAppState();
  const [plan, setPlan] = useState<(typeof plans)[number]['id']>('yearly');

  const subscribe = () => {
    // TODO: App Store aboneliği (RevenueCat / StoreKit) bağlanınca gerçek satın alma burada başlayacak.
    setPremium(true);
    router.back();
  };

  return (
    <ScrollView contentContainerStyle={{ padding: 20, paddingTop: insets.top + 12, gap: 18, paddingBottom: insets.bottom + 24 }}>
      <Pressable onPress={() => router.back()} hitSlop={12} style={{ alignSelf: 'flex-end' }} accessibilityLabel="Kapat">
        <Ionicons name="close" size={26} color={t.muted} />
      </Pressable>

      <View style={{ gap: 8, alignItems: 'center' }}>
        <Ionicons name="sparkles" size={40} color={t.premium} />
        <Text style={{ color: t.text, fontSize: 28, fontWeight: '800', textAlign: 'center' }}>AI Nabzı Pro</Text>
        <Text style={{ color: t.muted, fontSize: 16, textAlign: 'center', lineHeight: 22 }}>
          Yapay zekâyı işinde gerçekten kullanmak için ihtiyacın olan her şey.
        </Text>
      </View>

      <View style={{ gap: 10 }}>
        {features.map((f) => (
          <View key={f} style={{ flexDirection: 'row', gap: 10, alignItems: 'center' }}>
            <Ionicons name="checkmark-circle" size={20} color={t.accent} />
            <Text style={{ color: t.text, fontSize: 15, flex: 1 }}>{f}</Text>
          </View>
        ))}
      </View>

      <View style={{ gap: 10 }}>
        {plans.map((p) => {
          const active = p.id === plan;
          return (
            <Pressable key={p.id} onPress={() => setPlan(p.id)}>
              <Card style={{ borderWidth: 2, borderColor: active ? t.accent : t.border, flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                <Ionicons name={active ? 'radio-button-on' : 'radio-button-off'} size={22} color={active ? t.accent : t.muted} />
                <View style={{ flex: 1 }}>
                  <Text style={{ color: t.text, fontWeight: '800', fontSize: 16 }}>{p.title}</Text>
                  <Text style={{ color: t.muted, fontSize: 13 }}>{p.note}</Text>
                </View>
                <Text style={{ color: t.text, fontWeight: '700' }}>{p.price}</Text>
              </Card>
            </Pressable>
          );
        })}
      </View>

      <PrimaryButton label="Devam et" onPress={subscribe} />

      <Text style={{ color: t.muted, fontSize: 12, textAlign: 'center', lineHeight: 17 }}>
        Demo sürüm: gerçek ödeme henüz bağlı değil, "Devam et" Pro'yu yalnızca bu cihazda açar.{'\n'}
        Abonelik, dönem bitmeden en az 24 saat önce iptal edilmezse otomatik yenilenir.
      </Text>
    </ScrollView>
  );
}
