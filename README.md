# FAQ Chatbot

An intelligent FAQ chatbot that matches user questions to the most relevant answers using NLP preprocessing and cosine similarity. Built with Python, Flask, NLTK, and scikit-learn, with a modern chat UI for real-time interaction.

---

## Developer

| | |
|---|---|
| **Name** | Dhruv Patel |
| **Portfolio** | [https://developer.uxtech.in/](https://developer.uxtech.in/) |
| **LinkedIn** | [https://www.linkedin.com/in/drpatel-ai](https://www.linkedin.com/in/drpatel-ai) |

AI Engineer with a strong foundation in UX development — building intelligent, data-driven systems and seamless digital experiences using Python, JavaScript, and modern AI frameworks.

---

## Features

- **FAQ knowledge base** — Store questions and answers in a structured JSON file, organized by category
- **NLP preprocessing** — Tokenization, cleaning, stopword removal, and lemmatization using NLTK
- **Smart matching** — TF-IDF vectorization with cosine similarity to find the best FAQ match
- **Chat UI** — Responsive, dark-themed interface with typing indicators and confidence scores
- **Dynamic suggestions** — Rotating typewriter placeholders, live autocomplete, and context-aware follow-up questions
- **Category filters** — Browse suggestions by topic (Pricing, Security, Billing, Features, etc.)
- **Deduplication** — Already-asked questions are excluded from future suggestions

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| Backend | Python, Flask |
| NLP | NLTK |
| ML / Matching | scikit-learn (TF-IDF, cosine similarity) |
| Frontend | HTML, CSS, JavaScript |
| Data | JSON |

---

## Project Structure

```
Chatbot for FAQs/
├── app/
│   ├── __init__.py
│   ├── main.py            # Flask server & API routes
│   ├── nlp_processor.py   # NLTK text preprocessing
│   └── faq_matcher.py     # TF-IDF matching & suggestions
├── data/
│   └── faqs.json          # FAQ questions, answers & categories
├── static/
│   ├── css/style.css      # Chat UI styles
│   └── js/chat.js         # Frontend chat logic
├── templates/
│   └── index.html         # Chat interface
├── requirements.txt
├── run.py                 # Application entry point
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

1. **Clone or download the project**

2. **Create a virtual environment**

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**

   Windows (PowerShell):
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

   macOS / Linux:
   ```bash
   source venv/bin/activate
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**

   ```bash
   python run.py
   ```

6. **Open in your browser**

   Visit [http://127.0.0.1:5000](http://127.0.0.1:5000)

> NLTK data (tokenizers, stopwords, wordnet) is downloaded automatically on first run.

---

## Usage

1. Type a question in the chat input, or click a suggestion chip.
2. The bot preprocesses your question and finds the closest FAQ match.
3. The best answer is displayed along with a confidence score.
4. Related follow-up questions appear after each response.
5. Use category filters or the **New ideas** button for fresh suggestions.
6. Start typing (2+ characters) to see live autocomplete results.

### Example questions

- *"How much does it cost?"*
- *"Is my data secure?"*
- *"Can I use it offline?"*
- *"How do I cancel my subscription?"*

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Chat UI |
| `POST` | `/api/chat` | Send a question, receive the best-matching answer |
| `GET` | `/api/suggestions` | Dynamic suggestion chips (`?context=`, `?category=`, `?exclude=`) |
| `GET` | `/api/autocomplete` | Live search as user types (`?q=`) |
| `GET` | `/api/placeholders` | Rotating placeholder questions |
| `GET` | `/api/categories` | Available FAQ categories |
| `GET` | `/api/info` | Topic, description, and FAQ count |

### Chat request example

```bash
curl -X POST http://127.0.0.1:5000/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"message\": \"How much does it cost?\"}"
```

---

## Customization

### Add or edit FAQs

Edit `data/faqs.json`:

```json
{
  "id": 13,
  "question": "Your question here?",
  "category": "General",
  "answer": "Your answer here."
}
```

Restart the server after changing the FAQ file.

### Adjust matching sensitivity

In `app/faq_matcher.py`, change `DEFAULT_CONFIDENCE_THRESHOLD` (default: `0.15`). Lower values accept weaker matches; higher values are stricter.

### Change topic and branding

Update the `topic` and `description` fields at the top of `data/faqs.json`.

---

## How It Works

```
User Question
     │
     ▼
┌─────────────────┐
│  NLP Pipeline   │  clean → tokenize → remove stopwords → lemmatize
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  TF-IDF Vector  │  Convert to numerical representation
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cosine          │  Compare against all FAQ questions
│ Similarity      │
└────────┬────────┘
         │
         ▼
   Best Match → Return Answer + Related Suggestions
```

---

## License

This project is open source and available for personal and educational use.

---

## Connect

- **Portfolio:** [developer.uxtech.in](https://developer.uxtech.in/)
- **LinkedIn:** [linkedin.com/in/drpatel-ai](https://www.linkedin.com/in/drpatel-ai)

**Dhruv Patel** — AI Engineer · UX Developer
