function showToast(message, icon = '✅') {
  let toast = document.getElementById('__toast');
  if (!toast) {
    toast = document.createElement('div');
    toast.id = '__toast';
    toast.className = 'toast';
    document.body.appendChild(toast);
  }

  toast.innerHTML = `<span class="toast-icon">${icon}</span><span>${message}</span>`;
  toast.classList.add('show');
  clearTimeout(toast._timeout);
  toast._timeout = setTimeout(() => toast.classList.remove('show'), 3000);
}

function initRevealAnimations() {
  const revealElements = document.querySelectorAll('.reveal');
  if (!revealElements.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  }, { threshold: 0.12 });

  revealElements.forEach((element) => observer.observe(element));
}

function initBackToTopButton() {
  const button = document.getElementById('back-to-top');
  if (!button) return;

  const toggleButton = () => {
    const offset = window.pageYOffset || document.documentElement.scrollTop;
    if (offset > 400) {
      button.classList.add('show');
    } else {
      button.classList.remove('show');
    }
  };

  button.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });

  window.addEventListener('scroll', toggleButton);
  toggleButton();
}

function ensureNotePreviewOverlay() {
  let overlay = document.getElementById('note-preview-overlay');
  if (overlay) return overlay;

  overlay = document.createElement('div');
  overlay.id = 'note-preview-overlay';
  overlay.className = 'note-preview-overlay';
  overlay.innerHTML = `
    <div class="note-preview-dialog" role="dialog" aria-modal="true" aria-labelledby="note-preview-title">
      <div class="note-preview-header">
        <h3 id="note-preview-title">Note preview</h3>
        <button class="note-preview-close" type="button" aria-label="Close preview">&times;</button>
      </div>
      <iframe class="note-preview-frame" title="Note preview"></iframe>
    </div>
  `;
  document.body.appendChild(overlay);
  return overlay;
}

function initNotePreview() {
  const overlay = ensureNotePreviewOverlay();
  const title = overlay.querySelector('#note-preview-title');
  const frame = overlay.querySelector('.note-preview-frame');
  const closeButton = overlay.querySelector('.note-preview-close');

  const closePreview = () => {
    overlay.classList.remove('is-open');
    frame.src = 'about:blank';
    document.body.style.overflow = '';
  };

  document.addEventListener('click', (event) => {
    const button = event.target.closest('.note-preview-trigger');
    if (!button) return;

    event.preventDefault();
    title.textContent = button.dataset.previewTitle || 'Note preview';
    frame.src = button.dataset.previewUrl;
    overlay.classList.add('is-open');
    document.body.style.overflow = 'hidden';
  });

  closeButton.addEventListener('click', closePreview);
  overlay.addEventListener('click', (event) => {
    if (event.target === overlay) closePreview();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && overlay.classList.contains('is-open')) {
      closePreview();
    }
  });
}

function initNoteFeedbackToggles() {
  document.addEventListener('click', (event) => {
    const toggle = event.target.closest('.note-feedback-toggle');
    if (!toggle) return;

    event.preventDefault();
    const form = document.getElementById(toggle.dataset.feedbackTarget);
    if (!form) return;

    form.hidden = !form.hidden;
    if (!form.hidden) {
      form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  document.addEventListener('submit', (event) => {
    const form = event.target.closest('.note-feedback-form');
    if (form) {
      form.hidden = true;
    }
  });
}

function initNoteDeleteConfirmations() {
  document.addEventListener('submit', (event) => {
    const form = event.target.closest('.note-delete-form');
    if (!form) return;

    if (!window.confirm('Delete this uploaded note? This action cannot be undone.')) {
      event.preventDefault();
    }
  });
}

function initPlaceholderActions() {}

/* ========== DOUBT OVERLAY INITIALIZATION ========== */
function initDoubtOverlays() {
  // User Dashboard Doubt Overlay
  const userDoubtBtn = document.getElementById('open-user-doubt-tab');
  const userDoubtOverlay = document.getElementById('user-doubt-overlay');
  const closeUserDoubtBtn = document.getElementById('close-user-doubt-tab');
  const userDoubtForm = document.getElementById('user-doubt-form');

  if (userDoubtBtn && userDoubtOverlay) {
    userDoubtBtn.addEventListener('click', (e) => {
      e.preventDefault();
      userDoubtOverlay.style.display = 'block';
      document.body.style.overflow = 'hidden';
    });

    closeUserDoubtBtn.addEventListener('click', (e) => {
      e.preventDefault();
      userDoubtOverlay.style.display = 'none';
      document.body.style.overflow = '';
      if (userDoubtForm) userDoubtForm.reset();
    });

    userDoubtOverlay.addEventListener('click', (e) => {
      if (e.target === userDoubtOverlay) {
        userDoubtOverlay.style.display = 'none';
        document.body.style.overflow = '';
        if (userDoubtForm) userDoubtForm.reset();
      }
    });

    if (userDoubtForm) {
      userDoubtForm.addEventListener('submit', (e) => {
        const question = userDoubtForm.querySelector('[name="question"]').value.trim();
        const subject = userDoubtForm.querySelector('[name="subject"]').value;
        
        if (!question || !subject) {
          e.preventDefault();
          showToast('Please fill all fields', '⚠️');
        }
      });
    }
  }

  // Instructor Dashboard Doubt Overlay
  const instructorDoubtBtn = document.getElementById('open-instructor-doubt-tab');
  const instructorDoubtOverlay = document.getElementById('instructor-doubt-overlay');
  const closeInstructorDoubtBtn = document.getElementById('close-instructor-doubt-tab');
  const instructorDoubtForm = document.getElementById('instructor-doubt-form');

  if (instructorDoubtBtn && instructorDoubtOverlay) {
    instructorDoubtBtn.addEventListener('click', (e) => {
      e.preventDefault();
      instructorDoubtOverlay.style.display = 'block';
      document.body.style.overflow = 'hidden';
    });

    closeInstructorDoubtBtn.addEventListener('click', (e) => {
      e.preventDefault();
      instructorDoubtOverlay.style.display = 'none';
      document.body.style.overflow = '';
      if (instructorDoubtForm) instructorDoubtForm.reset();
    });

    instructorDoubtOverlay.addEventListener('click', (e) => {
      if (e.target === instructorDoubtOverlay) {
        instructorDoubtOverlay.style.display = 'none';
        document.body.style.overflow = '';
        if (instructorDoubtForm) instructorDoubtForm.reset();
      }
    });

    if (instructorDoubtForm) {
      instructorDoubtForm.addEventListener('submit', (e) => {
        const question = instructorDoubtForm.querySelector('[name="question"]').value.trim();
        const subject = instructorDoubtForm.querySelector('[name="subject"]').value;
        
        if (!question || !subject) {
          e.preventDefault();
          showToast('Please fill all fields', '⚠️');
        }
      });
    }
  }

  // Close overlays on Escape key
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
      if (userDoubtOverlay && userDoubtOverlay.style.display === 'block') {
        userDoubtOverlay.style.display = 'none';
        document.body.style.overflow = '';
      }
      if (instructorDoubtOverlay && instructorDoubtOverlay.style.display === 'block') {
        instructorDoubtOverlay.style.display = 'none';
        document.body.style.overflow = '';
      }
    }
  });
}

function initGlobalSiteScripts() {
  initRevealAnimations();
  initBackToTopButton();
  initNotePreview();
  initNoteFeedbackToggles();
  initNoteDeleteConfirmations();
  initPlaceholderActions();
  initDoubtOverlays();
}

document.addEventListener('DOMContentLoaded', initGlobalSiteScripts);
