# Hand Frame FX 🎬✋

A webcam app where you frame a shot with both hands — the four fingertips
(index + thumb of each hand) draw a live quadrilateral, and a stylized visual
effect renders **only inside that shape**, composited over the real-time
camera feed.

![Effects contact sheet](effects_contact_sheet.png)

## Effects

| # | Name | Look |
|---|------|------|
| 1 | **comic** | Pop-art posterize with a red → orange → yellow → white gradient |
| 2 | **paper** | Black ink outlines over dotted stipple shading on warm cream paper |
| 3 | **grid** | Greyscale subject under a crisp technical grid |
| 4 | **pixel glass** | Frosted, saturated base broken into chunky glass tiles |

## How it works

- **MediaPipe Hands** detects both hands and reports the index-tip and
  thumb-tip position for each — no strict pose/angle gate, so a loose L, a
  claw, or an open palm all work.
- The four points form a quadrilateral (`cv2.convexHull`), which becomes a
  mask. The current effect renders only inside that mask, hard-edged, over
  the live frame.
- Corner points are smoothed (EMA) to kill jitter, and the last known shape
  is held for a few frames on brief tracking dropouts.
- **Switch effects hands-free**: bring your two hands close together and
  the effect advances automatically — handy for recording without breaking
  the shot to hit a key. Space bar also works.

## Requirements

- **Windows, Mac, or Linux** with a working webcam
- **Python 3.9, 3.10, or 3.11** (MediaPipe does not yet fully support 3.12+)

## Setup

Clone the repo, then from inside the project folder:

```bash
python -m venv venv
```

Activate the environment:

```bash
# Windows
venv\Scripts\activate

# Mac/Linux
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

## Run it

```bash
python hand_frame_fx.py
```

Hold both hands up like you're framing a shot. A quadrilateral appears
between your fingertips with an effect rendered inside it.

## Controls

| Key | Action |
|---|---|
| `space` | advance to the next effect |
| bring both hands close together | also advances to the next effect (hands-free) |
| `r` | start/stop recording an `.mp4` next to the script |
| `l` | toggle hand-landmark debug overlay |
| `q` | quit (finalizes any in-progress recording cleanly) |

Recordings are timestamped `.mp4` files (falls back to `.avi`/XVID if mp4
isn't supported on your system) saved in the project folder. The FPS
counter and "REC" badge are drawn only on-screen — they're never baked into
the saved file, and playback speed is locked to real time.

## Regenerate the contact sheet

Applies all 4 effects to a source image and tiles them side-by-side into
`effects_contact_sheet.png`:

```bash
python make_contact_sheet.py            # synthetic demo scene
python make_contact_sheet.py cam        # grabs one live webcam frame
python make_contact_sheet.py path/to/photo.jpg
```

## Project structure

```
hand-frame-fx/
├── hand_frame_fx.py         # main webcam app
├── make_contact_sheet.py    # effect preview generator
├── requirements.txt         # pinned dependencies
├── effects_contact_sheet.png
└── README.md
```

## Troubleshooting

- **Camera won't open**: the script auto-tries camera indices 0–4. If it
  still fails, close other apps using the camera (Zoom, Teams) and check
  your OS camera privacy permissions.
- **MediaPipe import errors**: make sure you installed via
  `requirements.txt` and didn't let pip pull a newer MediaPipe — versions
  0.10.30+ removed the API this project depends on.
- **PowerShell blocks `venv\Scripts\activate`**: run
  `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, or use
  Command Prompt instead.
