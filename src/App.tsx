import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowLeft, ArrowRight, BookOpen, SpeakerHigh, SpeakerSlash, X, ArrowUpRight, ArrowClockwise } from '@phosphor-icons/react';
import { BookHeader } from './BookHeader';
import { chapters } from './content/chapters';
import { BookScene } from './book/BookScene';
import { BookAudio } from './book/audio';
import type { BookSnapshot, Chapter } from './types';

type Panel = 'contents' | 'reading' | 'edition' | null;
const initialState: BookSnapshot = { phase: 'loading', chapter: 0, progress: 0 };
const asset = (path: string) => `${import.meta.env.BASE_URL}${path}`;
const initialReducedMotion = () => {
  const system = matchMedia('(prefers-reduced-motion: reduce)').matches;
  try { return localStorage.getItem('simone-weil-reduced-motion') === 'true' || system; }
  catch { return system; }
};

function ChapterWords({ chapter, sources = false }: { chapter: Chapter; sources?: boolean }) {
  return <>
    <div className="chapter-kicker"><span>{chapter.place}</span><span>{chapter.period}</span></div>
    <h2>{chapter.title}</h2>
    <p className="chapter-paragraph">{chapter.paragraph}</p>
    <blockquote><p>“{chapter.quote.text}”</p><cite>Simone Weil</cite></blockquote>
    {sources && <div className="quotation-source">
      <p><a href={chapter.quote.url} target="_blank" rel="noreferrer">{chapter.quote.work}<ArrowUpRight size={14} /></a></p>
      <p>{chapter.quote.locator}</p>
      <p>{chapter.quote.translation}</p>
      {chapter.quote.note && <p>{chapter.quote.note}</p>}
    </div>}
  </>;
}

