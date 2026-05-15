const API_BASE = localStorage.getItem("hackbd_api_base") || "http://127.0.0.1:8000/api/v1";

const state = {
  token: localStorage.getItem("hackbd_token") || "",
  me: null,
};

const els = {
  apiStatus: document.querySelector("#apiStatus"),
  toast: document.querySelector("#toast"),
  profileBox: document.querySelector("#profileBox"),
  sessionTitle: document.querySelector("#sessionTitle"),
  logoutButton: document.querySelector("#logoutButton"),
  hackathonList: document.querySelector("#hackathonList"),
  studentOutput: document.querySelector("#studentOutput"),
  organizerList: document.querySelector("#organizerList"),
  judgeOutput: document.querySelector("#judgeOutput"),
  talentList: document.querySelector("#talentList"),
  adminOutput: document.querySelector("#adminOutput"),
};

function formData(form) {
  return Object.fromEntries(new FormData(form).entries());
}

function splitCsv(value) {
  return String(value || "")
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

function parseCriteria(value) {
  return Object.fromEntries(
    splitCsv(value).map((pair) => {
      const [key, rawScore] = pair.split(":").map((item) => item.trim());
      return [key, Number(rawScore || 0)];
    }),
  );
}

function showToast(message, type = "ok") {
  els.toast.textContent = message;
  els.toast.classList.toggle("error", type === "error");
  els.toast.classList.remove("hidden");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => els.toast.classList.add("hidden"), 4200);
}

async function api(path, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  const text = await response.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = text;
  }
  if (!response.ok) {
    const detail = data?.detail || data || response.statusText;
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return data;
}

async function apiForm(path, body) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams(body),
  });
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data?.detail || response.statusText);
  }
  return data;
}

function renderJson(target, data) {
  target.innerHTML = `<pre class="json-box">${escapeHtml(JSON.stringify(data, null, 2))}</pre>`;
}

async function downloadProtectedCsv(path, filename) {
  if (!requireLogin()) return;
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Authorization: `Bearer ${state.token}` },
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || response.statusText);
  }
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function empty(label) {
  return `<div class="empty">${escapeHtml(label)}</div>`;
}

function card(title, body, meta = "", actions = "") {
  return `
    <article class="card">
      <div>
        <h3>${escapeHtml(title)}</h3>
        ${body ? `<p>${escapeHtml(body)}</p>` : ""}
      </div>
      ${meta ? `<div class="meta-row">${meta}</div>` : ""}
      ${actions ? `<div class="button-row">${actions}</div>` : ""}
    </article>
  `;
}

function tag(value, className = "tag") {
  return `<span class="${className}">${escapeHtml(value || "none")}</span>`;
}

function requireLogin() {
  if (!state.token) {
    showToast("Login first to use this action.", "error");
    return false;
  }
  return true;
}

async function checkApi() {
  try {
    const response = await fetch("http://127.0.0.1:8000/health");
    if (!response.ok) throw new Error("offline");
    els.apiStatus.textContent = "API: online";
    els.apiStatus.classList.remove("offline");
  } catch {
    els.apiStatus.textContent = "API: offline";
    els.apiStatus.classList.add("offline");
  }
}

async function loadMe() {
  if (!state.token) {
    state.me = null;
    renderProfile();
    return;
  }
  try {
    state.me = await api("/me");
    renderProfile();
  } catch (error) {
    state.token = "";
    localStorage.removeItem("hackbd_token");
    renderProfile();
    showToast(error.message, "error");
  }
}

function renderProfile() {
  if (!state.me) {
    els.sessionTitle.textContent = "Not logged in";
    els.profileBox.textContent = "Login to use protected API actions.";
    els.profileBox.classList.add("muted");
    els.logoutButton.classList.add("hidden");
    return;
  }

  els.sessionTitle.textContent = state.me.full_name;
  els.profileBox.classList.remove("muted");
  els.logoutButton.classList.remove("hidden");
  els.profileBox.innerHTML = `
    <div class="profile-line"><strong>Email</strong><span>${escapeHtml(state.me.email)}</span></div>
    <div class="profile-line"><strong>Role</strong><span>${tag(state.me.role, "role")}</span></div>
    <div class="profile-line"><strong>University</strong><span>${escapeHtml(state.me.university || "Not set")}</span></div>
    <div class="profile-line"><strong>Pending</strong><span>${state.me.pending_role_requests?.length || 0}</span></div>
  `;
}

