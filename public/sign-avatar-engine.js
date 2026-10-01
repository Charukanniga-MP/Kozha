/**
 * Signify Sign Language Avatar Engine & Animation Controller
 * -------------------------------------------------------------
 * Provides dynamic speech-to-sign translation, ISL/BSL/ASL dataset management,
 * state machine controls, playback queues, and CWASA 3D WebGL avatar integration.
 */
(function(window) {
  'use strict';

  // Available Sign Languages & Datasets
  const SIGN_LANG_DB = {
    isl: {
      code: 'isl',
      name: 'Indian Sign Language (ISL)',
      flag: '🇮🇳',
      sigml: ['/data/Indian_SL.sigml', '/data/ISL_authored.sigml'],
      csv: null,
      alphabet: null
    },
    bsl: {
      code: 'bsl',
      name: 'British Sign Language (BSL)',
      flag: '🇬🇧',
      sigml: ['/data/hamnosys_bsl_version1.sigml', '/data/BSL_bobsl_authored.sigml'],
      csv: '/data/hamnosys_bsl.csv',
      alphabet: '/data/bsl_alphabet_sigml.sigml'
    },
    asl: {
      code: 'asl',
      name: 'American Sign Language (ASL)',
      flag: '🇺🇸',
      sigml: ['/data/American_SL_ASL.sigml', '/data/ASL_wlasl_msasl_authored.sigml'],
      csv: '/data/asl_concepts.csv',
      alphabet: '/data/asl_alphabet_sigml.sigml'
    }
  };

  const STOPWORDS = new Set([
    'a', 'an', 'the', 'and', 'or', 'but', 'if', 'then', 'than', 'of', 'to', 'in', 'on', 'at', 
    'for', 'from', 'with', 'as', 'by', 'is', 'are', 'am', 'be', 'been', 'was', 'were', 'do', 
    'does', 'did', 'that', 'this', 'those', 'these', 'it', 'my', 'your', 'our'
  ]);

  const FALLBACK_ALPHABET = '/data/bsl_alphabet_sigml.sigml';

  // Levenshtein distance for fuzzy sign matching
  function levenshtein(a, b) {
    const m = a.length, n = b.length;
    if (!m) return n; if (!n) return m;
    const dp = new Array(n + 1);
    for (let j = 0; j <= n; j++) dp[j] = j;
    for (let i = 1; i <= m; i++) {
      let prev = dp[0]; dp[0] = i;
      for (let j = 1; j <= n; j++) {
        const temp = dp[j];
        dp[j] = Math.min(dp[j] + 1, dp[j - 1] + 1, prev + (a[i - 1] === b[j - 1] ? 0 : 1));
        prev = temp;
      }
    }
    return dp[n];
  }

  function similarity(a, b) {
    if (!a || !b) return 0;
    return 1 - levenshtein(a, b) / Math.max(a.length, b.length);
  }

  function glossBase(gloss) {
    return String(gloss)
      .toLowerCase()
      .replace(/\(.*?\)/g, '')
      .replace(/#\d+$/g, '')
      .replace(/\d+[a-z]?\^?$/g, '')
      .replace(/^_num-/g, '')
      .replace(/_\(.*?\)/g, '')
      .replace(/[^a-z0-9À-ɏͰ-ϿЀ-ӿĀ-ſ]+/g, ' ')
      .trim();
  }

  class SignLanguageManager {
    constructor() {
      this.currentLang = 'isl';
      this.glossToSign = new Map();
      this.letterToSign = new Map();
      this.baseToGloss = new Map();
      this.conceptToGloss = new Map();
      this.isLoading = false;
      this.switchCounter = 0;
      this.listeners = [];
    }

    addListener(cb) {
      if (typeof cb === 'function') this.listeners.push(cb);
    }

    notifyListeners(event, data) {
      this.listeners.forEach(cb => {
        try { cb(event, data); } catch (e) { console.error(e); }
      });
    }

    async setLanguage(langCode) {
      if (!SIGN_LANG_DB[langCode]) {
        console.warn(`[SignLanguageManager] Unsupported language: ${langCode}, defaulting to ISL`);
        langCode = 'isl';
      }

      this.currentLang = langCode;
      this.isLoading = true;
      this.notifyListeners('loading_start', { lang: langCode });

      const myId = ++this.switchCounter;
      this.glossToSign.clear();
      this.letterToSign.clear();
      this.baseToGloss.clear();
      this.conceptToGloss.clear();

      const db = SIGN_LANG_DB[langCode];

      try {
        for (let i = 0; i < db.sigml.length; i++) {
          if (this.switchCounter !== myId) return;
          await this.loadSigmlUrl(db.sigml[i]);
        }
        if (this.switchCounter !== myId) return;
        if (db.csv) await this.loadConceptCsvUrl(db.csv);
        if (this.switchCounter !== myId) return;
        if (db.alphabet) await this.loadAlphabetSigmlUrl(db.alphabet);

        if (this.switchCounter !== myId) return;
        this.extractEmbeddedAlphabet();

        if (this.letterToSign.size < 26) {
          await this.loadAlphabetSigmlUrl(FALLBACK_ALPHABET);
        }
      } catch (err) {
        console.error('[SignLanguageManager] Error loading sign language dataset:', err);
      } finally {
        if (this.switchCounter === myId) {
          this.isLoading = false;
          this.notifyListeners('loaded', {
            lang: langCode,
            signCount: this.glossToSign.size,
            alphabetCount: this.letterToSign.size
          });
        }
      }
    }

    rebuildBaseIndex() {
      this.baseToGloss.clear();
      for (const g of this.glossToSign.keys()) {
        const b = glossBase(g);
        if (!this.baseToGloss.has(b)) this.baseToGloss.set(b, g);
      }
    }

    async loadSigmlUrl(url) {
      try {
        const res = await fetch(url, { cache: 'no-cache' });
        if (!res.ok) return;
        const xmlText = await res.text();
        const doc = new DOMParser().parseFromString(xmlText, 'application/xml');
        const signs = Array.from(doc.querySelectorAll('hns_sign'));
        for (const s of signs) {
          const gloss = (s.getAttribute('gloss') || '').trim().toLowerCase();
          if (!gloss) continue;
          this.glossToSign.set(gloss, s.outerHTML);
        }
        this.rebuildBaseIndex();
      } catch (e) {
        console.warn(`[SignLanguageManager] Failed to load SiGML ${url}:`, e);
      }
    }

    async loadAlphabetSigmlUrl(url) {
      try {
        const res = await fetch(url, { cache: 'no-cache' });
        if (!res.ok) return;
        const xmlText = await res.text();
        const doc = new DOMParser().parseFromString(xmlText, 'application/xml');
        const signs = Array.from(doc.querySelectorAll('hns_sign'));
        for (const s of signs) {
          const gloss = (s.getAttribute('gloss') || '').trim().toUpperCase();
          if (gloss.length === 1 && gloss >= 'A' && gloss <= 'Z') {
            this.letterToSign.set(gloss, s.outerHTML);
          }
        }
      } catch (e) {
        console.warn(`[SignLanguageManager] Failed to load alphabet ${url}:`, e);
      }
    }

    async loadConceptCsvUrl(url) {
      try {
        const res = await fetch(url, { cache: 'no-cache' });
        if (!res.ok) return;
        let txt = await res.text();
        if (txt.charCodeAt(0) === 0xFEFF) txt = txt.slice(1);
        const delim = txt.includes('\t') ? '\t' : ',';
        const lines = txt.split(/\r?\n/).filter(l => l.trim());
        const header = (lines.shift() || '').split(delim).map(s => s.trim().toLowerCase());
        const ci = header.indexOf('concept'), gi = header.indexOf('gloss');
        if (ci < 0 || gi < 0) return;
        for (const line of lines) {
          const cols = line.split(delim);
          const concept = (cols[ci] || '').trim().toLowerCase();
          const gloss = (cols[gi] || '').trim().toLowerCase();
          if (concept && gloss) this.conceptToGloss.set(glossBase(concept), gloss);
        }
      } catch (e) {
        console.warn(`[SignLanguageManager] Failed to load CSV ${url}:`, e);
      }
    }

    extractEmbeddedAlphabet() {
      for (const entry of this.glossToSign.entries()) {
        const upper = entry[0].toUpperCase();
        if (upper.length === 1 && upper >= 'A' && upper <= 'Z' && !this.letterToSign.has(upper)) {
          this.letterToSign.set(upper, entry[1]);
        }
      }
    }

    /**
     * Map text tokens into available sign language glosses or fingerspelling blocks
     */
    generateSequence(text) {
      const rawTokens = text.toLowerCase().replace(/[^\w\s]/g, ' ').split(/\s+/).filter(Boolean);
      const mappedBlocks = [];
      const missingTokens = [];
      const wordDetails = [];

      for (const token of rawTokens) {
        let hnsXml = null;
        let matchType = 'none';

        // 1. Exact Gloss Match
        if (this.glossToSign.has(token)) {
          hnsXml = this.glossToSign.get(token);
          matchType = 'exact';
        } 
        // 2. Concept Mapping Match
        else {
          const tBase = glossBase(token);
          if (this.conceptToGloss.has(tBase)) {
            const gloss = this.conceptToGloss.get(tBase);
            if (this.glossToSign.has(gloss)) {
              hnsXml = this.glossToSign.get(gloss);
              matchType = 'concept';
            }
          }
          // 3. Base Gloss Match
          if (!hnsXml && this.baseToGloss.has(tBase)) {
            const gloss = this.baseToGloss.get(tBase);
            if (this.glossToSign.has(gloss)) {
              hnsXml = this.glossToSign.get(gloss);
              matchType = 'base';
            }
          }
          // 4. Fuzzy Match
          if (!hnsXml) {
            let bestBase = null, bestScore = 0;
            for (const b of this.baseToGloss.keys()) {
              const s = similarity(tBase, b);
              if (s > bestScore) { bestScore = s; bestBase = b; }
            }
            if (bestBase && bestScore >= 0.82) {
              const gloss = this.baseToGloss.get(bestBase);
              if (this.glossToSign.has(gloss)) {
                hnsXml = this.glossToSign.get(gloss);
                matchType = 'fuzzy';
              }
            }
          }
        }

        if (hnsXml) {
          mappedBlocks.push(hnsXml);
          wordDetails.push({ word: token, type: matchType, xml: hnsXml });
        } else {
          // 5. Fallback to Fingerspelling
          const fingerBlocks = [];
          for (const char of token.toUpperCase()) {
            if (this.letterToSign.has(char)) {
              fingerBlocks.push(this.letterToSign.get(char));
            }
          }
          if (fingerBlocks.length > 0) {
            mappedBlocks.push(...fingerBlocks);
            wordDetails.push({ word: token, type: 'fingerspell', xmls: fingerBlocks });
          } else {
            missingTokens.push(token);
            wordDetails.push({ word: token, type: 'missing' });
          }
        }
      }

      let sigmlXml = null;
      if (mappedBlocks.length > 0) {
        sigmlXml = `<?xml version="1.0" encoding="utf-8"?>\n<sigml>\n${mappedBlocks.join('\n')}\n</sigml>`;
      }

      return {
        rawText: text,
        tokens: rawTokens,
        sigmlXml: sigmlXml,
        missingTokens: missingTokens,
        wordDetails: wordDetails,
        lang: this.currentLang
      };
    }
  }

  /**
   * Animation Controller & Queue Engine for 3D CWASA Avatars
   */
  class AvatarAnimationEngine {
    constructor() {
      this.langManager = new SignLanguageManager();
      this.isCwasaReady = false;
      this.avatars = {
        0: { id: 'luna', state: 'IDLE', queue: [], currentItem: null },
        1: { id: 'anna', state: 'IDLE', queue: [], currentItem: null }
      };
      this.stateListeners = [];
    }

    addStateListener(cb) {
      if (typeof cb === 'function') this.stateListeners.push(cb);
    }

    notifyStateChange(avIndex, state, info) {
      if (this.avatars[avIndex]) {
        this.avatars[avIndex].state = state;
      }
      this.stateListeners.forEach(cb => {
        try { cb(avIndex, state, info); } catch (e) { console.error(e); }
      });
    }

    async init(initialLang = 'isl') {
      await this.langManager.setLanguage(initialLang);
      this.initCwasa();
    }

    initCwasa() {
      if (window.CWASA && window.CWASA.ready) {
        this.mountCwasa();
        return;
      }

      var waited = 0, tick = 100, limit = 10000;
      const check = () => {
        if (window.CWASA) {
          this.mountCwasa();
        } else {
          waited += tick;
          if (waited < limit) setTimeout(check, tick);
          else console.warn('[AvatarAnimationEngine] CWASA library not found on page');
        }
      };
      check();
    }

    mountCwasa() {
      if (this.isCwasaReady || !window.CWASA) return;
      try {
        window.CWASA.init({
          useClientConfig: false,
          useCwaConfig: true,
          avSettings: [
            {
              width: 440,
              height: 340,
              avList: 'avsfull',
              initAv: 'luna',
              ambIdle: true,
              allowFrameSteps: false,
              allowSiGMLText: false
            },
            {
              width: 440,
              height: 340,
              avList: 'avsfull',
              initAv: 'anna',
              ambIdle: true,
              allowFrameSteps: false,
              allowSiGMLText: false
            }
          ]
        });

        if (window.CWASA.ready && typeof window.CWASA.ready.then === 'function') {
          window.CWASA.ready.then(() => {
            this.isCwasaReady = true;
            console.log('[AvatarAnimationEngine] CWASA 3D WebGL Avatars Ready');
            this.notifyStateChange(0, 'IDLE', { ready: true });
            this.notifyStateChange(1, 'IDLE', { ready: true });
          }).catch(err => {
            console.warn('[AvatarAnimationEngine] CWASA init warning:', err);
            this.isCwasaReady = true;
          });
        } else {
          setTimeout(() => {
            this.isCwasaReady = true;
            this.notifyStateChange(0, 'IDLE', { ready: true });
            this.notifyStateChange(1, 'IDLE', { ready: true });
          }, 500);
        }
      } catch (err) {
        console.error('[AvatarAnimationEngine] CWASA init exception:', err);
      }
    }

    /**
     * Enqueue speech text to be signed by a specific avatar
     * @param {number} avIndex 0 for Luna (Box 1), 1 for Anna (Box 2)
     * @param {string} text Speech or text phrase
     */
    speak(avIndex, text) {
      if (!text || !text.trim()) return;

      const av = this.avatars[avIndex];
      if (!av) return;

      this.notifyStateChange(avIndex, 'PROCESSING', { text });

      const sequence = this.langManager.generateSequence(text);

      if (!sequence.sigmlXml) {
        console.warn(`[AvatarAnimationEngine] No sign animation sequence available for phrase: "${text}"`);
        this.notifyStateChange(avIndex, 'ERROR', {
          text,
          message: 'Sign animation unavailable for this phrase.',
          missingTokens: sequence.missingTokens
        });
        setTimeout(() => {
          this.notifyStateChange(avIndex, 'IDLE', {});
        }, 3000);
        return sequence;
      }

      // Add to playback queue
      av.queue.push(sequence);
      this.processQueue(avIndex);
      return sequence;
    }

    processQueue(avIndex) {
      const av = this.avatars[avIndex];
      if (!av || av.state === 'SIGNING') return;
      if (av.queue.length === 0) {
        this.notifyStateChange(avIndex, 'IDLE', {});
        return;
      }

      const item = av.queue.shift();
      av.currentItem = item;

      this.notifyStateChange(avIndex, 'SIGNING', {
        text: item.rawText,
        sequence: item,
        lang: item.lang
      });

      if (window.CWASA && this.isCwasaReady) {
        try {
          window.CWASA.playSiGMLText(item.sigmlXml, avIndex);
        } catch (e) {
          console.error('[AvatarAnimationEngine] playSiGMLText error:', e);
        }
      }

      // Estimate animation playback duration (approx 650ms per sign block)
      const tokenCount = item.wordDetails.length || 1;
      const durationMs = Math.max(2000, tokenCount * 700);

      setTimeout(() => {
        av.currentItem = null;
        if (av.queue.length > 0) {
          av.state = 'IDLE';
          this.processQueue(avIndex);
        } else {
          this.notifyStateChange(avIndex, 'IDLE', { text: item.rawText });
        }
      }, durationMs);
    }
  }

  // Create singleton instance
  window.SignAvatarEngine = new AvatarAnimationEngine();

})(window);
