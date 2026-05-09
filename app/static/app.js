// =========================
// AUTH / USUARIO
// =========================
const user = JSON.parse(localStorage.getItem("usuario"));

if (!user) {
    window.location.href = "/login-web";
}

// =========================
// USER NAME + MENU
// =========================
function initUserMenu() {
    const userName = document.getElementById("user-name");

    if (!userName) return;

    userName.textContent = user.nombre || user.username;

    userName.addEventListener("click", function (e) {
        e.stopPropagation();
        toggleMenu();
    });

    // cerrar al click afuera
    document.addEventListener("click", function (e) {
        const menu = document.getElementById("dropdown");
        const userMenu = document.querySelector(".user-menu");

        if (!userMenu.contains(e.target)) {
            menu.classList.add("hidden");
        }
    });
}

// =========================
// MENU FUNCTIONS
// =========================
function toggleMenu() {
    const menu = document.getElementById("dropdown");
    menu.classList.toggle("hidden");
}

function closeMenu() {
    document.getElementById("dropdown").classList.add("hidden");
}

function logout() {
    localStorage.removeItem("usuario");
    window.location.href = "/login-web";
}

// =========================
// DARK MODE
// =========================
function toggleDarkMode() {
    document.body.classList.toggle("dark");

    localStorage.setItem(
        "darkMode",
        document.body.classList.contains("dark")
    );

    updateThemeLabel();
    closeMenu();
}

function updateThemeLabel() {
    const el = document.getElementById("toggle-theme");

    if (!el) return;

    if (document.body.classList.contains("dark")) {
        el.textContent = "☀️ Modo claro";
    } else {
        el.textContent = "🌙 Modo oscuro";
    }
}

// cargar modo oscuro al iniciar
function initTheme() {
    if (localStorage.getItem("darkMode") === "true") {
        document.body.classList.add("dark");
    }

    updateThemeLabel();
}

// =========================
// INIT GLOBAL
// =========================
window.addEventListener("DOMContentLoaded", () => {
    initTheme();
    loadHeader();

    // ocultar config si no es ADMIN
    if (user?.rol !== "ADMIN") {
        document.getElementById("menu-config")?.remove();
    }
});

function authHeaders() {
    return {
        "Content-Type": "application/json",
        "x-user-id": user.id,
        "x-user-rol": user.rol
    };
}

// =========================
// TOAST
// =========================
function mostrarToast(mensaje, tipo = "success") {

//    console.log("TOAST CALLED:", mensaje, tipo); // 👈 add this

    const container = document.getElementById("toast-container");

    if (!container) return;

    const toast = document.createElement("div");
    toast.className =`toast ${tipo}`;
    toast.textContent = mensaje;

    container.appendChild(toast);

    // animación
    setTimeout(() => toast.classList.add("show"), 10);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// =========================
// HEADER REUTILIZABLE
// =========================
async function loadHeader() {

  const container = document.getElementById("header-container");

  if (!container) return; // 🔥 evita romper

  try {
    const res = await fetch("/static/header.html");

    if (!res.ok) {
      console.error("No se pudo cargar header.html");
      return;
    }

    const html = await res.text();
    container.innerHTML = html;

    initUserMenu();
    updateThemeLabel();

  } catch (err) {
    console.error("Error cargando header:", err);
  }
}