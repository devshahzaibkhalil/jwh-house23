(function () {
  "use strict";

  const API_BASE = "/api";
  const BOT_REPLY_DELAY_MS = 100; // 0.10s delay before the bot's reply appears
  const STORAGE_KEY = "jwh_session_id";
  const OPEN_KEY = "jwh_chat_open";
  const SPEAKER_KEY = "jwh_speaker_enabled";
  const root = document.getElementById("jwh-chat-root");
  if (!root) return;

  const ICONS = {
    chat: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H8l-4 4V5z"/></svg>`,
    close: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>`,
    plus: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 5v14M5 12h14"/></svg>`,
    speaker: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 9v6h4l5 4V5L8 9H4z"/><path d="M16 9c1.3 1.7 1.3 4.3 0 6M18.5 6.5c3.2 3.2 3.2 7.8 0 11"/></svg>`,
    mic: `<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="3" width="6" height="12" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M9 21h6"/></svg>`,
    paperclip: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 11.5 12.5 20a6 6 0 0 1-8.5-8.5l9-9a4 4 0 0 1 5.7 5.7l-9.1 9.1a2 2 0 0 1-2.8-2.8l8.2-8.2"/></svg>`,
    send: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 3 18 9-18 9 4-9-4-9zM7 12h14"/></svg>`,
    home: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m3 11 9-8 9 8v9H3v-9zM9 20v-6h6v6"/></svg>`,
    building: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 21V5h10v16M14 9h6v12M7 8h2M11 8h1M7 12h2M11 12h1M7 16h2M11 16h1M17 12h1M17 16h1M2 21h20"/></svg>`,
    warehouse: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 21V9l9-5 9 5v12M7 21v-8h10v8M8 16h8M8 19h8"/></svg>`,
    land: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 18c4-4 7 2 11-2s5-1 7 1M3 13c3-3 6 1 9-2s6-2 9 0M5 8l3-4 3 4"/></svg>`,
    projects: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20V7h6v13M10 20V4h6v16M16 20v-9h4v9M2 20h20"/></svg>`,
    mapPin: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0z"/><circle cx="12" cy="10" r="2.5"/></svg>`,
    users: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8M22 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    help: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.7 2.7 0 1 1 4.8 1.7c-.9.9-2.3 1.4-2.3 3M12 17h.01"/></svg>`,
    info: `<svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 11v6M12 7h.01"/></svg>`,
    funding: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16v11H4zM4 10h16M8 15h3M16 4v3M8 4v3"/></svg>`,
    buy: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M3 12h18M12 3v18M5 7l7-4 7 4v13H5z"/></svg>`,
    sell: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 20V9l8-5 8 5v11M8 20v-6h8v6M16 7l4-3M18 2l2 2-2 2"/></svg>`,
    question: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 5h16v11H8l-4 4V5z"/><path d="M9.5 9a2.6 2.6 0 1 1 4.7 1.6c-.8.8-2.2 1.3-2.2 2.8M12 16h.01"/></svg>`,
    check: `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg>`,
  };

  const STATE_OPTIONS = [
    ["AL","Alabama"],["AK","Alaska"],["AZ","Arizona"],["AR","Arkansas"],["CA","California"],
    ["CO","Colorado"],["CT","Connecticut"],["DE","Delaware"],["FL","Florida"],["GA","Georgia"],
    ["HI","Hawaii"],["ID","Idaho"],["IL","Illinois"],["IN","Indiana"],["IA","Iowa"],
    ["KS","Kansas"],["KY","Kentucky"],["LA","Louisiana"],["ME","Maine"],["MD","Maryland"],
    ["MA","Massachusetts"],["MI","Michigan"],["MN","Minnesota"],["MS","Mississippi"],["MO","Missouri"],
    ["MT","Montana"],["NE","Nebraska"],["NV","Nevada"],["NH","New Hampshire"],["NJ","New Jersey"],
    ["NM","New Mexico"],["NY","New York"],["NC","North Carolina"],["ND","North Dakota"],["OH","Ohio"],
    ["OK","Oklahoma"],["OR","Oregon"],["PA","Pennsylvania"],["RI","Rhode Island"],["SC","South Carolina"],
    ["SD","South Dakota"],["TN","Tennessee"],["TX","Texas"],["UT","Utah"],["VT","Vermont"],
    ["VA","Virginia"],["WA","Washington"],["WV","West Virginia"],["WI","Wisconsin"],["WY","Wyoming"],["DC","District of Columbia"]
  ];


  const WELCOME_SLIDES = [
    {
      image: "/static/img/welcome/sell-home.webp",
      eyebrow: "Sell with confidence",
      title: "Selling a House",
      description: "Share the property location, condition and preferred timeline. The team can review the information and discuss available selling options without forcing you into a public listing.",
      action: "Sell a Property",
      actionLabel: "Start a Seller Enquiry"
    },
    {
      image: "/static/img/welcome/buy-home.webp",
      eyebrow: "Buy with purpose",
      title: "Buying a Property",
      description: "Tell us the city, property type, buying range and intended use. Your requirements are organised into a clear property search profile for professional review.",
      action: "Buy a Property",
      actionLabel: "Share Buying Requirements"
    },
    {
      image: "/static/img/welcome/move-ready.webp",
      eyebrow: "Residential opportunities",
      title: "Move-In Ready Homes",
      description: "Explore residential opportunities that may suit personal buyers or long-term investors. Availability, pricing and property facts must be confirmed for each individual opportunity.",
      action: "Recent Real Estate Projects",
      actionLabel: "Explore Recent Projects"
    },
    {
      image: "/static/img/welcome/investment-home.webp",
      eyebrow: "Investment planning",
      title: "Renovation Opportunities",
      description: "Review properties that may require updates, repairs or repositioning. Investors should independently verify condition, repair costs, title and potential returns before proceeding.",
      action: "Join the Buyers Network",
      actionLabel: "Join the Buyers Network"
    },
    {
      image: "/static/img/welcome/new-construction.webp",
      eyebrow: "Property requirements",
      title: "New Construction and Growth",
      description: "Share the features, location and budget that matter to you. The team can use those details to understand the type of opportunity you are seeking.",
      action: "Ask a Real Estate Question",
      actionLabel: "Ask About This Property Type"
    }
  ];

  const PROPERTY_CARD_DATA = {
    "Single-Family Home": { image: "/static/img/welcome/sell-home.webp", detail: "Ideal for owner occupants or buyers seeking a traditional detached home." },
    "Apartment": { image: "/static/img/welcome/investment-home.webp", detail: "Suitable for urban living, rental ownership or multi-unit investment planning." },
    "Multifamily Property": { image: "/static/img/welcome/investment-home.webp", detail: "Designed for investors comparing multiple income-producing residential units." },
    "Commercial Property": { image: "/static/img/welcome/new-construction.webp", detail: "Use this for commercial buildings, business sites and mixed operating spaces." },
    "Warehouse": { image: "/static/img/welcome/new-construction.webp", detail: "Useful for storage, logistics, fulfilment or industrial operating requirements." },
    "Vacant Land": { image: "/static/img/welcome/move-ready.webp", detail: "For open parcels, buildable lots and undeveloped sites under review." },
    "Condominium": { image: "/static/img/property-types/condominium.jpg", detail: "A private residence within a shared community with common amenities." },
    "Townhouse": { image: "/static/img/property-types/townhouse.jpg", detail: "A multi-level attached home often suited to residential buyers and investors." },
    "Duplex": { image: "/static/img/property-types/duplex.jpg", detail: "A two-unit residential property often considered for living and rental income." },
    "Triplex": { image: "/static/img/property-types/triplex.jpg", detail: "A three-unit residential asset for investors seeking added rental flexibility." },
    "Fourplex": { image: "/static/img/welcome/investment-home.webp", detail: "A four-unit residential building for structured small multifamily ownership." },
    "Apartment Building": { image: "/static/img/property-types/apartment-building.jpg", detail: "For larger residential rental buildings with multiple units and income potential." },
    "Mobile or Manufactured Home": { image: "/static/img/property-types/mobile-manufactured-home.jpg", detail: "A manufactured or mobile residential home with location and ownership factors." },
    "Rental Property": { image: "/static/img/property-types/rental-property.jpg", detail: "Designed for buyers or sellers focused on income-producing residential property." },
    "Tenant-Occupied Property": { image: "/static/img/property-types/tenant-occupied-property.jpg", detail: "For properties currently leased or occupied by renters with active tenancy." },
    "Office Building": { image: "/static/img/property-types/office-building.jpg", detail: "Suited to administrative, professional or business office occupancy." },
    "Retail Property": { image: "/static/img/property-types/retail-property.jpg", detail: "For storefronts, shopping sites and customer-facing commercial space." },
    "Industrial Property": { image: "/static/img/property-types/industrial-property.jpg", detail: "Suitable for production, industrial use, logistics, yard operations or light manufacturing." },
    "Mixed-Use Property": { image: "/static/img/welcome/new-construction.webp", detail: "Combines residential, retail or office uses within one property opportunity." },
    "Medical Building": { image: "/static/img/property-types/medical-building.jpg", detail: "For healthcare, treatment, specialist office or medical-use property review." },
    "Agricultural Land": { image: "/static/img/property-types/agricultural-land.jpg", detail: "Open land intended for farming, cultivation, crops or agricultural operations." },
    "Farm or Ranch": { image: "/static/img/property-types/farm-ranch.jpg", detail: "A rural home, farmstead or ranch property with land and operational requirements." },
    "Development Land": { image: "/static/img/property-types/development-land.jpg", detail: "Land being prepared or considered for construction, subdivision or future development." },
    "Storage Facility": { image: "/static/img/property-types/storage-facility.jpg", detail: "A self-storage or specialty storage facility for business use, investment or acquisition." },
    "Hospitality Property": { image: "/static/img/property-types/hospitality-property.jpg", detail: "For hotels, lodging, guest accommodation and hospitality-oriented property review." },
    "Car Wash": { image: "/static/img/property-types/car-wash.jpg", detail: "A specialty commercial property designed for automated or full-service vehicle washing." },
    "Other": { image: "/static/img/welcome/buy-home.webp", detail: "Choose this when the property does not match the listed categories above." }
  };

  root.innerHTML = `
    <button class="jwh-bubble" id="jwh-bubble" aria-label="Open James Wholesale Homes chat">
      <img class="jwh-bubble-logo" src="/static/img/jwh-bubble-logo.png?v=30" alt=""><span class="jwh-dot" aria-hidden="true"></span>
    </button>
    <div class="jwh-bubble-teaser" id="jwh-bubble-teaser" hidden>
      <button class="jwh-bubble-teaser-main" id="jwh-bubble-teaser-open" type="button">
        <img src="/static/img/jwh-bubble-logo.png?v=30" alt="">
        <span><strong>Need help with a property?</strong><small>Open the James Wholesale Homes assistant.</small></span>
      </button>
      <button class="jwh-bubble-teaser-close" id="jwh-bubble-teaser-close" type="button" aria-label="Dismiss welcome prompt">${ICONS.close}</button>
    </div>
    <section class="jwh-window" id="jwh-window" aria-label="James Wholesale Homes Real Estate Assistant">
      <header class="jwh-header">
        <span class="jwh-brand-logo-wrap"><img class="jwh-brand-logo" src="/static/img/jwh-logo-header.png?v=30" alt="James Wholesale Homes"></span>
        <div class="jwh-header-info">
          <div class="jwh-header-title">James Wholesale Homes Assistant</div>
          <div class="jwh-header-status"><span class="dot"></span><span id="jwh-office-status">Enquiries accepted</span></div>
        </div>
        <div class="jwh-header-actions">
          <button id="jwh-speaker" type="button" title="Read answers aloud" aria-label="Read answers aloud">${ICONS.speaker}</button>
          <button id="jwh-newchat" type="button" title="Start new chat" aria-label="Start new chat">${ICONS.plus}</button>
          <button id="jwh-close" type="button" title="Close chat" aria-label="Close chat">${ICONS.close}</button>
        </div>
      </header>
      <div class="jwh-progress-wrap" id="jwh-progress-wrap" hidden>
        <div class="jwh-progress-meta"><span id="jwh-progress-label"></span><span id="jwh-progress-count"></span></div>
        <div class="jwh-progress-track"><span id="jwh-progress-bar"></span></div>
      </div>
      <div class="jwh-attachment-panel" id="jwh-attachment-panel" hidden>
        <button type="button" data-attach-action="file">Upload a file</button>
        <button type="button" data-attach-action="link">Add a property link</button>
      </div>
      <div class="jwh-messages" id="jwh-messages" aria-live="polite"></div>
      <div class="jwh-action-dock" id="jwh-action-dock">
        <div class="jwh-options" id="jwh-options"></div>
        <div class="jwh-input-area" id="jwh-input-area"></div>
      </div>
    </section>
    <div class="jwh-modal-backdrop" id="jwh-modal" hidden>
      <div class="jwh-modal-card" role="dialog" aria-modal="true">
        <h3>Start a new chat?</h3>
        <p>The current window will be cleared. Any submitted lead will remain stored securely.</p>
        <div class="jwh-modal-actions">
          <button class="secondary" id="jwh-modal-cancel">Keep Current Chat</button>
          <button class="primary" id="jwh-modal-confirm">Start New Chat</button>
        </div>
      </div>
    </div>
    <div class="jwh-showcase-modal" id="jwh-showcase-modal" hidden>
      <div class="jwh-showcase-dialog" role="dialog" aria-modal="true" aria-labelledby="jwh-showcase-title">
        <button class="jwh-showcase-close" id="jwh-showcase-close" type="button" aria-label="Close property details">${ICONS.close}</button>
        <img id="jwh-showcase-image" alt="">
        <div class="jwh-showcase-copy">
          <span class="jwh-showcase-eyebrow" id="jwh-showcase-eyebrow"></span>
          <h3 id="jwh-showcase-title"></h3>
          <p id="jwh-showcase-description"></p>
          <button class="jwh-primary-action" id="jwh-showcase-action" type="button"></button>
        </div>
      </div>
    </div>
    <input type="file" id="jwh-global-file" hidden accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx,.txt">
  `;
  const $ = (id) => document.getElementById(id);
  const bubble = $("jwh-bubble");
  const bubbleTeaser = $("jwh-bubble-teaser");
  const win = $("jwh-window");
  const messagesEl = $("jwh-messages");
  const optionsEl = $("jwh-options");
  const inputArea = $("jwh-input-area");
  const attachmentPanel = $("jwh-attachment-panel");
  const modal = $("jwh-modal");
  const showcaseModal = $("jwh-showcase-modal");
  let carouselTimer = null;
  let bubbleTeaserTimer = null;
  let activeShowcaseSlide = null;
  let sessionId = sessionStorage.getItem(STORAGE_KEY) || null;
  let currentStep = null;
  let currentInputType = null;
  let currentTurn = null;
  let speakerEnabled = sessionStorage.getItem(SPEAKER_KEY) === "1";
  let speechPaused = false;
  let speechQueue = [];
  let speechGeneration = 0;
  let availableVoices = [];
  let speechRecognition = null;

  setOfficeStatus();
  initialiseSpeechVoices();
  updateSpeakerButton();

  if (sessionStorage.getItem(OPEN_KEY) === "1") {
    openChat();
  } else {
    showBubbleTeaser();
  }

  bubble.addEventListener("click", openChat);
  $("jwh-bubble-teaser-open")?.addEventListener("click", openChat);
  $("jwh-bubble-teaser-close")?.addEventListener("click", hideBubbleTeaser);
  $("jwh-close").addEventListener("click", closeChat);
  $("jwh-newchat").addEventListener("click", () => { modal.hidden = false; });
  $("jwh-modal-cancel").addEventListener("click", () => { modal.hidden = true; });
  $("jwh-modal-confirm").addEventListener("click", startNewChat);
  $("jwh-speaker").addEventListener("click", toggleSpeaker);
  $("jwh-showcase-close").addEventListener("click", closeShowcaseModal);
  showcaseModal.addEventListener("click", (event) => { if (event.target === showcaseModal) closeShowcaseModal(); });
  $("jwh-showcase-action").addEventListener("click", () => {
    if (!activeShowcaseSlide) return;
    const action = activeShowcaseSlide.action;
    closeShowcaseModal();
    chooseOption(action);
  });
  root.addEventListener("pointerdown", (event) => {
    const button = event.target.closest(".jwh-menu-grid button, .jwh-options button, .jwh-property-grid button, .jwh-condition-grid button");
    if (!button) return;
    button.parentElement?.querySelectorAll(".is-selected").forEach((item) => item.classList.remove("is-selected"));
    button.classList.add("is-selected");
  });
  attachmentPanel.addEventListener("click", handleAttachmentAction);
  $("jwh-global-file").addEventListener("change", (event) => uploadFile(event.target.files[0], "Other"));

  function setOfficeStatus() {
    $("jwh-office-status").textContent = "Enquiries accepted";
  }

  function showBubbleTeaser() {
    if (!bubbleTeaser) return;
    bubbleTeaser.hidden = false;
    window.clearTimeout(bubbleTeaserTimer);
    requestAnimationFrame(() => bubbleTeaser.classList.add("visible"));
    bubbleTeaserTimer = window.setTimeout(() => hideBubbleTeaser(), 15000);
  }

  function hideBubbleTeaser() {
    if (!bubbleTeaser) return;
    window.clearTimeout(bubbleTeaserTimer);
    bubbleTeaser.classList.remove("visible");
    window.setTimeout(() => {
      if (bubbleTeaser && !bubbleTeaser.classList.contains("visible")) bubbleTeaser.hidden = true;
    }, 180);
  }

  function openChat() {
    hideBubbleTeaser();
    win.classList.add("open");
    sessionStorage.setItem(OPEN_KEY, "1");
    bubble.classList.remove("has-unread");
    if (!sessionId || messagesEl.children.length === 0) startChat();
  }

  function closeChat() {
    stopWelcomeCarousel();
    win.classList.remove("open");
    sessionStorage.setItem(OPEN_KEY, "0");
    speechGeneration += 1;
    speechQueue = [];
    speechPaused = false;
    window.speechSynthesis?.cancel();
    updateSpeakerButton();
  }

  async function apiFetch(url, options) {
    try {
      const response = await fetch(url, options);
      const data = await response.json();
      if (!response.ok) throw Object.assign(new Error(data.error || "The action could not be completed."), { data });
      return data;
    } catch (error) {
      appendMessage("bot", error.message || "The action could not be completed. Please try again.", "error");
      throw error;
    }
  }

  async function startChat() {
    const data = await apiFetch(`${API_BASE}/chat/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId }),
    });
    sessionId = data.session_id;
    sessionStorage.setItem(STORAGE_KEY, sessionId);
    messagesEl.innerHTML = "";
    if (data.history?.length) {
      data.history.forEach((message) => appendMessage(message.sender, message.content, message.validation_status === "invalid" ? "error" : ""));
    }
    renderBotTurn(data, !data.history?.length);
  }

  async function startNewChat() {
    modal.hidden = true;
    speechGeneration += 1;
    speechQueue = [];
    speechPaused = false;
    window.speechSynthesis?.cancel();
    const data = await apiFetch(`${API_BASE}/chat/new`, { method: "POST" });
    sessionId = data.session_id;
    sessionStorage.setItem(STORAGE_KEY, sessionId);
    messagesEl.innerHTML = "";
    optionsEl.innerHTML = "";
    inputArea.innerHTML = "";
    renderBotTurn(data, true);
  }

  async function sendMessage(payload) {
    try {
      return await apiFetch(`${API_BASE}/chat/message`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, ...payload }),
      });
    } catch (error) {
      if (error.data?.suggestion) renderSuggestionButtons(error.data.suggestion);
      return null;
    }
  }

  function scrollConversationToBottom() {
    requestAnimationFrame(() => {
      messagesEl.scrollTop = messagesEl.scrollHeight;
    });
  }

  function appendMessage(sender, text, cls) {
    if (!text) return;
    const div = document.createElement("div");
    div.className = `jwh-msg ${sender}${cls ? " " + cls : ""}`;
    div.textContent = text;
    messagesEl.appendChild(div);
    scrollConversationToBottom();
  }

  function showTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.className = "jwh-typing";
    indicator.setAttribute("aria-label", "Assistant is typing");
    indicator.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(indicator);
    scrollConversationToBottom();
    return indicator;
  }

  function renderBotTurn(data, appendPrompt = true) {
    stopWelcomeCarousel();
    currentStep = data.step;
    currentInputType = data.input_type;
    currentTurn = data;
    win.classList.toggle("welcome-screen", data.input_type === "welcome_menu");
    updateProgress(data.progress);
    optionsEl.innerHTML = "";
    inputArea.innerHTML = "";
    attachmentPanel.hidden = true;

    const completeTurn = () => {
      const showPromptBubble = appendPrompt && data.prompt && data.input_type !== "welcome_menu";
      if (showPromptBubble) appendMessage("bot", data.prompt);
      if (data.development_code) appendMessage("bot", `Development verification code: ${data.development_code}`, "dev");
      if (speakerEnabled && data.prompt && data.input_type !== "welcome_menu") speakText(data.prompt);

      if (data.reference_number) renderSubmissionSummary(data);

      if (data.options?.length && !["welcome_menu", "property_cards", "condition_cards", "projects", "locations"].includes(data.input_type)) {
        renderOptionButtons(data.options);
      }
      renderInputForType(data);
      scrollConversationToBottom();
    };

    if (appendPrompt && data.prompt && data.input_type !== "welcome_menu") {
      const typing = showTypingIndicator();
      window.setTimeout(() => {
        typing.remove();
        completeTurn();
      }, BOT_REPLY_DELAY_MS);
    } else {
      completeTurn();
    }
  }

  function updateProgress(progress) {
    const wrap = $("jwh-progress-wrap");
    if (!progress) { wrap.hidden = true; return; }
    wrap.hidden = false;
    $("jwh-progress-label").textContent = progress.label;
    $("jwh-progress-count").textContent = `Step ${progress.current} of ${progress.total}`;
    $("jwh-progress-bar").style.width = `${progress.percent}%`;
  }

  function renderStatistics(stats) {
    const panel = document.createElement("div");
    panel.className = "jwh-stat-strip";
    stats.slice(0, 2).forEach((stat) => {
      const item = document.createElement("div");
      item.innerHTML = `<strong>${escapeHtml(stat.value)}</strong><span>${escapeHtml(stat.label)}</span>`;
      panel.appendChild(item);
    });
    messagesEl.appendChild(panel);
    scrollConversationToBottom();
  }

  function renderSubmissionSummary(data) {
    const card = document.createElement("div");
    card.className = "jwh-confirmation-card";
    card.innerHTML = `
      <div class="jwh-confirmation-icon">${ICONS.check}</div>
      <div><strong>Reference ${escapeHtml(data.reference_number)}</strong>
      <span>${escapeHtml(data.preferred_contact_day || "No day selected")} · ${escapeHtml(data.preferred_contact_time || "No time selected")}</span>
      <span>${escapeHtml(data.masked_email || "")} ${escapeHtml(data.masked_phone || "")}</span></div>`;
    messagesEl.appendChild(card);
    scrollConversationToBottom();
  }

  function renderOptionButtons(options, className = "") {
    options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = className;
      button.textContent = option;
      button.addEventListener("click", () => chooseOption(option, button));
      optionsEl.appendChild(button);
    });
  }

  async function chooseOption(option, selectedButton = null) {
    if (selectedButton) {
      selectedButton.classList.add("is-selected");
      selectedButton.setAttribute("aria-pressed", "true");
    }
    appendMessage("user", option);
    await new Promise((resolve) => window.setTimeout(resolve, 100));
    optionsEl.innerHTML = "";
    const result = await sendMessage({ input: option });
    if (result) renderBotTurn(result);
  }

  function renderSuggestionButtons(suggestion) {
    optionsEl.innerHTML = "";
    const button = document.createElement("button");
    button.textContent = `Use ${suggestion}`;
    button.addEventListener("click", () => chooseOption(suggestion));
    optionsEl.appendChild(button);
  }

  function renderInputForType(data) {
    const type = data.input_type;
    if (type === "terminal") return renderTerminalActions();
    if (type === "welcome_menu") return renderWelcomeMenu(data.options || []);
    if (type === "property_cards") return renderPropertyCards(data.options || []);
    if (type === "condition_cards") return renderConditionCards(data.options || []);
    if (type === "projects") return renderProjects(data.projects || [], data.options || []);
    if (type === "locations") return renderLocations(data.locations || [], data.options || []);
    if (type === "funding_numbers") return renderFundingNumbers();
    if (type === "funding_amounts") return renderFundingAmounts();
    if (type === "seller_financials") return renderSellerFinancials();
    if (type === "location") return renderLocationForm();
    if (type === "currency_range") return renderCurrencyRange();
    if (type === "property_specifications") return renderSpecifications(data.property_type);
    if (type === "contact_preference") return renderContactPreference(data);
    if (type === "attachment_optional") return renderAttachmentStep();
    if (type === "consent") return renderConsent();
    if (type === "review") return renderReview(data.review_data || data.state_preview || {});
    if (type === "date") return renderDateInput();
    return renderTextInput(type);
  }

  function renderWelcomeMenu(options) {
    const groups = [
      { title: "Start an Enquiry", items: ["Sell a Property", "Buy a Property", "Submit a Funding Deal"] },
      { title: "Explore", items: ["Recent Real Estate Projects", "Featured Minnesota Locations", "Join the Buyers Network"] },
      { title: "Help and Information", items: ["Real Estate FAQs", "About James Wholesale Homes"] },
    ];
    inputArea.innerHTML = `<div class="jwh-menu-groups"><div class="jwh-welcome-intro"><strong>Welcome to James Wholesale Homes</strong></div></div>`;
    const container = inputArea.querySelector(".jwh-menu-groups");
    renderWelcomeCarousel(container);
    groups.forEach((group) => {
      const availableItems = group.items.filter((item) => options.includes(item));
      if (!availableItems.length) return;
      const section = document.createElement("section");
      section.className = "jwh-menu-section";
      section.innerHTML = `<h3>${group.title}</h3><div class="jwh-menu-grid"></div>`;
      const grid = section.querySelector(".jwh-menu-grid");
      availableItems.forEach((item) => {
        const button = document.createElement("button");
        button.type = "button";
        button.innerHTML = `<span class="jwh-menu-icon">${menuIcon(item)}</span><span class="jwh-menu-title">${escapeHtml(item)}</span><small>${menuDescription(item)}</small>`;
        button.addEventListener("click", () => chooseOption(item, button));
        grid.appendChild(button);
      });
      container.appendChild(section);
    });
    inputArea.scrollTop = 0;
  }

  function renderWelcomeCarousel(container) {
    const carousel = document.createElement("section");
    carousel.className = "jwh-welcome-carousel";
    carousel.setAttribute("aria-label", "Featured real estate services");
    carousel.innerHTML = `
      <div class="jwh-carousel-viewport">
        <div class="jwh-carousel-track"></div>
        <button class="jwh-carousel-arrow previous" type="button" aria-label="Previous image">‹</button>
        <button class="jwh-carousel-arrow next" type="button" aria-label="Next image">›</button>
      </div>
      <div class="jwh-carousel-dots" role="tablist" aria-label="Choose featured image"></div>`;
    const track = carousel.querySelector(".jwh-carousel-track");
    const dots = carousel.querySelector(".jwh-carousel-dots");
    let currentIndex = 0;

    WELCOME_SLIDES.forEach((slide, index) => {
      const card = document.createElement("button");
      card.className = "jwh-carousel-slide";
      card.type = "button";
      card.setAttribute("aria-label", `View details: ${slide.title}`);
      card.innerHTML = `<img src="${escapeAttribute(slide.image)}" alt="${escapeAttribute(slide.title)}"><span class="jwh-carousel-overlay"><small>${escapeHtml(slide.eyebrow)}</small><strong>${escapeHtml(slide.title)}</strong><em>View details</em></span>`;
      card.addEventListener("click", () => openShowcaseModal(slide));
      track.appendChild(card);

      const dot = document.createElement("button");
      dot.type = "button";
      dot.setAttribute("role", "tab");
      dot.setAttribute("aria-label", `Show ${slide.title}`);
      dot.addEventListener("click", () => showSlide(index));
      dots.appendChild(dot);
    });

    function showSlide(index) {
      currentIndex = (index + WELCOME_SLIDES.length) % WELCOME_SLIDES.length;
      track.style.transform = `translateX(-${currentIndex * 100}%)`;
      dots.querySelectorAll("button").forEach((dot, dotIndex) => {
        dot.classList.toggle("active", dotIndex === currentIndex);
        dot.setAttribute("aria-selected", dotIndex === currentIndex ? "true" : "false");
      });
    }

    carousel.querySelector(".previous").addEventListener("click", () => showSlide(currentIndex - 1));
    carousel.querySelector(".next").addEventListener("click", () => showSlide(currentIndex + 1));
    carousel.addEventListener("mouseenter", stopWelcomeCarousel);
    carousel.addEventListener("mouseleave", () => startWelcomeCarousel(() => showSlide(currentIndex + 1)));
    showSlide(0);
    startWelcomeCarousel(() => showSlide(currentIndex + 1));
    container.appendChild(carousel);
  }

  function startWelcomeCarousel(callback) {
    stopWelcomeCarousel();
    carouselTimer = window.setInterval(callback, 4200);
  }

  function stopWelcomeCarousel() {
    if (carouselTimer) window.clearInterval(carouselTimer);
    carouselTimer = null;
  }

  function openShowcaseModal(slide) {
    activeShowcaseSlide = slide;
    stopWelcomeCarousel();
    $("jwh-showcase-image").src = slide.image;
    $("jwh-showcase-image").alt = slide.title;
    $("jwh-showcase-eyebrow").textContent = slide.eyebrow;
    $("jwh-showcase-title").textContent = slide.title;
    $("jwh-showcase-description").textContent = slide.description;
    $("jwh-showcase-action").textContent = slide.actionLabel;
    showcaseModal.hidden = false;
  }

  function closeShowcaseModal() {
    showcaseModal.hidden = true;
    activeShowcaseSlide = null;
  }

  function menuIcon(item) {
    const icons = {
      "Sell a Property": ICONS.sell,
      "Buy a Property": ICONS.buy,
      "Submit a Funding Deal": ICONS.funding,
      "Recent Real Estate Projects": ICONS.projects,
      "Featured Minnesota Locations": ICONS.mapPin,
      "Join the Buyers Network": ICONS.users,
      "Real Estate FAQs": ICONS.help,
      "About James Wholesale Homes": ICONS.info,
      "Ask a Real Estate Question": ICONS.question,
    };
    return icons[item] || ICONS.home;
  }

  function menuDescription(item) {
    const descriptions = {
      "Sell a Property": "Request a review for a house, rental, land or commercial property.",
      "Buy a Property": "Share your location, property type and buying range.",
      "Submit a Funding Deal": "Provide investment property and deal information.",
      "Recent Real Estate Projects": "Review real buying, selling and renovation projects.",
      "Featured Minnesota Locations": "Explore markets currently featured by the company.",
      "Join the Buyers Network": "Receive matching off-market and wholesale opportunities.",
      "Real Estate FAQs": "Browse approved answers by real estate topic.",
      "About James Wholesale Homes": "Learn about the company and its services.",
      "Ask a Real Estate Question": "Send a question for team review.",
    };
    return descriptions[item] || "Continue";
  }

  function propertyIcon(name) {
    if (/Warehouse|Storage|Industrial/.test(name)) return ICONS.warehouse;
    if (/Apartment|Multifamily|Commercial|Office|Retail|Medical|Hospitality/.test(name)) return ICONS.building;
    if (/Land|Farm|Ranch|Agricultural|Development/.test(name)) return ICONS.land;
    return ICONS.home;
  }

  function propertyCardDetails(name) {
    const fallback = { image: "/static/img/welcome/buy-home.webp", detail: "Select this property type to continue with a relevant real estate enquiry." };
    return PROPERTY_CARD_DATA[name] || fallback;
  }

  function renderPropertyCards(options) {
    inputArea.innerHTML = `<div class="jwh-property-grid"></div>`;
    const grid = inputArea.firstElementChild;
    options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.className = option.includes("View All") || option.includes("Back to") ? "jwh-property-more" : "jwh-property-card";
      if (option.includes("View All") || option.includes("Back to")) {
        button.innerHTML = `<span>${escapeHtml(option)}</span>`;
      } else {
        const details = propertyCardDetails(option);
        button.innerHTML = `
          <span class="jwh-property-thumb">
            <img src="${escapeAttribute(details.image)}" alt="${escapeAttribute(option)}">
            <span class="jwh-property-thumb-overlay"></span>
            <span class="jwh-property-icon">${propertyIcon(option)}</span>
          </span>
          <span class="jwh-property-copy">
            <strong>${escapeHtml(option)}</strong>
            <small>${escapeHtml(details.detail)}</small>
          </span>`;
      }
      button.addEventListener("click", () => chooseOption(option, button));
      grid.appendChild(button);
    });
  }

  function renderConditionCards(options) {
    inputArea.innerHTML = `<div class="jwh-condition-grid"></div>`;
    const grid = inputArea.firstElementChild;
    options.forEach((option) => {
      const button = document.createElement("button");
      button.type = "button";
      button.innerHTML = `<strong>${escapeHtml(option)}</strong><span>${conditionDescription(option)}</span>`;
      button.addEventListener("click", () => chooseOption(option, button));
      grid.appendChild(button);
    });
  }

  function conditionDescription(value) {
    const descriptions = {
      "Excellent": "Recently updated or move-in ready.", "Good": "Generally maintained with limited work.",
      "Needs cosmetic updates": "Paint, flooring or fixtures may need attention.", "Needs minor repairs": "Several smaller repairs are expected.",
      "Needs major repairs": "Significant renovation may be required.", "Fire damaged": "Fire or smoke damage is present.",
      "Water damaged": "Water intrusion or related damage is present.", "Structural concerns": "Foundation or structural review may be needed.",
      "Condemned": "Government restrictions or orders may apply.", "Unknown": "The condition has not been fully assessed."
    };
    return descriptions[value] || "";
  }

  function renderProjects(projects, actions) {
    const container = document.createElement("div");
    container.className = "jwh-content-list";
    if (!projects.length) {
      container.innerHTML = `<div class="jwh-empty-state"><strong>No public projects have been added yet.</strong><span>The administrator can publish real buying, selling and renovation projects from the dashboard.</span></div>`;
    }
    projects.forEach((project) => {
      const card = document.createElement("article");
      card.className = "jwh-project-card";
      const image = project.image_paths?.[0];
      card.innerHTML = `${image ? `<img src="${escapeAttribute(image)}" alt="">` : `<div class="jwh-project-placeholder">${propertyIcon(project.property_type || "Property")}</div>`}
        <div><span class="jwh-kicker">${escapeHtml(project.status || project.project_category || "Project")}</span>
        <strong>${escapeHtml(project.title)}</strong>
        <small>${escapeHtml(project.public_location || [project.city, project.state].filter(Boolean).join(", "))}</small>
        <p>${escapeHtml(project.description || "")}</p></div>`;
      container.appendChild(card);
    });
    inputArea.appendChild(container);
    optionsEl.innerHTML = "";
    renderOptionButtons(actions);
  }

  function renderLocations(locations, actions) {
    const container = document.createElement("div");
    container.className = "jwh-location-grid";
    locations.forEach((location) => {
      const card = document.createElement("article");
      card.innerHTML = `<span class="jwh-kicker">${escapeHtml(location.service_tier || "Featured")}</span>
        <strong>${escapeHtml(location.city)}, ${escapeHtml(location.state)}</strong>
        <small>${escapeHtml(location.county || "Minnesota")}</small>
        <p>${escapeHtml(location.description || "Real estate enquiries are reviewed based on current availability and service coverage.")}</p>
        <div>${(location.property_categories || []).map((item) => `<span class="jwh-chip">${escapeHtml(item)}</span>`).join("")}</div>`;
      container.appendChild(card);
    });
    inputArea.appendChild(container);
    optionsEl.innerHTML = "";
    renderOptionButtons(actions);
  }

  function renderFundingNumbers() {
    inputArea.innerHTML = formCard(`
      ${moneyField("jwh-purchase-price", "Purchase price")}
      ${moneyField("jwh-reno-budget", "Renovation budget")}
      ${moneyField("jwh-arv", "Estimated ARV")}
      ${continueButton("jwh-funding-numbers-submit")}`);
    $("jwh-funding-numbers-submit").addEventListener("click", async () => {
      const payload = {
        purchase_price: value("jwh-purchase-price"), renovation_budget: value("jwh-reno-budget"), arv: value("jwh-arv")
      };
      appendMessage("user", `Purchase ${formatMoney(payload.purchase_price)}, renovation ${formatMoney(payload.renovation_budget)}, ARV ${formatMoney(payload.arv)}`);
      const result = await sendMessage(payload); if (result) renderBotTurn(result);
    });
    bindCurrencyInputs();
  }

  function renderFundingAmounts() {
    inputArea.innerHTML = formCard(`
      ${moneyField("jwh-requested-funding", "Requested funding")}
      ${moneyField("jwh-contribution", "Your contribution")}
      ${continueButton("jwh-funding-amounts-submit")}`);
    $("jwh-funding-amounts-submit").addEventListener("click", async () => {
      const payload = { requested_funding: value("jwh-requested-funding"), borrower_contribution: value("jwh-contribution") };
      appendMessage("user", `Requested ${formatMoney(payload.requested_funding)}, contribution ${formatMoney(payload.borrower_contribution)}`);
      const result = await sendMessage(payload); if (result) renderBotTurn(result);
    });
    bindCurrencyInputs();
  }

  function renderSellerFinancials() {
    inputArea.innerHTML = formCard(`
      <label>Mortgage on property<select id="jwh-has-mortgage"><option value="">Not sure</option><option>Yes</option><option>No</option></select></label>
      ${moneyField("jwh-mortgage-balance", "Approximate mortgage balance", false)}
      <label>Known liens<select id="jwh-has-liens"><option value="">Not sure</option><option>Yes</option><option>No</option></select></label>
      <label>Property taxes current<select id="jwh-taxes-current"><option value="">Not sure</option><option>Yes</option><option>No</option></select></label>
      <label>Currently in foreclosure<select id="jwh-foreclosure"><option value="">Not sure</option><option>Yes</option><option>No</option></select></label>
      ${continueButton("jwh-financial-submit")}`);
    bindCurrencyInputs();
    $("jwh-financial-submit").addEventListener("click", async () => {
      const details = {
        has_mortgage: value("jwh-has-mortgage"), mortgage_balance: rawMoney("jwh-mortgage-balance"),
        has_liens: value("jwh-has-liens"), taxes_current: value("jwh-taxes-current"), in_foreclosure: value("jwh-foreclosure")
      };
      appendMessage("user", "Property financial details provided");
      const result = await sendMessage({ seller_financials: details }); if (result) renderBotTurn(result);
    });
  }

  function renderLocationForm() {
    const stateOptions = STATE_OPTIONS.map(([code, name]) => `<option value="${code}">${name} (${code})</option>`).join("");
    inputArea.innerHTML = formCard(`
      <div class="jwh-location-guide jwh-full">
        <strong>Step 4: Verify the property location</strong>
        <span>Enter the ZIP code first. The chatbot will suggest the official city and state when available.</span>
      </div>
      <label class="jwh-full">Street address <span>optional for preliminary buyer searches</span><input id="jwh-loc-street" autocomplete="street-address"></label>
      <label>ZIP code<input id="jwh-loc-zip" inputmode="numeric" autocomplete="postal-code" maxlength="10" pattern="\d{5}(-\d{4})?" placeholder="55070" required><span class="jwh-field-feedback" id="jwh-zip-feedback">Enter a 5-digit ZIP or ZIP+4.</span></label>
      <label class="jwh-zip-action-label"><span>ZIP lookup</span><button class="jwh-secondary-action jwh-zip-lookup" id="jwh-zip-lookup" type="button">Find City & State</button></label>
      <label>City<input id="jwh-loc-city" list="jwh-city-suggestions" autocomplete="address-level2" required><datalist id="jwh-city-suggestions"></datalist></label>
      <label>State<select id="jwh-loc-state" autocomplete="address-level1"><option value="">Select state</option>${stateOptions}</select></label>
      <label>County <span>optional</span><input id="jwh-loc-county"></label>
      <div class="jwh-location-status jwh-full" id="jwh-location-status" hidden></div>
      ${continueButton("jwh-loc-submit", "Validate and Continue")}`);

    const zipInput = $("jwh-loc-zip");
    const cityInput = $("jwh-loc-city");
    const stateInput = $("jwh-loc-state");
    const feedback = $("jwh-zip-feedback");
    const status = $("jwh-location-status");
    const lookupButton = $("jwh-zip-lookup");
    let lookupTimer = null;

    function normaliseZipInput() {
      let cleaned = zipInput.value.replace(/[^\d-]/g, "").slice(0, 10);
      if (cleaned.length > 5 && !cleaned.includes("-")) cleaned = `${cleaned.slice(0, 5)}-${cleaned.slice(5, 9)}`;
      zipInput.value = cleaned;
      const valid = /^\d{5}(-\d{4})?$/.test(cleaned);
      feedback.textContent = valid ? "ZIP format is valid. Select Find City & State to verify it." : "Enter a valid 5-digit ZIP or ZIP+4.";
      feedback.classList.toggle("valid", valid);
      return valid;
    }

    async function lookupZip() {
      if (!normaliseZipInput()) return;
      lookupButton.disabled = true;
      lookupButton.textContent = "Checking ZIP…";
      status.hidden = false;
      status.className = "jwh-location-status jwh-full checking";
      status.textContent = "Checking the official city and state for this ZIP code.";
      try {
        const data = await apiFetch(`${API_BASE}/location/zip/${encodeURIComponent(zipInput.value.slice(0, 5))}`);
        const places = data.places || [];
        const suggestions = $("jwh-city-suggestions");
        suggestions.innerHTML = places.map((place) => `<option value="${escapeAttribute(place)}"></option>`).join("");
        if (data.state) stateInput.value = data.state;
        if (places.length) cityInput.value = places[0];
        if (data.validation_status === "Validated") {
          feedback.textContent = `ZIP verified: ${places.join(" or ")}, ${data.state}.`;
          feedback.classList.add("valid");
          status.className = "jwh-location-status jwh-full success";
          status.textContent = `Verified location: ${places.join(" / ")}, ${data.state} ${data.zip}`;
          lookupButton.textContent = "ZIP Verified";
        } else {
          status.className = "jwh-location-status jwh-full warning";
          status.textContent = data.message || "ZIP lookup is temporarily unavailable. Enter the city and state manually; the enquiry will be marked for review.";
          lookupButton.textContent = "Try ZIP Lookup Again";
        }
      } catch (error) {
        status.className = "jwh-location-status jwh-full warning";
        status.textContent = "The ZIP could not be verified. Check the number, or enter the city and state manually for team review.";
        lookupButton.textContent = "Try ZIP Lookup Again";
      } finally {
        lookupButton.disabled = false;
      }
    }

    zipInput.addEventListener("input", () => {
      const valid = normaliseZipInput();
      status.hidden = true;
      lookupButton.textContent = "Find City & State";
      window.clearTimeout(lookupTimer);
      if (valid && zipInput.value.length === 5) lookupTimer = window.setTimeout(lookupZip, 450);
    });
    lookupButton.addEventListener("click", lookupZip);

    $("jwh-loc-submit").addEventListener("click", async () => {
      const location = { street_address: value("jwh-loc-street"), city: value("jwh-loc-city"), state: value("jwh-loc-state"), zip: value("jwh-loc-zip"), county: value("jwh-loc-county") };
      if (!location.city || !location.state || !location.zip) return inlineError("City, state and ZIP code are required.");
      if (!/^\d{5}(-\d{4})?$/.test(location.zip)) return inlineError("Please enter a valid 5-digit ZIP or ZIP+4 code.");
      const submitButton = $("jwh-loc-submit");
      submitButton.disabled = true;
      submitButton.textContent = "Validating city, state and ZIP…";
      const result = await sendMessage({ location });
      if (!result) { submitButton.disabled = false; submitButton.textContent = "Validate and Continue"; return; }
      appendMessage("user", `${location.street_address ? location.street_address + ", " : ""}${location.city}, ${location.state} ${location.zip}`);
      renderBotTurn(result);
    });
  }

  function renderCurrencyRange() {
    inputArea.innerHTML = formCard(`
      ${moneyField("jwh-min", "Minimum amount")}
      ${moneyField("jwh-max", "Maximum amount")}
      ${continueButton("jwh-range-submit")}`);
    bindCurrencyInputs();
    $("jwh-range-submit").addEventListener("click", async () => {
      const min = rawMoney("jwh-min"), max = rawMoney("jwh-max");
      appendMessage("user", `${formatMoney(min)} to ${formatMoney(max)}`);
      const result = await sendMessage({ min, max }); if (result) renderBotTurn(result);
    });
  }

  function renderSpecifications(propertyType) {
    let fields = "";
    if (/Land|Farm|Ranch|Agricultural|Development/.test(propertyType || "")) {
      fields = `<label>Minimum acreage<input id="jwh-min-acreage" type="number" min="0" step="0.1"></label>
        <label>Maximum acreage<input id="jwh-max-acreage" type="number" min="0" step="0.1"></label>
        <label>Zoning preference<input id="jwh-zoning"></label>
        <label class="jwh-full">Important requirements<textarea id="jwh-spec-notes" rows="3" placeholder="Road access, utilities, development plans or other requirements"></textarea></label>`;
    } else if (/Warehouse|Commercial|Office|Retail|Industrial|Medical|Hospitality|Car Wash/.test(propertyType || "")) {
      fields = `<label>Minimum building area<input id="jwh-building-area" type="number" min="0" inputmode="numeric"></label>
        <label>Loading docks required<select id="jwh-loading"><option value="">No preference</option><option value="Yes">Yes</option><option value="No">No</option></select></label>
        <label>Zoning preference<input id="jwh-zoning"></label>
        <label class="jwh-full">Important requirements<textarea id="jwh-spec-notes" rows="3" placeholder="Parking, ceiling height, business use or other requirements"></textarea></label>`;
    } else {
      fields = `<label>Minimum bedrooms<input id="jwh-bedrooms" type="number" min="0" step="1"></label>
        <label>Minimum bathrooms<input id="jwh-bathrooms" type="number" min="0" step="0.5"></label>
        <label>Minimum square feet<input id="jwh-sqft" type="number" min="0" inputmode="numeric"></label>
        <label>Maximum repair level<select id="jwh-repair-level"><option value="">No preference</option><option>Move-in ready</option><option>Cosmetic repairs</option><option>Moderate renovation</option><option>Major renovation</option></select></label>
        <label class="jwh-full">Important requirements<textarea id="jwh-spec-notes" rows="3" placeholder="Parking, lot size, occupancy or other requirements"></textarea></label>`;
    }
    inputArea.innerHTML = formCard(`${fields}${continueButton("jwh-spec-submit")}`);
    $("jwh-spec-submit").addEventListener("click", async () => {
      const specifications = {
        min_bedrooms: optionalValue("jwh-bedrooms"), min_bathrooms: optionalValue("jwh-bathrooms"), min_sqft: optionalValue("jwh-sqft"),
        max_repair_level: optionalValue("jwh-repair-level"), min_acreage: optionalValue("jwh-min-acreage"), max_acreage: optionalValue("jwh-max-acreage"),
        zoning: optionalValue("jwh-zoning"), min_building_area: optionalValue("jwh-building-area"), loading_docks: optionalValue("jwh-loading"), notes: optionalValue("jwh-spec-notes")
      };
      appendMessage("user", "Property requirements provided");
      const result = await sendMessage({ specifications }); if (result) renderBotTurn(result);
    });
  }

  function renderContactPreference(data) {
    const days = (data.days || ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","No Preference"]).map((v) => `<option>${v}</option>`).join("");
    const times = (data.times || ["9:00 AM to 11:00 AM","11:00 AM to 1:00 PM","1:00 PM to 3:00 PM","3:00 PM to 5:00 PM","Any Time During Business Hours","No Preference"]).map((v) => `<option>${v}</option>`).join("");
    const zones = (data.time_zones || ["Eastern Time","Central Time","Mountain Time","Pacific Time","Alaska Time","Hawaii Time"]).map((v) => `<option ${v === "Central Time" ? "selected" : ""}>${v}</option>`).join("");
    inputArea.innerHTML = formCard(`
      <label>Preferred day<select id="jwh-day">${days}</select></label>
      <label>Preferred time<select id="jwh-time">${times}</select></label>
      <label class="jwh-full">Time zone<select id="jwh-zone">${zones}</select></label>
      ${continueButton("jwh-pref-submit")}`);
    $("jwh-pref-submit").addEventListener("click", async () => {
      const contact_preference = { day: value("jwh-day"), time: value("jwh-time"), time_zone: value("jwh-zone") };
      appendMessage("user", `${contact_preference.day}, ${contact_preference.time} (${contact_preference.time_zone})`);
      const result = await sendMessage({ contact_preference }); if (result) renderBotTurn(result);
    });
  }

  function renderAttachmentStep() {
    inputArea.innerHTML = formCard(`
      <label class="jwh-full">Document category<select id="jwh-doc-category"><option>Property photograph</option><option>Inspection report</option><option>Purchase agreement</option><option>Lease</option><option>Proof of funds</option><option>Repair estimate</option><option>Appraisal</option><option>Title document</option><option>Tax document</option><option selected>Other</option></select></label>
      <label class="jwh-full">Choose a file<input type="file" id="jwh-file-picker" accept=".pdf,.jpg,.jpeg,.png,.webp,.doc,.docx,.xls,.xlsx,.txt"></label>
      <button class="jwh-secondary-action" id="jwh-upload-btn" type="button">Upload Selected File</button>
      <label class="jwh-full">Property or document link<input id="jwh-link-input" placeholder="https://example.com/property"></label>
      <button class="jwh-secondary-action" id="jwh-link-btn" type="button">Add Link</button>
      ${continueButton("jwh-attachments-continue", "Continue")}`);
    $("jwh-upload-btn").addEventListener("click", () => uploadFile($("jwh-file-picker").files[0], value("jwh-doc-category")));
    $("jwh-link-btn").addEventListener("click", () => addLink(value("jwh-link-input")));
    $("jwh-attachments-continue").addEventListener("click", async () => {
      appendMessage("user", "Continue"); const result = await sendMessage({ input: "continue" }); if (result) renderBotTurn(result);
    });
  }

  function renderConsent() {
    inputArea.innerHTML = formCard(`
      <div class="jwh-consent-list">
        <label><input type="checkbox" id="jwh-consent-call" checked> Telephone call about this enquiry</label>
        <label><input type="checkbox" id="jwh-consent-text"> Text messages about this enquiry</label>
        <label><input type="checkbox" id="jwh-consent-email" checked> Email response and submission confirmation</label>
        <label class="optional"><input type="checkbox" id="jwh-consent-marketing"> Ongoing property alerts and marketing messages</label>
      </div>
      <p class="jwh-legal-note">Marketing permission is optional and separate from permission to respond to this enquiry. Message and data rates may apply.</p>
      ${continueButton("jwh-consent-submit")}`);
    $("jwh-consent-submit").addEventListener("click", async () => {
      const consent = { call: checked("jwh-consent-call"), text: checked("jwh-consent-text"), email: checked("jwh-consent-email"), marketing: checked("jwh-consent-marketing") };
      appendMessage("user", "Contact preferences confirmed"); const result = await sendMessage({ consent }); if (result) renderBotTurn(result);
    });
  }

  function renderReview(data) {
    const flowLabel = reviewFlowLabel(data.flow_type);
    const issues = Array.isArray(data.validation_errors) ? data.validation_errors : [];
    const ready = issues.length === 0;
    const statusClass = ready ? "success" : "warning";
    const statusText = ready ? "Ready for final submission" : "Please review the highlighted information";

    const sections = [];
    sections.push(reviewSection("Contact Details", ICONS.users, contactReviewItems(data)));

    if (["sell", "buy_and_sell"].includes(data.flow_type)) {
      sections.push(reviewSection("Property You Are Selling", ICONS.sell, sellerReviewItems(data)));
    }
    if (["buy", "investor_network"].includes(data.flow_type)) {
      sections.push(reviewSection("Property Requirements", ICONS.buy, buyerReviewItems(data, false)));
    }
    if (data.flow_type === "buy_and_sell") {
      sections.push(reviewSection("Property You Want to Buy", ICONS.buy, buyerReviewItems(data, true)));
    }
    if (data.flow_type === "funding") {
      sections.push(reviewSection("Funding Request", ICONS.funding, fundingReviewItems(data)));
    }

    sections.push(reviewSection("Preferred Follow-Up", ICONS.chat, followUpReviewItems(data)));

    const supportingItems = supportingReviewItems(data);
    if (supportingItems.length) sections.push(reviewSection("Question and Documents", ICONS.paperclip, supportingItems));

    const issueHtml = issues.length ? `
      <div class="jwh-review-alert warning">
        <strong>Validation check</strong>
        <ul>${issues.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
      </div>` : `
      <div class="jwh-review-alert success">
        <strong>Information checked</strong>
        <span>Your contact, location and enquiry details passed the final review checks.</span>
      </div>`;

    inputArea.innerHTML = `
      <div class="jwh-review-card">
        <div class="jwh-review-hero">
          <div class="jwh-review-hero-icon">${ICONS.check}</div>
          <div>
            <span class="jwh-review-eyebrow">Final review</span>
            <h3>Review Your Enquiry</h3>
            <p>Confirm the details below before they are securely sent to James Wholesale Homes.</p>
          </div>
        </div>
        <div class="jwh-review-badges">
          <span class="jwh-review-badge primary">${escapeHtml(flowLabel)}</span>
          ${data.client_classification ? `<span class="jwh-review-badge">${escapeHtml(data.client_classification)}</span>` : ""}
          ${data.service_area_status ? `<span class="jwh-review-badge">${escapeHtml(data.service_area_status)}</span>` : ""}
          <span class="jwh-review-badge ${statusClass}">${escapeHtml(statusText)}</span>
        </div>
        ${issueHtml}
        <div class="jwh-review-sections">${sections.join("")}</div>
        <div class="jwh-review-security-note">
          <span>${ICONS.check}</span>
          <p>Your details will be validated again on the server before submission. No enquiry is saved as a lead until you select <strong>Submit Enquiry</strong>.</p>
        </div>
        <div class="jwh-review-actions">
          <button class="jwh-primary-action" id="jwh-submit-review" ${ready ? "" : "disabled"}>${ready ? "Submit Enquiry" : "Complete Required Details"}</button>
          <button class="jwh-secondary-action" id="jwh-review-secondary">${ready ? "Start Again" : "Change Callback Time"}</button>
        </div>
      </div>`;

    const submitButton = $("jwh-submit-review");
    submitButton.addEventListener("click", async () => {
      if (submitButton.disabled) return;
      submitButton.disabled = true;
      submitButton.textContent = "Validating and Submitting…";
      appendMessage("user", "Submit Enquiry");
      const result = await sendMessage({ input: "submit" });
      if (result) renderBotTurn(result);
      else {
        submitButton.disabled = false;
        submitButton.textContent = "Submit Enquiry";
      }
    });
    $("jwh-review-secondary").addEventListener("click", async () => {
      if (ready) { modal.hidden = false; return; }
      appendMessage("user", "Change Callback Time");
      const result = await sendMessage({ input: "edit_callback_time" });
      if (result) renderBotTurn(result);
    });
    inputArea.scrollTop = 0;
  }

  function reviewSection(title, icon, items) {
    const validItems = items.filter((item) => item && item.value !== null && item.value !== undefined && String(item.value).trim() !== "");
    if (!validItems.length) return "";
    return `<section class="jwh-review-section">
      <div class="jwh-review-section-title"><span>${icon}</span><strong>${escapeHtml(title)}</strong></div>
      <div class="jwh-review-list">${validItems.map(reviewItem).join("")}</div>
    </section>`;
  }

  function reviewItem(item) {
    const status = item.status ? `<span class="jwh-review-item-status ${escapeAttribute(item.statusType || "")}">${escapeHtml(item.status)}</span>` : "";
    return `<div class="jwh-review-item ${item.full ? "full" : ""}">
      <span class="jwh-review-label">${escapeHtml(item.label)}</span>
      <div class="jwh-review-value"><strong>${item.html ? item.value : escapeHtml(item.value)}</strong>${status}</div>
    </div>`;
  }

  function contactReviewItems(data) {
    return [
      { label: "Full name", value: data.full_name },
      { label: "Email", value: data.email, status: data.email_verified ? "Verified" : "Provided", statusType: data.email_verified ? "success" : "neutral" },
      { label: "Phone", value: data.phone_display, status: data.phone_verified ? "Verified" : "Provided", statusType: data.phone_verified ? "success" : "neutral" },
    ];
  }

  function sellerReviewItems(data) {
    return [
      { label: "Property type", value: data.property_type },
      { label: "Property location", value: reviewLocation(data), status: data.address_validation_status || "Review required", statusType: data.address_validation_status === "Validated" ? "success" : "warning", full: true },
      { label: "Expected selling range", value: reviewRange(data.price_min, data.price_max) },
      { label: "Ownership", value: data.ownership_status },
      { label: "Occupancy", value: data.occupancy_status },
      { label: "Condition", value: data.condition_status },
      { label: "Selling timeline", value: data.timeline },
    ];
  }

  function buyerReviewItems(data, target) {
    const prefix = target ? "target_" : "";
    return [
      { label: "Property type", value: data[prefix + "property_type"] },
      { label: "Preferred location", value: reviewLocation(data, prefix), status: data[prefix + "address_validation_status"] || "Review required", statusType: data[prefix + "address_validation_status"] === "Validated" ? "success" : "warning", full: true },
      { label: "Buying budget", value: reviewRange(data[prefix + "price_min"], data[prefix + "price_max"]) },
      { label: "Intended use", value: data[prefix + "intended_use"] },
      { label: "Funding method", value: data[prefix + "funding_method"] },
      { label: "Purchase timeline", value: data[prefix + "timeline"] },
      ...(target ? [{ label: "Purchase depends on sale", value: data.purchase_depends_on_sale }] : []),
    ];
  }

  function fundingReviewItems(data) {
    return [
      { label: "Business name", value: data.business_name },
      { label: "Property type", value: data.property_type },
      { label: "Property location", value: reviewLocation(data), status: data.address_validation_status || "Review required", statusType: data.address_validation_status === "Validated" ? "success" : "warning", full: true },
      { label: "Purchase price", value: reviewMoney(data.purchase_price) },
      { label: "Renovation budget", value: reviewMoney(data.renovation_budget) },
      { label: "Estimated ARV", value: reviewMoney(data.estimated_arv) },
      { label: "Requested funding", value: reviewMoney(data.requested_funding) },
      { label: "Borrower contribution", value: reviewMoney(data.borrower_contribution) },
      { label: "Exit strategy", value: data.exit_strategy },
      { label: "Experience", value: data.experience_summary, full: true },
      { label: "Expected closing date", value: data.expected_closing_date },
    ];
  }

  function followUpReviewItems(data) {
    return [
      { label: "Preferred day", value: data.contact_day },
      { label: "Preferred time", value: data.contact_time },
      { label: "Time zone", value: data.time_zone },
    ];
  }

  function supportingReviewItems(data) {
    const items = [];
    if (data.user_question) items.push({ label: "Your question", value: data.user_question, full: true });
    if (Array.isArray(data.uploaded_files) && data.uploaded_files.length) {
      const files = data.uploaded_files.map((file) => `${escapeHtml(file.name)} <small>${escapeHtml(file.category)} · ${escapeHtml(file.scan_status)}</small>`).join("<br>");
      items.push({ label: `Uploaded files (${data.uploaded_files.length})`, value: files, html: true, full: true });
    }
    if (Array.isArray(data.submitted_links) && data.submitted_links.length) {
      const links = data.submitted_links.map((link) => `<span class="jwh-review-link">${escapeHtml(link)}</span>`).join("<br>");
      items.push({ label: `Submitted links (${data.submitted_links.length})`, value: links, html: true, full: true });
    }
    return items;
  }

  function reviewLocation(data, prefix = "") {
    const address = data[prefix + "street_address"];
    const city = data[prefix + "city"];
    const state = data[prefix + "state"];
    const zip = data[prefix + "zip"];
    const county = data[prefix + "county"];
    const lineOne = address || "";
    const lineTwo = [city, state].filter(Boolean).join(", ") + (zip ? ` ${zip}` : "");
    return [lineOne, lineTwo, county ? `${county} County` : ""].filter(Boolean).join(" · ");
  }

  function reviewRange(min, max) {
    if (min === null || min === undefined || max === null || max === undefined) return "";
    return `${formatMoney(min)} – ${formatMoney(max)}`;
  }

  function reviewMoney(value) {
    return value === null || value === undefined || value === "" ? "" : formatMoney(value);
  }

  function reviewFlowLabel(flow) {
    return ({
      sell: "Seller Enquiry",
      buy: "Buyer Enquiry",
      buy_and_sell: "Buy and Sell Enquiry",
      investor_network: "Investor Network Enquiry",
      funding: "Funding Enquiry",
      general_enquiry: "General Enquiry",
    })[flow] || "Real Estate Enquiry";
  }

  function renderDateInput() {
    inputArea.innerHTML = formCard(`<label class="jwh-full">Expected closing date<input type="date" id="jwh-date" min="${new Date().toISOString().slice(0,10)}"></label>${continueButton("jwh-date-submit")}`);
    $("jwh-date-submit").addEventListener("click", async () => {
      const val = value("jwh-date"); if (!val) return inlineError("Please select a date."); appendMessage("user", val); const result = await sendMessage({ input: val }); if (result) renderBotTurn(result);
    });
  }

  function renderTextInput(type) {
    const placeholder = {
      email: "name@example.com", phone: "(555) 555-5555", verification_code: "Six-digit code",
      text_optional: "Type your answer, or leave blank to continue"
    }[type] || "Type your message";
    const inputType = type === "email" ? "email" : type === "phone" ? "tel" : "text";
    inputArea.innerHTML = `<div class="jwh-composer">
      <button type="button" class="jwh-composer-tool" id="jwh-composer-voice" title="Voice input" aria-label="Voice input">${ICONS.mic}</button>
      <button type="button" class="jwh-composer-tool" id="jwh-composer-attach" title="Upload a file or add a link" aria-label="Upload a file or add a link">${ICONS.paperclip}</button>
      <input id="jwh-text-input" type="${inputType}" placeholder="${placeholder}" ${type === "verification_code" ? 'inputmode="numeric" maxlength="6"' : ""}>
      <button type="button" id="jwh-text-submit" aria-label="Send">${ICONS.send}</button>
    </div>`;
    const input = $("jwh-text-input");
    const voiceButton = $("jwh-composer-voice");
    const attachButton = $("jwh-composer-attach");
    const submit = async () => {
      const val = input.value.trim();
      if (type !== "text_optional" && !val) return;
      appendMessage("user", val || "Skipped");
      input.value = "";
      const result = await sendMessage({ input: val });
      if (result) renderBotTurn(result);
    };
    $("jwh-text-submit").addEventListener("click", submit);
    voiceButton.addEventListener("click", () => startVoiceInput(voiceButton));
    attachButton.addEventListener("click", () => {
      attachmentPanel.hidden = !attachmentPanel.hidden;
      attachButton.classList.toggle("active", !attachmentPanel.hidden);
    });
    input.addEventListener("keydown", (event) => { if (event.key === "Enter") submit(); });
    setTimeout(() => input.focus(), 50);
  }

  function renderTerminalActions() {
    inputArea.innerHTML = `<div class="jwh-terminal-actions"><button class="jwh-primary-action" id="jwh-terminal-new">Start New Chat</button><button class="jwh-secondary-action" id="jwh-terminal-close">Close Chat</button></div>`;
    $("jwh-terminal-new").addEventListener("click", () => { modal.hidden = false; });
    $("jwh-terminal-close").addEventListener("click", closeChat);
  }

  async function uploadFile(file, category) {
    if (!file) return inlineError("Choose a file before uploading.");
    appendMessage("user", `Uploading ${file.name}`);
    const formData = new FormData(); formData.append("session_id", sessionId); formData.append("file", file); formData.append("document_category", category || "Other");
    try {
      const data = await apiFetch(`${API_BASE}/chat/upload`, { method: "POST", body: formData });
      appendMessage("bot", `${data.original_filename} was received. Security scan status: ${data.scan_status}.`);
      $("jwh-global-file").value = "";
    } catch (_) { /* displayed by apiFetch */ }
  }

  async function addLink(url) {
    if (!url) return inlineError("Enter a link first.");
    try {
      const data = await apiFetch(`${API_BASE}/chat/link`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: sessionId, url }) });
      appendMessage("bot", data.message);
    } catch (_) { /* displayed by apiFetch */ }
  }

  function handleAttachmentAction(event) {
    const action = event.target.closest("button")?.dataset.attachAction;
    if (!action) return;
    attachmentPanel.hidden = true;
    $("jwh-composer-attach")?.classList.remove("active");
    if (action === "file") $("jwh-global-file").click();
    if (action === "link") {
      const panel = document.createElement("div");
      panel.className = "jwh-inline-link-panel";
      panel.innerHTML = `<input id="jwh-global-link" placeholder="https://example.com/property"><button id="jwh-global-link-add">Add Link</button>`;
      inputArea.prepend(panel);
      $("jwh-global-link-add").addEventListener("click", async () => { await addLink(value("jwh-global-link")); panel.remove(); });
    }
  }

  function initialiseSpeechVoices() {
    if (!("speechSynthesis" in window)) return;
    const load = () => { availableVoices = window.speechSynthesis.getVoices() || []; };
    load();
    window.speechSynthesis.addEventListener?.("voiceschanged", load);
  }

  function preferredSpeechVoice() {
    if (!availableVoices.length && "speechSynthesis" in window) {
      availableVoices = window.speechSynthesis.getVoices() || [];
    }
    const preferredNames = ["Microsoft Aria", "Microsoft Jenny", "Google US English", "Samantha"];
    for (const name of preferredNames) {
      const match = availableVoices.find((voice) => voice.name.includes(name));
      if (match) return match;
    }
    return availableVoices.find((voice) => /^en-US/i.test(voice.lang))
      || availableVoices.find((voice) => /^en/i.test(voice.lang))
      || null;
  }

  function splitSpeechText(text, maxLength = 220) {
    const clean = String(text || "").replace(/\s+/g, " ").trim();
    if (!clean) return [];
    const sentences = clean.match(/[^.!?]+[.!?]+|[^.!?]+$/g) || [clean];
    const chunks = [];
    let chunk = "";
    sentences.forEach((sentence) => {
      const next = `${chunk} ${sentence}`.trim();
      if (next.length <= maxLength) {
        chunk = next;
      } else {
        if (chunk) chunks.push(chunk);
        if (sentence.length <= maxLength) {
          chunk = sentence.trim();
        } else {
          const words = sentence.trim().split(" ");
          chunk = "";
          words.forEach((word) => {
            const candidate = `${chunk} ${word}`.trim();
            if (candidate.length > maxLength && chunk) { chunks.push(chunk); chunk = word; }
            else chunk = candidate;
          });
        }
      }
    });
    if (chunk) chunks.push(chunk);
    return chunks;
  }

  function toggleSpeaker() {
    if (!("speechSynthesis" in window)) {
      appendMessage("bot", "Audio reading is not supported by this browser. Try the latest version of Chrome or Edge.", "error");
      return;
    }

    if (window.speechSynthesis.speaking) {
      if (window.speechSynthesis.paused) {
        window.speechSynthesis.resume();
        speechPaused = false;
      } else {
        window.speechSynthesis.pause();
        speechPaused = true;
      }
      updateSpeakerButton();
      return;
    }

    if (speakerEnabled) {
      speakerEnabled = false;
      speechPaused = false;
      speechQueue = [];
      speechGeneration += 1;
      window.speechSynthesis.cancel();
      sessionStorage.setItem(SPEAKER_KEY, "0");
      updateSpeakerButton();
      return;
    }

    speakerEnabled = true;
    sessionStorage.setItem(SPEAKER_KEY, "1");
    updateSpeakerButton();
    const latestText = currentTurn?.prompt || [...messagesEl.querySelectorAll(".jwh-msg.bot")].pop()?.textContent;
    if (latestText) speakText(latestText);
  }

  function updateSpeakerButton() {
    const button = $("jwh-speaker");
    if (!button) return;
    const speaking = Boolean(window.speechSynthesis?.speaking);
    const paused = Boolean(window.speechSynthesis?.paused || speechPaused);
    button.classList.toggle("active", speakerEnabled);
    button.classList.toggle("speaking", speaking && !paused);
    button.classList.toggle("paused", paused);
    button.setAttribute("aria-pressed", String(speakerEnabled));
    button.setAttribute("aria-label", paused ? "Resume reading" : speaking ? "Pause reading" : speakerEnabled ? "Turn audio reading off" : "Read answers aloud");
    button.title = paused ? "Resume reading" : speaking ? "Pause reading" : speakerEnabled ? "Audio reading is on. Click to turn it off." : "Read answers aloud";
  }

  function speakNextChunk(generation = speechGeneration) {
    if (generation !== speechGeneration) return;
    if (!speakerEnabled || !speechQueue.length || !("speechSynthesis" in window)) {
      speechPaused = false;
      updateSpeakerButton();
      return;
    }
    const utterance = new SpeechSynthesisUtterance(speechQueue.shift());
    utterance.lang = "en-US";
    utterance.rate = 0.92;
    utterance.pitch = 1;
    utterance.volume = 1;
    const voice = preferredSpeechVoice();
    if (voice) utterance.voice = voice;
    utterance.onstart = () => {
      if (generation !== speechGeneration) return;
      speechPaused = false;
      updateSpeakerButton();
    };
    utterance.onend = () => {
      if (generation !== speechGeneration) return;
      if (speakerEnabled && speechQueue.length) speakNextChunk(generation);
      else updateSpeakerButton();
    };
    utterance.onerror = (event) => {
      if (generation !== speechGeneration) return;
      if (!["interrupted", "canceled"].includes(event.error)) {
        appendMessage("bot", "The browser could not play this answer. Please check that tab audio is not muted.", "error");
      }
      speechQueue = [];
      speechPaused = false;
      updateSpeakerButton();
    };
    window.speechSynthesis.speak(utterance);
    updateSpeakerButton();
  }

  function speakText(text) {
    if (!speakerEnabled || !("speechSynthesis" in window)) return;
    speechGeneration += 1;
    const generation = speechGeneration;
    window.speechSynthesis.cancel();
    speechPaused = false;
    speechQueue = splitSpeechText(text);
    window.setTimeout(() => speakNextChunk(generation), 60);
  }


  async function startVoiceInput(triggerButton = null) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const input = $("jwh-text-input");

    if (!input) {
      appendMessage("bot", "Voice input is available when a text field is open.", "error");
      return;
    }

    if (!window.isSecureContext && location.hostname !== "localhost" && location.hostname !== "127.0.0.1") {
      appendMessage("bot", "Voice input requires HTTPS. Open the chatbot through a secure HTTPS address.", "error");
      return;
    }

    if (!SpeechRecognition) {
      appendMessage("bot", "Voice input works best in Google Chrome or Microsoft Edge. This browser does not support speech recognition.", "error");
      return;
    }

    if (speechRecognition) {
      speechRecognition.stop();
      return;
    }

    try {
      if (navigator.mediaDevices?.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        stream.getTracks().forEach((track) => track.stop());
      }

      speechRecognition = new SpeechRecognition();
      speechRecognition.lang = "en-US";
      speechRecognition.interimResults = true;
      speechRecognition.continuous = false;
      speechRecognition.maxAlternatives = 1;
      triggerButton?.classList.add("listening");
      triggerButton?.setAttribute("aria-label", "Stop voice input");
      triggerButton?.setAttribute("title", "Listening… click to stop");

      speechRecognition.onresult = (event) => {
        let transcript = "";
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          transcript += event.results[i][0].transcript;
        }
        input.value = transcript.trim();
        input.dispatchEvent(new Event("input", { bubbles: true }));
        input.focus();
      };

      speechRecognition.onerror = (event) => {
        const messages = {
          "not-allowed": "Microphone permission was blocked. Allow microphone access in your browser and try again.",
          "service-not-allowed": "Voice recognition is blocked by the browser or iframe. Allow microphone access for this site.",
          "audio-capture": "No microphone was detected. Check your microphone connection and Windows privacy settings.",
          "no-speech": "No speech was detected. Click the microphone and speak clearly.",
          "network": "Voice recognition could not connect. Check your internet connection and try again."
        };
        appendMessage("bot", messages[event.error] || "Voice input could not be completed. Please try again or type your response.", "error");
      };

      speechRecognition.onend = () => {
        triggerButton?.classList.remove("listening");
        triggerButton?.setAttribute("aria-label", "Voice input");
        triggerButton?.setAttribute("title", "Voice input");
        speechRecognition = null;
      };

      speechRecognition.start();
    } catch (error) {
      triggerButton?.classList.remove("listening");
      speechRecognition = null;
      const denied = error?.name === "NotAllowedError" || error?.name === "SecurityError";
      appendMessage(
        "bot",
        denied
          ? "Microphone permission was blocked. Click the lock icon in the browser address bar, allow Microphone, then reload the page."
          : "The microphone could not be started. Check your microphone and browser permissions.",
        "error"
      );
    }
  }

  function formCard(content) { return `<div class="jwh-form-card">${content}</div>`; }
  function continueButton(id, label = "Continue") { return `<button class="jwh-primary-action jwh-full" type="button" id="${id}">${label}</button>`; }
  function moneyField(id, label) { return `<label>${label}<div class="jwh-money-field"><span>$</span><input id="${id}" inputmode="numeric" placeholder="0"></div></label>`; }
  function bindCurrencyInputs() { inputArea.querySelectorAll(".jwh-money-field input").forEach((input) => input.addEventListener("input", () => { const digits = input.value.replace(/\D/g, ""); input.dataset.raw = digits; input.value = digits ? Number(digits).toLocaleString("en-US") : ""; })); }
  function rawMoney(id) { const el = $(id); return el?.dataset.raw || el?.value?.replace(/[^\d.]/g, "") || ""; }
  function formatMoney(value) { const number = Number(String(value || "0").replace(/[^\d.]/g, "")); return Number.isFinite(number) ? number.toLocaleString("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }) : "$0"; }
  function value(id) { return $(id)?.value?.trim() || ""; }
  function optionalValue(id) { return $(id) ? value(id) : ""; }
  function checked(id) { return Boolean($(id)?.checked); }
  function humanise(value) { return value.replace(/_/g, " ").replace(/\b\w/g, (letter) => letter.toUpperCase()); }
  function inlineError(message) { appendMessage("bot", message, "error"); }
  function escapeHtml(value) { const div = document.createElement("div"); div.textContent = String(value ?? ""); return div.innerHTML; }
  function escapeAttribute(value) { return escapeHtml(value).replace(/"/g, "&quot;"); }
})();
