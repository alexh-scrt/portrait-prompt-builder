/**
 * app.js — Client-side JavaScript for the Portrait Prompt Builder.
 *
 * Responsibilities:
 *   1. Multi-step form navigation (show/hide steps, update progress indicator,
 *      validate required fields before advancing)
 *   2. Character counter updates for textarea and text inputs
 *   3. Visual selection state for card-style radio inputs (decade, mood, preset)
 *   4. Copy-to-clipboard functionality with toast feedback
 *   5. Download-as-.txt functionality using a synthetic anchor + Blob
 *   6. Generate button loading state
 *
 * This file is intentionally written in plain ES2020 with no dependencies
 * so it works in all modern browsers without a build step.
 *
 * @module app
 */

'use strict';

/* ============================================================
   CONSTANTS
   ============================================================ */

/** Total number of form steps. */
const TOTAL_STEPS = 4;

/** Duration (ms) before the copy toast auto-hides. */
const TOAST_DURATION_MS = 3000;

/** Duration (ms) before the copy button resets its label. */
const COPY_RESET_MS = 2500;

/* ============================================================
   UTILITY HELPERS
   ============================================================ */

/**
 * Returns the first element matching `selector` within `scope` (default: document).
 *
 * @param {string} selector - CSS selector string.
 * @param {ParentNode} [scope=document] - Root to search within.
 * @returns {Element|null}
 */
function qs(selector, scope = document) {
  return scope.querySelector(selector);
}

/**
 * Returns all elements matching `selector` within `scope` as a real Array.
 *
 * @param {string} selector - CSS selector string.
 * @param {ParentNode} [scope=document] - Root to search within.
 * @returns {Element[]}
 */
function qsa(selector, scope = document) {
  return Array.from(scope.querySelectorAll(selector));
}

/**
 * Adds an event listener and returns a cleanup function.
 *
 * @param {EventTarget} target
 * @param {string} type
 * @param {EventListenerOrEventListenerObject} handler
 * @param {AddEventListenerOptions} [options]
 * @returns {() => void} Cleanup function that removes the listener.
 */
function on(target, type, handler, options) {
  target.addEventListener(type, handler, options);
  return () => target.removeEventListener(type, handler, options);
}

/**
 * Clamps `value` between `min` and `max`.
 *
 * @param {number} value
 * @param {number} min
 * @param {number} max
 * @returns {number}
 */
function clamp(value, min, max) {
  return Math.min(Math.max(value, min), max);
}

/* ============================================================
   1. MULTI-STEP FORM NAVIGATION
   ============================================================ */

/**
 * Manages the multi-step form: shows/hides fieldsets, updates the step
 * progress indicator, and validates required fields before advancing.
 */
