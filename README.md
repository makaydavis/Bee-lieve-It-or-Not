# Bee-lieve It Or Not?

A browser-based quiz that challenges you to tell bees apart from their look-alikes. View a picture, choose **Bee** or **Not a bee**, and see how many points you can earn.

## Features

- Ten randomly selected pictures per game
- Bee pictures alongside flies and wasps
- Feedback after each answer and a score summary at the end
- A top-10 leaderboard saved locally
- Responsive browser interface; no graphical desktop is required

## Requirements

- Python 3.10 or later
- Tkinter, included with most standard Python installations
- Pillow, installed from `requirements.txt`

## Getting started

Clone the repository and open a terminal in the project folder:

```bash
git clone https://github.com/makaydavis/Bee-lieve-It-or-Not.git
cd Bee-lieve-It-or-Not
python -m pip install -r requirements.txt
python game.py
```

Open `http://localhost:8000` in your browser. In Codespaces, open forwarded port **8000** from the **Ports** tab. Stop the server with Ctrl+C in the terminal.

The server uses Python's built-in HTTP server and does not require Flask or a desktop display. Tkinter and Pillow remain project requirements because the desktop game implementation is kept in `game.py`.

## How to play

1. Select **Start the quiz**.
2. Look at each insect picture and choose **Bee** or **Not a bee**.
3. Continue through the pictures and review your score.
4. Enter your name to save your score to the leaderboard.

Flies and wasps count as **Not a bee**. Each game uses a random selection of available images.

## Project structure

```text
.
├── game.py
├── web_app.py
├── requirements.txt
├── Images/
│   ├── Bees/
│   ├── Flies/
│   └── Wasps/
├── static/
│   ├── app.js
│   └── style.css
├── templates/
│   └── index.html
└── README.md
```

Keep the `Images/Bees`, `Images/Flies`, and `Images/Wasps` folders alongside `game.py`. Supported image files are `.jpg`, `.jpeg`, and `.png`.

## Leaderboard

Scores are saved to `leaderboard.json` in the project folder and remain on that computer. The file is created the first time a score is saved. It is not a shared or online leaderboard.

## Image credits

The quiz uses the images included in the `Images` folders. Before publishing or redistributing the project, check and include the appropriate attribution and license for each image.