async function loadHackathons(filters = {}) {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value) params.set(key, value);
  });
  const suffix = params.toString() ? `?${params}` : "";
  try {
    const hackathons = await api(`/hackathons${suffix}`, { headers: {} });
    els.hackathonList.innerHTML =
      hackathons.length === 0
        ? empty("No published hackathons found.")
        : hackathons
            .map((item) =>
              card(
                item.title,
                item.description,
                `${tag(item.status)}${tag(item.university || "open")}${tag(item.theme || "general")}`,
                `<button class="button primary" data-register="${item.id}" type="button">Register</button>
                 <button class="button" data-copy-id="${item.id}" type="button">Use ID ${item.id}</button>`,
              ),
            )
            .join("");
  } catch (error) {
    els.hackathonList.innerHTML = empty(error.message);
  }
}

async function loadOrganizerHackathons() {
  if (!requireLogin()) return;
  try {
    const hackathons = await api("/organizer/hackathons");
    els.organizerList.innerHTML =
      hackathons.length === 0
        ? empty("No organizer hackathons yet.")
        : hackathons
            .map((item) =>
              card(
                `${item.title} #${item.id}`,
                item.description,
                `${tag(item.status)}${tag(item.university || "open")}${tag(item.theme || "general")}`,
                `<button class="button success" data-publish="${item.id}" type="button">Publish</button>
                 <button class="button" data-analytics="${item.id}" type="button">Analytics</button>
                 <button class="button" data-export-projects="${item.id}" type="button">Projects CSV</button>`,
              ),
            )
            .join("");
  } catch (error) {
    els.organizerList.innerHTML = empty(error.message);
  }
}

async function loadTalent(params = {}) {
  if (!requireLogin()) return;
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value) query.set(key, value);
  });
  try {
    const users = await api(`/talent/search?${query}`);
    els.talentList.innerHTML =
      users.length === 0
        ? empty("No students matched.")
        : users
            .map((user) =>
              card(
                `${user.full_name} #${user.id}`,
                user.bio || "No bio yet.",
                `${tag(user.university || "university n/a")}${tag((user.skills || []).join(", ") || "skills n/a")}`,
                `<button class="button primary" data-save-talent="${user.id}" type="button">Save interest</button>`,
              ),
            )
            .join("");
  } catch (error) {
    els.talentList.innerHTML = empty(error.message);
  }
}

async function loadAdminRoleRequests() {
  if (!requireLogin()) return;
  try {
    const requests = await api("/admin/role-requests");
    els.adminOutput.innerHTML =
      requests.length === 0
        ? empty("No pending role requests.")
        : requests
            .map((request) =>
              card(
                `Request #${request.id}`,
                request.reason,
                `${tag(request.requested_role)}${tag(request.university || "no university")}${tag(request.status)}`,
                `<button class="button success" data-approve-role="${request.id}" type="button">Approve</button>
                 <button class="button danger" data-reject-role="${request.id}" type="button">Reject</button>`,
              ),
            )
            .join("");
  } catch (error) {
    els.adminOutput.innerHTML = empty(error.message);
  }
}

function bindNavigation() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => {
      const view = button.dataset.view;
      document.querySelectorAll(".nav-button").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".view").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      document.querySelector(`#view-${view}`).classList.add("active");
    });
  });

  document.querySelectorAll("[data-auth-tab]").forEach((button) => {
    button.addEventListener("click", () => {
      document.querySelectorAll("[data-auth-tab]").forEach((item) => item.classList.remove("active"));
      document.querySelectorAll(".auth-form").forEach((item) => item.classList.add("hidden"));
      button.classList.add("active");
      document.querySelector(`#${button.dataset.authTab}Form`).classList.remove("hidden");
    });
  });
}

