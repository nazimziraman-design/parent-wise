import Ionicons from '@expo/vector-icons/Ionicons';
import * as Linking from 'expo-linking';
import { Text, View } from 'react-native';

import type { Brief } from '../content/types';
import { formatDate } from '../format';
import { useTheme } from '../theme';
import { Card } from './ui';

const parts = [
  { key: 'what', label: 'Ne?', icon: 'information-circle' },
  { key: 'why', label: 'Neden önemli?', icon: 'bulb' },
  { key: 'howTo', label: 'Sen nasıl kullanırsın?', icon: 'hand-right' },
] as const;

export function BriefView({ brief }: { brief: Brief }) {
  const t = useTheme();
  return (
    <View style={{ gap: 12 }}>
      <View style={{ gap: 4 }}>
        <Text style={{ color: t.accent, fontWeight: '700', fontSize: 13 }}>{formatDate(brief.date)}</Text>
        <Text style={{ color: t.text, fontWeight: '800', fontSize: 24, lineHeight: 30 }}>{brief.title}</Text>
      </View>
      {brief.items.map((item, i) => (
        <Card key={item.title} style={{ gap: 12 }}>
          <View style={{ flexDirection: 'row', gap: 10, alignItems: 'center' }}>
            <View
              style={{
                width: 28,
                height: 28,
                borderRadius: 14,
                backgroundColor: t.accentSoft,
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <Text style={{ color: t.accent, fontWeight: '800' }}>{i + 1}</Text>
            </View>
            <Text style={{ color: t.text, fontWeight: '800', fontSize: 18, flex: 1 }}>{item.title}</Text>
          </View>
          {parts.map((p) => (
            <View key={p.key} style={{ gap: 2 }}>
              <View style={{ flexDirection: 'row', gap: 6, alignItems: 'center' }}>
                <Ionicons name={p.icon} size={14} color={t.muted} />
                <Text style={{ color: t.muted, fontWeight: '700', fontSize: 13 }}>{p.label}</Text>
              </View>
              <Text style={{ color: t.text, fontSize: 15, lineHeight: 22 }}>{item[p.key]}</Text>
            </View>
          ))}
          {item.sources?.map((url) => (
            <Text key={url} style={{ color: t.accent, fontSize: 13 }} onPress={() => Linking.openURL(url)} numberOfLines={1}>
              Kaynak: {url}
            </Text>
          ))}
        </Card>
      ))}
    </View>
  );
}
