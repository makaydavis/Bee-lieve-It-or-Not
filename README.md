# Bee-lieve It Or Not?

A desktop quiz game that challenges you to tell bees apart from their look-alikes. View a picture, choose **Bee** or **Not a bee**, and see how many points you can earn.

## Features

- Ten randomly selected pictures per game
- Bee pictures alongside flies and wasps
- One point for each correct answer, with feedback after every guess
- A top-10 leaderboard that saves player names and scores locally

## Requirements

- Python 3.10 or later
- Tkinter, included with most standard Python installations
- Pillow, installed from `requirements.txt`

## Getting started

Clone the repository and open a terminal in the project folder:

```bash
git clone https://github.com/makaydavis/Bee-lieve-It-or-Not.git
cd Bee-lieve-It-or-Not
```

Optionally, create and activate a virtual environment:

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS or Linux:

```bash
source .venv/bin/activate
```

Install the dependency and start the game:

```bash
python -m pip install -r requirements.txt
python game.py
```

On Windows, use `py` in place of `python` if that is how Python is installed on your system.

## How to play

1. Select **Start playing**.
2. Look at each insect picture and choose **Bee** or **Not a bee**.
3. Select **Next picture** to continue.
4. At the end, enter your name and save your score to the leaderboard.

Flies and wasps count as **Not a bee**. Each game uses a random selection of available images.

## Project structure

```text
.
├── game.py
├── requirements.txt
├── Images/
│   ├── Bees/
│   ├── Flies/
│   └── Wasps/
└── README.md
```

Keep the `Images/Bees`, `Images/Flies`, and `Images/Wasps` folders alongside `game.py`. The game loads supported image files (`.jpg`, `.jpeg`, and `.png`) from these folders when it starts.

## Leaderboard

Scores are saved to `leaderboard.json` in the project folder and remain on that computer. The file is created the first time a score is saved. It is not a shared or online leaderboard.

## Image credits

The quiz uses the images included in the `Images` folders. Before publishing or redistributing the project, check and include the appropriate attribution and license for each image.