function initMultiStepForm() {
  const form = qs('#portrait-form');
  if (!form) return; // Not on a page with the form.

  /** @type {HTMLFieldSetElement[]} */
  const steps = qsa('.form-step', form);
  const stepDots = qsa('.step-dot', form);
  const progressLines = qsa('.step-progress__line', form);

  if (steps.length === 0) return;

  /** Currently visible step index (0-based). */
  let currentStep = 0;

  /**
   * Shows the step at `index` and hides all others.
   * Also updates the progress indicator dots.
   *
   * @param {number} index - 0-based step index to show.
   */
  function showStep(index) {
    const safeIndex = clamp(index, 0, steps.length - 1);

    steps.forEach((step, i) => {
      if (i === safeIndex) {
        step.removeAttribute('hidden');
        step.classList.add('form-step--active');
        step.setAttribute('aria-hidden', 'false');
      } else {
        step.setAttribute('hidden', '');
        step.classList.remove('form-step--active');
        step.setAttribute('aria-hidden', 'true');
      }
    });

    // Update progress dots
    stepDots.forEach((dot, i) => {
      dot.classList.remove('step-dot--active', 'step-dot--completed');
      dot.removeAttribute('data-active');
      dot.removeAttribute('aria-current');

      if (i === safeIndex) {
        dot.classList.add('step-dot--active');
        dot.setAttribute('data-active', '');
        dot.setAttribute('aria-current', 'step');
      } else if (i < safeIndex) {
        dot.classList.add('step-dot--completed');
      }
    });

    // Update connecting lines
    progressLines.forEach((line, i) => {
      if (i < safeIndex) {
        line.classList.add('step-progress__line--active');
      } else {
        line.classList.remove('step-progress__line--active');
      }
    });

    currentStep = safeIndex;

    // Scroll to top of form on step change
    form.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }

  /**
   * Validates all required inputs within the given step fieldset.
   * Focuses the first invalid field if any are found.
   *
   * @param {HTMLFieldSetElement} stepEl - The fieldset to validate.
   * @returns {boolean} True if all required fields in this step are filled.
   */
  function validateStep(stepEl) {
    const requiredInputs = qsa(
      'input[required], textarea[required], select[required]',
      stepEl
    );

    for (const input of requiredInputs) {
      if (input.type === 'radio') {
        // For radio groups, check that at least one in the group is checked.
        const groupName = input.name;
        const anyChecked = qs(
          `input[type="radio"][name="${groupName}"]:checked`,
          stepEl
        );
        if (!anyChecked) {
          // Find the first visible radio label to focus
          const firstLabel = qs(
            `label:has(input[name="${groupName}"])`,
            stepEl
          );
          if (firstLabel) firstLabel.focus();
          showValidationHint(stepEl, groupName);
          return false;
        }
      } else {
        if (!input.value.trim()) {
          input.focus();
          input.classList.add('form-input--error');
          on(input, 'input', () => input.classList.remove('form-input--error'), { once: true });
          return false;
        }
      }
    }
    return true;
  }

  /**
   * Briefly highlights a validation message near the radio group.
   *
   * @param {HTMLFieldSetElement} stepEl
   * @param {string} groupName
   */
  function showValidationHint(stepEl, groupName) {
    const existing = qs(`.form-error[data-group="${groupName}"]`, stepEl);
    if (existing) return; // Already showing.

    const group = qs(`[role="group"][aria-label]`, stepEl) ||
                  qs(`input[name="${groupName}"]`, stepEl)?.closest('.form-group');
    if (!group) return;

    const hint = document.createElement('p');
    hint.className = 'form-error';
    hint.setAttribute('role', 'alert');
    hint.setAttribute('data-group', groupName);
    hint.textContent = 'Please make a selection to continue.';
    group.appendChild(hint);

    setTimeout(() => hint.remove(), 3500);
  }

  // ── Wire up Next buttons ──
  qsa('.btn--next', form).forEach(btn => {
    on(btn, 'click', () => {
      const nextIndex = parseInt(btn.dataset.next, 10) - 1;
      const currentStepEl = steps[currentStep];
      if (!validateStep(currentStepEl)) return;
      showStep(nextIndex);
    });
  });

  // ── Wire up Back/Prev buttons ──
  qsa('.btn--prev', form).forEach(btn => {
    on(btn, 'click', () => {
      const prevIndex = parseInt(btn.dataset.prev, 10) - 1;
      showStep(prevIndex);
    });
  });

  // ── Wire up step dot navigation (allow clicking completed steps) ──
  stepDots.forEach((dot, i) => {
    on(dot, 'click', () => {
      // Only allow navigating to completed or current steps, not future ones
      if (i <= currentStep) {
        showStep(i);
      } else {
        // Try to advance through intermediate steps with validation
        let canAdvance = true;
        for (let s = currentStep; s < i; s++) {
          if (!validateStep(steps[s])) {
            canAdvance = false;
            break;
          }
        }
        if (canAdvance) showStep(i);
      }
    });
  });

  // ── If there are validation errors from the server, find which step
  //    has invalid fields and jump to it. ──
  const errorAlert = qs('.alert--error');
  if (errorAlert) {
    // Find the first step that has a required but unfilled field
    for (let i = 0; i < steps.length; i++) {
      const hasEmpty = qsa(
        'input[required], textarea[required]',
        steps[i]
      ).some(inp => {
        if (inp.type === 'radio') {
          return !qs(
            `input[type="radio"][name="${inp.name}"]:checked`,
            steps[i]
          );
        }
        return !inp.value.trim();
      });
      if (hasEmpty) {
        showStep(i);
        break;
      }
    }
  }

  // ── Initial render: ensure only step 0 is visible ──
  showStep(0);
}

/* ============================================================
   2. CHARACTER COUNTERS
   ============================================================ */

/**
 * Initialises character counter elements linked to their textarea/input
 * targets via `data-target` attributes.
 *
 * Expected HTML structure:
 *   <textarea id="setting" maxlength="200">…</textarea>
 *   <span class="char-count" data-max="200" data-target="setting"></span>
 */
