const authTabs = {
  login: {
    buttonId: 'btn-login',
    panelId: 'login-form',
  },
  signup: {
    buttonId: 'btn-signup',
    panelId: 'signup-form',
  },
};

function switchTab(tab) {
  if (!authTabs[tab]) {
    tab = 'login';
  }

  Object.values(authTabs).forEach(({ buttonId, panelId }) => {
    document.getElementById(buttonId)?.classList.remove('active');
    document.getElementById(panelId)?.classList.remove('active');
  });

  document.getElementById(authTabs[tab].buttonId)?.classList.add('active');
  document.getElementById(authTabs[tab].panelId)?.classList.add('active');

  const currentUrl = new URL(window.location.href);
  currentUrl.searchParams.set('tab', tab);
  window.history.replaceState({}, '', currentUrl);
}

function bindTabButtons() {
  Object.keys(authTabs).forEach((tab) => {
    const button = document.getElementById(authTabs[tab].buttonId);
    if (!button) return;
    button.addEventListener('click', (event) => {
      event.preventDefault();
      switchTab(tab);
      const panel = document.getElementById(authTabs[tab].panelId);
      panel?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  });
}

function bindExternalAuthLinks() {
  const authLinks = Array.from(document.querySelectorAll('a')).filter((link) => {
    return link.href.includes('?tab=login') || link.href.includes('?tab=signup');
  });

  authLinks.forEach((link) => {
    link.addEventListener('click', (event) => {
      const url = new URL(link.href);
      const requestedTab = url.searchParams.get('tab');
      if (requestedTab && authTabs[requestedTab]) {
        event.preventDefault();
        switchTab(requestedTab);
        document.getElementById(authTabs[requestedTab].panelId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

function initFormValidation() {
  const forms = document.querySelectorAll('form');
  forms.forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
        form.reportValidity();
        return;
      }

      const submitButton = form.querySelector('button[type="submit"]');
      if (submitButton) {
        submitButton.disabled = true;
        submitButton.textContent = 'Please wait...';
      }
    });
  });
}

function initAuthPage() {
  bindTabButtons();
  bindExternalAuthLinks();
  initFormValidation();

  const urlParams = new URLSearchParams(window.location.search);
  const activeTab = urlParams.get('tab') || document.body.dataset.activeTab || 'login';
  switchTab(activeTab);
}

document.addEventListener('DOMContentLoaded', initAuthPage);
