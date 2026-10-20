# The Long Road of Blue

A six-work exhibition built from the [Harvard Art Museums](https://harvardartmuseums.org) collection, plus **Exhibit Builder**, the small app used to make it.

- **`index.html`**: the exhibition. Open it in a browser; no server needed.
- **`app/`**: Exhibit Builder.

## The exhibition

Blue is rare in nature and hard to make. Six objects, oldest first, follow how people made it and how it moved across Asia:

1. Fragment of Egyptian blue on mud, Palace of Sargon II, Assyria, about 715 BCE
2. Jar with cobalt-blue splashes, Tang China, first half of the 700s
3. Cup with Lobed Rim and Human Faces, Iran, 1100s
4. Meiping bottle with a Daoist immortal, Ming China, 1457–1464
5. Dish with Peonies, Timurid Iran, about 1475
6. *Windy Seascape*, Fukami Sueharu, Japan, 2008

Each work has a wall label explaining why it belongs in the show.

## Exhibit Builder

Search the Harvard Art Museums collection by theme, pick up to six works, and lay them out as a timeline, oldest first, with a wall label for each.

### Run

```
python3 app/server.py
```

Then open http://localhost:8765.

You need a free API key from https://harvardartmuseums.org/collections/api. Put it in `app/.env` as `HAM_API_KEY=your-key` (this file is git-ignored) or set the `HAM_API_KEY` environment variable. Without a key, saved exhibits still open but search is turned off.

### Use

1. Type a theme and click **Search collection**. Only works with public images appear.
2. Click **Add to exhibit** on up to six works. They sort themselves by date.
3. Click any title, label, or "Why it's here" text to edit it. Labels for new works start from the museum's own description.
4. Click **Save** to write the exhibit to `app/exhibits/<title>.json`. Click **View as visitor** to hide the editing tools.

"The Long Road of Blue" ships as the first saved exhibit.

To rebuild `index.html` from a saved exhibit:

```
python3 build_index.py "Curator Name" app/exhibits/the-long-road-of-blue.json
```

## Credits

Object data comes from the Harvard Art Museums collection API. Images © President and Fellows of Harvard College.
