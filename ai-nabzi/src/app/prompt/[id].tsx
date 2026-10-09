import Ionicons from '@expo/vector-icons/Ionicons';
import * as Clipboard from 'expo-clipboard';
import * as Haptics from 'expo-haptics';
import { Redirect, Stack, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { Pressable, ScrollView, Text, View } from 'react-native';

import { Card, PrimaryButton } from '../../components/ui';
import { useAppState } from '../../state/AppState';
import { useTheme } from '../../theme';

/** Metni [YER TUTUCU] parçalarına böler; tek indeksler yer tutucudur. */
function splitPlaceholders(body: string) {
  return body.split(/(\[[^\]]+\])/g);
}

export default function PromptScreen() {
  const t = useTheme();
  const { id } = useLocalSearchParams<{ id: string }>();
  const { content, isPremium, isFavorite, toggleFavorite } = useAppState();
  const [copied, setCopied] = useState(false);
  const prompt = content.prompts.find((p) => p.id === id);

  if (!prompt) return <Redirect href="/prompts" />;
  if (prompt.premium && !isPremium) return <Redirect href="/paywall" />;

  const saved = isFavorite(prompt.id);

  const copy = async () => {
    await Clipboard.setStringAsync(prompt.body);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <>
      <Stack.Screen
        options={{
          title: prompt.category,
          headerRight: () => (
            <Pressable onPress={() => toggleFavorite(prompt.id)} hitSlop={12} accessibilityLabel={saved ? 'Kayıttan çıkar' : 'Kaydet'}>
              <Ionicons name={saved ? 'bookmark' : 'bookmark-outline'} size={22} color={t.accent} />
            </Pressable>
          ),
        }}
      />
      <ScrollView contentContainerStyle={{ padding: 16, gap: 16, paddingBottom: 40 }}>
        <View style={{ gap: 6 }}>
          <Text style={{ color: t.text, fontSize: 24, fontWeight: '800' }}>{prompt.title}</Text>
          <Text style={{ color: t.muted, fontSize: 15, lineHeight: 21 }}>{prompt.description}</Text>
        </View>

        <Card>
          <Text style={{ color: t.text, fontSize: 16, lineHeight: 24 }} selectable>
            {splitPlaceholders(prompt.body).map((part, i) =>
              i % 2 === 1 ? (
                <Text key={i} style={{ color: t.accent, fontWeight: '700', backgroundColor: t.accentSoft }}>
                  {part}
                </Text>
              ) : (
                part
              ),
            )}
          </Text>
        </Card>

        <PrimaryButton label={copied ? 'Kopyalandı' : 'Kopyala'} icon={copied ? 'checkmark' : 'copy-outline'} onPress={copy} />

        <Card style={{ gap: 6, backgroundColor: t.accentSoft, borderColor: t.accentSoft }}>
          <Text style={{ color: t.text, fontWeight: '700' }}>Nasıl kullanılır?</Text>
          <Text style={{ color: t.text, lineHeight: 20 }}>
            1. Kopyala ve kullandığın AI sohbetine yapıştır.{'\n'}
            2. <Text style={{ color: t.accent, fontWeight: '700' }}>[KÖŞELİ PARANTEZ]</Text> içindeki alanları kendi
            bilgilerinle değiştir.{'\n'}
            3. Cevabı beğenmezsen "daha kısa", "daha samimi" gibi tek bir düzeltme iste.
          </Text>
        </Card>
      </ScrollView>
    </>
  );
}
