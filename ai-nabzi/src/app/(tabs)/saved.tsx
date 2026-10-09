import Ionicons from '@expo/vector-icons/Ionicons';
import { FlatList, Text, View } from 'react-native';

import { PromptRow } from '../../components/ui';
import { useAppState } from '../../state/AppState';
import { useTheme } from '../../theme';

export default function SavedScreen() {
  const t = useTheme();
  const { content, favorites } = useAppState();
  const saved = favorites
    .map((id) => content.prompts.find((p) => p.id === id))
    .filter((p) => p !== undefined);

  return (
    <FlatList
      data={saved}
      keyExtractor={(p) => p.id}
      contentContainerStyle={{ padding: 16, gap: 10, flexGrow: 1 }}
      renderItem={({ item }) => <PromptRow prompt={item} />}
      ListEmptyComponent={
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', gap: 10, padding: 24 }}>
          <Ionicons name="bookmark-outline" size={40} color={t.muted} />
          <Text style={{ color: t.text, fontSize: 17, fontWeight: '700' }}>Henüz kaydedilen yok</Text>
          <Text style={{ color: t.muted, textAlign: 'center', lineHeight: 20 }}>
            Beğendiğin promptları kaydet, hepsi burada hazır dursun.
          </Text>
        </View>
      }
    />
  );
}
