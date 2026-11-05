# Fonts

Every font or glyph sheet the build reads ends up inside the released patch, so its licence must allow that. One row
per file; a font with no known licence doesn't go into a release.

| File | Source (URL, version) | Licence | Redistributable in a patch | Used for | Changes made |
|---|---|---|---|---|---|
| `fonts/en12.txt` | drawn for this project | MIT, same as repo | yes | all engine text (VWF) | - |
| `fonts/ArchivoNarrow-VF.ttf` | github.com/Omnibus-Type/ArchivoNarrow, via Google Fonts | OFL 1.1 (`fonts/licences/ArchivoNarrow-OFL.txt`) | yes, as rendered glyphs | graphics labels (`tools/gfx.py`), Bold instance | - |
| `fonts/LuckiestGuy-Regular.ttf` | via Google Fonts | Apache 2.0 (`fonts/licences/LuckiestGuy-LICENSE.txt`) | yes, as rendered glyphs | big banners and mode signs | - |
| `fonts/Anton-Regular.ttf` | github.com/googlefonts/AntonFont, via Google Fonts | OFL 1.1 (`fonts/licences/Anton-OFL.txt`) | yes, as rendered glyphs | painted signs | - |
