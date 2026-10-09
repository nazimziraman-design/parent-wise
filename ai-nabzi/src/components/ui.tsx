import Ionicons from '@expo/vector-icons/Ionicons';
import { Link } from 'expo-router';
import type { ReactNode } from 'react';
import { Pressable, StyleSheet, Text, View, type ViewStyle } from 'react-native';

import type { Prompt } from '../content/types';
import { useAppState } from '../state/AppState';
import { useTheme } from '../theme';

export function Card({ children, style }: { children: ReactNode; style?: ViewStyle }) {
  const t = useTheme();
  return <View style={[styles.card, { backgroundColor: t.card, borderColor: t.border }, style]}>{children}</View>;
}

export function Chip({ label, active, onPress }: { label: string; active?: boolean; onPress?: () => void }) {
  const t = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={[styles.chip, { backgroundColor: active ? t.accent : t.card, borderColor: active ? t.accent : t.border }]}
    >
      <Text style={{ color: active ? t.accentText : t.text, fontWeight: '600', fontSize: 14 }}>{label}</Text>
    </Pressable>
  );
}

export function PremiumBadge() {
  const t = useTheme();
  return (
    <View style={[styles.badge, { backgroundColor: t.premiumSoft }]}>
      <Ionicons name="lock-closed" size={11} color={t.premium} />
      <Text style={{ color: t.premium, fontSize: 11, fontWeight: '700' }}>PRO</Text>
    </View>
  );
}

export function PrimaryButton({ label, onPress, icon }: { label: string; onPress: () => void; icon?: keyof typeof Ionicons.glyphMap }) {
  const t = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.button, { backgroundColor: t.accent, opacity: pressed ? 0.85 : 1 }]}
    >
      {icon && <Ionicons name={icon} size={18} color={t.accentText} />}
      <Text style={{ color: t.accentText, fontWeight: '700', fontSize: 16 }}>{label}</Text>
    </Pressable>
  );
}

export function PromptRow({ prompt }: { prompt: Prompt }) {
  const t = useTheme();
  const { isPremium, isFavorite } = useAppState();
  const locked = prompt.premium && !isPremium;
  return (
    <Link href={locked ? '/paywall' : { pathname: '/prompt/[id]', params: { id: prompt.id } }} asChild>
      <Pressable style={({ pressed }) => [{ opacity: pressed ? 0.7 : 1 }]}>
        <Card style={{ flexDirection: 'row', alignItems: 'center', gap: 12 }}>
          <View style={{ flex: 1, gap: 4 }}>
            <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
              <Text style={[styles.rowTitle, { color: t.text }]} numberOfLines={1}>
                {prompt.title}
              </Text>
              {locked && <PremiumBadge />}
            </View>
            <Text style={{ color: t.muted, fontSize: 14 }} numberOfLines={2}>
              {prompt.description}
            </Text>
          </View>
          {isFavorite(prompt.id) ? (
            <Ionicons name="bookmark" size={18} color={t.accent} />
          ) : (
            <Ionicons name="chevron-forward" size={18} color={t.muted} />
          )}
        </Card>
      </Pressable>
    </Link>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  const t = useTheme();
  return <Text style={[styles.section, { color: t.muted }]}>{children}</Text>;
}

const styles = StyleSheet.create({
  card: { borderRadius: 16, borderWidth: StyleSheet.hairlineWidth, padding: 16 },
  chip: { paddingHorizontal: 14, paddingVertical: 8, borderRadius: 999, borderWidth: 1 },
  badge: { flexDirection: 'row', alignItems: 'center', gap: 3, paddingHorizontal: 6, paddingVertical: 2, borderRadius: 6 },
  button: { flexDirection: 'row', gap: 8, alignItems: 'center', justifyContent: 'center', paddingVertical: 15, borderRadius: 14 },
  rowTitle: { fontSize: 16, fontWeight: '700', flexShrink: 1 },
  section: { fontSize: 13, fontWeight: '700', letterSpacing: 0.6, textTransform: 'uppercase', marginTop: 8 },
});
