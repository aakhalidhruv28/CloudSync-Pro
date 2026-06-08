"""Flask server for the FAQ chatbot."""

from pathlib import Path

from flask import Flask, jsonify, render_template, request

from app.faq_matcher import FAQMatcher

BASE_DIR = Path(__file__).resolve().parent.parent
FAQ_PATH = BASE_DIR / "data" / "faqs.json"

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
)

matcher = FAQMatcher(FAQ_PATH)


def _parse_exclude_ids(raw: str | None) -> list[int]:
    if not raw:
        return []
    ids = []
    for part in raw.split(","):
        part = part.strip()
        if part.isdigit():
            ids.append(int(part))
    return ids


@app.route("/")
def index():
    return render_template(
        "index.html",
        topic=matcher.topic,
        description=matcher.description,
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json(silent=True) or {}
    question = data.get("message", "").strip()

    if not question:
        return jsonify({"error": "Message is required."}), 400

    result = matcher.match(question)
    return jsonify(
        {
            "answer": result["answer"],
            "matched": result["matched"],
            "matched_question": result["matched_question"],
            "faq_id": result["faq_id"],
            "category": result["category"],
            "confidence": result["confidence"],
            "related_suggestions": result.get("related_suggestions", []),
        }
    )


@app.route("/api/suggestions")
def suggestions():
    exclude_ids = _parse_exclude_ids(request.args.get("exclude"))
    context_faq_id = request.args.get("context")
    category = request.args.get("category")
    query = request.args.get("q", "").strip()

    context_id = int(context_faq_id) if context_faq_id and context_faq_id.isdigit() else None

    items = matcher.get_dynamic_suggestions(
        exclude_ids=exclude_ids,
        context_faq_id=context_id,
        query=query or None,
        category=category or None,
        limit=int(request.args.get("limit", 5)),
    )
    return jsonify({"suggestions": items})


@app.route("/api/autocomplete")
def autocomplete():
    partial = request.args.get("q", "").strip()
    exclude_ids = _parse_exclude_ids(request.args.get("exclude"))

    items = matcher.get_autocomplete(
        partial=partial,
        limit=int(request.args.get("limit", 6)),
        exclude_ids=exclude_ids,
    )
    return jsonify({"results": items})


@app.route("/api/placeholders")
def placeholders():
    return jsonify({"placeholders": matcher.get_placeholder_questions()})


@app.route("/api/categories")
def categories():
    return jsonify({"categories": matcher.categories})


@app.route("/api/info")
def info():
    return jsonify(
        {
            "topic": matcher.topic,
            "description": matcher.description,
            "faq_count": matcher.faq_count,
            "categories": matcher.categories,
        }
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