function initCharCounters() {
  qsa('.char-count').forEach(counter => {
    const targetId = counter.dataset.target;
    const max = parseInt(counter.dataset.max, 10);
    if (!targetId || isNaN(max)) return;

    const input = qs(`#${targetId}`);
    if (!input) return;

    /**
     * Updates the counter text and warning classes.
     */
    function updateCount() {
      const remaining = max - input.value.length;
      counter.textContent = `${remaining} / ${max}`;

      counter.classList.remove('char-count--warning', 'char-count--danger');
      if (remaining <= 0) {
        counter.classList.add('char-count--danger');
      } else if (remaining <= Math.ceil(max * 0.15)) {
        counter.classList.add('char-count--warning');
      }
    }

    // Initial render
    updateCount();

    on(input, 'input', updateCount);
    on(input, 'paste', () => setTimeout(updateCount, 0));
  });
}

/* ============================================================
   3. CARD RADIO VISUAL SELECTION STATE
   ============================================================ */

/**
 * Adds/removes the `--selected` modifier class on card-style radio
 * labels when their associated hidden radio input changes.
 *
 * Works for: `.decade-card`, `.mood-card`, `.radio-card`, `.preset-card`.
 */
function initCardRadios() {
  const cardSelectors = [
    { card: '.decade-card', selected: 'decade-card--selected' },
    { card: '.mood-card',   selected: 'mood-card--selected' },
    { card: '.radio-card',  selected: 'radio-card--selected' },
    { card: '.preset-card', selected: 'preset-card--selected' },
  ];

  cardSelectors.forEach(({ card, selected }) => {
    const labels = qsa(card);
    if (labels.length === 0) return;

    labels.forEach(label => {
      const radio = qs('input[type="radio"]', label);
      if (!radio) return;

      // Update sibling cards when this one is selected
      on(radio, 'change', () => {
        // Find all sibling labels sharing the same radio name
        const groupName = radio.name;
        qsa(`${card} input[type="radio"][name="${groupName}"]`).forEach(r => {
          const parentLabel = r.closest(card);
          if (parentLabel) {
            parentLabel.classList.toggle(selected, r.checked);
          }
        });
      });

      // Keyboard: allow Space/Enter to select when label is focused
      on(label, 'keydown', (e) => {
        if (e.key === ' ' || e.key === 'Enter') {
          e.preventDefault();
          radio.checked = true;
          radio.dispatchEvent(new Event('change', { bubbles: true }));
        }
      });

      // Make labels focusable for keyboard navigation
      if (!label.hasAttribute('tabindex')) {
        label.setAttribute('tabindex', '0');
      }
    });

    // Sync initial checked state (e.g. when re-rendering with form_data)
    labels.forEach(label => {
      const radio = qs('input[type="radio"]', label);
      if (radio && radio.checked) {
        label.classList.add(selected);
      }
    });
  });
}

/* ============================================================
   4. COPY TO CLIPBOARD
   ============================================================ */

/**
 * Wires up the copy-to-clipboard button on the result page.
 *
 * Tries the modern `navigator.clipboard.writeText` API first, with a
 * `textarea` `execCommand('copy')` fallback for older browsers.
 */
