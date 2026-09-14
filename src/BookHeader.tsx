import { useState } from 'react';
import { List } from '@phosphor-icons/react';
import '@fontsource/cinzel/latin-400.css';
import './BookHeader.css';

type Props = {
  reading: boolean;
  busy: boolean;
  onAbout: () => void;
  onContents: () => void;
};

const asset = (file: string) => `${import.meta.env.BASE_URL}textures/${file}`;

export function BookHeader({ reading, busy, onAbout, onContents }: Props) {
  const [artworkReady, setArtworkReady] = useState(false);

  return <header className={`book-header${artworkReady ? ' has-artwork' : ''}`}>
    <picture className="book-header-art" aria-hidden="true">
      <source media="(max-width: 760px)" srcSet={asset('header-mobile.webp')} />
      <img src={asset('header-desktop.webp')} alt="" width="3344" height="343" fetchPriority="high"
        draggable={false} onLoad={() => setArtworkReady(true)} onError={() => setArtworkReady(false)} />
    </picture>
    <div className="book-header-content">
      <button className="book-header-wordmark" onClick={onAbout} aria-label="About The Life of Simone Weil">
        <span>SIMONE WEIL</span><small>A LIFE IN 12 CHAPTERS</small>
      </button>
      <div className="book-header-actions">
        <span className="book-header-dates">1909 — 1943</span>
        {reading
          ? <button className="book-header-link" onClick={onContents} disabled={busy} aria-label="Contents">
            <List size={24} weight="light" /><span>Contents</span>
          </button>
          : <button className="book-header-link book-header-about" onClick={onAbout} aria-label="About this edition">
            <span>About<span className="book-header-about-detail"> this edition</span></span>
          </button>}
      </div>
    </div>
  </header>;
}
