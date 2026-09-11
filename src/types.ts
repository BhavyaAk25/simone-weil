export interface Quotation {
  text: string;
  work: string;
  locator: string;
  translation: string;
  url: string;
  note?: string;
}

export interface Chapter {
  id: number;
  slug: string;
  title: string;
  period: string;
  place: string;
  idea: string;
  paragraph: string;
  quote: Quotation;
  scene: string;
  poster: string;
}

export type BookPhase = 'loading' | 'closed' | 'entering' | 'reading' | 'turning' | 'error';

export interface BookSnapshot {
  phase: BookPhase;
  chapter: number;
  progress: number;
  error?: string;
}
