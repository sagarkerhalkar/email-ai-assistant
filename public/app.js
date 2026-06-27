const state = {
  mailbox: null,
  selectedId: null,
  activeCategory: "all",
  selectedForTrash: new Set(),
  lastBulkMessage: "",
  gmailStatus: null
};

const els = {
  accountEmail: document.querySelector("#accountEmail"),
  mailCount: document.querySelector("#mailCount"),
  alertCount: document.querySelector("#alertCount"),
  trashCount: document.querySelector("#trashCount"),
  bulkStatus: document.querySelector("#bulkStatus"),
  filters: document.querySelector("#categoryFilters"),
  gmailStatus: document.querySelector("#gmailStatus"),
  connectGmail: document.querySelector("#connectGmailButton"),
  findAttachments: document.querySelector("#findAttachmentsButton"),
  models: document.querySelector("#modelRoutes"),
  list: document.querySelector("#emailList"),
  detail: document.querySelector("#emailDetail"),
  refresh: document.querySelector("#refreshButton"),
  selectCleanable: document.querySelector("#selectCleanableButton"),
  bulkTrash: document.querySelector("#bulkTrashButton")
};

els.refresh.addEventListener("click", () => loadMailbox());
els.connectGmail.addEventListener("click", async () => {
  const response = await fetch("/api/gmail/auth-url");
  const result = await response.json();
  if (result.authUrl) {
    window.open(result.authUrl, "_blank", "noopener");
  }
});
els.findAttachments.addEventListener("click", async () => {
  const result = await postJson("/api/gmail/find-attachments", {
    query: "filename:pdf (cv OR resume)"
  });
  state.lastBulkMessage = result.ok
    ? `Saved ${result.saved.length} attachment(s)`
    : result.message;
  await loadMailbox();
});
els.selectCleanable.addEventListener("click", () => {
  filteredEmails()
    .filter((email) => email.actionPolicy.canRecommendTrash)
    .forEach((email) => state.selectedForTrash.add(email.id));
  state.lastBulkMessage = "";
  render();
});
els.bulkTrash.addEventListener("click", async () => {
  const ids = Array.from(state.selectedForTrash);
  if (!ids.length) return;

  const result = await postJson("/api/bulk-trash", {
    emailIds: ids,
    approved: true
  });
  state.selectedForTrash.clear();
  state.selectedId = null;
  state.lastBulkMessage = result.message;
  await loadMailbox();
});

await loadMailbox();

async function loadMailbox() {
  els.list.innerHTML = `<div class="detail-empty">Loading analyzed mail...</div>`;
  const response = await fetch("/api/emails");
  state.mailbox = await response.json();
  state.gmailStatus = state.mailbox.account?.gmail ?? null;
  const liveIds = new Set(state.mailbox.emails.map((email) => email.id));
  state.selectedForTrash = new Set([...state.selectedForTrash].filter((id) => liveIds.has(id)));
  state.selectedId = state.selectedId && liveIds.has(state.selectedId)
    ? state.selectedId
    : state.mailbox.emails[0]?.id ?? null;
  render();
}

function render() {
  const mailbox = state.mailbox;
  if (!mailbox) return;

  els.accountEmail.textContent = mailbox.account?.email || "Sample mailbox";
  renderGmailStatus(mailbox.account);
  els.mailCount.textContent = `${mailbox.emails.length} mails`;
  els.alertCount.textContent = `${mailbox.alerts.length} alerts`;
  els.trashCount.textContent = `${mailbox.trashReview.length} trash review`;
  els.bulkStatus.textContent = state.lastBulkMessage || `${state.selectedForTrash.size} selected for Trash`;
  els.bulkTrash.disabled = state.selectedForTrash.size === 0;

  renderFilters(mailbox);
  renderModels(mailbox.models);
  renderList();
  renderDetail(mailbox.emails.find((email) => email.id === state.selectedId));
}

function renderGmailStatus(account) {
  const gmail = account?.gmail;
  if (!gmail) {
    els.gmailStatus.textContent = "Gmail status unavailable";
    return;
  }

  if (gmail.connected) {
    els.gmailStatus.textContent = `Connected as ${account.email}`;
    els.connectGmail.textContent = "Reconnect";
    els.findAttachments.disabled = false;
    return;
  }

  if (!gmail.credentialsPresent) {
    els.gmailStatus.textContent = "Add private Gmail credentials";
    els.findAttachments.disabled = true;
    return;
  }

  els.gmailStatus.textContent = "Ready to connect";
  els.findAttachments.disabled = true;
}

