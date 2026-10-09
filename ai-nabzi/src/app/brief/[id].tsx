import { Redirect, useLocalSearchParams } from 'expo-router';
import { ScrollView } from 'react-native';

import { BriefView } from '../../components/BriefView';
import { useAppState } from '../../state/AppState';

export default function BriefScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { content, isPremium } = useAppState();
  const brief = content.briefs.find((b) => b.id === id);

  if (!brief) return <Redirect href="/" />;
  if (!isPremium) return <Redirect href="/paywall" />;

  return (
    <ScrollView contentContainerStyle={{ padding: 16, paddingBottom: 40 }}>
      <BriefView brief={brief} />
    </ScrollView>
  );
}
