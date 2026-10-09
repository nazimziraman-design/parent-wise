import Ionicons from '@expo/vector-icons/Ionicons';
import { useMemo, useState } from 'react';
import { FlatList, ScrollView, Text, TextInput, View } from 'react-native';

import { Chip, PromptRow } from '../../components/ui';
import { categories } from '../../content/prompts';
import { useAppState } from '../../state/AppState';
import { useTheme } from '../../theme';

const ALL = 'Tümü';

export default function PromptsScreen() {
  const t = useTheme();
  const { content } = useAppState();
  const [category, setCategory] = useState<string>(ALL);
  const [query, setQuery] = useState('');

  const list = useMemo(() => {
    const q = query.trim().toLocaleLowerCase('tr');
    return content.prompts.filter(
      (p) =>
        (category === ALL || p.category === category) &&
        (!q || `${p.title} ${p.description}`.toLocaleLowerCase('tr').includes(q)),
    );
  }, [content.prompts, category, query]);

  const cats = [ALL, ...categories.filter((c) => content.prompts.some((p) => p.category === c))];

  return (
    <FlatList
      data={list}
      keyExtractor={(p) => p.id}
      contentContainerStyle={{ padding: 16, gap: 10, paddingBottom: 40 }}
      keyboardShouldPersistTaps="handled"
      ListHeaderComponent={
        <View style={{ gap: 12, marginBottom: 4 }}>
          <View
            style={{
              flexDirection: 'row',
              alignItems: 'center',
              gap: 8,
              backgroundColor: t.card,
              borderColor: t.border,
              borderWidth: 1,
              borderRadius: 12,
              paddingHorizontal: 12,
            }}
          >
            <Ionicons name="search" size={18} color={t.muted} />
            <TextInput
              value={query}
              onChangeText={setQuery}
              placeholder="Prompt ara…"
              placeholderTextColor={t.muted}
              style={{ flex: 1, color: t.text, paddingVertical: 12, fontSize: 16 }}
              clearButtonMode="while-editing"
            />
          </View>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={{ gap: 8 }}>
            {cats.map((c) => (
              <Chip key={c} label={c} active={c === category} onPress={() => setCategory(c)} />
            ))}
          </ScrollView>
        </View>
      }
      ListEmptyComponent={<Text style={{ color: t.muted, textAlign: 'center', marginTop: 24 }}>Sonuç bulunamadı.</Text>}
      renderItem={({ item }) => <PromptRow prompt={item} />}
    />
  );
}
