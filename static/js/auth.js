// Widget de sesión (Google Sign-In) compartido por todas las páginas.
// Cada página solo necesita un <div id="authSlot"></div> en su nav y
// cargar este script; este archivo hace fetch a /api/me y decide qué
// mostrar. No hay estado de sesión en el HTML servido por Flask: todas
// las páginas son iguales para logueados y no logueados hasta que este
// script corre.
(function () {
    const GOOGLE_G = `<svg width="16" height="16" viewBox="0 0 18 18" aria-hidden="true">
        <path fill="#4285F4" d="M17.64 9.2c0-.64-.06-1.25-.16-1.84H9v3.48h4.84a4.14 4.14 0 0 1-1.8 2.72v2.26h2.9c1.7-1.57 2.7-3.87 2.7-6.62z"/>
        <path fill="#34A853" d="M9 18c2.43 0 4.47-.8 5.96-2.18l-2.9-2.26c-.8.54-1.84.86-3.06.86-2.35 0-4.34-1.59-5.05-3.72H.96v2.33A9 9 0 0 0 9 18z"/>
        <path fill="#FBBC05" d="M3.95 10.7A5.4 5.4 0 0 1 3.67 9c0-.59.1-1.17.28-1.7V4.97H.96A9 9 0 0 0 0 9c0 1.45.35 2.83.96 4.03l2.99-2.33z"/>
        <path fill="#EA4335" d="M9 3.58c1.32 0 2.51.46 3.44 1.35l2.58-2.58C13.46.89 11.43 0 9 0A9 9 0 0 0 .96 4.97l2.99 2.33C4.66 5.17 6.65 3.58 9 3.58z"/>
    </svg>`;

    function esc(s) {
        return String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    }

    async function render() {
        const slot = document.getElementById('authSlot');
        if (!slot) return;
        let user = null;
        try {
            const r = await fetch('/api/me');
            user = await r.json();
        } catch (e) { /* sin conexión: se queda como invitado */ }

        if (user) {
            slot.innerHTML = `
                <div class="auth-user">
                    ${user.picture ? `<img class="auth-avatar" src="${esc(user.picture)}" alt="" onerror="this.style.display='none'">` : ''}
                    <span class="auth-name">${esc(user.name || user.email || 'Cuenta')}</span>
                    <a href="/logout" class="auth-btn auth-btn-out" title="Cerrar sesión">Salir</a>
                </div>`;
        } else {
            slot.innerHTML = `<a href="/login/google" class="auth-btn auth-btn-google">${GOOGLE_G}<span>Iniciar sesión</span></a>`;
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', render);
    } else {
        render();
    }
})();
