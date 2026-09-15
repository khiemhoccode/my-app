"""
Web trắc nghiệm - 2 chế độ: Chọn đề cụ thể / Ngẫu nhiên trộn tất cả các đề
Chạy: python app.py
Mở trình duyệt: http://127.0.0.1:5000
"""

import json
import random
import time
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, session, abort

app = Flask(__name__)
app.secret_key = "doi-chuoi-nay-thanh-gi-do-bi-mat"  # đổi khi triển khai thật

DATA_DIR = Path(__file__).parent / "data"
NUM_QUESTIONS = 40          # số câu hỏi mỗi lượt thi (lấy hết nếu đề có ít hơn)
TIME_LIMIT_SECONDS = 30 * 60  # 30 phút
RANDOM_MODE_ID = "__random__"  # id đặc biệt đại diện cho chế độ "Ngẫu nhiên"


def load_all_decks():
    """Đọc tất cả các file .json trong thư mục data/, mỗi file là một đề thi.
    Mỗi câu hỏi được gắn thêm deck_id để chế độ ngẫu nhiên vẫn tra cứu lại đúng nguồn.
    """
    decks = {}
    for path in sorted(DATA_DIR.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            payload = json.load(f)
        deck_id = path.stem  # ví dụ "de1", "de2"
        questions = payload["questions"]
        for q in questions:
            q["_deck_id"] = deck_id
        decks[deck_id] = {
            "id": deck_id,
            "title": payload.get("title", deck_id),
            "questions": questions,
        }
    return decks


DECKS = load_all_decks()


def all_questions_pool():
    """Gộp toàn bộ câu hỏi từ mọi đề lại thành 1 pool để bốc ngẫu nhiên."""
    pool = []
    for deck in DECKS.values():
        pool.extend(deck["questions"])
    return pool


@app.route("/")
def home():
    deck_list = []
    for deck_id, deck in DECKS.items():
        total = len(deck["questions"])
        missing = sum(1 for q in deck["questions"] if not q.get("answer"))
        deck_list.append({
            "id": deck_id,
            "title": deck["title"],
            "total": total,
            "has_answers": missing == 0,
        })

    total_all = sum(d["total"] for d in deck_list)
    return render_template("index.html", decks=deck_list, total_all=total_all)


def _start_common(chosen, mode_label, deck_id):
    """Lưu thông tin gọn nhẹ vào session và trả về redirect tới /quiz."""
    session["mode_label"] = mode_label
    session["deck_id"] = deck_id  # None nếu là chế độ ngẫu nhiên
    session["quiz_refs"] = [{"deck": q["_deck_id"], "id": q["id"]} for q in chosen]
    session["quiz_answers"] = {
        f'{q["_deck_id"]}:{q["id"]}': q.get("answer") for q in chosen
    }

    order = {}
    for q in chosen:
        key = f'{q["_deck_id"]}:{q["id"]}'
        letters = list(q["options"].keys())
        random.shuffle(letters)
        order[key] = letters
    session["quiz_order"] = order

    session["start_time"] = time.time()
    return redirect(url_for("quiz"))


@app.route("/start/<deck_id>")
def start_quiz(deck_id):
    deck = DECKS.get(deck_id)
    if not deck:
        abort(404)

    pool = deck["questions"].copy()
    random.shuffle(pool)
    num = min(NUM_QUESTIONS, len(pool))
    chosen = pool[:num]
    return _start_common(chosen, deck["title"], deck_id)


@app.route("/start-random")
def start_random():
    pool = all_questions_pool().copy()
    random.shuffle(pool)
    num = min(NUM_QUESTIONS, len(pool))
    chosen = pool[:num]
    return _start_common(chosen, "Ngẫu nhiên (trộn tất cả các đề)", None)


def build_quiz_data():
    """Tra lại nội dung đầy đủ của các câu hỏi từ (deck, id) + thứ tự đã lưu trong session."""
    lookup = {}
    for deck in DECKS.values():
        for q in deck["questions"]:
            lookup[(q["_deck_id"], q["id"])] = q

    quiz_data = []
    for ref in session["quiz_refs"]:
        key = f'{ref["deck"]}:{ref["id"]}'
        q = lookup[(ref["deck"], ref["id"])]
        letters = session["quiz_order"][key]
        options = [(letter, q["options"][letter]) for letter in letters]
        quiz_data.append({
            "key": key,
            "question": q["question"],
            "options": options,
        })
    return quiz_data


@app.route("/quiz")
def quiz():
    if "quiz_refs" not in session:
        return redirect(url_for("home"))

    start_time = session.get("start_time", time.time())
    elapsed = time.time() - start_time
    remaining = max(0, TIME_LIMIT_SECONDS - int(elapsed))

    if remaining <= 0:
        return redirect(url_for("submit_quiz"))

    return render_template(
        "quiz.html",
        deck_title=session["mode_label"],
        questions=build_quiz_data(),
        remaining=remaining,
    )


@app.route("/submit", methods=["POST", "GET"])
def submit_quiz():
    if "quiz_answers" not in session:
        return redirect(url_for("home"))

    lookup = {}
    for deck in DECKS.values():
        for q in deck["questions"]:
            lookup[(q["_deck_id"], q["id"])] = q

    correct_answers = session["quiz_answers"]
    refs = session["quiz_refs"]

    score = 0
    scored_total = 0  # chỉ tính điểm trên các câu có đáp án đúng đã biết
    details = []

    for ref in refs:
        key = f'{ref["deck"]}:{ref["id"]}'
        field_name = f"q_{key}"
        chosen = request.form.get(field_name)  # None nếu bỏ trống (hết giờ)
        correct = correct_answers[key]  # có thể là None nếu đề chưa có đáp án
        is_correct = (correct is not None and chosen == correct)
        if correct is not None:
            scored_total += 1
            if is_correct:
                score += 1

        q_full = lookup[(ref["deck"], ref["id"])]
        details.append({
            "question": q_full["question"],
            "options": q_full["options"],
            "correct": correct,
            "chosen": chosen,
            "is_correct": is_correct,
            "deck_title": DECKS[ref["deck"]]["title"],
        })

    total = len(refs)
    percent = round(score / scored_total * 100, 1) if scored_total else None
    mode_label = session.get("mode_label", "")

    session.clear()

    return render_template(
        "result.html",
        deck_title=mode_label,
        score=score,
        total=total,
        scored_total=scored_total,
        percent=percent,
        details=details,
    )


if __name__ == "__main__":
    import os
    # host="0.0.0.0" để các máy khác trong cùng mạng wifi/LAN truy cập được
    # PORT: Hugging Face Spaces (Docker SDK) mặc định expose cổng 7860
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