function initCopyButton() {
  const copyBtn = qs('#copy-btn');
  if (!copyBtn) return;

  const copyBtnText = qs('#copy-btn-text');
  const toast = qs('#copy-toast');
  const toastMessage = qs('#toast-message');

  /** @type {number|null} Timer ID for resetting the button label. */
  let resetTimer = null;
  /** @type {number|null} Timer ID for hiding the toast. */
  let toastTimer = null;

  /**
   * Retrieves the prompt text to copy.
   * Prefers the `window.PORTRAIT_PROMPT` variable injected by the template,
   * then falls back to the hidden textarea, then the visible prompt div.
   *
   * @returns {string}
   */
  function getPromptText() {
    if (typeof window.PORTRAIT_PROMPT === 'string' && window.PORTRAIT_PROMPT) {
      return window.PORTRAIT_PROMPT;
    }
    const textarea = qs('#prompt-textarea');
    if (textarea) return textarea.value;
    const div = qs('#prompt-text');
    if (div) return div.textContent || '';
    return '';
  }

  /**
   * Shows the success/error toast with the given message.
   *
   * @param {string} message
   * @param {boolean} [isError=false]
   */
  function showToast(message, isError = false) {
    if (!toast) return;

    if (toastMessage) toastMessage.textContent = message;

    const toastIcon = qs('.toast__icon', toast);
    if (toastIcon) toastIcon.textContent = isError ? '❌' : '✅';

    toast.removeAttribute('hidden');
    toast.style.display = '';

    // Clear any previous auto-hide timer
    if (toastTimer !== null) clearTimeout(toastTimer);
    toastTimer = setTimeout(() => {
      toast.setAttribute('hidden', '');
      toastTimer = null;
    }, TOAST_DURATION_MS);
  }

  /**
   * Sets the copy button into its "copied" success state.
   */
  function setCopiedState() {
    copyBtn.classList.add('copied');
    if (copyBtnText) copyBtnText.textContent = '✅ Copied!';
    copyBtn.setAttribute('aria-label', 'Prompt copied to clipboard');

    if (resetTimer !== null) clearTimeout(resetTimer);
    resetTimer = setTimeout(() => {
      copyBtn.classList.remove('copied');
      if (copyBtnText) copyBtnText.textContent = 'Copy to Clipboard';
      copyBtn.setAttribute('aria-label', 'Copy prompt to clipboard');
      resetTimer = null;
    }, COPY_RESET_MS);
  }

  /**
   * Performs the clipboard copy using `navigator.clipboard` or falls back
   * to `document.execCommand`.
   *
   * @param {string} text - Text to copy.
   * @returns {Promise<void>}
   */
  async function copyToClipboard(text) {
    if (!text) {
      showToast('Nothing to copy.', true);
      return;
    }

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
      } else {
        // Fallback: use a temporary textarea + execCommand
        const tmp = document.createElement('textarea');
        tmp.value = text;
        tmp.style.position = 'fixed';
        tmp.style.left = '-9999px';
        tmp.style.top = '-9999px';
        tmp.setAttribute('aria-hidden', 'true');
        document.body.appendChild(tmp);
        tmp.focus();
        tmp.select();
        const success = document.execCommand('copy');
        document.body.removeChild(tmp);
        if (!success) throw new Error('execCommand copy failed');
      }

      setCopiedState();
      showToast('Prompt copied to clipboard!');
    } catch (err) {
      console.error('[PortraitPromptBuilder] Clipboard copy failed:', err);
      showToast('Copy failed — please select and copy manually.', true);
    }
  }

  on(copyBtn, 'click', () => {
    copyToClipboard(getPromptText());
  });
}

/* ============================================================
   5. DOWNLOAD AS .TXT
   ============================================================ */

/**
 * Wires up the download-as-.txt button on the result page.
 *
 * Creates a `Blob` from the prompt text, generates an object URL,
 * triggers a synthetic click on a temporary anchor, then cleans up.
 */
function initDownloadButton() {
  const downloadBtn = qs('#download-btn');
  if (!downloadBtn) return;

  /**
   * Retrieves the prompt text for download.
   * Uses the same priority as the copy function: window var → textarea → div.
   *
   * @returns {string}
   */
  function getPromptText() {
    if (typeof window.PORTRAIT_PROMPT === 'string' && window.PORTRAIT_PROMPT) {
      return window.PORTRAIT_PROMPT;
    }
    const textarea = qs('#prompt-textarea');
    if (textarea) return textarea.value;
    const div = qs('#prompt-text');
    if (div) return div.textContent || '';
    return '';
  }

  /**
   * Determines the download filename.
   * Prefers `window.PORTRAIT_FILENAME`, then the button's `data-filename`,
   * then falls back to a generic name.
   *
   * @returns {string}
   */
  function getFilename() {
    if (typeof window.PORTRAIT_FILENAME === 'string' && window.PORTRAIT_FILENAME) {
      return window.PORTRAIT_FILENAME;
    }
    if (downloadBtn.dataset.filename) {
      return downloadBtn.dataset.filename;
    }
    return 'portrait-prompt.txt';
  }

  on(downloadBtn, 'click', () => {
    const text = getPromptText();
    if (!text) {
      console.warn('[PortraitPromptBuilder] No prompt text found for download.');
      return;
    }

    try {
      const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);

      const anchor = document.createElement('a');
      anchor.href = url;
      anchor.download = getFilename();
      anchor.style.display = 'none';
      anchor.setAttribute('aria-hidden', 'true');

      document.body.appendChild(anchor);
      anchor.click();

      // Clean up after a short delay to allow the browser to initiate download
      setTimeout(() => {
        document.body.removeChild(anchor);
        URL.revokeObjectURL(url);
      }, 200);

      // Brief visual feedback on the button
      const originalText = downloadBtn.querySelector('.btn__text');
      if (originalText) {
        const orig = originalText.textContent;
        originalText.textContent = '✅ Downloaded!';
        setTimeout(() => {
          originalText.textContent = orig;
        }, 2000);
      }
    } catch (err) {
      console.error('[PortraitPromptBuilder] Download failed:', err);
    }
  });
}

