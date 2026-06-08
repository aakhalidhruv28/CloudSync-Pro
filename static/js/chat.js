const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const messageInput = document.getElementById("messageInput");
const sendBtn = document.getElementById("sendBtn");
const suggestionsEl = document.getElementById("suggestions");
const stickySuggestions = document.getElementById("stickySuggestions");
const stickySuggestionChips = document.getElementById("stickySuggestionChips");
const stickyLabel = document.getElementById("stickyLabel");
const categoryFilters = document.getElementById("categoryFilters");
const refreshSuggestionsBtn = document.getElementById("refreshSuggestionsBtn");
const placeholderGhost = document.getElementById("placeholderGhost");
const autocompleteList = document.getElementById("autocompleteList");

const state = {
  isLoading: false,
  askedFaqIds: new Set(),
  lastFaqId: null,
  activeCategory: null,
  placeholders: [],
  placeholderIndex: 0,
  placeholderCharIndex: 0,
  isDeleting: false,
  autocompleteResults: [],
  autocompleteIndex: -1,
  autocompleteVisible: false,
};

let placeholderTimer = null;
let autocompleteTimer = null;

function scrollToBottom() {
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function excludeParam() {
  return Array.from(state.askedFaqIds).join(",");
}

function createSuggestionChip(item, onClick) {
  const chip = document.createElement("button");
  chip.type = "button";
  chip.className = "suggestion-chip";
  chip.dataset.faqId = item.id;

  const category = document.createElement("span");
  category.className = "chip-category";
  category.textContent = item.category || "General";

  const text = document.createElement("span");
  text.className = "chip-text";
  text.textContent = item.question;

  chip.appendChild(category);
  chip.appendChild(text);
  chip.addEventListener("click", () => onClick(item.question, item.id));
  return chip;
}

function renderSuggestionChips(container, items, onClick) {
  container.innerHTML = "";
  items.forEach((item) => {
    container.appendChild(createSuggestionChip(item, onClick));
  });
}

function createMessageElement(role, text, meta = null, followUpSuggestions = null) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.innerHTML = role === "user"
    ? `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`
    : `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`;

  const content = document.createElement("div");
  content.className = "message-content";
  const paragraph = document.createElement("p");
  paragraph.textContent = text;
  content.appendChild(paragraph);

  if (meta) {
    const metaEl = document.createElement("div");
    metaEl.className = "message-meta";
    metaEl.textContent = meta;
    content.appendChild(metaEl);
  }

  if (followUpSuggestions?.length) {
    const block = document.createElement("div");
    block.className = "suggestions-block follow-up";
    const label = document.createElement("p");
    label.className = "suggestions-label";
    label.textContent = "You might also ask";
    const chips = document.createElement("div");
    chips.className = "suggestions";
    renderSuggestionChips(chips, followUpSuggestions, (question, id) => sendMessage(question, id));
    block.appendChild(label);
    block.appendChild(chips);
    content.appendChild(block);
  }

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);
  return wrapper;
}

