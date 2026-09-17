# Credits

## Story and quotations

Biography: original English prose prepared for this project by Codex, grounded in the [Stanford Encyclopedia of Philosophy](https://plato.stanford.edu/entries/simone-weil/), [American Weil Society](https://simoneweilsociety.org/about), [Bibliothèque nationale de France](https://www.bnf.fr/fr/simone-weil-la-pensee-en-action), and the primary writings recorded in [the source register](docs/SOURCES.md).

Quotation author: **Simone Weil (1909–1943)**. All twelve displayed English excerpts are translations prepared for this project by Codex from the linked French originals. No existing English translator is credited for this project’s wording.

| Spreads | French work and checked edition | Editorial status |
| --- | --- | --- |
| 1, 2, 7 | *Attente de Dieu*, La Colombe, 1950 | Letters and essays collected after Weil’s death; childhood, student years, and spiritual experiences are viewed retrospectively. |
| 3, 5 | *La Condition ouvrière*, Gallimard, 1951 | Two excerpts from “Lettre à une élève (1934),” in a posthumous collection. |
| 4 | *Oppression et Liberté*, Gallimard, 1955 | Essay composed in 1934; posthumous edition. |
| 6 | *L’Espagnole*, Abrüpt, 2018 | Modern reprint of the letter to Georges Bernanos, usually dated 1938. |
| 8 | *La Source grecque*, Gallimard, 1953 | The Iliad essay first appeared during Weil’s life, in 1940–1941; the collection is posthumous. |
| 9, 12 | *La Pesanteur et la Grâce*, Plon, 1948 | Notebook extracts selected and arranged by Gustave Thibon; collection first published in 1947. |
| 10 | *L’Enracinement*, Gallimard, 1949 | Written in 1943 and published posthumously. |
| 11 | *Écrits de Londres et dernières lettres*, Gallimard, 1957 | “La Personne et le Sacré,” written in 1943; posthumous collection. |

The source register provides the link, locator, date, and context for each quotation. Source access: **8 September 2026**. Use is limited to short attributed excerpts. Modern editorial introductions, annotations, and published English translations are not included. Keep attribution and links with reused excerpts.

## Visuals, type and sound

- Cover and spine portrait: anonymous photograph of Simone Weil in New York, 1942, [Wikimedia Commons source and public-domain designation](https://commons.wikimedia.org/wiki/File:Simone_Weil_(1909-1943)_portrait.png). Bundled unchanged as `public/textures/simone-weil-portrait.png`; mapped onto the book meshes. Accessed 11 September 2026.
- Spine engraving: generated with the built-in OpenAI image tool as a style transfer of the credited portrait, then resized/encoded as `public/textures/simone-weil-spine.jpg`. Prompt and provenance: [PORTRAIT-ASSET](docs/PORTRAIT-ASSET.md).
- Book and paper scenery: original Blender geometry constructed for this project with reproducible Python scripts. Editable sources and animation conventions accompany the runtime exports.
- Paper and walnut texture maps: generated for this project with OpenAI Image Generation. Exact prompts and processing are recorded in [MATERIALS](docs/MATERIALS.md).
- Bookshop environment: generated image used only as the distant setting; the interactive book remains 3D geometry and casts real rendered shadows. See [BOOKSHOP-ASSET](docs/BOOKSHOP-ASSET.md).
- Paris architectural engraving: original generated albedo artwork printed onto the actual folding wall meshes, with modeled roofs and paper edges. See [ARCHITECTURE-ASSET](docs/ARCHITECTURE-ASSET.md).
- Header ornament: original OpenAI-generated artwork based on the approved design, rendered through a separate Blender silhouette/UV pipeline with baked material relief. Desktop and phone compositions, source files and reproducible scripts are recorded in [HEADER-ASSETS](docs/HEADER-ASSETS.md).
- Cinzel: Natanael Gama and contributors, SIL Open Font License 1.1, distributed locally through [Fontsource](https://fontsource.org/fonts/cinzel); used for the header title.
- Cormorant Garamond: Christian Thalmann and contributors, SIL Open Font License 1.1, distributed through Fontsource.
- Inter: Rasmus Andersson and contributors, SIL Open Font License 1.1, distributed through Fontsource.
- Interface icons: Phosphor Icons, MIT license, through `@phosphor-icons/react`.
- Music: original, quiet Spanish-guitar-inspired synthesized arpeggios in `src/book/audio.ts`, with soft room reflections and filtered-noise page rustle. No external recording or claim about Weil’s personal listening preferences.
- Three.js, React, Vite and supporting libraries retain their respective package licenses. Blender is the authoring tool; no Blender executable is distributed with this site.

The reference images establish visual direction. They are not presented as renders of the implemented book. Scenes are artistic interpretations, not claims to reconstruct undocumented biographical events.

Font and icon license notices are included in `public/licenses/`. Blender cover lettering uses the macOS Baskerville typeface converted to mesh outlines; the font software is not redistributed.

Piano auditions (pending selection): original short compositions rendered with Salamander Grand Piano samples by Alexander Holm, CC BY 3.0. Samples are pitch-shifted, equalized, trimmed and mixed with soft room reflections. See [audio attribution](scripts/audio/LICENSE.md). These are choices for this edition, not documented preferences of Simone Weil. The current website soundtrack is unchanged.

Guitar auditions (pending selection): FreePats Spanish classical guitar by Roberto, version 2019-06-18, CC0 1.0. Original sparse arrangements with softened attacks, filtering, room resonance and fades. [Source and licensing](https://freepats.zenvoid.org/Guitar/acoustic-guitar.html); bundled notice in `public/audio/guitar-previews/LICENSE.md`.
