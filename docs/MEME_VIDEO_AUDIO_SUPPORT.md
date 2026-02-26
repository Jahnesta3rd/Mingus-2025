# Video and Audio Meme Support

The app supports **video** and **audio** memes in addition to images (GIF, PNG, etc.). They use the **same folder layout and themes** as image memes and are displayed correctly on the vibe-check and meme splash pages.

---

## What was added

| Layer | Change |
|--------|--------|
| **DB** | Migration **006** adds `media_type` (`'image'`, `'video'`, or `'audio'`) to the `memes` table. |
| **Populate script** | Accepts video (`.mp4`, `.webm`, `.mov`, `.ogg`) and audio (`.mp3`, `.wav`, `.ogg`, `.m4a`, `.aac`) files; sets `media_type` from the file extension (or from manifest). |
| **API** | `/api/user-meme` includes `media_type` in the response (from DB or inferred from URL for older rows). |
| **Frontend** | Vibe-check and meme splash render `<video>` or `<audio>` when `media_type` is `video` or `audio`, and `<img>` otherwise. |

---

## Where to put video/audio files (same location and themes)

Use the **same** `memes_source` folder and **same day subfolders** you use for images:

- **sunday_faith** — Sunday, faith  
- **monday_work_life** — Monday, work life  
- **tuesday_friendships** — Tuesday, friendships  
- **wednesday_children** — Wednesday, children  
- **thursday_relationships** — Thursday, relationships  
- **friday_going_out** — Friday, going out  
- **saturday_mixed** — Saturday, mixed  

You can **mix** images, video, and audio in the same folder. For example:

```
memes_source/
  sunday_faith/
    gratitude.gif
    spiritual.mp4
    meditation.mp3
  monday_work_life/
    monday_motivation.png
    focus_work.mp4
  tuesday_friendships/
    friends_01.webm
```

The script infers **day_of_week** and **category** from the folder name for every file (image, video, or audio). No extra setup is required.

---

## Steps to save and use video/audio in the same themes

### 1. Apply the media_type migration (once)

From the repo root:

```bash
sqlite3 mingus_memes.db < migrations/006_meme_media_type.sql
```

If you use `MINGUS_MEME_DB_PATH`:

```bash
sqlite3 "$MINGUS_MEME_DB_PATH" < migrations/006_meme_media_type.sql
```

(The populate script can also add the column automatically if it’s missing.)

### 2. Put video/audio files in the same day folders

- Add **video** (e.g. `.mp4`, `.webm`, `.mov`) and **audio** (e.g. `.mp3`, `.wav`, `.m4a`) into the same subfolders you use for images:
  - `memes_source/sunday_faith/`
  - `memes_source/monday_work_life/`
  - … etc.

- Same theme rules: files in `sunday_faith/` are treated as Sunday + faith; files in `monday_work_life/` as Monday + work_life; and so on.

### 3. Run the populate script (same command as before)

From the repo root:

```bash
python3 scripts/populate_memes_from_files.py memes_source --copy
```

- The script picks up **all** allowed files (images + video + audio) recursively.
- Copies them into **static/memes/** preserving subfolders (e.g. `static/memes/sunday_faith/meditation.mp3`).
- Inserts DB rows with **image_url** = `/memes/<path>` and **media_type** = `image` / `video` / `audio` from the file extension.

Optional: use a manifest CSV to override **media_type**, caption, or other fields. Add a column **media_type** with values `image`, `video`, or `audio`.

### 4. Confirm on the vibe-check page

- Open the app and go through the vibe-check flow.
- When the API returns a meme with `media_type: "video"` or `"audio"`, the page will show a **&lt;video&gt;** or **&lt;audio&gt;** player instead of an image.
- Video and audio memes are chosen the same way as image memes (e.g. by day and random selection).

---

## Supported file types

| Media   | Extensions |
|---------|------------|
| Image   | `.gif`, `.png`, `.jpg`, `.jpeg`, `.webp` |
| Video   | `.mp4`, `.webm`, `.mov`, `.ogg` |
| Audio   | `.mp3`, `.wav`, `.ogg`, `.m4a`, `.aac` |

Note: `.ogg` is treated as **video** by the API when inferring from URL (e.g. for old rows without `media_type`). For audio-only `.ogg`, use a manifest and set **media_type** = `audio`, or rely on the populate script (which sets `media_type` from the extension using its own rules: `.ogg` in `AUDIO_EXTENSIONS` → audio).

---

## Summary

1. Run **migrations/006_meme_media_type.sql** once.  
2. Place **video and audio files** in the same **memes_source/** day subfolders as your image memes.  
3. Run **`python3 scripts/populate_memes_from_files.py memes_source --copy`** so they’re copied to **static/memes/** and inserted with the correct **media_type** and theme (day/category).  
4. The vibe-check and meme splash pages will display them with the right player (**&lt;video&gt;** or **&lt;audio&gt;**). No extra configuration is needed beyond using the same folders and themes as before.
