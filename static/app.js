const homeView = document.querySelector("#home-view");
const gameView = document.querySelector("#game-view");
const resultsView = document.querySelector("#results-view");
const notice = document.querySelector("#notice");
const startButton = document.querySelector("#start-button");
const answerButtons = [...document.querySelectorAll(".answer-button")];
const nextButton = document.querySelector("#next-button");
let finalScore = 0;

async function request(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
  });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

function showNotice(message = "") {
  notice.textContent = message;
  notice.hidden = !message;
}

function renderLeaderboard(element, entries) {
  element.replaceChildren();
  if (!entries.length) {
    const empty = document.createElement("li");
    empty.className = "empty-ranking";
    empty.textContent = "No scores yet. Make the first mark.";
    element.append(empty);
    return;
  }
  entries.forEach((entry, index) => {
    const row = document.createElement("li");
    const rank = document.createElement("span");
    const name = document.createElement("span");
    const score = document.createElement("span");
    rank.className = "rank-number";
    name.className = "rank-name";
    score.className = "rank-score";
    rank.textContent = String(index + 1).padStart(2, "0");
    name.textContent = entry.name;
    score.textContent = `${entry.score} pts`;
    row.append(rank, name, score);
    element.append(row);
  });
}

async function refreshLeaderboard() {
  const { entries } = await request("/api/leaderboard");
  renderLeaderboard(document.querySelector("#home-leaderboard"), entries);
  renderLeaderboard(document.querySelector("#results-leaderboard"), entries);
}

async function loadPreviews() {
  const { images } = await request("/api/previews");
  const labels = ["BEE", "FLY", "WASP"];
  const board = document.querySelector("#preview-board");
  board.replaceChildren();
  images.forEach((src, index) => {
    const frame = document.createElement("div");
    const image = document.createElement("img");
    const label = document.createElement("span");
    frame.className = "preview-photo";
    image.src = src;
    image.alt = `${labels[index]} specimen`;
    image.loading = "lazy";
    label.className = "preview-label";
    label.textContent = labels[index];
    frame.append(image, label);
    board.append(frame);
  });
}

function showView(view) {
  homeView.hidden = view !== "home";
  gameView.hidden = view !== "game";
  resultsView.hidden = view !== "results";
  showNotice();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderQuestion(question) {
  document.querySelector("#question-count").innerHTML = `${String(question.index).padStart(2, "0")} <span>/ ${String(question.total).padStart(2, "0")}</span>`;
  document.querySelector("#image-index").textContent = `SPECIMEN ${String(question.index).padStart(2, "0")}`;
  document.querySelector("#question-image").src = question.image;
  document.querySelector("#score-value").textContent = question.score;
  document.querySelector("#progress-fill").style.width = `${(question.index / question.total) * 100}%`;
  document.querySelector("#feedback").textContent = "";
  document.querySelector("#feedback").className = "feedback";
  answerButtons.forEach((button) => { button.disabled = false; });
  nextButton.hidden = true;
  nextButton.textContent = question.index === question.total ? "See your score" : "Next picture";
}

async function startGame() {
  startButton.disabled = true;
  showNotice();
  try {
    const question = await request("/api/game", { method: "POST", body: "{}" });
    renderQuestion(question);
    showView("game");
  } catch (error) {
    showNotice(error.message);
  } finally {
    startButton.disabled = false;
  }
}

async function submitAnswer(button) {
  answerButtons.forEach((item) => { item.disabled = true; });
  try {
    const result = await request("/api/answer", {
      method: "POST",
      body: JSON.stringify({ is_bee: button.dataset.answer === "true" }),
    });
    const feedback = document.querySelector("#feedback");
    feedback.className = `feedback ${result.correct ? "correct" : "incorrect"}`;
    feedback.textContent = result.correct
      ? "That's right. +1 point."
      : `Not quite. This is ${result.correct_answer}.`;
    document.querySelector("#score-value").textContent = result.score;
    nextButton.hidden = false;
  } catch (error) {
    answerButtons.forEach((item) => { item.disabled = false; });
    showNotice(error.message);
  }
}

async function advanceQuestion() {
  nextButton.disabled = true;
  try {
    const result = await request("/api/next", { method: "POST", body: "{}" });
    if (result.finished) {
      finalScore = result.score;
      document.querySelector("#final-score").textContent = `You spotted ${result.score} of ${result.total} correctly.`;
      document.querySelector("#player-name").disabled = false;
      document.querySelector("#score-form button").disabled = false;
      document.querySelector("#save-feedback").textContent = "";
      showView("results");
      await refreshLeaderboard();
    } else {
      renderQuestion(result);
    }
  } catch (error) {
    showNotice(error.message);
  } finally {
    nextButton.disabled = false;
  }
}

async function saveScore(event) {
  event.preventDefault();
  const nameInput = document.querySelector("#player-name");
  const feedback = document.querySelector("#save-feedback");
  const saveButton = document.querySelector("#score-form button");
  saveButton.disabled = true;
  feedback.textContent = "";
  try {
    const { entries } = await request("/api/score", {
      method: "POST",
      body: JSON.stringify({ name: nameInput.value }),
    });
    renderLeaderboard(document.querySelector("#home-leaderboard"), entries);
    renderLeaderboard(document.querySelector("#results-leaderboard"), entries);
    nameInput.disabled = true;
    feedback.textContent = "Score saved to the hall of fame.";
    document.querySelector("#score-form label").textContent = "Your field score is on the board";
  } catch (error) {
    feedback.textContent = error.message;
    saveButton.disabled = false;
  }
}

startButton.addEventListener("click", startGame);
answerButtons.forEach((button) => button.addEventListener("click", () => submitAnswer(button)));
nextButton.addEventListener("click", advanceQuestion);
document.querySelector("#quit-button").addEventListener("click", () => showView("home"));
document.querySelector("#score-form").addEventListener("submit", saveScore);
document.querySelector("#play-again-button").addEventListener("click", startGame);
document.querySelector("#footer-year").textContent = new Date().getFullYear();

Promise.all([refreshLeaderboard(), loadPreviews()]).catch((error) => showNotice(error.message));
