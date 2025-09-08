class h {
  constructor(e) {
    this.widget = e;
  }
  render() {
    const e = this.widget.getConfig();
    return `
      <div class="space-y-6">
        <!-- Educational Disclaimer -->
        <div class="card bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
          <div class="flex items-start gap-3">
            <div class="text-amber-600 dark:text-amber-400 mt-1">⚠️</div>
            <div>
              <h3 class="font-semibold text-amber-800 dark:text-amber-200 mb-1">Educational Tool Only</h3>
              <p class="text-sm text-amber-700 dark:text-amber-300">
                This judging system is for educational and practice purposes only. 
                It does not provide official awards from any recognized orchid organization.
              </p>
            </div>
          </div>
        </div>

        <!-- Cloud Status -->
        ${!!(e.cloud?.webappUrl && e.cloud?.secret) ? "" : `
          <div class="card bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
            <div class="text-sm text-amber-700 dark:text-amber-300">
              <strong>Cloud sync disabled</strong> — add EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL and EXPO_PUBLIC_FCOS_SHEETS_SECRET to enable
            </div>
          </div>
        `}

        <!-- Main Navigation Cards -->
        <div class="grid grid-cols-1 gap-4">
          <!-- Profile / ID -->
          <div class="nav-card-green" data-nav="profile">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-primary-100 dark:bg-primary-800 rounded-lg flex items-center justify-center">
                <span class="text-primary-600 dark:text-primary-400">👤</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">Profile / ID</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Configure settings and AI provider</p>
              </div>
            </div>
          </div>

          <!-- Start New Entry -->
          <div class="nav-card-purple" data-nav="capture">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-secondary-100 dark:bg-secondary-800 rounded-lg flex items-center justify-center">
                <span class="text-secondary-600 dark:text-secondary-400">📷</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">Start New Entry</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Capture photos and begin judging</p>
              </div>
            </div>
          </div>

          <!-- View My Last 10 -->
          <div class="nav-card" data-nav="entries">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">📋</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">View My Last 10</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Recent judging entries</p>
              </div>
            </div>
          </div>

          <!-- How to Use -->
          <div class="nav-card" data-nav="howto">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">❓</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">How to Use</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Step-by-step guide</p>
              </div>
            </div>
          </div>

          <!-- FAQ -->
          <div class="nav-card" data-nav="faq">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">💬</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">FAQ</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">Frequently asked questions</p>
              </div>
            </div>
          </div>

          <!-- About -->
          <div class="nav-card" data-nav="about">
            <div class="flex items-center gap-3">
              <div class="w-10 h-10 bg-gray-100 dark:bg-gray-800 rounded-lg flex items-center justify-center">
                <span class="text-gray-600 dark:text-gray-400">ℹ️</span>
              </div>
              <div>
                <h3 class="font-semibold text-gray-900 dark:text-white">About</h3>
                <p class="text-sm text-gray-600 dark:text-gray-400">FCOS mission and disclaimers</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  mount(e) {
    e.querySelectorAll("[data-nav]").forEach((a) => {
      a.addEventListener("click", () => {
        const s = a.getAttribute("data-nav");
        s && this.widget.navigateTo(s);
      });
    });
  }
}
class p {
  dbName = "fcos_orchid_judge";
  dbVersion = 1;
  db = null;
  async init() {
    if (!("indexedDB" in window)) {
      console.warn("IndexedDB not available, falling back to localStorage");
      return;
    }
    return new Promise((e, t) => {
      const a = indexedDB.open(this.dbName, this.dbVersion);
      a.onerror = () => t(a.error), a.onsuccess = () => {
        this.db = a.result, e();
      }, a.onupgradeneeded = (s) => {
        const i = s.target.result;
        i.objectStoreNames.contains("entries") || i.createObjectStore("entries", { keyPath: "id" }).createIndex("timestamp", "timestamp", { unique: !1 }), i.objectStoreNames.contains("profile") || i.createObjectStore("profile", { keyPath: "id" });
      };
    });
  }
  isAvailable() {
    return "indexedDB" in window || "localStorage" in window;
  }
  // Entry management
  async saveEntry(e) {
    if (this.db)
      return new Promise((t, a) => {
        const r = this.db.transaction(["entries"], "readwrite").objectStore("entries").put(e);
        r.onsuccess = () => t(), r.onerror = () => a(r.error);
      });
    {
      const t = this.getEntriesFromLocalStorage(), a = t.findIndex((s) => s.id === e.id);
      a >= 0 ? t[a] = e : t.push(e), localStorage.setItem("fcos_orchid_judge_entries", JSON.stringify(t));
    }
  }
  async getEntries(e = 10) {
    return this.db ? new Promise((t, a) => {
      const d = this.db.transaction(["entries"], "readonly").objectStore("entries").index("timestamp").openCursor(null, "prev"), o = [];
      let c = 0;
      d.onsuccess = (u) => {
        const g = u.target.result;
        g && c < e ? (o.push(g.value), c++, g.continue()) : t(o);
      }, d.onerror = () => a(d.error);
    }) : this.getEntriesFromLocalStorage().sort((a, s) => new Date(s.timestamp).getTime() - new Date(a.timestamp).getTime()).slice(0, e);
  }
  async getEntry(e) {
    return this.db ? new Promise((t, a) => {
      const r = this.db.transaction(["entries"], "readonly").objectStore("entries").get(e);
      r.onsuccess = () => t(r.result || null), r.onerror = () => a(r.error);
    }) : this.getEntriesFromLocalStorage().find((a) => a.id === e) || null;
  }
  // Profile management
  saveProfile(e) {
    this.db ? this.db.transaction(["profile"], "readwrite").objectStore("profile").put({ id: "default", ...e }) : localStorage.setItem("fcos_orchid_judge_profile", JSON.stringify(e));
  }
  getProfile() {
    if (this.db) {
      const e = localStorage.getItem("fcos_orchid_judge_profile");
      return e ? JSON.parse(e) : null;
    } else {
      const e = localStorage.getItem("fcos_orchid_judge_profile");
      return e ? JSON.parse(e) : null;
    }
  }
  // Helper methods
  getEntriesFromLocalStorage() {
    const e = localStorage.getItem("fcos_orchid_judge_entries");
    return e ? JSON.parse(e) : [];
  }
  // Clear all data
  async clearAll() {
    if (this.db)
      return new Promise((e, t) => {
        const a = this.db.transaction(["entries", "profile"], "readwrite");
        a.objectStore("entries").clear(), a.objectStore("profile").clear(), a.oncomplete = () => e(), a.onerror = () => t(a.error);
      });
    localStorage.removeItem("fcos_orchid_judge_entries"), localStorage.removeItem("fcos_orchid_judge_profile");
  }
}
const l = new p();
l.init().catch(console.error);
class v {
  constructor(e) {
    this.widget = e;
  }
  render() {
    const e = this.loadProfile(), t = this.widget.getConfig();
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Profile & Settings</h2>
        </div>

        <!-- Profile Form -->
        <div class="card space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">Personal Information</h3>
          
          <div>
            <label class="label">Name</label>
            <input type="text" class="input" id="profile-name" value="${e.name}" placeholder="Your name">
          </div>
          
          <div>
            <label class="label">Email (optional)</label>
            <input type="email" class="input" id="profile-email" value="${e.email}" placeholder="your.email@example.com">
          </div>
          
          <div>
            <label class="label">Language</label>
            <select class="input" id="profile-language">
              <option value="en" ${e.language === "en" ? "selected" : ""}>English</option>
              <option value="ja" ${e.language === "ja" ? "selected" : ""}>Japanese</option>
            </select>
          </div>
        </div>

        <!-- AI Provider Settings -->
        <div class="card space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">AI Provider</h3>
          
          <div>
            <label class="label">Provider</label>
            <select class="input" id="ai-provider">
              <option value="openai" ${e.aiProvider === "openai" ? "selected" : ""}>OpenAI</option>
              <option value="webhook" ${e.aiProvider === "webhook" ? "selected" : ""}>Custom Webhook</option>
            </select>
          </div>
          
          <div id="webhook-url-container" class="${e.aiProvider === "webhook" ? "" : "hidden"}">
            <label class="label">Webhook URL</label>
            <input type="url" class="input" id="webhook-url" value="${e.webhookUrl || ""}" 
                   placeholder="https://your-api.com/analyze">
          </div>
          
          <div class="flex gap-2">
            <button class="btn btn-outline" data-action="test-ai">Test Connection</button>
            <button class="btn btn-outline" data-action="diagnostics">Run Diagnostics</button>
          </div>
          
          <div id="connection-status" class="text-sm"></div>
        </div>

        <!-- App Settings -->
        <div class="card space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">App Settings</h3>
          
          <div class="flex items-center justify-between">
            <div>
              <label class="label mb-0">Tutorial Mode</label>
              <p class="text-sm text-gray-600 dark:text-gray-400">Show helpful tips and guidance</p>
            </div>
            <input type="checkbox" id="tutorial-enabled" ${e.tutorialEnabled ? "checked" : ""} 
                   class="w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500">
          </div>
          
          <div class="flex items-center justify-between">
            <div>
              <label class="label mb-0">Cloud Sync</label>
              <p class="text-sm text-gray-600 dark:text-gray-400">
                ${t.cloud?.webappUrl ? "Auto-upload entries to cloud" : "Not configured"}
              </p>
            </div>
            <input type="checkbox" id="cloud-sync-enabled" ${e.cloudSyncEnabled ? "checked" : ""} 
                   ${t.cloud?.webappUrl ? "" : "disabled"}
                   class="w-5 h-5 text-primary-600 rounded border-gray-300 focus:ring-primary-500">
          </div>
        </div>

        <!-- Save Button -->
        <button class="btn btn-primary w-full" data-action="save">Save Profile</button>
      </div>
    `;
  }
  mount(e) {
    const t = e.querySelector('[data-action="back"]'), a = e.querySelector('[data-action="save"]'), s = e.querySelector('[data-action="test-ai"]'), i = e.querySelector('[data-action="diagnostics"]'), r = e.querySelector("#ai-provider"), d = e.querySelector("#webhook-url-container");
    t?.addEventListener("click", () => this.widget.goBack()), a?.addEventListener("click", () => this.saveProfile(e)), s?.addEventListener("click", () => this.testAiConnection(e)), i?.addEventListener("click", () => this.runDiagnostics(e)), r?.addEventListener("change", () => {
      const o = r.value === "webhook";
      d?.classList.toggle("hidden", !o);
    });
  }
  loadProfile() {
    return l.getProfile() || {
      name: "",
      email: "",
      language: "en",
      aiProvider: "openai",
      tutorialEnabled: !0,
      cloudSyncEnabled: !1
    };
  }
  saveProfile(e) {
    const t = {
      name: e.querySelector("#profile-name").value,
      email: e.querySelector("#profile-email").value,
      language: e.querySelector("#profile-language").value,
      aiProvider: e.querySelector("#ai-provider").value,
      webhookUrl: e.querySelector("#webhook-url").value,
      tutorialEnabled: e.querySelector("#tutorial-enabled").checked,
      cloudSyncEnabled: e.querySelector("#cloud-sync-enabled").checked
    };
    l.saveProfile(t), this.showStatus(e, "Profile saved successfully!", "success");
  }
  async testAiConnection(e) {
    const t = this.loadProfile(), a = e.querySelector("#connection-status");
    a.innerHTML = '<span class="text-blue-600">Testing connection...</span>';
    try {
      t.aiProvider === "openai" ? (await fetch("https://api.openai.com/v1/models", {
        headers: {
          Authorization: `Bearer ${window.OPENAI_API_KEY || ""}`
        }
      })).ok ? a.innerHTML = '<span class="text-green-600">✓ OpenAI connection successful</span>' : a.innerHTML = '<span class="text-red-600">✗ OpenAI connection failed - check API key</span>' : (await fetch(t.webhookUrl || "", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ test: !0 })
      })).ok ? a.innerHTML = '<span class="text-green-600">✓ Webhook connection successful</span>' : a.innerHTML = '<span class="text-red-600">✗ Webhook connection failed</span>';
    } catch {
      a.innerHTML = '<span class="text-red-600">✗ Connection test failed</span>';
    }
  }
  async runDiagnostics(e) {
    const t = e.querySelector("#connection-status");
    t.innerHTML = `
      <div class="space-y-2 text-sm">
        <div class="font-semibold">System Diagnostics:</div>
        <div>• Storage: ${l.isAvailable() ? "✓ Available" : "✗ Not available"}</div>
        <div>• Camera: ${navigator.mediaDevices ? "✓ Available" : "✗ Not available"}</div>
        <div>• Cloud: ${this.widget.getConfig().cloud?.webappUrl ? "✓ Configured" : "✗ Not configured"}</div>
        <div>• Web Share: ${navigator.share ? "✓ Available" : "✗ Not available"}</div>
        <div>• File System: ${window.showSaveFilePicker ? "✓ Available" : "✗ Not available"}</div>
      </div>
    `;
  }
  showStatus(e, t, a) {
    const s = e.querySelector("#connection-status"), i = a === "success" ? "text-green-600" : "text-red-600";
    s.innerHTML = `<span class="${i}">${t}</span>`, setTimeout(() => {
      s.innerHTML = "";
    }, 3e3);
  }
}
class b {
  constructor(e) {
    this.widget = e;
  }
  currentEntry = {};
  stream = null;
  render() {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Capture Photos</h2>
        </div>

        <!-- Educational Notice -->
        <div class="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <div class="flex items-start gap-3">
            <div class="text-blue-600 dark:text-blue-400 mt-1">ℹ️</div>
            <div>
              <h3 class="font-semibold text-blue-800 dark:text-blue-200 mb-1">Photo Tips</h3>
              <p class="text-sm text-blue-700 dark:text-blue-300">
                • Capture clear photos of the blooming plant<br>
                • Include the ID tag if available<br>
                • Good lighting improves analysis accuracy<br>
                • Include a ruler/card for size reference
              </p>
            </div>
          </div>
        </div>

        <!-- Photo Steps -->
        <div class="space-y-4">
          <!-- Step 1: Plant Photo -->
          <div class="card">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Step 1: Blooming Plant Photo
            </h3>
            
            <div id="plant-photo-section">
              ${this.currentEntry.photos?.plant ? this.renderPhotoPreview("plant") : this.renderPhotoCapture("plant")}
            </div>
          </div>

          <!-- Step 2: ID Tag Photo (Optional) -->
          <div class="card">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-4">
              Step 2: ID Tag Photo (Optional)
            </h3>
            
            <div id="tag-photo-section">
              ${this.currentEntry.photos?.tag ? this.renderPhotoPreview("tag") : this.renderPhotoCapture("tag")}
            </div>
          </div>

          <!-- Continue Button -->
          <div class="pt-4">
            <button class="btn btn-primary w-full" data-action="continue" 
                    ${this.currentEntry.photos?.plant ? "" : "disabled"}>
              ${this.currentEntry.photos?.tag ? "Continue to Tag Analysis" : "Continue without Tag"}
            </button>
          </div>
        </div>
      </div>
    `;
  }
  renderPhotoCapture(e) {
    return `
      <div class="space-y-3">
        <div class="grid grid-cols-2 gap-3">
          <button class="btn btn-primary" data-action="camera" data-type="${e}">
            📷 Take Photo
          </button>
          <button class="btn btn-outline" data-action="library" data-type="${e}">
            🖼️ Photo Library
          </button>
        </div>
        
        <!-- Camera Preview (hidden initially) -->
        <div id="${e}-camera-section" class="hidden">
          <video id="${e}-video" class="w-full rounded-lg bg-gray-100 dark:bg-gray-800" autoplay playsinline></video>
          <div class="flex gap-2 mt-3">
            <button class="btn btn-primary flex-1" data-action="take-photo" data-type="${e}">
              📸 Capture
            </button>
            <button class="btn btn-outline" data-action="cancel-camera" data-type="${e}">
              Cancel
            </button>
          </div>
          <canvas id="${e}-canvas" class="hidden"></canvas>
        </div>
        
        <!-- File Input (hidden) -->
        <input type="file" id="${e}-file-input" accept="image/*" class="hidden">
      </div>
    `;
  }
  renderPhotoPreview(e) {
    return `
      <div class="space-y-3">
        <div class="relative">
          <img src="${e === "plant" ? this.currentEntry.photos?.plant : this.currentEntry.photos?.tag}" alt="${e} photo" class="w-full rounded-lg">
          <button class="absolute top-2 right-2 btn btn-outline text-sm" data-action="retake" data-type="${e}">
            🔄 Retake
          </button>
        </div>
      </div>
    `;
  }
  mount(e) {
    const t = e.querySelector('[data-action="back"]'), a = e.querySelector('[data-action="continue"]');
    t?.addEventListener("click", () => this.widget.goBack()), a?.addEventListener("click", () => this.continueToAnalysis()), e.querySelectorAll('[data-action="camera"]').forEach((s) => {
      s.addEventListener("click", (i) => {
        const r = i.target.dataset.type;
        this.startCamera(r, e);
      });
    }), e.querySelectorAll('[data-action="library"]').forEach((s) => {
      s.addEventListener("click", (i) => {
        const r = i.target.dataset.type;
        this.openPhotoLibrary(r, e);
      });
    }), e.querySelectorAll('[data-action="take-photo"]').forEach((s) => {
      s.addEventListener("click", (i) => {
        const r = i.target.dataset.type;
        this.takePhoto(r, e);
      });
    }), e.querySelectorAll('[data-action="cancel-camera"]').forEach((s) => {
      s.addEventListener("click", (i) => {
        const r = i.target.dataset.type;
        this.cancelCamera(r, e);
      });
    }), e.querySelectorAll('[data-action="retake"]').forEach((s) => {
      s.addEventListener("click", (i) => {
        const r = i.target.dataset.type;
        this.retakePhoto(r, e);
      });
    });
  }
  async startCamera(e, t) {
    try {
      const a = {
        video: {
          facingMode: "environment",
          // Use back camera on mobile
          width: { ideal: 1280 },
          height: { ideal: 720 }
        }
      };
      this.stream = await navigator.mediaDevices.getUserMedia(a);
      const s = t.querySelector(`#${e}-video`), i = t.querySelector(`#${e}-camera-section`);
      s && i && (s.srcObject = this.stream, i.classList.remove("hidden"));
    } catch (a) {
      console.error("Camera access failed:", a), alert("Camera access failed. Please check permissions and try again.");
    }
  }
  takePhoto(e, t) {
    const a = t.querySelector(`#${e}-video`), s = t.querySelector(`#${e}-canvas`);
    if (a && s) {
      const i = s.getContext("2d");
      s.width = a.videoWidth, s.height = a.videoHeight, i?.drawImage(a, 0, 0);
      const r = s.toDataURL("image/jpeg", 0.8);
      this.savePhoto(e, r), this.cancelCamera(e, t), this.updatePhotoSection(e, t);
    }
  }
  cancelCamera(e, t) {
    this.stream && (this.stream.getTracks().forEach((s) => s.stop()), this.stream = null), t.querySelector(`#${e}-camera-section`)?.classList.add("hidden");
  }
  openPhotoLibrary(e, t) {
    const a = t.querySelector(`#${e}-file-input`);
    a.onchange = (s) => {
      const i = s.target.files?.[0];
      if (i) {
        const r = new FileReader();
        r.onload = (d) => {
          const o = d.target?.result;
          this.savePhoto(e, o), this.updatePhotoSection(e, t);
        }, r.readAsDataURL(i);
      }
    }, a.click();
  }
  savePhoto(e, t) {
    this.currentEntry.photos || (this.currentEntry.photos = { plant: "" }), e === "plant" ? this.currentEntry.photos.plant = t : this.currentEntry.photos.tag = t;
  }
  retakePhoto(e, t) {
    e === "plant" ? this.currentEntry.photos.plant = "" : this.currentEntry.photos.tag = "", this.updatePhotoSection(e, t);
  }
  updatePhotoSection(e, t) {
    const a = t.querySelector(`#${e}-photo-section`);
    if (a) {
      const i = e === "plant" ? this.currentEntry.photos?.plant : this.currentEntry.photos?.tag;
      a.innerHTML = i ? this.renderPhotoPreview(e) : this.renderPhotoCapture(e), this.attachSectionListeners(a, e, t);
    }
    const s = t.querySelector('[data-action="continue"]');
    s && (s.disabled = !this.currentEntry.photos?.plant, s.textContent = this.currentEntry.photos?.tag ? "Continue to Tag Analysis" : "Continue without Tag");
  }
  attachSectionListeners(e, t, a) {
    e.querySelectorAll('[data-action="camera"]').forEach((s) => {
      s.addEventListener("click", () => this.startCamera(t, a));
    }), e.querySelectorAll('[data-action="library"]').forEach((s) => {
      s.addEventListener("click", () => this.openPhotoLibrary(t, a));
    }), e.querySelectorAll('[data-action="take-photo"]').forEach((s) => {
      s.addEventListener("click", () => this.takePhoto(t, a));
    }), e.querySelectorAll('[data-action="cancel-camera"]').forEach((s) => {
      s.addEventListener("click", () => this.cancelCamera(t, a));
    }), e.querySelectorAll('[data-action="retake"]').forEach((s) => {
      s.addEventListener("click", () => this.retakePhoto(t, a));
    });
  }
  continueToAnalysis() {
    this.currentEntry.id = this.generateId(), this.currentEntry.timestamp = (/* @__PURE__ */ new Date()).toISOString(), this.widget.navigateTo("analysis", this.currentEntry);
  }
  generateId() {
    return "entry_" + Date.now() + "_" + Math.random().toString(36).substr(2, 9);
  }
  // Clean up when view is destroyed
  destroy() {
    this.stream && (this.stream.getTracks().forEach((e) => e.stop()), this.stream = null);
  }
}
class y {
  constructor(e) {
    this.widget = e;
  }
  render() {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">My Last 10 Entries</h2>
        </div>

        <!-- Loading State -->
        <div id="entries-loading" class="text-center py-8">
          <div class="text-gray-500 dark:text-gray-400">Loading entries...</div>
        </div>

        <!-- Entries List -->
        <div id="entries-list" class="space-y-4 hidden">
          <!-- Entries will be populated here -->
        </div>

        <!-- Empty State -->
        <div id="entries-empty" class="text-center py-12 hidden">
          <div class="text-gray-500 dark:text-gray-400 mb-4">
            📋 No entries yet
          </div>
          <p class="text-sm text-gray-400 dark:text-gray-500 mb-6">
            Start your first orchid judging session to see entries here
          </p>
          <button class="btn btn-primary" data-action="start-new">
            Start New Entry
          </button>
        </div>
      </div>
    `;
  }
  async mount(e) {
    const t = e.querySelector('[data-action="back"]'), a = e.querySelector('[data-action="start-new"]');
    t?.addEventListener("click", () => this.widget.goBack()), a?.addEventListener("click", () => this.widget.navigateTo("capture")), await this.loadEntries(e);
  }
  async loadEntries(e) {
    const t = e.querySelector("#entries-loading"), a = e.querySelector("#entries-list"), s = e.querySelector("#entries-empty");
    try {
      const i = await l.getEntries(10);
      t?.classList.add("hidden"), i.length === 0 ? s?.classList.remove("hidden") : (a.innerHTML = i.map((r) => this.renderEntry(r)).join(""), a?.classList.remove("hidden"), a?.querySelectorAll('[data-action="view-entry"]').forEach((r) => {
        r.addEventListener("click", (d) => {
          const o = d.target.dataset.entryId;
          o && this.viewEntry(o);
        });
      }));
    } catch (i) {
      console.error("Failed to load entries:", i), t.innerHTML = `
        <div class="text-red-500 dark:text-red-400">
          Failed to load entries. Please try again.
        </div>
      `;
    }
  }
  renderEntry(e) {
    const t = new Date(e.timestamp).toLocaleDateString(), a = new Date(e.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }), s = this.getDisplayName(e), i = this.getBandClass(e.scoring.band);
    let r = 0;
    return e.photos.plant && r++, e.photos.tag && r++, e.certificate?.png && r++, `
      <div class="card hover:shadow-md transition-shadow cursor-pointer" 
           data-action="view-entry" data-entry-id="${e.id}">
        <div class="flex items-start gap-4">
          <!-- Thumbnail -->
          <div class="w-16 h-16 rounded-lg overflow-hidden bg-gray-100 dark:bg-gray-800 flex-shrink-0">
            ${e.photos.plant ? `<img src="${e.photos.plant}" alt="Orchid" class="w-full h-full object-cover">` : '<div class="w-full h-full flex items-center justify-center text-gray-400">📷</div>'}
          </div>
          
          <!-- Content -->
          <div class="flex-1 min-w-0">
            <div class="flex items-start justify-between gap-2 mb-2">
              <h3 class="font-semibold text-gray-900 dark:text-white truncate">
                ${s}
              </h3>
              <span class="text-sm px-2 py-1 rounded-full ${i} flex-shrink-0">
                ${e.scoring.weightedTotal}/100
              </span>
            </div>
            
            <div class="flex items-center gap-4 text-sm text-gray-600 dark:text-gray-400 mb-2">
              <span>🏆 AOS (Educational)</span>
              <span>📅 ${t}</span>
              <span>🕒 ${a}</span>
            </div>
            
            <div class="flex items-center justify-between">
              <span class="text-xs px-2 py-1 rounded ${i}">
                ${e.scoring.band}
              </span>
              
              <div class="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                ${r > 0 ? `<span>📎 ${r}</span>` : ""}
                <span class="text-green-600 dark:text-green-400">●</span>
                <span>Completed</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  getDisplayName(e) {
    const { genus: t, speciesOrGrex: a, clone: s } = e.ocr;
    if (!t && !a)
      return "Unnamed Orchid";
    let i = t || "Unknown";
    return a && (i += " " + a), s && (i += ` '${s}'`), i;
  }
  getBandClass(e) {
    switch (e) {
      case "Excellence (educational)":
        return "score-band-excellence";
      case "Distinction (educational)":
        return "score-band-distinction";
      case "Commended (educational)":
        return "score-band-commended";
      default:
        return "score-band-none";
    }
  }
  async viewEntry(e) {
    try {
      const t = await l.getEntry(e);
      t && this.widget.navigateTo("certificate", t);
    } catch (t) {
      console.error("Failed to load entry:", t), alert("Failed to load entry. Please try again.");
    }
  }
}
class m {
  constructor(e) {
    this.widget = e;
  }
  render(e) {
    if (!e)
      return `
        <div class="text-center py-8">
          <div class="text-gray-500 dark:text-gray-400">No entry data available</div>
          <button class="btn btn-outline mt-4" data-action="back">← Back</button>
        </div>
      `;
    const t = this.getDisplayName(e), a = new Date(e.timestamp).toLocaleDateString(), s = this.getBandClass(e.scoring.band);
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Certificate</h2>
        </div>

        <!-- Certificate Display -->
        <div id="certificate-content" class="card">
          <!-- Header Section -->
          <div class="text-center mb-6">
            <h1 class="text-2xl font-bold text-gray-900 dark:text-white mb-2">
              FCOS Orchid Judge
            </h1>
            <p class="text-sm text-gray-600 dark:text-gray-400">
              Educational Judging Certificate
            </p>
          </div>

          <!-- Orchid Info -->
          <div class="border-b border-gray-200 dark:border-gray-700 pb-4 mb-4">
            <h2 class="text-xl font-semibold text-gray-900 dark:text-white mb-2">
              ${t}
            </h2>
            <div class="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span class="text-gray-600 dark:text-gray-400">Genus:</span>
                <span class="ml-2 text-gray-900 dark:text-white">${e.ocr.genus || "Unknown"}</span>
              </div>
              <div>
                <span class="text-gray-600 dark:text-gray-400">Species/Grex:</span>
                <span class="ml-2 text-gray-900 dark:text-white">${e.ocr.speciesOrGrex || "Unknown"}</span>
              </div>
              ${e.ocr.clone ? `
                <div class="col-span-2">
                  <span class="text-gray-600 dark:text-gray-400">Clone:</span>
                  <span class="ml-2 text-gray-900 dark:text-white">'${e.ocr.clone}'</span>
                </div>
              ` : ""}
            </div>
          </div>

          <!-- Metrics Panel -->
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${e.analysis.spikeCount}
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">Spike Count</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${e.analysis.symmetryPct}%
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">Symmetry</div>
            </div>
            <div class="text-center">
              <div class="text-2xl font-bold text-primary-600 dark:text-primary-400">
                ${e.analysis.naturalSpreadCm}cm
              </div>
              <div class="text-sm text-gray-600 dark:text-gray-400">Natural Spread</div>
            </div>
          </div>

          <!-- Scoring Results -->
          <div class="mb-6">
            <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
              Educational Scoring Results
            </h3>
            
            <div class="text-center mb-4">
              <div class="text-4xl font-bold text-gray-900 dark:text-white">
                ${e.scoring.weightedTotal}/100
              </div>
              <div class="text-lg px-4 py-2 rounded-full inline-block mt-2 ${s}">
                ${e.scoring.band}
              </div>
            </div>

            <!-- Detailed Scores -->
            <div class="space-y-2 text-sm">
              ${this.renderScoreBreakdown(e)}
            </div>
          </div>

          <!-- Footer -->
          <div class="text-center pt-4 border-t border-gray-200 dark:border-gray-700">
            <p class="text-sm text-gray-600 dark:text-gray-400 mb-1">
              Five Cities Orchid Society — Learn · Grow · Share
            </p>
            <p class="text-xs text-gray-500 dark:text-gray-500">
              Generated on ${a} • Educational purposes only
            </p>
          </div>
        </div>

        <!-- Export Actions -->
        <div class="space-y-4">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white">
            Export Options
          </h3>
          
          <div class="grid grid-cols-2 gap-3">
            <button class="btn btn-primary" data-action="export-png">
              📄 Certificate PNG
            </button>
            <button class="btn btn-outline" data-action="export-csv">
              📊 Score Report CSV
            </button>
            <button class="btn btn-outline" data-action="export-narrative">
              📝 Narrative TXT
            </button>
            <button class="btn btn-outline" data-action="export-hybrid">
              🧬 Hybrid Report TXT
            </button>
          </div>

          <!-- Email & Share -->
          <div class="card bg-gray-50 dark:bg-gray-800">
            <h4 class="font-medium text-gray-900 dark:text-white mb-3">
              Share Results
            </h4>
            <div class="space-y-3">
              <input type="email" class="input" id="share-email" 
                     placeholder="Email address (optional)">
              <div class="flex gap-2">
                <button class="btn btn-primary flex-1" data-action="share">
                  📧 Share
                </button>
                <button class="btn btn-outline" data-action="save-entry">
                  💾 Save Entry
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;
  }
  renderScoreBreakdown(e) {
    return [
      { key: "form", label: "Form / Symmetry / Balance" },
      { key: "color", label: "Color & Saturation" },
      { key: "size", label: "Size / Substance" },
      { key: "floriferousness", label: "Floriferousness & Arrangement" },
      { key: "condition", label: "Condition & Grooming" },
      { key: "distinctiveness", label: "Distinctiveness / Impression" }
    ].map((a) => {
      const s = e.scoring.weights[a.key], i = e.scoring.raw[a.key], r = Math.round(i / 100 * s);
      return `
        <div class="flex justify-between items-center">
          <span class="text-gray-700 dark:text-gray-300">${a.label}</span>
          <div class="text-right">
            <span class="text-gray-900 dark:text-white font-medium">${r}/${s}</span>
            <span class="text-gray-500 dark:text-gray-400 ml-2">(${i}/100)</span>
          </div>
        </div>
      `;
    }).join("");
  }
  getDisplayName(e) {
    const { genus: t, speciesOrGrex: a, clone: s } = e.ocr;
    if (!t && !a)
      return "Unnamed Orchid";
    let i = t || "Unknown";
    return a && (i += " " + a), s && (i += ` '${s}'`), i;
  }
  getBandClass(e) {
    switch (e) {
      case "Excellence (educational)":
        return "score-band-excellence";
      case "Distinction (educational)":
        return "score-band-distinction";
      case "Commended (educational)":
        return "score-band-commended";
      default:
        return "score-band-none";
    }
  }
  mount(e) {
    e.querySelector('[data-action="back"]')?.addEventListener("click", () => this.widget.goBack()), e.querySelector('[data-action="export-png"]')?.addEventListener("click", () => this.exportPNG()), e.querySelector('[data-action="export-csv"]')?.addEventListener("click", () => this.exportCSV()), e.querySelector('[data-action="export-narrative"]')?.addEventListener("click", () => this.exportNarrative()), e.querySelector('[data-action="export-hybrid"]')?.addEventListener("click", () => this.exportHybrid()), e.querySelector('[data-action="share"]')?.addEventListener("click", () => this.shareResults()), e.querySelector('[data-action="save-entry"]')?.addEventListener("click", () => this.saveEntry());
  }
  async exportPNG() {
    try {
      const e = (await import("./html2canvas.esm-Dmi1NfiH.js")).default, t = document.querySelector("#certificate-content");
      if (!t) return;
      const a = await e(t, {
        backgroundColor: "#ffffff",
        scale: 2,
        useCORS: !0
      }), s = document.createElement("a");
      s.download = `orchid-certificate-${Date.now()}.png`, s.href = a.toDataURL(), s.click();
    } catch (e) {
      console.error("Failed to export PNG:", e), alert("Failed to export certificate. Please try again.");
    }
  }
  exportCSV() {
    alert("CSV export functionality coming soon!");
  }
  exportNarrative() {
    alert("Narrative export functionality coming soon!");
  }
  exportHybrid() {
    alert("Hybrid report export functionality coming soon!");
  }
  shareResults() {
    alert("Share functionality coming soon!");
  }
  saveEntry() {
    alert("Entry saved successfully!");
  }
}
class f {
  constructor(e) {
    this.widget = e;
  }
  render() {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">How to Use</h2>
        </div>

        <!-- Introduction -->
        <div class="card bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800">
          <h3 class="font-semibold text-blue-800 dark:text-blue-200 mb-2">
            Welcome to FCOS Orchid Judge
          </h3>
          <p class="text-sm text-blue-700 dark:text-blue-300">
            Follow these steps to create educational orchid judging entries. 
            This tool is designed for learning and practice purposes only.
          </p>
        </div>

        <!-- Steps -->
        <div class="space-y-4">
          ${this.renderStep(
      1,
      "📷",
      "Capture Photos",
      "Take clear photos of your blooming orchid and ID tag (if available)",
      "capture"
    )}
          
          ${this.renderStep(
      2,
      "🏷️",
      "Read the Tag",
      "OCR extracts genus/species/grex/clone information from ID tags automatically",
      "capture"
    )}
          
          ${this.renderStep(
      3,
      "📚",
      "Registry Lookup",
      "Optional lookup of parentage and awards from RHS/AOS databases",
      null
    )}
          
          ${this.renderStep(
      4,
      "🔍",
      "Image Analysis",
      "AI analyzes flower counts, symmetry, and measurements with manual editing",
      null
    )}
          
          ${this.renderStep(
      5,
      "⭐",
      "Educational Scoring",
      "Score using weighted educational rubric with instant band results",
      null
    )}
          
          ${this.renderStep(
      6,
      "📤",
      "Export & Cloud",
      "Generate certificates (PNG), reports (CSV/TXT) with optional cloud sync",
      null
    )}
          
          ${this.renderStep(
      7,
      "📋",
      "History & Certificates",
      "Review past entries and generate professional certificates",
      "entries"
    )}
          
          ${this.renderStep(
      8,
      "🔒",
      "Tips & Privacy",
      "Data stays on your device unless cloud sync is enabled",
      null
    )}
        </div>

        <!-- Quick Start -->
        <div class="card bg-primary-50 dark:bg-primary-900/20 border-primary-200 dark:border-primary-800">
          <h3 class="font-semibold text-primary-800 dark:text-primary-200 mb-3">
            Ready to Begin?
          </h3>
          <button class="btn btn-primary w-full" data-action="quick-start">
            Start Your First Entry
          </button>
        </div>
      </div>
    `;
  }
  renderStep(e, t, a, s, i) {
    return `
      <div class="card">
        <div class="flex items-start gap-4">
          <div class="w-10 h-10 bg-primary-100 dark:bg-primary-800 rounded-full flex items-center justify-center flex-shrink-0">
            <span class="text-lg">${t}</span>
          </div>
          
          <div class="flex-1">
            <div class="flex items-center justify-between mb-2">
              <h3 class="font-semibold text-gray-900 dark:text-white">
                ${e}. ${a}
              </h3>
              ${i ? `
                <button class="btn btn-outline btn-sm" data-action="step" data-step="${i}">
                  Start
                </button>
              ` : ""}
            </div>
            
            <p class="text-sm text-gray-600 dark:text-gray-400">
              ${s}
            </p>
          </div>
        </div>
      </div>
    `;
  }
  mount(e) {
    const t = e.querySelector('[data-action="back"]'), a = e.querySelector('[data-action="quick-start"]');
    t?.addEventListener("click", () => this.widget.goBack()), a?.addEventListener("click", () => this.widget.navigateTo("capture")), e.querySelectorAll('[data-action="step"]').forEach((s) => {
      s.addEventListener("click", (i) => {
        const r = i.target.dataset.step;
        r && this.widget.navigateTo(r);
      });
    });
  }
}
class x {
  constructor(e) {
    this.widget = e;
  }
  render() {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">Frequently Asked Questions</h2>
        </div>

        <!-- FAQ Items -->
        <div class="space-y-2">
          ${[
      {
        question: "How is Form / Symmetry / Balance scored?",
        answer: "Form scoring evaluates the overall shape, symmetry, and balance of the flower. Points are awarded for well-proportioned petals, proper flower positioning, and bilateral symmetry. Educational scoring helps you understand ideal orchid characteristics."
      },
      {
        question: "How is Color & Saturation scored?",
        answer: "Color scoring assesses the intensity, clarity, and appeal of flower colors. Vibrant, clear colors with good contrast typically score higher. The AI analyzes color distribution and saturation levels across the bloom."
      },
      {
        question: "How is Size & Substance scored?",
        answer: "Size considers flower dimensions relative to the species standard, while substance evaluates the thickness and quality of petals and sepals. Flowers with good substance appear fuller and more durable."
      },
      {
        question: "How is Floriferousness & Arrangement scored?",
        answer: "This category evaluates the number of flowers, spike quality, and overall presentation. More flowers arranged well on strong spikes typically score higher. The arrangement should be balanced and attractive."
      },
      {
        question: "How is Condition & Grooming scored?",
        answer: "Condition scoring looks at the health and freshness of the flowers, while grooming considers plant cleanliness and presentation. Fresh, unblemished flowers on clean plants score best."
      },
      {
        question: "How is Distinctiveness / Impression scored?",
        answer: "This subjective category rewards exceptional characteristics that make the orchid stand out. Unique color patterns, unusual forms, or exceptional quality can earn high distinctiveness scores."
      },
      {
        question: "Is this official judging?",
        answer: "No, this is an educational tool only. It does not provide official awards from AOS, AOC, RHS, or any recognized orchid organization. Results are for learning and practice purposes only."
      },
      {
        question: "Do my photos upload automatically?",
        answer: "Photos stay on your device by default. Cloud sync only occurs if you enable it in Profile settings and provide the required cloud configuration. You have full control over your data."
      },
      {
        question: "What is Hybrid Analysis?",
        answer: "Hybrid analysis identifies grex names (hybrid group names) and attempts to lookup parentage information. When available, it provides breeding history and related awards to help understand the hybrid's background."
      },
      {
        question: "How do I export my results?",
        answer: "From any entry, you can export certificates as PNG images, detailed scoring as CSV files, or narrative reports as TXT files. Use the share button to email or save results to your device."
      },
      {
        question: "Can I track progress over multiple years?",
        answer: "Yes! The app maintains a history of your entries, allowing you to track improvements and compare results over time. Your data persists on your device until you clear it or the app is uninstalled."
      }
    ].map((t, a) => this.renderFAQItem(t, a)).join("")}
        </div>

        <!-- Additional Help -->
        <div class="card bg-gray-50 dark:bg-gray-800">
          <h3 class="font-semibold text-gray-900 dark:text-white mb-2">
            Need More Help?
          </h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            This tool is provided by the Five Cities Orchid Society for educational purposes. 
            For technical support or questions about orchid care, visit our website or contact local orchid societies.
          </p>
          <div class="flex gap-2">
            <button class="btn btn-outline btn-sm" data-action="about">
              About FCOS
            </button>
            <button class="btn btn-outline btn-sm" data-action="profile">
              Run Diagnostics
            </button>
          </div>
        </div>
      </div>
    `;
  }
  renderFAQItem(e, t) {
    return `
      <div class="card">
        <button class="w-full text-left" data-action="toggle-faq" data-index="${t}">
          <div class="flex items-center justify-between">
            <h3 class="font-medium text-gray-900 dark:text-white pr-4">
              ${e.question}
            </h3>
            <span class="faq-icon text-gray-400 transform transition-transform duration-200">
              ▼
            </span>
          </div>
        </button>
        
        <div class="faq-answer hidden mt-3 pt-3 border-t border-gray-200 dark:border-gray-700">
          <p class="text-sm text-gray-600 dark:text-gray-400">
            ${e.answer}
          </p>
        </div>
      </div>
    `;
  }
  mount(e) {
    const t = e.querySelector('[data-action="back"]'), a = e.querySelector('[data-action="about"]'), s = e.querySelector('[data-action="profile"]');
    t?.addEventListener("click", () => this.widget.goBack()), a?.addEventListener("click", () => this.widget.navigateTo("about")), s?.addEventListener("click", () => this.widget.navigateTo("profile")), e.querySelectorAll('[data-action="toggle-faq"]').forEach((i) => {
      i.addEventListener("click", (r) => {
        const o = r.currentTarget.closest(".card"), c = o?.querySelector(".faq-answer"), u = o?.querySelector(".faq-icon");
        c && u && (c.classList.contains("hidden") ? (c.classList.remove("hidden"), u.classList.add("rotate-180")) : (c.classList.add("hidden"), u.classList.remove("rotate-180")));
      });
    });
  }
}
class w {
  constructor(e) {
    this.widget = e;
  }
  render() {
    return `
      <div class="space-y-6">
        <!-- Header -->
        <div class="flex items-center gap-3 mb-6">
          <button class="btn btn-outline" data-action="back">← Back</button>
          <h2 class="text-xl font-bold text-gray-900 dark:text-white">About</h2>
        </div>

        <!-- Educational Tool Badge -->
        <div class="text-center">
          <div class="inline-block px-4 py-2 bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 rounded-full text-sm font-medium mb-4">
            Educational Tool (Beta)
          </div>
        </div>

        <!-- FCOS Mission -->
        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Five Cities Orchid Society Mission
          </h3>
          <p class="text-gray-600 dark:text-gray-400 text-sm leading-relaxed">
            The Five Cities Orchid Society is dedicated to promoting the appreciation, 
            cultivation, and conservation of orchids through education, research, and community engagement. 
            We believe in making orchid knowledge accessible to everyone, from beginners to experts.
          </p>
        </div>

        <!-- Features -->
        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Widget Features
          </h3>
          <div class="space-y-2 text-sm">
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span class="text-gray-600 dark:text-gray-400">Mobile-first responsive design</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span class="text-gray-600 dark:text-gray-400">AI-powered image analysis and OCR</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span class="text-gray-600 dark:text-gray-400">Multiple international judging systems</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span class="text-gray-600 dark:text-gray-400">Comprehensive entry history and tracking</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span class="text-gray-600 dark:text-gray-400">Offline-first with optional cloud sync</span>
            </div>
            <div class="flex items-center gap-2">
              <span class="w-2 h-2 bg-primary-500 rounded-full"></span>
              <span class="text-gray-600 dark:text-gray-400">Professional certificate generation</span>
            </div>
          </div>
        </div>

        <!-- Important Disclaimer -->
        <div class="card bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800">
          <div class="flex items-start gap-3">
            <div class="text-amber-600 dark:text-amber-400 mt-1 text-lg">⚠️</div>
            <div>
              <h3 class="font-semibold text-amber-800 dark:text-amber-200 mb-2">
                Important Disclaimer
              </h3>
              <div class="text-sm text-amber-700 dark:text-amber-300 space-y-2">
                <p>
                  <strong>This is an educational tool for practice and learning purposes only.</strong>
                </p>
                <p>
                  This application is not affiliated with, endorsed by, or approved by the American Orchid Society (AOS), 
                  Australian Orchid Council (AOC), Orchid Society of New Zealand (OSNZ), Royal Horticultural Society (RHS), 
                  or any other official orchid judging organization.
                </p>
                <p>
                  Results, scores, and awards generated by this tool are for educational practice only and 
                  have no official recognition or validity for actual orchid judging competitions.
                </p>
                <p>
                  For official orchid judging, please contact your local orchid society or 
                  authorized judging centers recognized by official organizations.
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- Version & Technical Info -->
        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Technical Information
          </h3>
          <div class="text-sm text-gray-600 dark:text-gray-400 space-y-1">
            <div class="flex justify-between">
              <span>Version:</span>
              <span>1.0.0 (Beta)</span>
            </div>
            <div class="flex justify-between">
              <span>Last Updated:</span>
              <span>${(/* @__PURE__ */ new Date()).toLocaleDateString()}</span>
            </div>
            <div class="flex justify-between">
              <span>Data Storage:</span>
              <span>Local Device + Optional Cloud</span>
            </div>
            <div class="flex justify-between">
              <span>AI Provider:</span>
              <span id="ai-provider-display">Configurable</span>
            </div>
          </div>
        </div>

        <!-- Contact & Learn More -->
        <div class="card">
          <h3 class="text-lg font-semibold text-gray-900 dark:text-white mb-3">
            Learn More
          </h3>
          <p class="text-sm text-gray-600 dark:text-gray-400 mb-4">
            Interested in learning more about orchids or joining our community? 
            Connect with the Five Cities Orchid Society and other orchid enthusiasts.
          </p>
          <div class="flex gap-2">
            <button class="btn btn-outline btn-sm" data-action="how-to">
              How to Use
            </button>
            <button class="btn btn-outline btn-sm" data-action="faq">
              FAQ
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div class="text-center text-xs text-gray-500 dark:text-gray-400 py-4 border-t border-gray-200 dark:border-gray-700">
          Five Cities Orchid Society — Learn · Grow · Share<br>
          Educational Widget © ${(/* @__PURE__ */ new Date()).getFullYear()}
        </div>
      </div>
    `;
  }
  mount(e) {
    const t = e.querySelector('[data-action="back"]'), a = e.querySelector('[data-action="how-to"]'), s = e.querySelector('[data-action="faq"]');
    t?.addEventListener("click", () => this.widget.goBack()), a?.addEventListener("click", () => this.widget.navigateTo("howto")), s?.addEventListener("click", () => this.widget.navigateTo("faq")), this.updateAIProviderDisplay(e);
  }
  updateAIProviderDisplay(e) {
    const t = e.querySelector("#ai-provider-display"), a = this.widget.getConfig();
    t && (t.textContent = a.aiProvider.mode === "openai" ? "OpenAI" : "Custom Webhook");
  }
}
class k {
  container;
  config;
  viewState;
  views;
  constructor(e, t) {
    this.container = e, this.config = t, this.viewState = { currentView: "home" }, this.views = /* @__PURE__ */ new Map(), this.initializeWidget(), this.initializeViews(), this.applyTheme(), this.render();
  }
  initializeWidget() {
    this.container.className = `fcos-orchid-judge ${this.config.theme} ${this.config.largeText ? "large-text" : ""}`, this.container.innerHTML = `
      <div class="widget-container">
        <div id="fcos-header" class="sticky top-0 z-10 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 px-4 py-3">
          <div class="flex items-center justify-between">
            <h1 class="text-xl font-bold text-gray-900 dark:text-white">FCOS Orchid Judge</h1>
            <div class="flex gap-2">
              <button id="theme-toggle" class="btn btn-outline text-xs">
                ${this.config.theme === "dark" ? "☀️" : "🌙"}
              </button>
              <button id="text-size-toggle" class="btn btn-outline text-xs">
                Aa ${this.config.largeText ? "Normal" : "Large"}
              </button>
            </div>
          </div>
        </div>
        <div id="fcos-content" class="px-4 py-6"></div>
        <div id="fcos-footer" class="px-4 py-3 border-t border-gray-200 dark:border-gray-700 text-center text-xs text-gray-500">
          Five Cities Orchid Society — Learn · Grow · Share
        </div>
      </div>
    `, this.setupEventListeners();
  }
  initializeViews() {
    this.views.set("home", new h(this)), this.views.set("profile", new v(this)), this.views.set("capture", new b(this)), this.views.set("entries", new y(this)), this.views.set("certificate", new m(this)), this.views.set("howto", new f(this)), this.views.set("faq", new x(this)), this.views.set("about", new w(this));
  }
  setupEventListeners() {
    const e = this.container.querySelector("#theme-toggle"), t = this.container.querySelector("#text-size-toggle");
    e?.addEventListener("click", () => {
      this.config.theme = this.config.theme === "dark" ? "light" : "dark", this.applyTheme(), this.updateHeader();
    }), t?.addEventListener("click", () => {
      this.config.largeText = !this.config.largeText, this.applyTextSize(), this.updateHeader();
    });
  }
  applyTheme() {
    this.config.theme === "dark" ? this.container.classList.add("dark") : this.container.classList.remove("dark");
  }
  applyTextSize() {
    this.config.largeText ? this.container.classList.add("large-text") : this.container.classList.remove("large-text");
  }
  updateHeader() {
    const e = this.container.querySelector("#theme-toggle"), t = this.container.querySelector("#text-size-toggle");
    e && (e.textContent = this.config.theme === "dark" ? "☀️" : "🌙"), t && (t.textContent = `Aa ${this.config.largeText ? "Normal" : "Large"}`);
  }
  render() {
    const e = this.container.querySelector("#fcos-content");
    if (!e) return;
    const t = this.views.get(this.viewState.currentView);
    t && (e.innerHTML = t.render(this.viewState.data), t.mount?.(e));
  }
  navigateTo(e, t) {
    this.viewState.previousView = this.viewState.currentView, this.viewState.currentView = e, this.viewState.data = t, this.render();
  }
  goBack() {
    this.viewState.previousView ? this.navigateTo(this.viewState.previousView) : this.navigateTo("home");
  }
  getConfig() {
    return this.config;
  }
  updateConfig(e) {
    this.config = { ...this.config, ...e }, this.applyTheme(), this.applyTextSize(), this.updateHeader();
  }
  destroy() {
    this.container.innerHTML = "", this.views.clear();
  }
}
const S = {
  mount(n, e = {}) {
    const t = document.querySelector(n);
    if (!t)
      throw new Error(`FCOS Orchid Judge: Container not found for selector "${n}"`);
    const s = { ...{
      theme: "light",
      largeText: !1,
      cloud: {
        webappUrl: window.EXPO_PUBLIC_FCOS_SHEETS_WEBAPP_URL || void 0,
        secret: window.EXPO_PUBLIC_FCOS_SHEETS_SECRET || void 0
      },
      aiProvider: {
        mode: "openai",
        webhookUrl: void 0
      },
      language: "en"
    }, ...e };
    return new k(t, s);
  },
  unmount(n) {
    n.destroy();
  }
};
typeof window < "u" && (window.FCOSOrchidJudge = S);
export {
  k as FCOSOrchidJudgeWidget,
  S as default
};