function bindForms() {
  document.querySelector("#loginForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formData(event.currentTarget);
    try {
      const token = await apiForm("/auth/login", {
        username: data.email,
        password: data.password,
      });
      state.token = token.access_token;
      localStorage.setItem("hackbd_token", state.token);
      await loadMe();
      showToast("Logged in.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#registerForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    const data = formData(event.currentTarget);
    try {
      await api("/auth/register", {
        method: "POST",
        body: JSON.stringify({
          ...data,
          skills: splitCsv(data.skills),
        }),
      });
      showToast("Account created. You can login now.");
      event.currentTarget.reset();
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#roleRequestForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const data = formData(event.currentTarget);
    try {
      await api("/me/request-role", {
        method: "POST",
        body: JSON.stringify(data),
      });
      await loadMe();
      showToast("Role request submitted.");
      event.currentTarget.reset();
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#hackathonFilters").addEventListener("submit", (event) => {
    event.preventDefault();
    loadHackathons(formData(event.currentTarget));
  });

  document.querySelector("#registerHackathonForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const data = formData(event.currentTarget);
    try {
      const registration = await api(`/hackathons/${data.hackathon_id}/register`, { method: "POST" });
      renderJson(els.studentOutput, registration);
      showToast("Registered for hackathon.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#teamForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const data = formData(event.currentTarget);
    try {
      const team = await api("/teams", {
        method: "POST",
        body: JSON.stringify({
          ...data,
          hackathon_id: Number(data.hackathon_id),
          desired_skills: splitCsv(data.desired_skills),
        }),
      });
      renderJson(els.studentOutput, team);
      showToast("Team created.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#projectForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const data = formData(event.currentTarget);
    try {
      const project = await api("/projects", {
        method: "POST",
        body: JSON.stringify({
          ...data,
          team_id: Number(data.team_id),
          image_urls: splitCsv(data.image_urls),
        }),
      });
      renderJson(els.studentOutput, project);
      showToast("Project draft created.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#hackathonForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const data = formData(event.currentTarget);
    try {
      await api("/organizer/hackathons", {
        method: "POST",
        body: JSON.stringify({
          ...data,
          min_team_size: Number(data.min_team_size),
          max_team_size: Number(data.max_team_size),
        }),
      });
      await loadOrganizerHackathons();
      showToast("Hackathon created.");
      event.currentTarget.reset();
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#scoreForm").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!requireLogin()) return;
    const data = formData(event.currentTarget);
    try {
      const score = await api(`/projects/${data.project_id}/score`, {
        method: "POST",
        body: JSON.stringify({
          total_score: Number(data.total_score),
          criteria_scores: parseCriteria(data.criteria_scores),
          feedback: data.feedback,
        }),
      });
      renderJson(els.judgeOutput, score);
      showToast("Score submitted.");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.querySelector("#talentSearchForm").addEventListener("submit", (event) => {
    event.preventDefault();
    loadTalent(formData(event.currentTarget));
  });
}

function bindButtons() {
  els.logoutButton.addEventListener("click", () => {
    state.token = "";
    state.me = null;
    localStorage.removeItem("hackbd_token");
    renderProfile();
    showToast("Logged out.");
  });

  document.querySelector("#refreshHackathons").addEventListener("click", () => loadHackathons());
  document.querySelector("#loadOrganizerHackathons").addEventListener("click", loadOrganizerHackathons);
  document.querySelector("#loadRoleRequests").addEventListener("click", loadAdminRoleRequests);
  document.querySelector("#loadRegistrations").addEventListener("click", async () => {
    if (!requireLogin()) return;
    try {
      renderJson(els.studentOutput, await api("/student/registrations"));
    } catch (error) {
      showToast(error.message, "error");
    }
  });
  document.querySelector("#loadJudgeAssignments").addEventListener("click", async () => {
    if (!requireLogin()) return;
    try {
      renderJson(els.judgeOutput, await api("/judge/assignments"));
    } catch (error) {
      showToast(error.message, "error");
    }
  });
  document.querySelector("#loadSavedTalent").addEventListener("click", async () => {
    if (!requireLogin()) return;
    try {
      renderJson(els.talentList, await api("/talent/saved"));
    } catch (error) {
      showToast(error.message, "error");
    }
  });
  document.querySelector("#loadReports").addEventListener("click", async () => {
    if (!requireLogin()) return;
    try {
      renderJson(els.adminOutput, await api("/admin/reports"));
    } catch (error) {
      showToast(error.message, "error");
    }
  });
  document.querySelector("#loadUsers").addEventListener("click", async () => {
    if (!requireLogin()) return;
    try {
      const users = await api("/admin/users");
      els.adminOutput.innerHTML = users
        .map((user) =>
          card(
            `${user.full_name} #${user.id}`,
            user.email,
            `${tag(user.role, "role")}${tag(user.university || "no university")}`,
            "",
          ),
        )
        .join("");
    } catch (error) {
      showToast(error.message, "error");
    }
  });

  document.body.addEventListener("click", async (event) => {
    const button = event.target.closest("button[data-register], button[data-copy-id], button[data-publish], button[data-analytics], button[data-export-projects], button[data-approve-role], button[data-reject-role], button[data-save-talent]");
    if (!button) return;

    try {
      if (button.dataset.copyId) {
        document.querySelector("#registerHackathonForm [name='hackathon_id']").value = button.dataset.copyId;
        showToast(`Hackathon ID ${button.dataset.copyId} copied into the student form.`);
      }
      if (button.dataset.register) {
        if (!requireLogin()) return;
        const registration = await api(`/hackathons/${button.dataset.register}/register`, { method: "POST" });
        renderJson(els.studentOutput, registration);
        showToast("Registered.");
      }
      if (button.dataset.publish) {
        if (!requireLogin()) return;
        await api(`/organizer/hackathons/${button.dataset.publish}/publish`, { method: "PATCH" });
        await loadOrganizerHackathons();
        await loadHackathons();
        showToast("Hackathon published.");
      }
      if (button.dataset.analytics) {
        if (!requireLogin()) return;
        renderJson(els.organizerList, await api(`/organizer/hackathons/${button.dataset.analytics}/analytics`));
      }
      if (button.dataset.exportProjects) {
        if (!requireLogin()) return;
        await downloadProtectedCsv(
          `/organizer/hackathons/${button.dataset.exportProjects}/export/projects`,
          `hackathon-${button.dataset.exportProjects}-projects.csv`,
        );
        showToast("Projects CSV downloaded.");
      }
      if (button.dataset.approveRole) {
        if (!requireLogin()) return;
        await api(`/admin/role-requests/${button.dataset.approveRole}/approve`, {
          method: "POST",
          body: JSON.stringify({ note: "Approved from frontend console." }),
        });
        await loadAdminRoleRequests();
        showToast("Role request approved.");
      }
      if (button.dataset.rejectRole) {
        if (!requireLogin()) return;
        await api(`/admin/role-requests/${button.dataset.rejectRole}/reject`, {
          method: "POST",
          body: JSON.stringify({ note: "Rejected from frontend console." }),
        });
        await loadAdminRoleRequests();
        showToast("Role request rejected.");
      }
      if (button.dataset.saveTalent) {
        if (!requireLogin()) return;
        await api("/talent/interest", {
          method: "POST",
          body: JSON.stringify({
            student_id: Number(button.dataset.saveTalent),
            note: "Saved from frontend console.",
          }),
        });
        showToast("Talent interest saved.");
      }
    } catch (error) {
      showToast(error.message, "error");
    }
  });
}

async function boot() {
  bindNavigation();
  bindForms();
  bindButtons();
  renderProfile();
  await checkApi();
  await loadMe();
  await loadHackathons();
}

boot();
