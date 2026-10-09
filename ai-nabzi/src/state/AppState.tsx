import AsyncStorage from '@react-native-async-storage/async-storage';
import Constants from 'expo-constants';
import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from 'react';

import { briefs as bundledBriefs } from '../content/briefs';
import { prompts as bundledPrompts } from '../content/prompts';
import type { ContentBundle } from '../content/types';

const FAVORITES_KEY = 'favorites.v1';
const PREMIUM_KEY = 'premium.demo.v1';
const CONTENT_CACHE_KEY = 'content.cache.v1';

const bundled: ContentBundle = { version: 0, sample: true, briefs: bundledBriefs, prompts: bundledPrompts };

type AppState = {
  content: ContentBundle;
  favorites: string[];
  isFavorite: (id: string) => boolean;
  toggleFavorite: (id: string) => void;
  /**
   * Şimdilik demo: gerçek ödeme (App Store aboneliği) bağlanınca bu değer
   * mağazadaki abonelik durumundan gelecek.
   */
  isPremium: boolean;
  setPremium: (value: boolean) => void;
};

const Ctx = createContext<AppState | null>(null);

function isBundle(x: unknown): x is ContentBundle {
  const b = x as ContentBundle;
  return !!b && typeof b.version === 'number' && Array.isArray(b.briefs) && Array.isArray(b.prompts);
}

export function AppStateProvider({ children }: { children: ReactNode }) {
  const [content, setContent] = useState<ContentBundle>(bundled);
  const [favorites, setFavorites] = useState<string[]>([]);
  const [isPremium, setIsPremium] = useState(false);

  useEffect(() => {
    (async () => {
      try {
        const [fav, prem, cached] = await AsyncStorage.multiGet([FAVORITES_KEY, PREMIUM_KEY, CONTENT_CACHE_KEY]);
        if (fav[1]) setFavorites(JSON.parse(fav[1]));
        if (prem[1]) setIsPremium(prem[1] === '1');
        if (cached[1]) {
          const c = JSON.parse(cached[1]);
          if (isBundle(c) && c.version > bundled.version) setContent(c);
        }
      } catch {
        // Bozuk kayıt: varsayılanlarla devam et.
      }

      // Uzak içerik: app.json > extra.contentUrl doluysa yeni brifing/prompt'ları çek.
      const url = Constants.expoConfig?.extra?.contentUrl as string | undefined;
      if (!url) return;
      try {
        const res = await fetch(url, { headers: { 'Cache-Control': 'no-cache' } });
        const remote = await res.json();
        if (isBundle(remote)) {
          setContent((cur) => (remote.version > cur.version ? remote : cur));
          await AsyncStorage.setItem(CONTENT_CACHE_KEY, JSON.stringify(remote));
        }
      } catch {
        // Çevrimdışı: önbellek veya paketteki içerik kullanılır.
      }
    })();
  }, []);

  const toggleFavorite = useCallback((id: string) => {
    setFavorites((cur) => {
      const next = cur.includes(id) ? cur.filter((x) => x !== id) : [id, ...cur];
      AsyncStorage.setItem(FAVORITES_KEY, JSON.stringify(next)).catch(() => {});
      return next;
    });
  }, []);

  const setPremium = useCallback((value: boolean) => {
    setIsPremium(value);
    AsyncStorage.setItem(PREMIUM_KEY, value ? '1' : '0').catch(() => {});
  }, []);

  const value = useMemo<AppState>(
    () => ({
      content,
      favorites,
      isFavorite: (id) => favorites.includes(id),
      toggleFavorite,
      isPremium,
      setPremium,
    }),
    [content, favorites, toggleFavorite, isPremium, setPremium],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAppState(): AppState {
  const v = useContext(Ctx);
  if (!v) throw new Error('useAppState must be used inside AppStateProvider');
  return v;
}
