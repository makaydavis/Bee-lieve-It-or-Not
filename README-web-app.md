# Bee-lieve It Or Not? — Web App

The web app is a browser-based insect quiz served by Python's built-in HTTP
server. It does not need Flask or a graphical desktop.

## Requirements

- Python 3.10 or later
- The project files, including the `Images`, `static`, and `templates` folders

The web app uses only Python's standard library. Pillow and Tkinter are used by
the separate desktop game, not by the web app.

## Run locally

From the repository folder:

```bash
python web_app.py
```

Open [http://localhost:8000](http://localhost:8000) in a browser. Stop the
server with **Ctrl+C** in the terminal.

To use a different port, set the `PORT` environment variable. For example, on
Linux or macOS:

```bash
PORT=8080 python web_app.py
```

Then open `http://localhost:8080`.

### GitHub Codespaces

Run `python web_app.py`, then open port **8000** from the **Ports** tab. Use
the forwarded URL to play in your browser.

## Play

1. Select **Start the quiz**.
2. For each picture, choose **Bee** or **Not a bee**.
3. Answer all ten questions to see your score.
4. Enter a name to save your score to the leaderboard.

The quiz selects up to ten random images from the available bee, fly, and wasp
images. Flies and wasps count as **Not a bee**. The leaderboard keeps the top
ten scores in `leaderboard.json` on the computer running the app; it is not
shared between separate installations or servers.

## Project files

- [`web_app.py`](./web_app.py) — web server and game API
- [`templates/index.html`](./templates/index.html) — page markup
- [`static/app.js`](./static/app.js) — browser game behavior
- [`static/style.css`](./static/style.css) — page styling
- [`Images/`](./Images/) — quiz images, organized into `Bees`, `Flies`, and
  `Wasps`
- `leaderboard.json` — created in the project folder when a score is saved

The app supports `.jpg`, `.jpeg`, and `.png` images in the three image
categories. Keep the image folders alongside `web_app.py`.

## Image credits

Before publishing or redistributing the project, check and include the
appropriate attribution and license for each image in the `Images` folders.
