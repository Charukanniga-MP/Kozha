/**
 * Kozha Front-End Authentication Manager.
 * Supports Email/Password login, registration, Google OAuth, and Navbar Profile Widget.
 */
(function () {
  const TOKEN_KEY = "kozha_auth_token";
  const USER_KEY = "kozha_auth_user";

  window.KozhaAuth = {
    getToken() {
      return localStorage.getItem(TOKEN_KEY) || sessionStorage.getItem(TOKEN_KEY) || "";
    },
    getUser() {
      try {
        const u = localStorage.getItem(USER_KEY) || sessionStorage.getItem(USER_KEY);
        return u ? JSON.parse(u) : null;
      } catch (e) {
        return null;
      }
    },
    setSession(token, user, remember = true) {
      const storage = remember ? localStorage : sessionStorage;
      storage.setItem(TOKEN_KEY, token);
      storage.setItem(USER_KEY, JSON.stringify(user));
      this.updateNavbarUI();
    },
    clearSession() {
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
      sessionStorage.removeItem(TOKEN_KEY);
      sessionStorage.removeItem(USER_KEY);
      this.updateNavbarUI();
      window.location.reload();
    },
    async fetchProfile() {
      const token = this.getToken();
      if (!token) return null;
      try {
        const res = await fetch("/api/auth/me", {
          headers: { Authorization: `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          if (data.user) {
            localStorage.setItem(USER_KEY, JSON.stringify(data.user));
            this.updateNavbarUI();
            return data.user;
          }
        } else {
          this.clearSession();
        }
      } catch (e) {
        console.warn("Auth check error:", e);
      }
      return null;
    },
    async login(email, password, remember = true) {
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Login failed");
      }
      this.setSession(data.token, data.user, remember);
      return data.user;
    },
    async signup(email, password, name, remember = true) {
      const res = await fetch("/api/auth/signup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, name }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Registration failed");
      }
      this.setSession(data.token, data.user, remember);
      return data.user;
    },
    async loginGooglePayload(email, name, picture) {
      const res = await fetch("/api/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name, picture }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "Google login failed");
      }
      this.setSession(data.token, data.user, true);
      return data.user;
    },
    updateNavbarUI() {
      const user = this.getUser();
      const authContainers = document.querySelectorAll(".kozha-nav-auth");
      authContainers.forEach((container) => {
        if (!user) {
          container.innerHTML = `
            <a href="/login.html" class="kz-btn-signin" style="
              display: inline-flex;
              align-items: center;
              gap: 8px;
              padding: 8px 18px;
              background: #c2410c;
              color: #ffffff;
              border-radius: 9999px;
              font-weight: 600;
              font-size: 0.9rem;
              text-decoration: none;
              transition: all 0.2s ease;
            ">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>
              Sign In
            </a>
          `;
        } else {
          const initials = user.name ? user.name.charAt(0).toUpperCase() : "U";
          container.innerHTML = `
            <div style="position: relative; display: inline-block;">
              <button id="kz-user-menu-btn" style="
                display: flex;
                align-items: center;
                gap: 10px;
                background: #f3f4f6;
                border: 1px solid #e5e7eb;
                padding: 6px 14px;
                border-radius: 9999px;
                cursor: pointer;
                font-family: inherit;
              ">
                <div style="
                  width: 28px;
                  height: 28px;
                  border-radius: 50%;
                  background: #c2410c;
                  color: #fff;
                  display: flex;
                  align-items: center;
                  justify-content: center;
                  font-weight: 700;
                  font-size: 0.85rem;
                ">${initials}</div>
                <span style="font-weight: 600; font-size: 0.9rem; color: #1f2937;">${escapeHtml(user.name)}</span>
              </button>
              <div id="kz-user-dropdown" style="
                display: none;
                position: absolute;
                right: 0;
                top: 42px;
                background: #ffffff;
                border: 1px solid #e5e7eb;
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1);
                border-radius: 12px;
                width: 200px;
                padding: 8px 0;
                z-index: 1000;
              ">
                <div style="padding: 10px 16px; border-bottom: 1px solid #f3f4f6;">
                  <p style="margin:0; font-size:0.85rem; font-weight:700; color:#111827;">${escapeHtml(user.name)}</p>
                  <p style="margin:0; font-size:0.75rem; color:#6b7280;">${escapeHtml(user.email)}</p>
                </div>
                <button onclick="KozhaAuth.clearSession()" style="
                  width: 100%;
                  text-align: left;
                  padding: 10px 16px;
                  background: none;
                  border: none;
                  color: #ef4444;
                  font-weight: 600;
                  font-size: 0.88rem;
                  cursor: pointer;
                ">Sign Out</button>
              </div>
            </div>
          `;
          const btn = document.getElementById("kz-user-menu-btn");
          const menu = document.getElementById("kz-user-dropdown");
          if (btn && menu) {
            btn.onclick = (e) => {
              e.stopPropagation();
              menu.style.display = menu.style.display === "block" ? "none" : "block";
            };
            document.addEventListener("click", () => {
              menu.style.display = "none";
            });
          }
        }
      });
    },
  };

  function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/[&<>"']/g, (m) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;" }[m]));
  }

  document.addEventListener("DOMContentLoaded", () => {
    KozhaAuth.fetchProfile();
  });
})();
