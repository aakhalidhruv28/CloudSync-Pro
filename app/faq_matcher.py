"""Match user questions to FAQs using TF-IDF and cosine similarity."""

import json
import random
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.nlp_processor import NLPProcessor

DEFAULT_CONFIDENCE_THRESHOLD = 0.15
FALLBACK_RESPONSE = (
    "I'm not sure I have an answer for that. "
    "Try rephrasing your question, or ask about pricing, security, "
    "file sharing, supported platforms, or account settings."
)


class FAQMatcher:
    """Find the best-matching FAQ for a user question."""

    def __init__(self, faq_path: str | Path, confidence_threshold: float = DEFAULT_CONFIDENCE_THRESHOLD):
        self._processor = NLPProcessor()
        self._confidence_threshold = confidence_threshold
        self._faqs: list[dict] = []
        self._vectorizer: TfidfVectorizer | None = None
        self._faq_matrix = None
        self._topic = ""
        self._description = ""
        self._categories: list[str] = []

        self.load_faqs(faq_path)

    def load_faqs(self, faq_path: str | Path) -> None:
        """Load FAQ data and build the similarity index."""
        path = Path(faq_path)
        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        self._topic = data.get("topic", "FAQ")
        self._description = data.get("description", "")
        self._faqs = data.get("faqs", [])
        self._categories = sorted(
            {faq.get("category", "General") for faq in self._faqs}
        )
        self._build_index()

    def _build_index(self) -> None:
        """Preprocess FAQ questions and vectorize with TF-IDF."""
        if not self._faqs:
            return

        processed_questions = [
            self._processor.preprocess(faq["question"]) for faq in self._faqs
        ]

        self._vectorizer = TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=1,
            sublinear_tf=True,
        )
        self._faq_matrix = self._vectorizer.fit_transform(processed_questions)

    @property
    def topic(self) -> str:
        return self._topic

    @property
    def description(self) -> str:
        return self._description

    @property
    def faq_count(self) -> int:
        return len(self._faqs)

    @property
    def categories(self) -> list[str]:
        return self._categories

    def _faq_index_by_id(self, faq_id: int) -> int | None:
        for idx, faq in enumerate(self._faqs):
            if faq["id"] == faq_id:
                return idx
        return None

    def _compute_similarities(self, text: str) -> np.ndarray | None:
        if not self._faqs or self._vectorizer is None:
            return None

        processed = self._processor.preprocess(text)
        if not processed.strip():
            return np.zeros(len(self._faqs))

        query_vector = self._vectorizer.transform([processed])
        return cosine_similarity(query_vector, self._faq_matrix).flatten()

    def _exclude_indices(self, exclude_ids: list[int] | None) -> set[int]:
        if not exclude_ids:
            return set()
        excluded = set()
        for faq_id in exclude_ids:
            idx = self._faq_index_by_id(faq_id)
            if idx is not None:
                excluded.add(idx)
        return excluded

    def _rank_faqs(
        self,
        text: str,
        limit: int,
        exclude_ids: list[int] | None = None,
        category: str | None = None,
    ) -> list[dict]:
        similarities = self._compute_similarities(text)
        if similarities is None:
            return []

        excluded = self._exclude_indices(exclude_ids)
        ranked_indices = np.argsort(similarities)[::-1]

        results = []
        for idx in ranked_indices:
            if idx in excluded:
                continue
            faq = self._faqs[idx]
            if category and faq.get("category", "General") != category:
                continue
            results.append(
                {
                    "id": faq["id"],
                    "question": faq["question"],
                    "category": faq.get("category", "General"),
                    "score": round(float(similarities[idx]), 4),
                }
            )
            if len(results) >= limit:
                break
        return results

    def match(self, user_question: str) -> dict:
        """Return the best FAQ match with confidence score."""
        if not user_question.strip():
            return self._no_match_response("Please type a question.")

        if not self._faqs or self._vectorizer is None:
            return self._no_match_response("FAQ database is not loaded.")

        processed_query = self._processor.preprocess(user_question)
        if not processed_query.strip():
            return self._no_match_response(
                "I couldn't understand that. Please try a different question."
            )

        similarities = self._compute_similarities(user_question)
        if similarities is None:
            return self._no_match_response("FAQ database is not loaded.")

        best_idx = int(similarities.argmax())
        best_score = float(similarities[best_idx])

        if best_score < self._confidence_threshold:
            related = self.get_dynamic_suggestions(
                query=user_question,
                limit=4,
            )
            return {
                **self._no_match_response(FALLBACK_RESPONSE, confidence=best_score),
                "related_suggestions": related,
            }

        best_faq = self._faqs[best_idx]
        related = self.get_related_questions(
            faq_id=best_faq["id"],
            limit=4,
        )
        return {
            "matched": True,
            "answer": best_faq["answer"],
            "matched_question": best_faq["question"],
            "faq_id": best_faq["id"],
            "category": best_faq.get("category", "General"),
            "confidence": round(best_score, 4),
            "related_suggestions": related,
        }

    def _no_match_response(self, message: str, confidence: float = 0.0) -> dict:
        return {
            "matched": False,
            "answer": message,
            "matched_question": None,
            "faq_id": None,
            "category": None,
            "confidence": round(confidence, 4),
            "related_suggestions": [],
        }

    def get_related_questions(
        self,
        faq_id: int | None = None,
        query: str | None = None,
        limit: int = 4,
        exclude_ids: list[int] | None = None,
    ) -> list[dict]:
        """Return FAQs semantically related to a matched FAQ or query."""
        exclude_ids = list(exclude_ids or [])
        if faq_id is not None:
            exclude_ids.append(faq_id)
            anchor = self._faqs[self._faq_index_by_id(faq_id)]["question"]
        elif query:
            anchor = query
        else:
            return self.get_dynamic_suggestions(limit=limit, exclude_ids=exclude_ids)

        return self._rank_faqs(anchor, limit=limit, exclude_ids=exclude_ids)

    def get_autocomplete(
        self,
        partial: str,
        limit: int = 6,
        exclude_ids: list[int] | None = None,
    ) -> list[dict]:
        """Return FAQ questions matching partial user input."""
        partial = partial.strip()
        if len(partial) < 2:
            return []

        semantic_matches = self._rank_faqs(
            partial, limit=limit * 2, exclude_ids=exclude_ids
        )

        partial_lower = partial.lower()
        literal_matches = []
        for faq in self._faqs:
            if faq["id"] in (exclude_ids or []):
                continue
            question_lower = faq["question"].lower()
            if partial_lower in question_lower:
                literal_matches.append(
                    {
                        "id": faq["id"],
                        "question": faq["question"],
                        "category": faq.get("category", "General"),
                        "score": 1.0,
                        "highlight": self._highlight_match(faq["question"], partial),
                    }
                )

        seen_ids = set()
        combined = []
        for item in literal_matches + semantic_matches:
            if item["id"] in seen_ids:
                continue
            seen_ids.add(item["id"])
            if "highlight" not in item:
                item["highlight"] = self._highlight_match(item["question"], partial)
            combined.append(item)
            if len(combined) >= limit:
                break
        return combined

    def get_dynamic_suggestions(
        self,
        exclude_ids: list[int] | None = None,
        context_faq_id: int | None = None,
        query: str | None = None,
        category: str | None = None,
        limit: int = 5,
    ) -> list[dict]:
        """Build context-aware suggestions mixing related, category, and fresh picks."""
        exclude_ids = list(exclude_ids or [])
        suggestions: list[dict] = []
        seen_ids = set(exclude_ids)

        def add_items(items: list[dict]) -> None:
            for item in items:
                if item["id"] in seen_ids:
                    continue
                seen_ids.add(item["id"])
                suggestions.append(item)
                if len(suggestions) >= limit:
                    return

        if context_faq_id is not None:
            add_items(
                self.get_related_questions(
                    faq_id=context_faq_id,
                    limit=limit,
                    exclude_ids=exclude_ids,
                )
            )

        if query and len(suggestions) < limit:
            add_items(
                self._rank_faqs(
                    query,
                    limit=limit - len(suggestions),
                    exclude_ids=list(seen_ids),
                    category=category,
                )
            )

        if category and len(suggestions) < limit:
            category_faqs = [
                {
                    "id": faq["id"],
                    "question": faq["question"],
                    "category": faq.get("category", "General"),
                    "score": 0.0,
                }
                for faq in self._faqs
                if faq.get("category") == category and faq["id"] not in seen_ids
            ]
            random.shuffle(category_faqs)
            add_items(category_faqs[: limit - len(suggestions)])

        if len(suggestions) < limit:
            remaining = [
                {
                    "id": faq["id"],
                    "question": faq["question"],
                    "category": faq.get("category", "General"),
                    "score": 0.0,
                }
                for faq in self._faqs
                if faq["id"] not in seen_ids
            ]
            random.shuffle(remaining)
            add_items(remaining[: limit - len(suggestions)])

        return suggestions[:limit]

    def get_placeholder_questions(self, limit: int = 8) -> list[str]:
        """Return shuffled FAQ questions for rotating input placeholders."""
        questions = [faq["question"] for faq in self._faqs]
        random.shuffle(questions)
        return questions[:limit]

    def get_questions_by_category(self, category: str, limit: int = 4) -> list[dict]:
        """Return FAQ questions filtered by category."""
        matched = [
            {
                "id": faq["id"],
                "question": faq["question"],
                "category": faq.get("category", "General"),
            }
            for faq in self._faqs
            if faq.get("category", "General") == category
        ]
        return matched[:limit]

    @staticmethod
    def _highlight_match(question: str, partial: str) -> str:
        if not partial.strip():
            return question
        pattern = re.compile(re.escape(partial.strip()), re.IGNORECASE)
        return pattern.sub(lambda m: f"<mark>{m.group(0)}</mark>", question)