function renderFilters(mailbox) {
  const counts = {
    all: mailbox.emails.length,
    ...mailbox.counts
  };

  const labels = {
    all: "All",
    important_finance: "Finance",
    company_hr: "Company / HR",
    career_recruiter: "Career",
    home_renewal: "Home",
    study_summary: "Study",
    marketing_promotion: "Marketing",
    low_value_loan_offer: "Loan / Spam",
    social_update: "Social",
    personal: "Personal",
    needs_review: "Review"
  };

  els.filters.innerHTML = Object.entries(counts)
    .map(
      ([category, count]) => `
        <button class="filter-button ${state.activeCategory === category ? "active" : ""}" type="button" data-category="${category}">
          <span>${labels[category] ?? category}</span>
          <span class="filter-count">${count}</span>
        </button>
      `
    )
    .join("");

  els.filters.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      state.activeCategory = button.dataset.category;
      const visible = filteredEmails();
      state.selectedId = visible[0]?.id ?? null;
      state.lastBulkMessage = "";
      render();
    });
  });
}

function renderModels(models) {
  els.models.innerHTML = Object.values(models)
    .map(
      (route) => `
        <div class="model-route">
          <strong>${title(route.task)}</strong>
          <span>${route.model}</span>
        </div>
      `
    )
    .join("");
}

function renderList() {
  const emails = filteredEmails();
  if (!emails.length) {
    els.list.innerHTML = `<div class="detail-empty">No mail in this category.</div>`;
    return;
  }

  els.list.innerHTML = emails.map(renderEmailCard).join("");

  els.list.querySelectorAll("[data-open-id]").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedId = button.dataset.openId;
      render();
    });
  });

  els.list.querySelectorAll("[data-select-id]").forEach((checkbox) => {
    checkbox.addEventListener("change", () => {
      if (checkbox.checked) {
        state.selectedForTrash.add(checkbox.dataset.selectId);
      } else {
        state.selectedForTrash.delete(checkbox.dataset.selectId);
      }
      state.lastBulkMessage = "";
      render();
    });
  });
}

function renderEmailCard(email) {
  const priorityLevel = email.priority >= 80 ? "high" : email.priority >= 50 ? "medium" : "low";
  const selected = state.selectedForTrash.has(email.id);
  const cleanable = email.actionPolicy.canRecommendTrash;

  return `
    <article class="email-card ${priorityLevel} ${email.id === state.selectedId ? "active" : ""}">
      <label class="select-mail ${cleanable ? "" : "disabled"}">
        <input type="checkbox" data-select-id="${email.id}" ${selected ? "checked" : ""} ${cleanable ? "" : "disabled"} />
        <span>${cleanable ? "Select" : "Protected"}</span>
      </label>
      <button class="email-open" type="button" data-open-id="${email.id}">
        <div class="email-meta">
          <span>${escapeHtml(email.senderName ?? email.from)}</span>
          <span>${formatDate(email.receivedAt)}</span>
        </div>
        <div class="email-subject">${escapeHtml(email.subject)}</div>
        <p class="email-preview">${escapeHtml(email.summary.bullets[0] ?? email.body)}</p>
        <div class="email-tags">
          <span class="pill ${priorityLevel}">${escapeHtml(email.categoryLabel)}</span>
          <span class="pill">${email.recommendedAction.replaceAll("_", " ")}</span>
        </div>
      </button>
    </article>
  `;
}

function renderDetail(email) {
  if (!email) {
    els.detail.className = "detail-empty";
    els.detail.innerHTML = "Select a mail to review its summary, policy, and draft.";
    return;
  }

  const priorityLevel = email.priority >= 80 ? "high" : email.priority >= 50 ? "medium" : "low";
  els.detail.className = "detail-panel";
  els.detail.innerHTML = `
    <div class="detail-header">
      <div class="email-meta">
        <span>${escapeHtml(email.from)}</span>
        <span>${formatDate(email.receivedAt)}</span>
      </div>
      <h2>${escapeHtml(email.subject)}</h2>
      <p>${escapeHtml(email.senderName ?? email.from)}</p>
      <div class="detail-tags">
        <span class="pill ${priorityLevel}">${escapeHtml(email.categoryLabel)}</span>
        <span class="confidence">${Math.round(email.confidence * 100)}% confidence</span>
        <span class="action-label">${email.recommendedAction.replaceAll("_", " ")}</span>
        ${email.attachmentRequest?.required ? `<span class="action-label">attachment needed</span>` : ""}
      </div>
    </div>
    <div class="detail-body">
      <section>
        <h3>Summary</h3>
        <ul class="summary-list">
          ${email.summary.bullets.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
        <p class="toast">${escapeHtml(email.summary.action)}</p>
      </section>

      <section>
        <h3>Policy</h3>
        <ul class="policy-list">
          ${email.actionPolicy.checks.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}
        </ul>
      </section>

      ${renderAlert(email)}
      ${renderAttachments(email)}
      ${renderDraft(email)}
      ${renderFeedback(email)}
    </div>
  `;

  bindDetailActions(email);
}

