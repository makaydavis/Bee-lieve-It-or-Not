from __future__ import annotations

import json
import random
import tkinter as tk
from pathlib import Path
from tkinter import messagebox
from typing import Callable, TypedDict

try:
    from PIL import Image, ImageOps, ImageTk
except ImportError as error:
    raise SystemExit(
        "Bee-lieve It Or Not? needs Pillow to display its JPEG images.\n"
        "Install it by running: pip install -r requirements.txt"
    ) from error


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "Images"
LEADERBOARD_FILE = BASE_DIR / "leaderboard.json"
QUESTIONS_PER_GAME = 10
LEADERBOARD_LIMIT = 10
IMAGE_SIZE = (680, 360)

BACKGROUND = "#fff9e9"
CARD = "#ffffff"
INK = "#263238"
MUTED = "#65737b"
HONEY = "#f4b400"
HONEY_DARK = "#d99700"
GREEN = "#24845b"
RED = "#c34b3c"


class LeaderboardEntry(TypedDict):
    name: str
    score: int


def load_questions() -> list[tuple[Path, bool]]:
    questions: list[tuple[Path, bool]] = []
    for folder_name, is_bee in (("Bees", True), ("Flies", False), ("Wasps", False)):
        folder = IMAGE_DIR / folder_name
        if not folder.is_dir():
            raise FileNotFoundError(f"Could not find the image folder:\n{folder}")
        questions.extend(
            (image_path, is_bee)
            for image_path in folder.iterdir()
            if image_path.is_file() and image_path.suffix.lower() in {".jpg", ".jpeg", ".png"}
        )

    if not any(is_bee for _, is_bee in questions):
        raise ValueError(f"No bee images were found in:\n{IMAGE_DIR / 'Bees'}")
    if not any(not is_bee for _, is_bee in questions):
        raise ValueError(f"No fly or wasp images were found in:\n{IMAGE_DIR}")
    return questions


def load_leaderboard() -> list[LeaderboardEntry]:
    if not LEADERBOARD_FILE.exists():
        return []

    try:
        with LEADERBOARD_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        messagebox.showwarning(
            "Leaderboard could not be loaded",
            f"The saved leaderboard could not be read:\n{error}\n\n"
            "A new leaderboard will be used for this game.",
        )
        return []

    if not isinstance(data, list):
        messagebox.showwarning(
            "Leaderboard could not be loaded",
            "The saved leaderboard has an unexpected format. A new leaderboard "
            "will be used for this game.",
        )
        return []

    entries: list[LeaderboardEntry] = []
    invalid_entries = 0
    for entry in data:
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("name"), str)
            and isinstance(entry.get("score"), int)
            and not isinstance(entry.get("score"), bool)
        ):
            entries.append({"name": entry["name"], "score": entry["score"]})
        else:
            invalid_entries += 1
    if invalid_entries:
        messagebox.showwarning(
            "Leaderboard entries skipped",
            f"{invalid_entries} saved leaderboard entry or entries had an unexpected "
            "format and were skipped.",
        )
    return sorted(entries, key=lambda entry: entry["score"], reverse=True)[:LEADERBOARD_LIMIT]