/* ============================================================
   6. GENERATE BUTTON LOADING STATE
   ============================================================ */

/**
 * Adds a loading spinner and disables the generate button when the form
 * is submitted to prevent double-submissions and provide user feedback.
 */
function initGenerateButton() {
  const form = qs('#portrait-form');
  const generateBtn = qs('#generate-btn');
  if (!form || !generateBtn) return;

  on(form, 'submit', () => {
    const btnText = qs('.btn__text', generateBtn);
    const btnSpinner = qs('.btn__spinner', generateBtn);

    generateBtn.disabled = true;
    generateBtn.setAttribute('aria-busy', 'true');

    if (btnText) btnText.textContent = 'Generating…';
    if (btnSpinner) btnSpinner.removeAttribute('hidden');

    // Safety: re-enable after 15 seconds in case of network issues
    setTimeout(() => {
      if (generateBtn.disabled) {
        generateBtn.disabled = false;
        generateBtn.removeAttribute('aria-busy');
        if (btnText) btnText.textContent = '✨ Generate My Prompt';
        if (btnSpinner) btnSpinner.setAttribute('hidden', '');
      }
    }, 15000);
  });
}

/* ============================================================
   7. KEYBOARD NAVIGATION ENHANCEMENTS
   ============================================================ */

/**
 * Enhances keyboard navigation for card grids (decade, mood, preset).
 * Allows arrow-key navigation within each radio group.
 */
function initKeyboardNavigation() {
  const radioGroups = qsa('[role="group"]');

  radioGroups.forEach(group => {
    const cards = qsa('.decade-card, .mood-card, .preset-card, .radio-card', group);
    if (cards.length === 0) return;

    cards.forEach((card, i) => {
      on(card, 'keydown', (e) => {
        let targetIndex = -1;

        if (e.key === 'ArrowRight' || e.key === 'ArrowDown') {
          e.preventDefault();
          targetIndex = (i + 1) % cards.length;
        } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
          e.preventDefault();
          targetIndex = (i - 1 + cards.length) % cards.length;
        } else if (e.key === 'Home') {
          e.preventDefault();
          targetIndex = 0;
        } else if (e.key === 'End') {
          e.preventDefault();
          targetIndex = cards.length - 1;
        }

        if (targetIndex >= 0) {
          cards[targetIndex].focus();
        }
      });
    });
  });
}

/* ============================================================
   8. PROMPT TEXT SELECTION HELPER
   ============================================================ */

/**
 * Allows clicking the prompt text div to select all text within it,
 * making it easy to manually copy even without the clipboard API.
 */
function initPromptTextSelection() {
  const promptText = qs('#prompt-text');
  if (!promptText) return;

  on(promptText, 'click', () => {
    const selection = window.getSelection();
    if (!selection) return;

    const range = document.createRange();
    range.selectNodeContents(promptText);
    selection.removeAllRanges();
    selection.addRange(range);
  });

  // Keyboard: select all on Enter or Space
  on(promptText, 'keydown', (e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      const selection = window.getSelection();
      if (!selection) return;
      const range = document.createRange();
      range.selectNodeContents(promptText);
      selection.removeAllRanges();
      selection.addRange(range);
    }
  });
}

/* ============================================================
   MAIN INITIALISATION
   ============================================================ */

/**
 * Main entry point. Called when the DOM is ready.
 * Initialises all modules conditionally based on which elements exist
 * in the current page's DOM.
 */
function init() {
  // Form page features
  initMultiStepForm();
  initCharCounters();
  initCardRadios();
  initGenerateButton();
  initKeyboardNavigation();

  // Result page features
  initCopyButton();
  initDownloadButton();
  initPromptTextSelection();
}

// Kick off when DOM is parsed
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', init);
} else {
  // DOM already ready (script loaded with defer or at end of body)
  init();
}
