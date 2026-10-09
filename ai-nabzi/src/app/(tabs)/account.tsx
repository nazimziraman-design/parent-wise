import Ionicons from '@expo/vector-icons/Ionicons';
import Constants from 'expo-constants';
import { router } from 'expo-router';
import { ScrollView, Text, View } from 'react-native';

import { Card, PrimaryButton } from '../../components/ui';
import { useAppState } from '../../state/AppState';
import { useTheme } from '../../theme';

export default function AccountScreen() {
  const t = useTheme();
  const { isPremium, setPremium, favorites, content } = useAppState();
  const freeCount = content.prompts.filter((p) => !p.premium).length;

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16 }}>
      <Card style={{ gap: 10 }}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10 }}>
          <Ionicons name={isPremium ? 'star' : 'star-outline'} size={22} color={isPremium ? t.premium : t.muted} />
          <Text style={{ color: t.text, fontSize: 18, fontWeight: '800' }}>
            {isPremium ? 'AI Nabzı Pro' : 'Ücretsiz plan'}
          </Text>
        </View>
        <Text style={{ color: t.muted, lineHeight: 20 }}>
          {isPremium
            ? `Tüm ${content.prompts.length} prompt, brifing arşivi ve yeni paketler açık.`
            : `Günlük brifing ve ${freeCount} prompt ücretsiz. Pro ile tüm kütüphane ve arşiv açılır.`}
        </Text>
        {isPremium ? (
          <Text style={{ color: t.muted, fontSize: 13 }} onPress={() => setPremium(false)}>
            Demo: Pro'yu kapat
          </Text>
        ) : (
          <PrimaryButton label="Pro'ya geç" icon="sparkles" onPress={() => router.push('/paywall')} />
        )}
      </Card>

      <Card style={{ gap: 6 }}>
        <Text style={{ color: t.text, fontWeight: '700' }}>Kaydedilen prompt: {favorites.length}</Text>
        <Text style={{ color: t.muted, fontSize: 13 }}>Kayıtların bu cihazda saklanır.</Text>
      </Card>

      <Text style={{ color: t.muted, fontSize: 12, textAlign: 'center' }}>
        AI Nabzı {Constants.expoConfig?.version ?? ''}
      </Text>
    </ScrollView>
  );
}