class BeeGame:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.all_questions = load_questions()
        self.leaderboard = load_leaderboard()
        self.questions: list[tuple[Path, bool]] = []
        self.question_index = 0
        self.score = 0
        self.answered = False
        self.current_photo: ImageTk.PhotoImage | None = None

        self.root.title("Bee-lieve It Or Not?")
        self.root.configure(bg=BACKGROUND)
        self.root.minsize(720, 680)
        self.root.geometry("900x760")
        self.show_home()

    def clear_screen(self) -> None:
        for child in self.root.winfo_children():
            child.destroy()

    def add_bee_decorations(self) -> None:
        for side in ("left", "right"):
            canvas = tk.Canvas(
                self.root,
                bg=BACKGROUND,
                highlightthickness=0,
                borderwidth=0,
            )
            if side == "left":
                canvas.place(x=0, y=0, width=110, relheight=1)
            else:
                canvas.place(relx=1, y=0, width=110, relheight=1, anchor="ne")
            canvas.bind(
                "<Configure>",
                lambda event, target=canvas: self.draw_bee_decorations(target)
                if event.width and event.height
                else None,
            )

    @staticmethod
    def draw_cartoon_bee(
        canvas: tk.Canvas,
        center_x: float,
        center_y: float,
        scale: float,
        direction: int,
    ) -> None:
        def x(offset: float) -> float:
            return center_x + offset * scale * direction

        def y(offset: float) -> float:
            return center_y + offset * scale

        outline = "#493817"
        canvas.create_oval(
            x(-13), y(-24), x(7), y(1),
            fill="#d9eff5", outline="#93bdc7", width=1.5, tags="bee",
        )
        canvas.create_oval(
            x(-3), y(-26), x(17), y(-2),
            fill="#eaf7f7", outline="#93bdc7", width=1.5, tags="bee",
        )
        canvas.create_line(
            [x(-24), y(10), x(-32), y(20), x(-39), y(17)],
            fill=outline, width=2, smooth=True, tags="bee",
        )
        canvas.create_line(
            [x(-10), y(14), x(-15), y(24), x(-22), y(22)],
            fill=outline, width=2, smooth=True, tags="bee",
        )
        canvas.create_line(
            [x(2), y(14), x(0), y(24), x(-7), y(24)],
            fill=outline, width=2, smooth=True, tags="bee",
        )
        canvas.create_polygon(
            x(-34), y(-5), x(-27), y(0), x(-34), y(5),
            fill=HONEY, outline=outline, width=1.5, tags="bee",
        )
        canvas.create_oval(
            x(-30), y(-15), x(14), y(15),
            fill=HONEY, outline=outline, width=2, tags="bee",
        )
        for stripe_x in (-18, -5):
            half_height = 12 * (1 - (stripe_x / 22) ** 2) ** 0.5
            canvas.create_polygon(
                x(stripe_x - 2.5), y(-half_height),
                x(stripe_x + 2.5), y(-half_height),
                x(stripe_x + 2.5), y(half_height),
                x(stripe_x - 2.5), y(half_height),
                fill=outline, outline="", tags="bee",
            )
        canvas.create_oval(
            x(8), y(-10), x(28), y(10),
            fill="#ffd65a", outline=outline, width=1.5, tags="bee",
        )
        canvas.create_oval(
            x(19), y(-5), x(22), y(-2),
            fill=outline, outline=outline, tags="bee",
        )
        canvas.create_line(
            [x(19), y(-9), x(23), y(-16), x(27), y(-17)],
            fill=outline, width=1.5, smooth=True, tags="bee",
        )
        canvas.create_line(
            [x(11), y(-10), x(12), y(-17), x(16), y(-19)],
            fill=outline, width=1.5, smooth=True, tags="bee",
        )

    def draw_bee_decorations(self, canvas: tk.Canvas) -> None:
        width = canvas.winfo_width()
        height = canvas.winfo_height()
        if width < 100 or height < 100:
            return

        canvas.delete("bee")
        scale = min(height / 760, (width - 12) / 70, 1.0)
        center_x = width / 2
        self.draw_cartoon_bee(canvas, center_x, height * 0.30, scale * 0.82, 1)
        self.draw_cartoon_bee(canvas, center_x, height * 0.70, scale * 0.66, -1)

    def make_card(self) -> tk.Frame:
        return tk.Frame(self.root, bg=CARD, padx=32, pady=28)

    def show_home(self) -> None:
        self.clear_screen()
        self.add_bee_decorations()
        content = tk.Frame(self.root, bg=BACKGROUND)
        content.pack(expand=True, fill="both", padx=110, pady=40)

        tk.Label(
            content,
            text="Bee-lieve It Or Not?",
            font=("Segoe UI", 34, "bold"),
            fg=INK,
            bg=BACKGROUND,
        ).pack(pady=(60, 10))
        tk.Label(
            content,
            text="Can you tell a bee from a look-alike?",
            font=("Segoe UI", 16),
            fg=MUTED,
            bg=BACKGROUND,
        ).pack(pady=(0, 24))

        card = self.make_card()
        card.pack(pady=18)
        tk.Label(
            card,
            text=f"{QUESTIONS_PER_GAME} pictures  ·  1 point for each correct answer",
            font=("Segoe UI", 13),
            fg=INK,
            bg=CARD,
        ).pack(pady=(0, 20))
        self.make_button(card, "Start playing", self.start_game, HONEY, INK).pack(
            ipadx=28, ipady=10
        )

        self.show_leaderboard(content, heading="Top players")

    def start_game(self) -> None:
        self.questions = random.sample(
            self.all_questions, min(QUESTIONS_PER_GAME, len(self.all_questions))
        )
        self.question_index = 0
        self.score = 0
        self.show_question()

    def show_question(self) -> None:
        self.clear_screen()
        self.add_bee_decorations()
        self.answered = False

        content = tk.Frame(self.root, bg=BACKGROUND)
        content.pack(expand=True, fill="both", padx=110, pady=24)
        header = tk.Frame(content, bg=BACKGROUND)
        header.pack(fill="x", pady=(0, 14))

        total = len(self.questions)
        tk.Label(
            header,
            text=f"QUESTION {self.question_index + 1} OF {total}",
            font=("Segoe UI", 11, "bold"),
            fg=MUTED,
            bg=BACKGROUND,
        ).pack(side="left")
        tk.Label(
            header,
            text=f"Score: {self.score}",
            font=("Segoe UI", 12, "bold"),
            fg=INK,
            bg=BACKGROUND,
        ).pack(side="right")

        card = self.make_card()
        card.pack(expand=True, fill="both")
        tk.Label(
            card,
            text="Is this a bee?",
            font=("Segoe UI", 24, "bold"),
            fg=INK,
            bg=CARD,
        ).pack(pady=(0, 14))

        image_path, _ = self.questions[self.question_index]
        try:
            with Image.open(image_path) as image:
                display_image = ImageOps.contain(
                    image.convert("RGB"),
                    IMAGE_SIZE,
                    method=Image.Resampling.LANCZOS,
                )
            self.current_photo = ImageTk.PhotoImage(display_image)
        except OSError as error:
            messagebox.showerror(
                "Could not open image",
                f"The image could not be displayed:\n{image_path}\n\n{error}",
            )
            self.root.destroy()
            return

        image_label = tk.Label(card, image=self.current_photo, bg=CARD)
        image_label.pack(expand=True, pady=(0, 12))

        self.feedback = tk.Label(
            card,
            text="",
            font=("Segoe UI", 13, "bold"),
            bg=CARD,
            fg=INK,
        )
        self.feedback.pack(pady=(0, 10))

        buttons = tk.Frame(card, bg=CARD)
        buttons.pack()
        self.answer_buttons: list[tk.Button] = []
        for text, answer in (("Bee", True), ("Not a bee", False)):
            button = self.make_button(
                buttons,
                text,
                lambda choice=answer: self.answer(choice),
                HONEY if answer else "#e8eef0",
                INK,
            )
            button.pack(side="left", padx=8, ipadx=24, ipady=10)
            self.answer_buttons.append(button)

        self.next_button = self.make_button(
            card, "Next picture", self.next_question, "#263238", "#ffffff"
        )

    def answer(self, choice: bool) -> None:
        if self.answered:
            return
        self.answered = True
        correct_answer = self.questions[self.question_index][1]
        for button in self.answer_buttons:
            button.configure(state="disabled")

        if choice == correct_answer:
            self.score += 1
            self.feedback.configure(text="That's right! +1 point", fg=GREEN)
        else:
            answer_text = "a bee" if correct_answer else "not a bee"
            self.feedback.configure(text=f"Not quite — this is {answer_text}.", fg=RED)

        self.next_button.pack(pady=(2, 0), ipadx=16, ipady=8)

    def next_question(self) -> None:
        self.question_index += 1
        if self.question_index >= len(self.questions):
            self.show_game_over()
        else:
            self.show_question()

    def show_game_over(self, score_saved: bool = False) -> None:
        self.clear_screen()
        self.add_bee_decorations()
        content = tk.Frame(self.root, bg=BACKGROUND)
        content.pack(expand=True, fill="both", padx=110, pady=24)

        card = self.make_card()
        card.pack(expand=True, fill="both")
        tk.Label(
            card,
            text="Game over!",
            font=("Segoe UI", 27, "bold"),
            fg=INK,
            bg=CARD,
        ).pack(pady=(8, 4))
        tk.Label(
            card,
            text=f"You got {self.score} out of {len(self.questions)} correct.",
            font=("Segoe UI", 16),
            fg=MUTED,
            bg=CARD,
        ).pack(pady=(0, 18))

        if score_saved:
            tk.Label(
                card,
                text="Your score has been saved!",
                font=("Segoe UI", 13, "bold"),
                fg=GREEN,
                bg=CARD,
            ).pack(pady=(4, 8))
        else:
            tk.Label(
                card,
                text="Add your name to the leaderboard",
                font=("Segoe UI", 13, "bold"),
                fg=INK,
                bg=CARD,
            ).pack(pady=(4, 8))
            form = tk.Frame(card, bg=CARD)
            form.pack()
            self.name_entry = tk.Entry(form, font=("Segoe UI", 13), width=22)
            self.name_entry.pack(side="left", padx=(0, 8), ipady=5)
            self.make_button(form, "Save score", self.save_score, HONEY, INK).pack(
                side="left", ipadx=10, ipady=5
            )
            self.name_error = tk.Label(card, text="", font=("Segoe UI", 10), fg=RED, bg=CARD)
            self.name_error.pack(pady=(4, 0))

        self.show_leaderboard(card, heading="Leaderboard")
        self.make_button(card, "Play again", self.start_game, "#263238", "#ffffff").pack(
            pady=(16, 0), ipadx=18, ipady=8
        )

    def save_score(self) -> None:
        name = self.name_entry.get().strip()
        if not name:
            self.name_error.configure(text="Please enter your name.")
            self.name_entry.focus_set()
            return
        if len(name) > 20:
            self.name_error.configure(text="Please use 20 characters or fewer.")
            self.name_entry.focus_set()
            return

        updated_leaderboard = self.leaderboard + [{"name": name, "score": self.score}]
        updated_leaderboard.sort(key=lambda entry: entry["score"], reverse=True)
        updated_leaderboard = updated_leaderboard[:LEADERBOARD_LIMIT]
        try:
            with LEADERBOARD_FILE.open("w", encoding="utf-8") as file:
                json.dump(updated_leaderboard, file, ensure_ascii=False, indent=2)
        except OSError as error:
            messagebox.showerror(
                "Could not save score",
                f"The score could not be saved to:\n{LEADERBOARD_FILE}\n\n{error}",
            )
            return

        self.leaderboard = updated_leaderboard
        self.show_game_over(score_saved=True)

    def show_leaderboard(self, parent: tk.Widget, heading: str) -> None:
        section_background = str(parent.cget("bg"))
        section = tk.Frame(parent, bg=section_background)
        section.pack(pady=(14, 0))
        tk.Label(
            section,
            text=heading,
            font=("Segoe UI", 16, "bold"),
            fg=INK,
            bg=section_background,
        ).pack(pady=(0, 6))

        if not self.leaderboard:
            tk.Label(
                section,
                text="No scores yet — be the first!",
                font=("Segoe UI", 11),
                fg=MUTED,
                bg=section_background,
            ).pack()
            return

        for rank, entry in enumerate(self.leaderboard, start=1):
            tk.Label(
                section,
                text=f"{rank}.  {entry['name']}  —  {entry['score']} points",
                font=("Segoe UI", 11),
                fg=INK,
                bg=section_background,
            ).pack(anchor="w", pady=1)

    @staticmethod
    def make_button(
        parent: tk.Widget,
        text: str,
        command: Callable[[], None],
        background: str,
        foreground: str,
    ) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI", 12, "bold"),
            bg=background,
            fg=foreground,
            activebackground=HONEY_DARK,
            activeforeground=INK,
            relief="flat",
            borderwidth=0,
            cursor="hand2",
        )


def main() -> None:
    root = tk.Tk()
    try:
        BeeGame(root)
    except (OSError, ValueError) as error:
        messagebox.showerror("Could not start game", str(error))
        root.destroy()
        return
    root.mainloop()


if __name__ == "__main__":
    main()
