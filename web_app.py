from __future__ import annotations

import json
import mimetypes
import os
import random
import secrets
import threading
from dataclasses import dataclass
from http import HTTPStatus
from http.cookies import CookieError, SimpleCookie
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit


BASE_DIR = Path(__file__).resolve().parent
IMAGE_DIR = BASE_DIR / "Images"
LEADERBOARD_FILE = BASE_DIR / "leaderboard.json"
TEMPLATE_FILE = BASE_DIR / "templates" / "index.html"
STATIC_DIR = BASE_DIR / "static"
QUESTIONS_PER_GAME = 10
LEADERBOARD_LIMIT = 10
IMAGE_CATEGORIES = ("Bees", "Flies", "Wasps")
SUPPORTED_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
COOKIE_NAME = "bee_game_session"


@dataclass
class GameSession:
    questions: list[tuple[str, str, bool]]
    index: int = 0
    score: int = 0
    answered: bool = False
    saved: bool = False


SESSIONS: dict[str, GameSession] = {}
SESSIONS_LOCK = threading.Lock()
LEADERBOARD_LOCK = threading.Lock()


def load_questions() -> list[tuple[str, str, bool]]:
    questions: list[tuple[str, str, bool]] = []
    for category, is_bee in (("Bees", True), ("Flies", False), ("Wasps", False)):
        folder = IMAGE_DIR / category
        if not folder.is_dir():
            raise FileNotFoundError(f"Could not find the image folder: {folder}")
        questions.extend(
            (category, image_path.name, is_bee)
            for image_path in sorted(folder.iterdir())
            if image_path.is_file() and image_path.suffix.lower() in SUPPORTED_IMAGE_SUFFIXES
        )

    if not any(is_bee for _, _, is_bee in questions):
        raise ValueError(f"No bee images were found in: {IMAGE_DIR / 'Bees'}")
    if not any(not is_bee for _, _, is_bee in questions):
        raise ValueError(f"No fly or wasp images were found in: {IMAGE_DIR}")
    return questions


def load_leaderboard() -> list[dict[str, str | int]]:
    try:
        with LEADERBOARD_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []
    entries = [
        {"name": entry["name"], "score": entry["score"]}
        for entry in data
        if (
            isinstance(entry, dict)
            and isinstance(entry.get("name"), str)
            and isinstance(entry.get("score"), int)
            and not isinstance(entry.get("score"), bool)
        )
    ]
    return sorted(entries, key=lambda entry: entry["score"], reverse=True)[:LEADERBOARD_LIMIT]


def image_url(question: tuple[str, str, bool]) -> str:
    category, filename, _ = question
    return f"/images/{category}/{filename}"


class BeeRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        path = urlsplit(self.path).path
        if path == "/":
            self.send_file(TEMPLATE_FILE, "text/html; charset=utf-8")
        elif path == "/api/leaderboard":
            self.send_json(HTTPStatus.OK, {"entries": load_leaderboard()})
        elif path == "/api/previews":
            try:
                questions = load_questions()
            except (OSError, ValueError) as error:
                self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
                return
            previews = []
            for category in IMAGE_CATEGORIES:
                category_questions = [item for item in questions if item[0] == category]
                if category_questions:
                    previews.append(image_url(random.choice(category_questions)))
            self.send_json(HTTPStatus.OK, {"images": previews})
        elif path.startswith("/images/"):
            self.serve_image(path)
        elif path in ("/static/app.js", "/static/style.css"):
            filename = path.removeprefix("/static/")
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            self.send_file(STATIC_DIR / filename, content_type)
        elif path == "/favicon.ico":
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
        else:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def do_POST(self) -> None:
        path = urlsplit(self.path).path
        try:
            payload = self.read_json()
        except (ValueError, json.JSONDecodeError) as error:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": str(error)})
            return

        if path == "/api/game":
            self.start_game()
        elif path == "/api/answer":
            self.answer_question(payload)
        elif path == "/api/next":
            self.next_question()
        elif path == "/api/score":
            self.save_score(payload)
        else:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})

    def read_json(self) -> dict[str, object]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Invalid request length") from error
        if length < 0 or length > 16_384:
            raise ValueError("Request is too large")
        if length == 0:
            return {}
        payload = json.loads(self.rfile.read(length))
        if not isinstance(payload, dict):
            raise ValueError("Expected a JSON object")
        return payload

    def session(self, create: bool = False) -> tuple[str | None, GameSession | None, str | None]:
        cookies = SimpleCookie()
        try:
            cookies.load(self.headers.get("Cookie", ""))
        except CookieError:
            pass
        cookie = cookies.get(COOKIE_NAME)
        session_id = cookie.value if cookie else None
        if session_id:
            with SESSIONS_LOCK:
                game = SESSIONS.get(session_id)
            if game is not None:
                return session_id, game, None
        if not create:
            return None, None, None

        session_id = secrets.token_urlsafe(24)
        game = None
        with SESSIONS_LOCK:
            SESSIONS[session_id] = GameSession(questions=[])
        return session_id, game, session_id

    def start_game(self) -> None:
        try:
            questions = load_questions()
        except (OSError, ValueError) as error:
            self.send_json(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(error)})
            return

        session_id, _, new_cookie = self.session(create=True)
        assert session_id is not None
        game = GameSession(
            questions=random.sample(questions, min(QUESTIONS_PER_GAME, len(questions)))
        )
        with SESSIONS_LOCK:
            SESSIONS[session_id] = game
        self.send_json(HTTPStatus.OK, self.question_payload(game), new_cookie)

    def answer_question(self, payload: dict[str, object]) -> None:
        choice = payload.get("is_bee")
        if not isinstance(choice, bool):
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Choose Bee or Not a bee."})
            return
        _, game, _ = self.session()
        if game is None or not game.questions:
            self.send_json(HTTPStatus.CONFLICT, {"error": "Start a game first."})
            return
        if game.answered:
            self.send_json(HTTPStatus.CONFLICT, {"error": "This picture was already answered."})
            return

        is_bee = game.questions[game.index][2]
        correct = choice == is_bee
        if correct:
            game.score += 1
        game.answered = True
        result = {
            "correct": correct,
            "score": game.score,
            "correct_answer": "a bee" if is_bee else "not a bee",
        }
        self.send_json(HTTPStatus.OK, result)

    def next_question(self) -> None:
        _, game, _ = self.session()
        if game is None or not game.questions:
            self.send_json(HTTPStatus.CONFLICT, {"error": "Start a game first."})
            return
        if not game.answered:
            self.send_json(HTTPStatus.CONFLICT, {"error": "Answer this picture first."})
            return

        if game.index + 1 == len(game.questions):
            self.send_json(
                HTTPStatus.OK,
                {"finished": True, "score": game.score, "total": len(game.questions)},
            )
            return

        game.index += 1
        game.answered = False
        self.send_json(HTTPStatus.OK, self.question_payload(game))

    def save_score(self, payload: dict[str, object]) -> None:
        session_id, game, _ = self.session()
        if game is None or not game.questions or not game.answered:
            self.send_json(HTTPStatus.CONFLICT, {"error": "Finish a game before saving a score."})
            return
        if game.index != len(game.questions) - 1:
            self.send_json(HTTPStatus.CONFLICT, {"error": "Finish the round before saving a score."})
            return
        if game.saved:
            self.send_json(HTTPStatus.CONFLICT, {"error": "This score was already saved."})
            return

        name = payload.get("name")
        if not isinstance(name, str) or not name.strip():
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Please enter your name."})
            return
        name = name.strip()
        if len(name) > 20:
            self.send_json(HTTPStatus.BAD_REQUEST, {"error": "Please use 20 characters or fewer."})
            return

        with LEADERBOARD_LOCK:
            entries = load_leaderboard()
            entries.append({"name": name, "score": game.score})
            entries.sort(key=lambda entry: entry["score"], reverse=True)
            entries = entries[:LEADERBOARD_LIMIT]
            try:
                with LEADERBOARD_FILE.open("w", encoding="utf-8") as file:
                    json.dump(entries, file, ensure_ascii=False, indent=2)
            except OSError as error:
                self.send_json(
                    HTTPStatus.INTERNAL_SERVER_ERROR,
                    {"error": f"Could not save the leaderboard: {error}"},
                )
                return
        game.saved = True
        self.send_json(HTTPStatus.OK, {"entries": entries})

    @staticmethod
    def question_payload(game: GameSession) -> dict[str, object]:
        question = game.questions[game.index]
        return {
            "index": game.index + 1,
            "total": len(game.questions),
            "score": game.score,
            "image": image_url(question),
        }

    def serve_image(self, path: str) -> None:
        parts = path.split("/", 3)
        if len(parts) != 4:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        category, filename = parts[2], unquote(parts[3])
        if category not in IMAGE_CATEGORIES or Path(filename).name != filename:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        image_path = IMAGE_DIR / category / filename
        if image_path.suffix.lower() not in SUPPORTED_IMAGE_SUFFIXES or not image_path.is_file():
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        self.send_file(image_path, content_type)

    def send_file(self, path: Path, content_type: str) -> None:
        try:
            content = path.read_bytes()
        except OSError:
            self.send_json(HTTPStatus.NOT_FOUND, {"error": "Not found"})
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(content)

    def send_json(
        self,
        status: HTTPStatus,
        payload: dict[str, object],
        new_cookie: str | None = None,
    ) -> None:
        content = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Cache-Control", "no-store")
        if new_cookie:
            self.send_header(
                "Set-Cookie",
                f"{COOKIE_NAME}={new_cookie}; Path=/; HttpOnly; SameSite=Lax",
            )
        self.end_headers()
        self.wfile.write(content)


def main() -> None:
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), BeeRequestHandler)
    print(f"Bee-lieve It Or Not? is running at http://localhost:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
