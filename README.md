# The Life of Simone Weil

[Open the published book](https://bhavyaak25.github.io/simone-weil/) · [Source repository](https://github.com/BhavyaAk25/simone-weil)

A twelve-chapter interactive biography built as a real 3D pop-up book. Blender authors the leather book, paper scenes and baked hinges; Three.js renders them in a Vite, React and TypeScript website. Each spread pairs original English prose with a short attributed project translation of Simone Weil.

## Run locally

Requirements: Node.js 22.12 or newer, npm, and a browser with WebGL 2 for the animated edition. The illustrated edition works without 3D rendering.

```sh
npm ci
npm run dev -- --port 4173
```

Open `http://localhost:4173/simone-weil/`. Click the spine or the opening button, tap, or press Enter. Navigate with the arrows, horizontal swipes or the contents. Music starts with the opening click, tap or Enter and can be muted. A visible 3D control returns from the illustrated edition to the same chapter. Reduced-motion preferences bypass the entrance and page animations.

`?read` opens the illustrated edition directly. In development only, `?inspect` exposes a frame-position control and rendering measurements for inspecting the real entrance and turn sequence. Set progress to `0`, start an animation, then advance to a value between `0` and `1`. Uncheck the frame hold to run normally. These tools are excluded from the production interface.

## Build and verify

```sh
npm run typecheck
npm test
npm run validate:assets
npm run build
npm run test:sites
npm run preview -- --port 4173
```

During the first two-spread milestone use `npm run validate:assets -- --milestone`. The release check requires all twelve chapter GLBs, source Blender files, and fallback posters. The validator samples binary geometry through animation poses; browser checks are still required to detect visual discontinuities, readability and input failures. See [QA](docs/QA.md) for observed results and remaining checks.

The static output is **`dist/client`**, with base path **`/simone-weil/`**. The build also preserves the starter's optional Sites artifacts under `dist/server` and `dist/.openai`.

## Blender source and exports

Blender 5.1 was used for the source scenes. Rebuild the first working milestone on macOS with:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup --python scripts/blender/build_book.py -- --milestone
```

The script also accepts `--book` and `--chapters 1 2 3 4 5 6 7 8 9 10 11 12`. Runtime exports go to `public/models`, posters to `public/posters`, and editable scenes to `assets/source`. See [PIPELINE](docs/PIPELINE.md) before modifying coordinate conventions or animation names.

`.blend` sources use Git LFS. Run `git lfs install` before committing sources and `git lfs pull` after cloning. Optimized GLBs, textures and posters are ordinary Git files, directly usable by static hosting.

## Project organization

- `src/`: application, typed story manifest, browser renderer and motion schedules.
- `scripts/blender/`: reproducible model construction and export.
- `assets/source/`: editable Blender sources.
- `public/models/`, `public/textures/`, `public/posters/`: deployable assets.
- `docs/`: agreed brief, user corrections, story research, pipeline, plan and verification.
- `tests/`: focused transition, content and asset checks; preserved Sites worker checks.

The shared rules and ownership are in [AGENTS.md](AGENTS.md). The rejected initial prototype and required corrections are recorded in [REVISION](docs/REVISION.md), so future work preserves the user's intent.

## Publication

Published to the public repository `BhavyaAk25/simone-weil` and GitHub Pages. Every push to `main` runs type checking, tests, all thirteen asset validations, a production build and packaging checks before deploying `dist/client`. The first successful deployment and live-browser checks are recorded in [QA](docs/QA.md).

No account, backend, visitor API, paid service or custom domain is required. See [CREDITS](CREDITS.md) and the [source register](docs/SOURCES.md) for assets and quotations. Physical-phone performance must be measured on a real device; mobile browser dimensions on a desktop are not a phone benchmark.