function renderAttachments(email) {
  if (!email.attachmentRequest?.required && !email.suggestedAttachments?.length) return "";

  const attachments = email.suggestedAttachments ?? [];
  const body = attachments.length
    ? attachments.map((item) => `
        <label class="attachment-option">
          <input type="checkbox" data-attachment-path="${escapeHtml(item.path)}" ${item.suggested ? "checked" : ""} />
          <span>${escapeHtml(item.name)}</span>
        </label>
      `).join("")
    : `<p class="toast">No local attachment found yet. Add your CV to private/cv.pdf or use Find CV files after connecting Gmail.</p>`;

  return `
    <section>
      <h3>Attachments</h3>
      <div class="attachment-list">${body}</div>
    </section>
  `;
}

function renderAlert(email) {
  if (!email.alert.shouldNotify) return "";

  return `
    <section>
      <h3>Alert</h3>
      <p>${escapeHtml(email.alert.message)}</p>
      <div class="action-row">
        <button class="secondary-button" type="button" data-action="notify">Notify here</button>
      </div>
      <div id="notifyToast" class="toast"></div>
    </section>
  `;
}

function renderDraft(email) {
  if (!email.draft) return "";

  return `
    <section>
      <h3>Draft</h3>
      <textarea id="draftBox" class="draft-box">${escapeHtml(email.draft)}</textarea>
      <div class="action-row">
        <button class="primary-button" type="button" data-action="send">Send approved draft</button>
        <button class="secondary-button" type="button" data-action="save-feedback">Save feedback</button>
      </div>
      <div id="sendToast" class="toast"></div>
    </section>
  `;
}

function renderFeedback(email) {
  return `
    <section>
      <h3>Learning</h3>
      <div class="action-row">
        <button class="secondary-button" type="button" data-action="mark-useful">Useful</button>
        <button class="danger-button" type="button" data-action="mark-trash">Trash review</button>
      </div>
      <div id="feedbackToast" class="toast">${escapeHtml(email.usefulness)} usefulness</div>
    </section>
  `;
}

function bindDetailActions(email) {
  const notifyButton = els.detail.querySelector('[data-action="notify"]');
  const sendButton = els.detail.querySelector('[data-action="send"]');
  const saveFeedbackButton = els.detail.querySelector('[data-action="save-feedback"]');
  const markUsefulButton = els.detail.querySelector('[data-action="mark-useful"]');
  const markTrashButton = els.detail.querySelector('[data-action="mark-trash"]');

  notifyButton?.addEventListener("click", async () => {
    const result = await postJson("/api/notify", { alert: email.alert });
    await showBrowserNotification(email.alert.message);
    els.detail.querySelector("#notifyToast").textContent = result.status;
  });

  sendButton?.addEventListener("click", async () => {
    const draft = els.detail.querySelector("#draftBox").value;
    const attachmentPaths = [...els.detail.querySelectorAll("[data-attachment-path]:checked")]
      .map((input) => input.dataset.attachmentPath);
    const result = await postJson("/api/send-draft", {
      emailId: email.id,
      draft,
      approved: true,
      attachmentRequest: email.attachmentRequest,
      attachmentPaths
    });
    els.detail.querySelector("#sendToast").textContent = result.message;
    await saveFeedback(email, { draftApproved: true });
  });

  saveFeedbackButton?.addEventListener("click", async () => {
    await saveFeedback(email, { draftRejected: false });
  });

  markUsefulButton?.addEventListener("click", async () => {
    await saveFeedback(email, { notes: "Marked useful by user." });
  });

  markTrashButton?.addEventListener("click", async () => {
    await saveFeedback(email, {
      correctedCategory: "low_value_loan_offer",
      notes: "Marked for trash review by user."
    });
  });
}

async function showBrowserNotification(message) {
  if (!("Notification" in window) || !message) return;
  if (Notification.permission === "default") {
    await Notification.requestPermission();
  }
  if (Notification.permission === "granted") {
    new Notification("Email AI Assistant", { body: message });
  }
}

async function saveFeedback(email, patch) {
  const result = await postJson("/api/feedback", {
    emailId: email.id,
    sender: email.from,
    category: email.category,
    ...patch
  });
  const target = els.detail.querySelector("#feedbackToast") ?? els.detail.querySelector("#sendToast");
  if (target) {
    target.textContent = result.ok ? "Learning saved" : "Feedback failed";
  }
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  return response.json();
}

function filteredEmails() {
  const emails = state.mailbox?.emails ?? [];
  if (state.activeCategory === "all") return emails;
  return emails.filter((email) => email.category === state.activeCategory);
}

function title(value) {
  return value.replaceAll("_", " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}
