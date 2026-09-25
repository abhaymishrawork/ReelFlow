# Fonts

The engine searches this folder first, then the system font folders. A stack entry like
`PlayfairDisplay-Italic-VF.ttf@Bold Italic` selects a named instance of a variable font.

These files are bundled here. They come from the google/fonts repo and use the SIL Open Font License:

| File | Instances used | Styles |
|---|---|---|
| `PlayfairDisplay-Italic-VF.ttf` | Italic, Bold Italic | aura, dyn-storyline, ml-aura |
| `GreatVibes-Regular.ttf` | - | dyn-quill |
| `GochiHand-Regular.ttf` | - | chalk, monument |
| `CabinSketch-Bold.ttf` | - | chalk (hero) |
| `DancingScript-VF.ttf` | Bold | ml-blockbuster, play-cursive |
| `Inter-VF.ttf` | Regular, Medium | liquid-glass, dyn-quill, dyn-storyline |
| `LibreCaslonText-VF.ttf` | Regular | sunburst |

These fonts are expected to be installed system-wide: Poppins, Anton, Montserrat and Helvetica Neue. Anton,
Poppins and Montserrat are free on Google Fonts. Helvetica Neue falls back to Archivo Black, Arial Black or Arial.
