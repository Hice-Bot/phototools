(function () {
  const key = window.CLERK_PUBLISHABLE_KEY || 'pk_test_dummy_phototools';

  async function loadClerk() {
    if (!key || key.includes('dummy')) return null;
    if (!window.Clerk) {
      await new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.async = true;
        script.crossOrigin = 'anonymous';
        script.src = 'https://cdn.jsdelivr.net/npm/@clerk/clerk-js@latest/dist/clerk.browser.js';
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
      });
    }
    await window.Clerk.load({ publishableKey: key });
    return window.Clerk;
  }

  async function renderAuth() {
    const slot = document.getElementById('authSlot');
    if (!slot) return;
    const clerk = await loadClerk().catch(() => null);
    slot.innerHTML = '';
    if (!clerk) {
      const badge = document.createElement('span');
      badge.className = 'btn btn-secondary btn-small';
      badge.textContent = 'Dummy auth';
      slot.appendChild(badge);
      return;
    }
    if (clerk.user) {
      clerk.mountUserButton(slot);
    } else {
      const signIn = document.createElement('button');
      signIn.className = 'btn btn-secondary btn-small';
      signIn.type = 'button';
      signIn.textContent = 'Sign in';
      signIn.addEventListener('click', () => clerk.openSignIn());
      slot.appendChild(signIn);
    }
  }

  window.PhotoToolsAuth = {
    async getToken() {
      const clerk = await loadClerk().catch(() => null);
      return clerk?.session ? clerk.session.getToken() : null;
    },
    async openSignIn() {
      const clerk = await loadClerk().catch(() => null);
      if (clerk) clerk.openSignIn();
      else alert('Clerk is in dummy mode. Set CLERK_PUBLISHABLE_KEY to enable real sign-in.');
    },
    async mountPricingTable(el) {
      const clerk = await loadClerk().catch(() => null);
      if (clerk?.mountPricingTable) {
        clerk.mountPricingTable(el);
        return true;
      }
      return false;
    },
  };

  document.addEventListener('DOMContentLoaded', renderAuth);
})();
