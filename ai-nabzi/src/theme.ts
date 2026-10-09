import { useColorScheme } from 'react-native';

const light = {
  bg: '#F6F7FB',
  card: '#FFFFFF',
  text: '#121527',
  muted: '#5B6078',
  border: '#E3E5EE',
  accent: '#5B4CF0',
  accentText: '#FFFFFF',
  accentSoft: '#ECEAFE',
  premium: '#B7791F',
  premiumSoft: '#FDF3E1',
};

const dark: typeof light = {
  bg: '#0B1020',
  card: '#151A2E',
  text: '#EEF0FA',
  muted: '#9CA2BD',
  border: '#262C45',
  accent: '#8B7FFF',
  accentText: '#0B1020',
  accentSoft: '#231F4A',
  premium: '#F2B84B',
  premiumSoft: '#3A2D12',
};

export type Theme = typeof light;

export function useTheme(): Theme {
  return useColorScheme() === 'dark' ? dark : light;
}
