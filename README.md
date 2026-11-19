# Happiness through volunteering

This is the slide deck for the Sustainable Happiness assignment by Vedansh and Tohraan.

The live deck is at https://happiness-through-volunteering.vercel.app. Press **F** for full screen and **→** to go forward.

## How the deck is made

You don't edit `index.html` by hand. A script **generates** it, so any edit you make there directly is lost the next time the script runs.

| What you want to change | Where it lives |
|---|---|
| Wording on a slide (headlines, cards, captions) | Search for the words in `build/game.py` first. If they aren't there, look in `build/index.before-game.html`. |
| Speaker notes | Inside `<aside class="notes">…</aside>` in the same two files |
| Which photo goes in which frame | The `PAIRS` dict and the `evidence(...)` calls in `build/game.py` |
| Photos | `images/`: Vedansh's real photos (`blood-*`, `langar-*`, `run-*`) and Tohraan's geotagged ones (`images/placeholders/t-*`) |
| Look and animation | `build/game.css` and `build/game.js` |

## Edit, then preview

You need Python 3.

```sh
python3 build/game.py          # rebuild index.html from the source files
open index.html                # check it in your browser
```

To find where a piece of text lives, run `grep -rn "the words" build/game.py build/index.before-game.html`.

## PDF and PowerPoint (optional)

The export scripts need `pip install playwright python-pptx pillow` and then `playwright install chromium`.

```sh
python3 build/export.py        # makes Sustainable-Happiness-Project.pdf (flat image slides)
python3 build/pptx_editable.py # makes the editable PowerPoint
```

## Publishing

Commit and push your changes. Tohraan runs `build/deploy.sh`, which updates the live link and needs his Vercel login.
