/**
 * TrackWeave API Client
 * Centralises all fetch calls to the FastAPI backend.
 * Automatically attaches the JWT access token and handles 401 refresh.
 */

const API_BASE = "/api";

// ── Token storage ─────────────────────────────────────────────────────────────
const Auth = {
  getAccess()  { return localStorage.getItem("tw_access"); },
  getRefresh() { return localStorage.getItem("tw_refresh"); },
  save(tokens) {
    localStorage.setItem("tw_access",  tokens.access_token);
    localStorage.setItem("tw_refresh", tokens.refresh_token);
  },
  clear() {
    localStorage.removeItem("tw_access");
    localStorage.removeItem("tw_refresh");
    localStorage.removeItem("tw_user");
  },
  saveUser(user) { localStorage.setItem("tw_user", JSON.stringify(user)); },
  getUser()      {
    try { return JSON.parse(localStorage.getItem("tw_user")); }
    catch { return null; }
  },
  isLoggedIn()   { return !!Auth.getAccess(); },
};

// ── Core fetch wrapper ────────────────────────────────────────────────────────
async function apiFetch(path, options = {}, retry = true) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  const token = Auth.getAccess();
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${API_BASE}${path}`, { ...options, headers });

  // Try to refresh token once on 401
  if (res.status === 401 && retry) {
    const refreshed = await tryRefresh();
    if (refreshed) return apiFetch(path, options, false);
    Auth.clear();
    window.location.href = "/signin.html";
    return;
  }

  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try { const body = await res.json(); detail = body.detail || detail; } catch {}
    throw new Error(detail);
  }

  if (res.status === 204) return null;
  return res.json();
}

async function tryRefresh() {
  const rt = Auth.getRefresh();
  if (!rt) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
    });
    if (!res.ok) return false;
    const tokens = await res.json();
    Auth.save(tokens);
    return true;
  } catch { return false; }
}

// ── Public API ────────────────────────────────────────────────────────────────
const API = {
  // Auth
  register: (data)         => apiFetch("/auth/register",  { method: "POST", body: JSON.stringify(data) }),
  login:    (data)         => apiFetch("/auth/login",     { method: "POST", body: JSON.stringify(data) }),
  me:       ()             => apiFetch("/auth/me"),

  // Users
  getProfile:   (username) => apiFetch(`/users/${username}`),
  updateProfile:(data)     => apiFetch("/users/me",       { method: "PATCH", body: JSON.stringify(data) }),
  uploadAvatar: (file) => {
    const fd = new FormData();
    fd.append("file", file);
    const headers = {};
    const token = Auth.getAccess();
    if (token) headers["Authorization"] = `Bearer ${token}`;
    return fetch(`${API_BASE}/users/me/avatar`, { method: "POST", headers, body: fd })
      .then(r => r.ok ? r.json() : r.json().then(b => Promise.reject(new Error(b.detail))));
  },
  userPosts: (username, skip = 0) => apiFetch(`/users/${username}/posts?skip=${skip}`),

  // Posts
  getPosts:   (skip = 0, sort = "new") => apiFetch(`/posts/?skip=${skip}&sort=${sort}`),
  getPost:    (id)                     => apiFetch(`/posts/${id}`),
  createPost: (data)                   => apiFetch("/posts/",     { method: "POST",  body: JSON.stringify(data) }),
  updatePost: (id, data)               => apiFetch(`/posts/${id}`,{ method: "PATCH", body: JSON.stringify(data) }),
  deletePost: (id)                     => apiFetch(`/posts/${id}`,{ method: "DELETE" }),

  // Comments
  getComments:   (postId)        => apiFetch(`/comments/post/${postId}`),
  createComment: (postId, data)  => apiFetch(`/comments/post/${postId}`, { method: "POST",  body: JSON.stringify(data) }),
  updateComment: (id, data)      => apiFetch(`/comments/${id}`,          { method: "PATCH", body: JSON.stringify(data) }),
  deleteComment: (id)            => apiFetch(`/comments/${id}`,          { method: "DELETE" }),

  // Votes
  vote: (data) => apiFetch("/votes/", { method: "POST", body: JSON.stringify(data) }),
};

// ── UI helpers ────────────────────────────────────────────────────────────────
function timeAgo(dateStr) {
  const diff = (Date.now() - new Date(dateStr)) / 1000;
  if (diff < 60)    return `${Math.floor(diff)}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
}

function avatarEl(user, size = 32) {
  if (user?.avatar_url) {
    return `<img src="${user.avatar_url}" class="rounded-full object-cover" style="width:${size}px;height:${size}px;" alt="${user.username}" />`;
  }
  const initials = (user?.display_name || user?.username || "?")[0].toUpperCase();
  return `<div class="rounded-full bg-[#00e054] flex items-center justify-center text-[#14181c] font-bold" style="width:${size}px;height:${size}px;font-size:${Math.max(10,size*0.4)}px;">${initials}</div>`;
}

/** Render the navbar: show username+avatar if logged in, else Sign in/Create Account links */
function renderNavAuth() {
  const user = Auth.getUser();
  const container = document.getElementById("navAuth");
  if (!container) return;
  if (user) {
    container.innerHTML = `
      <a href="/feed.html" class="text-[#9ab] no-underline text-sm hover:text-white transition-colors duration-200">Feed</a>
      <a href="/profile.html?u=${user.username}" class="flex items-center gap-2 no-underline">
        ${avatarEl(user, 30)}
        <span class="text-white text-sm font-medium hidden md:inline">${user.display_name || user.username}</span>
      </a>
      <button onclick="signOut()" class="text-[#9ab] text-sm hover:text-white transition-colors duration-200 bg-transparent border-none cursor-pointer">Sign out</button>
    `;
  } else {
    container.innerHTML = `
      <a href="/signin.html" class="text-[#00e054] no-underline text-sm font-normal hover:text-[#00ff5e] transition-colors duration-200">Sign in</a>
      <a href="/register.html" class="bg-[#00e054] text-[#14181c] no-underline text-sm font-semibold py-2 px-5 rounded-md hover:bg-[#00ff5e] transition-colors duration-200">Create Account</a>
    `;
  }
}

function signOut() {
  Auth.clear();
  window.location.href = "/";
}

// Bootstrap auth state from the server on every page load
async function initAuth() {
  if (Auth.isLoggedIn()) {
    try {
      const user = await API.me();
      Auth.saveUser(user);
    } catch { /* token may have been manually deleted on server — clear */ Auth.clear(); }
  }
  renderNavAuth();
}
