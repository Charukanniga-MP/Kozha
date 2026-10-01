/**
 * Signify Global Accessibility Manager & Live DOM Applier
 * Applies text sizing, theme modes, high contrast, animation controls,
 * audio settings, caption styling, and account-specific persistence.
 */
(function(window) {
  'use strict';

  const DEFAULT_ACCESSIBILITY_SETTINGS = {
    textSize: 'normal',       // 'small', 'normal', 'large', 'extra-large'
    theme: 'light',           // 'light', 'dark', 'high-contrast'
    highContrast: false,      // true / false
    reduceAnimations: false,  // true / false
    voiceFeedback: true,      // true / false
    speechSpeed: 50,          // 0 to 100 slider value (50 = Normal rate 1.0)
    speechVolume: 50,         // 0 to 100 slider value (50 = Normal vol 0.7)
    soundNotifications: true, // true / false
    muteAllSounds: false,     // true / false
    keyboardNavigation: false,// true / false
    largerButtons: false,     // true / false
    voiceCommands: true,      // true / false
    cameraGuidance: true,     // true / false
    showCaptions: true,       // true / false
    captionSize: 'normal',    // 'small', 'normal', 'large'
    captionBackground: 'light',// 'light', 'dark', 'transparent'
    showTooltips: true,       // true / false
    readingAssistance: false  // true / false
  };

  const SignifyAccessibility = {
    settings: { ...DEFAULT_ACCESSIBILITY_SETTINGS },

    getDefaults: function() {
      return { ...DEFAULT_ACCESSIBILITY_SETTINGS };
    },

    // Initialize accessibility for active user account
    init: async function() {
      let userData = null;
      if (window.SignifyUserStore) {
        userData = await window.SignifyUserStore.loadUserData();
      }

      if (userData && userData.accessibility) {
        this.settings = { ...DEFAULT_ACCESSIBILITY_SETTINGS, ...userData.accessibility };
      } else {
        this.settings = { ...DEFAULT_ACCESSIBILITY_SETTINGS };
      }

      this.applyToDOM(this.settings);

      // Listen for user switches
      window.addEventListener('signify:user_switched', async () => {
        await this.init();
      });

      window.addEventListener('signify:user_data_loaded', (e) => {
        if (e.detail && e.detail.accessibility) {
          this.settings = { ...DEFAULT_ACCESSIBILITY_SETTINGS, ...e.detail.accessibility };
          this.applyToDOM(this.settings);
        }
      });
    },

    // Apply settings to DOM elements, root html element, and active listeners
    applyToDOM: function(s) {
      const doc = document.documentElement;
      if (!doc) return;

      // 1. Text Size
      doc.classList.remove('text-size-small', 'text-size-normal', 'text-size-large', 'text-size-extra-large');
      doc.classList.add(`text-size-${s.textSize || 'normal'}`);

      // 2. Theme
      doc.classList.remove('theme-light', 'theme-dark', 'theme-high-contrast');
      doc.classList.add(`theme-${s.theme || 'light'}`);

      // 3. High Contrast
      if (s.highContrast || s.theme === 'high-contrast') {
        doc.classList.add('high-contrast');
      } else {
        doc.classList.remove('high-contrast');
      }

      // 4. Reduce Animations
      if (s.reduceAnimations) {
        doc.classList.add('reduce-animations');
      } else {
        doc.classList.remove('reduce-animations');
      }

      // 5. Larger Buttons
      if (s.largerButtons) {
        doc.classList.add('larger-buttons');
      } else {
        doc.classList.remove('larger-buttons');
      }

      // 6. Keyboard Navigation
      if (s.keyboardNavigation) {
        doc.classList.add('keyboard-nav-active');
      } else {
        doc.classList.remove('keyboard-nav-active');
      }

      // 7. Show Tooltips
      if (s.showTooltips) {
        doc.classList.add('show-tooltips-active');
      } else {
        doc.classList.remove('show-tooltips-active');
      }

      // 8. Reading Assistance
      if (s.readingAssistance) {
        doc.classList.add('reading-assistance');
      } else {
        doc.classList.remove('reading-assistance');
      }

      // Dispatch custom event for page components (e.g. preview card, audio engines)
      window.dispatchEvent(new CustomEvent('signify:accessibility_changed', { detail: s }));
    },

    // Voice feedback helper
    speak: function(text) {
      if (this.settings.muteAllSounds || !this.settings.voiceFeedback) return;
      if (!('speechSynthesis' in window)) return;

      try {
        window.speechSynthesis.cancel(); // Stop current speech
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Map 0-100 to speech rate (0.6 to 1.6)
        const speedVal = Number(this.settings.speechSpeed) || 50;
        utterance.rate = 0.6 + (speedVal / 100) * 1.0;

        // Map 0-100 to volume (0 to 1.0)
        const volVal = Number(this.settings.speechVolume) || 50;
        utterance.volume = Math.min(1.0, Math.max(0.1, volVal / 100));

        window.speechSynthesis.speak(utterance);
      } catch (e) {
        console.warn('Speech synthesis error:', e);
      }
    },

    // Sound chime helper
    playNotificationSound: function() {
      if (this.settings.muteAllSounds || !this.settings.soundNotifications) return;
      try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        const vol = (Number(this.settings.speechVolume) || 50) / 100;
        
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.15); // A5

        gain.gain.setValueAtTime(vol * 0.2, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.3);

        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.35);
      } catch (e) {}
    },

    // Save accessibility settings to user store
    saveSettings: async function(newSettings) {
      this.settings = { ...this.settings, ...newSettings };
      this.applyToDOM(this.settings);

      if (window.SignifyUserStore) {
        await window.SignifyUserStore.updateField('accessibility', this.settings);
      }
      this.playNotificationSound();
      return this.settings;
    },

    // Reset settings to defaults
    resetToDefaults: async function() {
      this.settings = { ...DEFAULT_ACCESSIBILITY_SETTINGS };
      this.applyToDOM(this.settings);

      if (window.SignifyUserStore) {
        await window.SignifyUserStore.updateField('accessibility', this.settings);
      }
      this.playNotificationSound();
      return this.settings;
    }
  };

  window.SignifyAccessibility = SignifyAccessibility;

  // Auto initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => SignifyAccessibility.init());
  } else {
    SignifyAccessibility.init();
  }

})(window);
