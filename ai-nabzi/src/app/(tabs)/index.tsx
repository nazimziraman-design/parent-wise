import Ionicons from '@expo/vector-icons/Ionicons';
import { Link } from 'expo-router';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { BriefView } from '../../components/BriefView';
import { Card, PremiumBadge, PromptRow, SectionTitle } from '../../components/ui';
import { formatDate } from '../../format';
import { useAppState } from '../../state/AppState';
import { useTheme } from '../../theme';

export default function TodayScreen() {
  const t = useTheme();
  const { content, isPremium } = useAppState();
  const [latest, ...archive] = [...content.briefs].sort((a, b) => b.date.localeCompare(a.date));

  // Günün promptu: ücretsiz promptlar arasında tarihe göre döner.
  const free = content.prompts.filter((p) => !p.premium);
  const dayIndex = Math.floor(Date.now() / 86_400_000);
  const promptOfDay = free.length ? free[dayIndex % free.length] : undefined;

  return (
    <ScrollView contentContainerStyle={{ padding: 16, gap: 16, paddingBottom: 40 }}>
      {content.sample && (
        <Card style={{ backgroundColor: t.accentSoft, borderColor: t.accentSoft, flexDirection: 'row', gap: 10 }}>
          <Ionicons name="flask" size={18} color={t.accent} />
          <Text style={{ color: t.text, flex: 1, fontSize: 13, lineHeight: 18 }}>
            Örnek içerik gösteriliyor. Günlük AI haberleri yayın akışı bağlandığında burada görünecek.
          </Text>
        </Card>
      )}

      {latest ? <BriefView brief={latest} /> : <Text style={{ color: t.muted }}>Henüz brifing yok.</Text>}

      {promptOfDay && (
        <View style={{ gap: 8 }}>
          <SectionTitle>Günün promptu</SectionTitle>
          <PromptRow prompt={promptOfDay} />
        </View>
      )}

      {archive.length > 0 && (
        <View style={{ gap: 8 }}>
          <SectionTitle>Arşiv</SectionTitle>
          {archive.map((b) => (
            <Link
              key={b.id}
              href={isPremium ? { pathname: '/brief/[id]', params: { id: b.id } } : '/paywall'}
              asChild
            >
              <Pressable style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}>
                <Card style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
                  <View style={{ flex: 1, gap: 2 }}>
                    <Text style={{ color: t.muted, fontSize: 12, fontWeight: '600' }}>{formatDate(b.date)}</Text>
                    <Text style={{ color: t.text, fontSize: 16, fontWeight: '700' }}>{b.title}</Text>
                  </View>
                  {isPremium ? <Ionicons name="chevron-forward" size={18} color={t.muted} /> : <PremiumBadge />}
                </Card>
              </Pressable>
            </Link>
          ))}
        </View>
      )}
    </ScrollView>
  );
}