export function App() {
  const stageRef = useRef<HTMLDivElement>(null);
  const sceneRef = useRef<BookScene | null>(null);
  const audioRef = useRef(new BookAudio());
  const musicStarted = useRef(false);
  const resumeChapter = useRef<number | undefined>(undefined);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const gesture = useRef<{ x: number; y: number; time: number } | null>(null);
  const [state, setState] = useState<BookSnapshot>(initialState);
  const [fallback, setFallback] = useState(() => new URLSearchParams(location.search).has('read'));
  const [retry, setRetry] = useState(0);
  const [sound, setSound] = useState(false);
  const [audioError, setAudioError] = useState('');
  const [panel, setPanel] = useState<Panel>(null);
  const inspect = import.meta.env.DEV && new URLSearchParams(location.search).has('inspect');
  const [inspectionProgress, setInspectionProgress] = useState('0');
  const [inspectionPaused, setInspectionPaused] = useState(inspect);
  const [metrics, setMetrics] = useState('');
  const [reduced, setReduced] = useState(initialReducedMotion);
  const chapter = chapters[state.chapter];
  const reading = state.phase === 'reading' || state.phase === 'turning' || fallback;
  const busy = !fallback && state.phase !== 'reading';

  useEffect(() => {
    const media = matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => setReduced(media.matches);
    media.addEventListener('change', update);
    return () => media.removeEventListener('change', update);
  }, []);

  useEffect(() => {
    if (fallback || !stageRef.current) return;
    let scene: BookScene | undefined;
    setState(initialState);
    try {
      scene = new BookScene(stageRef.current, {
        chapters,
        initialChapter: resumeChapter.current,
        reducedMotion: reduced,
        onChange: setState,
        onRustle: () => audioRef.current.rustle(),
      });
      sceneRef.current = scene;
      if (inspect) scene.setInspectionProgress(0);
      void scene.init();
      if (import.meta.env.DEV) {
        Object.assign(window, { __bookDebug: { getState: () => scene?.state, getMetrics: () => scene?.getMetrics() } });
      }
    } catch {
      setState({ ...initialState, phase: 'error', error: 'Your browser could not start the 3D edition. The illustrated edition is ready to read.' });
    }
    return () => { scene?.dispose(); sceneRef.current = null; };
  }, [fallback, retry]);

  useEffect(() => { sceneRef.current?.setReducedMotion(reduced); }, [reduced]);

  useEffect(() => () => audioRef.current.dispose(), []);

  useEffect(() => {
    if (!inspect) return;
    const timer = setInterval(() => setMetrics(JSON.stringify(sceneRef.current?.getMetrics() ?? {})), 1000);
    return () => clearInterval(timer);
  }, [inspect]);

  const turn = useCallback((target: number) => {
    if (target < 0 || target >= chapters.length) return;
    if (fallback) setState(previous => ({ ...previous, phase: 'reading', chapter: target, error: undefined }));
    else void sceneRef.current?.goTo(target);
  }, [fallback]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (panel || event.altKey || event.ctrlKey || event.metaKey || event.target instanceof HTMLInputElement) return;
      if (event.key === 'ArrowRight' && reading) { event.preventDefault(); turn(state.chapter + 1); }
      if (event.key === 'ArrowLeft' && reading) { event.preventDefault(); turn(state.chapter - 1); }
      if (event.key === 'Enter' && state.phase === 'closed' && event.target === document.body) openBook();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [panel, reading, state.chapter, state.phase, turn]);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (panel && !dialog.open) dialog.showModal();
    if (!panel && dialog.open) dialog.close();
  }, [panel]);

  const enableSound = async () => {
    musicStarted.current = true;
    try { setSound(await audioRef.current.toggle()); setAudioError(''); }
    catch { setAudioError('Sound is unavailable in this browser. You can continue reading.'); }
  };

  const startMusic = () => {
    if (musicStarted.current) return;
    musicStarted.current = true;
    void audioRef.current.toggle().then(setSound).catch(() => {
      setAudioError('Use the sound control to enable music in this browser.');
    });
  };

  const openBook = (skip = false) => {
    startMusic();
    sceneRef.current?.enter(skip);
  };

  const illustrated = () => {
    startMusic();
    setFallback(true);
    setState(previous => ({ ...previous, phase: 'reading', error: undefined }));
    setPanel(null);
  };

  const retryGraphics = () => {
    resumeChapter.current = state.chapter;
    setFallback(false);
    setRetry(value => value + 1);
  };

  return <main className={`experience ${reading ? 'is-reading' : 'is-closed'} ${fallback ? 'is-illustrated' : ''}`} data-phase={fallback ? 'illustrated' : state.phase} data-chapter={state.chapter + 1}>
    {inspect && <aside className="inspection-tools" aria-label="Development animation inspection">
      <label><input type="checkbox" checked={inspectionPaused} onChange={event => {
        setInspectionPaused(event.target.checked);
        sceneRef.current?.setInspectionProgress(event.target.checked ? Number(inspectionProgress) : null);
      }} /> Hold animation at a frame</label>
      <label>Animation progress <input type="number" min="0" max="1" step="0.01" value={inspectionProgress} onChange={event => {
        setInspectionProgress(event.target.value);
        if (inspectionPaused) sceneRef.current?.setInspectionProgress(Number(event.target.value));
      }} /></label>
      <button onClick={() => sceneRef.current?.inspectContextLoss()}>Simulate graphics loss</button>
      <button onClick={() => sceneRef.current?.resetMetrics()}>Reset measurements</button>
      <output aria-label="Rendering measurements">{metrics}</output>
    </aside>}
    <a className="skip-link" href="#chapter-reading" onClick={() => { if (!reading) illustrated(); }}>Skip to the story</a>
    <BookHeader reading={reading} busy={busy} onAbout={() => setPanel('edition')} onContents={() => setPanel('contents')} />

    {!fallback && <div className="book-stage" ref={stageRef}
      onPointerMove={event => {
        const rect = event.currentTarget.getBoundingClientRect();
        sceneRef.current?.setPointer((event.clientX - rect.left) / rect.width * 2 - 1, (event.clientY - rect.top) / rect.height * 2 - 1);
      }}
      onPointerLeave={() => sceneRef.current?.setPointer(0, 0)}
      onPointerDown={event => { gesture.current = { x: event.clientX, y: event.clientY, time: performance.now() }; }}
      onPointerUp={event => {
        const start = gesture.current;
        gesture.current = null;
        if (!start || panel) return;
        const dx = event.clientX - start.x;
        const dy = event.clientY - start.y;
        if (state.phase === 'closed' && Math.abs(dx) < 12 && Math.abs(dy) < 12) openBook();
        else if (state.phase === 'reading' && Math.abs(dx) > 65 && Math.abs(dx) > Math.abs(dy) * 1.5 && performance.now() - start.time < 1000) turn(state.chapter + (dx < 0 ? 1 : -1));
      }}
      onPointerCancel={() => { gesture.current = null; }} />}

    {state.phase === 'loading' && !fallback && <section className="loading-state" aria-live="polite" aria-label="Loading the book">
      <div className="loading-monogram">SW</div>
      <p>Preparing the pages</p>
      <div className="loading-track" role="progressbar" aria-label="Book loading" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(state.progress * 100)}><span style={{ width: `${Math.max(5, state.progress * 100)}%` }} /></div>
      <button className="quiet-link" onClick={illustrated}>Read the illustrated edition</button>
    </section>}

    {state.phase === 'closed' && !fallback && <section className="invitation">
      <p className="eyebrow">AN EXTRAORDINARY LIFE, UNFOLDING</p>
      <button className="open-book-button" onClick={() => openBook()}><span>Open the book</span><ArrowRight size={25} weight="light" /></button>
      <p className="invitation-note">A story of courage, belonging, and independence.</p>
    </section>}

    {state.phase === 'entering' && !fallback && <button className="skip-entrance text-button" onClick={() => openBook(true)}>Skip opening<ArrowRight size={17} /></button>}

    {state.phase === 'error' && !fallback && <section className="error-state" role="alert">
      <BookOpen size={40} weight="thin" />
      <h1>The story is still here.</h1>
      <p>{state.error}</p>
      <button className="solid-button" onClick={illustrated}>Read the illustrated edition<ArrowRight size={19} /></button>
      <button className="text-button" onClick={retryGraphics}><ArrowClockwise size={18} />Try 3D again</button>
    </section>}

    {reading && <>
      {fallback && <div className="illustrated-stage"><img src={asset(chapter.poster)} alt={`Paper scene for ${chapter.title}`} /><span className="illustrated-label">ILLUSTRATED EDITION</span></div>}
      <article id="chapter-reading" tabIndex={-1} className={`chapter-reading ${fallback ? 'is-visible' : ''}`} aria-label={`Chapter ${chapter.id}: ${chapter.title}`}>
        <ChapterWords chapter={chapter} />
        <button className="source-link" onClick={() => setPanel('reading')}>Quotation & source<ArrowUpRight size={14} /></button>
      </article>
      <footer className="book-footer">
        <nav className="page-navigation" aria-label="Book pages">
          {!fallback && state.chapter === 0
            ? <button className="round-button" aria-label="Return to the closed 3D book" title="Return to the closed book" onClick={() => sceneRef.current?.returnToShelf()} disabled={busy}>3D</button>
            : <button className="round-button" aria-label="Previous chapter" onClick={() => turn(state.chapter - 1)} disabled={busy || state.chapter === 0}><ArrowLeft size={25} weight="light" /></button>}
          {fallback && <button className="return-3d" onClick={retryGraphics} aria-label="Return to the 3D book">3D</button>}
          <button className="page-count" onClick={() => setPanel('contents')} disabled={busy} aria-label={`Chapter ${state.chapter + 1} of 12. Open contents`}><span>{String(state.chapter + 1).padStart(2, '0')}</span><span className="count-line" /><span>12</span></button>
          <button className="round-button" aria-label="Next chapter" onClick={() => turn(state.chapter + 1)} disabled={busy || state.chapter === chapters.length - 1}><ArrowRight size={25} weight="light" /></button>
        </nav>
        <div className="reading-tools">
          <button className="tool-button" onClick={() => setPanel('reading')} aria-label="Read chapter and quotation source"><BookOpen size={22} weight="light" /><span>Read</span></button>
          <button className="tool-button" onClick={() => void enableSound()} aria-label={sound ? 'Mute sound' : 'Enable sound'} aria-pressed={sound}>{sound ? <SpeakerHigh size={22} weight="light" /> : <SpeakerSlash size={22} weight="light" />}<span>Sound {sound ? 'on' : 'off'}</span></button>
        </div>
      </footer>
      <p className="screen-reader" aria-live="polite" aria-atomic="true">{state.phase === 'turning' ? 'Turning the page.' : `Chapter ${state.chapter + 1} of 12: ${chapter.title}.`}</p>
      {(state.error || audioError) && <div className="status-toast" role="status">{state.error || audioError}</div>}
    </>}

    <dialog ref={dialogRef} className={`book-dialog ${panel === 'contents' ? 'contents-dialog' : ''}`} onCancel={() => setPanel(null)} onClick={event => { if (event.target === event.currentTarget) setPanel(null); }}>
      <div className="dialog-paper">
        <button className="dialog-close" aria-label="Close dialog" onClick={() => setPanel(null)}><X size={25} weight="light" /></button>
        {panel === 'contents' && <>
          <p className="eyebrow">THE LIFE OF SIMONE WEIL</p><h2>12 chapters.</h2>
          <p className="dialog-intro">A life lived close to the questions.</p>
          <ol className="contents-list">{chapters.map((item, index) => <li key={item.id}>
            <button aria-current={index === state.chapter ? 'page' : undefined} onClick={() => { turn(index); setPanel(null); }}>
              <span className="contents-number">{String(item.id).padStart(2, '0')}</span><span><strong>{item.title}</strong><small>{item.period}</small></span><ArrowUpRight size={18} weight="light" />
            </button>
          </li>)}</ol>
        </>}
        {panel === 'reading' && <div className="reading-dialog"><p className="eyebrow">CHAPTER {String(chapter.id).padStart(2, '0')} / 12</p><ChapterWords chapter={chapter} sources /></div>}
        {panel === 'edition' && <div className="edition-dialog">
          <p className="eyebrow">ABOUT THIS EDITION</p><h2>Who was Simone Weil?</h2>
          <p>Simone Weil (1909–1943) was a French philosopher, teacher, and writer who wanted to understand how people could live with dignity. She supported workers, took factory jobs, and later helped the Free French in London. Her encounters with poverty, war, and Christianity shaped her writing about justice, attention, and belonging. She died at 34, leaving ideas that still ask us to notice people whose suffering is easily ignored.</p>
          <p>This book’s paper scenes are artistic interpretations. The words beneath each scene connect her experiences to her ideas; the quotations are short translations made for this edition from verified French texts.</p>
          <p>Open any chapter’s reading view to find its quotation, original work, and source. Historical context draws on the <a href="https://plato.stanford.edu/entries/simone-weil/" target="_blank" rel="noreferrer">Stanford Encyclopedia of Philosophy</a> and the <a href="https://simoneweilsociety.org/about" target="_blank" rel="noreferrer">American Weil Society</a>.</p>
          <label className="motion-setting"><input type="checkbox" checked={reduced} onChange={event => {
            setReduced(event.target.checked);
            try { localStorage.setItem('simone-weil-reduced-motion', String(event.target.checked)); } catch { /* The setting still works when storage is unavailable. */ }
          }} /> Reduce motion</label>
          <div className="edition-actions"><button className="solid-button" onClick={fallback ? () => { setPanel(null); retryGraphics(); } : illustrated}>{fallback ? 'Return to the 3D book' : 'Read the illustrated edition'}<ArrowRight size={19} /></button></div>
          <p className="edition-credit">An independent project by Bhavya Khimavat.</p>
        </div>}
      </div>
    </dialog>
  </main>;
}
