export type BriefItem = {
  title: string;
  /** Ne oldu / konu nedir */
  what: string;
  /** Neden önemli */
  why: string;
  /** Sen nasıl kullanırsın */
  howTo: string;
  /** Doğrulanmış kaynak bağlantıları (haber maddelerinde zorunlu) */
  sources?: string[];
};

export type Brief = {
  id: string;
  date: string; // YYYY-MM-DD
  title: string;
  items: BriefItem[];
  premium?: boolean;
};

export type Prompt = {
  id: string;
  category: string;
  title: string;
  description: string;
  /** [KÖŞELİ_PARANTEZ] alanlarını kullanıcı doldurur */
  body: string;
  premium: boolean;
};

export type ContentBundle = {
  version: number;
  sample?: boolean;
  briefs: Brief[];
  prompts: Prompt[];
};