function showTypingIndicator() {
  const wrapper = document.createElement("div");
  wrapper.className = "message bot";
  wrapper.id = "typingIndicator";

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`;

  const content = document.createElement("div");
  content.className = "message-content";
  content.innerHTML = `<div class="typing-indicator"><span></span><span></span><span></span></div>`;

  wrapper.appendChild(avatar);
  wrapper.appendChild(content);
  chatMessages.appendChild(wrapper);
  scrollToBottom();
}

function removeTypingIndicator() {
  document.getElementById("typingIndicator")?.remove();
}

function hideAutocomplete() {
  autocompleteList.hidden = true;
  autocompleteList.innerHTML = "";
  state.autocompleteResults = [];
  state.autocompleteIndex = -1;
  state.autocompleteVisible = false;
  messageInput.setAttribute("aria-expanded", "false");
}

function showAutocomplete(results) {
  autocompleteList.innerHTML = "";
  if (!results.length) {
    hideAutocomplete();
    return;
  }

  results.forEach((item, index) => {
    const li = document.createElement("li");
    li.className = "autocomplete-item";
    li.role = "option";
    li.id = `autocomplete-option-${index}`;
    li.dataset.index = index;
    li.innerHTML = `
      <span class="autocomplete-category">${item.category}</span>
      <span class="autocomplete-text">${item.highlight || item.question}</span>
    `;
    li.addEventListener("mousedown", (e) => {
      e.preventDefault();
      selectAutocomplete(index);
    });
    autocompleteList.appendChild(li);
  });

  autocompleteList.hidden = false;
  state.autocompleteResults = results;
  state.autocompleteIndex = -1;
  state.autocompleteVisible = true;
  messageInput.setAttribute("aria-expanded", "true");
  updateAutocompleteHighlight();
}

function updateAutocompleteHighlight() {
  const items = autocompleteList.querySelectorAll(".autocomplete-item");
  items.forEach((item, index) => {
    item.classList.toggle("active", index === state.autocompleteIndex);
    if (index === state.autocompleteIndex) {
      messageInput.setAttribute("aria-activedescendant", item.id);
    }
  });
  if (state.autocompleteIndex < 0) {
    messageInput.removeAttribute("aria-activedescendant");
  }
}

function selectAutocomplete(index) {
  const item = state.autocompleteResults[index];
  if (!item) return;
  messageInput.value = item.question;
  hideAutocomplete();
  sendMessage(item.question, item.id);
}

async function fetchSuggestions({ contextId = null, category = null, label = "Try asking" } = {}) {
  const params = new URLSearchParams({ limit: "5", exclude: excludeParam() });
  if (contextId) params.set("context", contextId);
  if (category) params.set("category", category);
  if (state.lastFaqId && !contextId) params.set("context", state.lastFaqId);

  const response = await fetch(`/api/suggestions?${params}`);
  const data = await response.json();

  stickyLabel.textContent = label;
  renderSuggestionChips(stickySuggestionChips, data.suggestions, (question, id) => sendMessage(question, id));
}

async function loadWelcomeSuggestions() {
  const response = await fetch(`/api/suggestions?limit=4&exclude=${excludeParam()}`);
  const data = await response.json();
  renderSuggestionChips(suggestionsEl, data.suggestions, (question, id) => sendMessage(question, id));
}

async function loadCategories() {
  const response = await fetch("/api/categories");
  const data = await response.json();

  const allChip = document.createElement("button");
  allChip.type = "button";
  allChip.className = "category-chip active";
  allChip.textContent = "All";
  allChip.addEventListener("click", () => setActiveCategory(null, allChip));
  categoryFilters.appendChild(allChip);

  data.categories.forEach((category) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = "category-chip";
    chip.textContent = category;
    chip.addEventListener("click", () => setActiveCategory(category, chip));
    categoryFilters.appendChild(chip);
  });
}

function setActiveCategory(category, clickedChip) {
  state.activeCategory = category;
  categoryFilters.querySelectorAll(".category-chip").forEach((chip) => {
    chip.classList.toggle("active", chip === clickedChip);
  });

  const label = category ? `${category} questions` : "Try asking";
  fetchSuggestions({ category, label });
}

async function loadPlaceholders() {
  const response = await fetch("/api/placeholders");
  const data = await response.json();
  state.placeholders = data.placeholders.length
    ? data.placeholders
    : ["Ask me anything about our product..."];
  startPlaceholderAnimation();
}

function startPlaceholderAnimation() {
  if (placeholderTimer) clearTimeout(placeholderTimer);

  const tick = () => {
    if (messageInput.value || document.activeElement === messageInput) {
      placeholderGhost.textContent = "";
      placeholderTimer = setTimeout(tick, 500);
      return;
    }

    const current = state.placeholders[state.placeholderIndex] || "";
    const prefix = "Try: ";

    if (!state.isDeleting && state.placeholderCharIndex <= current.length) {
      placeholderGhost.textContent = prefix + current.slice(0, state.placeholderCharIndex);
      state.placeholderCharIndex += 1;
      placeholderTimer = setTimeout(tick, 45);
      return;
    }

    if (!state.isDeleting && state.placeholderCharIndex > current.length) {
      placeholderTimer = setTimeout(() => {
        state.isDeleting = true;
        tick();
      }, 1800);
      return;
    }

    if (state.isDeleting && state.placeholderCharIndex > 0) {
      placeholderGhost.textContent = prefix + current.slice(0, state.placeholderCharIndex);
      state.placeholderCharIndex -= 1;
      placeholderTimer = setTimeout(tick, 25);
      return;
    }

    state.isDeleting = false;
    state.placeholderIndex = (state.placeholderIndex + 1) % state.placeholders.length;
    placeholderTimer = setTimeout(tick, 350);
  };

  tick();
}

async function fetchAutocomplete(query) {
  if (query.length < 2) {
    hideAutocomplete();
    return;
  }

  const params = new URLSearchParams({
    q: query,
    exclude: excludeParam(),
    limit: "6",
  });
  const response = await fetch(`/api/autocomplete?${params}`);
  const data = await response.json();
  showAutocomplete(data.results);
}

async function sendMessage(text, knownFaqId = null) {
  if (!text.trim() || state.isLoading) return;

  state.isLoading = true;
  sendBtn.disabled = true;
  messageInput.value = "";
  hideAutocomplete();
  placeholderGhost.textContent = "";

  chatMessages.appendChild(createMessageElement("user", text));
  scrollToBottom();
  showTypingIndicator();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text }),
    });

    removeTypingIndicator();

    if (!response.ok) {
      const err = await response.json();
      chatMessages.appendChild(
        createMessageElement("bot", err.error || "Something went wrong. Please try again.")
      );
    } else {
      const data = await response.json();
      if (data.faq_id) {
        state.askedFaqIds.add(data.faq_id);
        state.lastFaqId = data.faq_id;
      } else if (knownFaqId) {
        state.askedFaqIds.add(knownFaqId);
        state.lastFaqId = knownFaqId;
      }

      let meta = null;
      if (data.matched && data.matched_question) {
        const categoryLabel = data.category ? ` · ${data.category}` : "";
        meta = `Matched: "${data.matched_question}" (${(data.confidence * 100).toFixed(0)}%${categoryLabel})`;
      }

      chatMessages.appendChild(
        createMessageElement(
          "bot",
          data.answer,
          meta,
          data.related_suggestions
        )
      );

      await fetchSuggestions({
        contextId: data.faq_id || state.lastFaqId,
        category: state.activeCategory,
        label: data.matched ? "Related questions" : "Try these instead",
      });
    }
  } catch {
    removeTypingIndicator();
    chatMessages.appendChild(
      createMessageElement("bot", "Connection error. Please check that the server is running.")
    );
  }

  state.isLoading = false;
  sendBtn.disabled = false;
  messageInput.focus();
  startPlaceholderAnimation();
  scrollToBottom();
}

chatForm.addEventListener("submit", (e) => {
  e.preventDefault();
  if (state.autocompleteVisible && state.autocompleteIndex >= 0) {
    selectAutocomplete(state.autocompleteIndex);
    return;
  }
  sendMessage(messageInput.value);
});

messageInput.addEventListener("input", () => {
  placeholderGhost.textContent = "";
  clearTimeout(autocompleteTimer);
  autocompleteTimer = setTimeout(() => {
    fetchAutocomplete(messageInput.value.trim());
  }, 220);
});

messageInput.addEventListener("focus", () => {
  placeholderGhost.textContent = "";
  if (messageInput.value.trim().length >= 2) {
    fetchAutocomplete(messageInput.value.trim());
  }
});

messageInput.addEventListener("blur", () => {
  setTimeout(() => {
    hideAutocomplete();
    if (!messageInput.value) startPlaceholderAnimation();
  }, 150);
});

messageInput.addEventListener("keydown", (e) => {
  if (!state.autocompleteVisible || !state.autocompleteResults.length) {
    if (e.key === "Tab" && !messageInput.value && stickySuggestionChips.firstChild) {
      e.preventDefault();
      stickySuggestionChips.firstChild.click();
    }
    return;
  }

  if (e.key === "ArrowDown") {
    e.preventDefault();
    state.autocompleteIndex = Math.min(
      state.autocompleteIndex + 1,
      state.autocompleteResults.length - 1
    );
    updateAutocompleteHighlight();
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    state.autocompleteIndex = Math.max(state.autocompleteIndex - 1, 0);
    updateAutocompleteHighlight();
  } else if (e.key === "Escape") {
    hideAutocomplete();
  } else if (e.key === "Tab" && state.autocompleteIndex >= 0) {
    e.preventDefault();
    selectAutocomplete(state.autocompleteIndex);
  }
});

refreshSuggestionsBtn.addEventListener("click", () => {
  fetchSuggestions({
    category: state.activeCategory,
    label: state.activeCategory ? `${state.activeCategory} picks` : "Fresh suggestions",
  });
});

loadWelcomeSuggestions();
loadCategories();
loadPlaceholders();
fetchSuggestions();
messageInput.focus();
