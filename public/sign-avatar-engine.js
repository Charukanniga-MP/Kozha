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
        const serializer = new XMLSerializer();
        const signs = Array.from(doc.querySelectorAll('hns_sign'));
        for (const s of signs) {
          const gloss = (s.getAttribute('gloss') || '').trim().toLowerCase();
          if (!gloss) continue;
          const sXml = s.outerHTML || serializer.serializeToString(s);
          this.glossToSign.set(gloss, sXml);
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
        const serializer = new XMLSerializer();
        const signs = Array.from(doc.querySelectorAll('hns_sign'));
        for (const s of signs) {
          const gloss = (s.getAttribute('gloss') || '').trim().toUpperCase();
          if (gloss.length === 1 && gloss >= 'A' && gloss <= 'Z') {
            const sXml = s.outerHTML || serializer.serializeToString(s);
            this.letterToSign.set(gloss, sXml);
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

      const lookupPhrase = (phrase) => {
        const p = phrase.toLowerCase().trim();
        // 1. Exact Gloss
        if (this.glossToSign.has(p)) return { xml: this.glossToSign.get(p), type: 'exact', gloss: p };
        const pUnder = p.replace(/\s+/g, '_');
        if (this.glossToSign.has(pUnder)) return { xml: this.glossToSign.get(pUnder), type: 'exact', gloss: pUnder };
        const pHyphen = p.replace(/\s+/g, '-');
        if (this.glossToSign.has(pHyphen)) return { xml: this.glossToSign.get(pHyphen), type: 'exact', gloss: pHyphen };

        // 2. Base form
        const b = glossBase(p);
        if (this.baseToGloss.has(b)) {
          const g = this.baseToGloss.get(b);
          if (this.glossToSign.has(g)) return { xml: this.glossToSign.get(g), type: 'base', gloss: g };
        }

        // 3. Concept map
        if (this.conceptToGloss.has(b)) {
          const g = this.conceptToGloss.get(b);
          if (this.glossToSign.has(g)) return { xml: this.glossToSign.get(g), type: 'concept', gloss: g };
        }

        // 4. Fuzzy similarity for single words
        if (p.length > 3) {
          let bestBase = null, bestScore = 0;
          for (const k of this.baseToGloss.keys()) {
            const s = similarity(b, k);
            if (s > bestScore) { bestScore = s; bestBase = k; }
          }
          if (bestBase && bestScore >= 0.82) {
            const g = this.baseToGloss.get(bestBase);
            if (this.glossToSign.has(g)) return { xml: this.glossToSign.get(g), type: 'fuzzy', gloss: g };
          }
        }

        return null;
      };

      let i = 0;
      while (i < rawTokens.length) {
        let matched = null;
        let consumed = 1;

        // Try 3-word n-gram
        if (i + 3 <= rawTokens.length) {
          const tri = rawTokens.slice(i, i + 3).join(' ');
          matched = lookupPhrase(tri);
          if (matched) consumed = 3;
        }

        // Try 2-word n-gram
        if (!matched && i + 2 <= rawTokens.length) {
          const bi = rawTokens.slice(i, i + 2).join(' ');
          matched = lookupPhrase(bi);
          if (matched) consumed = 2;
        }

        // Try 1-word token
        if (!matched) {
          const single = rawTokens[i];
          matched = lookupPhrase(single);
          consumed = 1;
        }

        if (matched) {
          mappedBlocks.push(matched.xml);
          wordDetails.push({
            word: rawTokens.slice(i, i + consumed).join(' '),
            type: matched.type,
            gloss: matched.gloss,
            xml: matched.xml
          });
          i += consumed;
        } else {
          const token = rawTokens[i];
          // If it's a stopword in a multi-token sentence, skip it gracefully
          if (STOPWORDS.has(token) && rawTokens.length > 1) {
            wordDetails.push({ word: token, type: 'omitted' });
            i++;
            continue;
          }

          // Fallback to Fingerspelling
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
          i++;
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
      this.isMeshReady = false;
      this.cwasaMounted = false;
      this.avatars = {
        0: { id: 'luna', state: 'LOADING', ready: false, queue: [], currentItem: null, lastText: '', fallbackTimer: null },
        1: { id: 'anna', state: 'LOADING', ready: false, queue: [], currentItem: null, lastText: '', fallbackTimer: null }
      };
      this.stateListeners = [];
    }

    addStateListener(cb) {
      if (typeof cb === 'function') {
        this.stateListeners.push(cb);
        if (this.isMeshReady) {
          try { cb(0, 'IDLE', { ready: true, avatar: this.avatars[0].id }); } catch (e) {}
          if (this.avatars[1] && this.avatars[1].ready) {
            try { cb(1, 'IDLE', { ready: true, avatar: this.avatars[1].id }); } catch (e) {}
          }
        }
      }
    }

    notifyStateChange(avIndex, state, info = {}) {
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
      if (this.cwasaMounted || !window.CWASA) return;
      this.cwasaMounted = true;

      // Register CWASA lifecycle hooks
      if (window.CWASA.addHook) {
        window.CWASA.addHook('avatarready', (evt) => {
          console.log('[AvatarAnimationEngine] *** AVATAR MESH BOUND & READY (avatarready hook fired) ***', evt);
          this.isCwasaReady = true;
          this.isMeshReady = true;

          const avIdx = (evt && typeof evt.av === 'number') ? evt.av : null;
          const targets = avIdx !== null ? [avIdx] : [0, 1];
          targets.forEach(idx => {
            if (this.avatars[idx]) {
              this.avatars[idx].ready = true;
              this.notifyStateChange(idx, 'IDLE', { ready: true, avatar: this.avatars[idx].id });
              if (this.avatars[idx].queue.length > 0) {
                this.processQueue(idx);
              }
            }
          });
        }, '*');

        window.CWASA.addHook('animidle', (evt) => {
          const avIdx = (evt && typeof evt.av === 'number') ? evt.av : 0;
          const av = this.avatars[avIdx];
          if (av && av.state === 'SIGNING') {
            if (av.fallbackTimer) {
              clearTimeout(av.fallbackTimer);
              av.fallbackTimer = null;
            }
            av.currentItem = null;
            if (av.queue.length > 0) {
              av.state = 'IDLE';
              this.processQueue(avIdx);
            } else {
              av.state = 'IDLE';
              this.notifyStateChange(avIdx, 'IDLE', { text: av.lastText, avatar: av.id });
            }
          }
        }, '*');

        window.CWASA.addHook('animactive', (evt) => {
          const avIdx = (evt && typeof evt.av === 'number') ? evt.av : 0;
          const av = this.avatars[avIdx];
          if (av && av.currentItem) {
            this.notifyStateChange(avIdx, 'SIGNING', {
              text: av.currentItem.rawText,
              avatar: av.id
            });
          }
        }, '*');
      }

      try {
        const hasAv1 = !!document.querySelector('.CWASAAvatar.av1');
        const avSettings = [
          {
            width: hasAv1 ? 440 : 720,
            height: hasAv1 ? 340 : 540,
            avList: 'avsfull',
            initAv: 'luna',
            ambIdle: true,
            allowFrameSteps: false,
            allowSiGMLText: false
          }
        ];

        if (hasAv1) {
          avSettings.push({
            width: 440,
            height: 340,
            avList: 'avsfull',
            initAv: 'anna',
            ambIdle: true,
            allowFrameSteps: false,
            allowSiGMLText: false
          });
        }

        window.CWASA.init({
          useClientConfig: false,
          useCwaConfig: true,
          avSettings: avSettings
        });

        if (window.CWASA.ready && typeof window.CWASA.ready.then === 'function') {
          window.CWASA.ready.then(() => {
            console.log('[AvatarAnimationEngine] CWASA core ready; awaiting 3D avatar mesh…');
          }).catch(err => {
            console.warn('[AvatarAnimationEngine] CWASA init warning:', err);
          });
        }
      } catch (err) {
        console.error('[AvatarAnimationEngine] CWASA init exception:', err);
      }
    }

    /**
     * Switch CWASA avatar model (luna, anna, marc, francoise)
     */
    switchAvatar(avName, avIndex = 0) {
      if (this.avatars[avIndex]) {
        this.avatars[avIndex].id = avName;
      }
      this.isMeshReady = false;
      const menu = document.querySelector(`.menuAv.av${avIndex}`);
      if (menu) {
        menu.value = avName;
        menu.dispatchEvent(new Event('change'));
      }
      this.notifyStateChange(avIndex, 'PROCESSING', { avatar: avName, text: `Loading ${avName}…` });
    }

    /**
     * Enqueue speech text to be signed by a specific avatar
     * @param {number} avIndex 0 for Luna (Box 1), 1 for Anna (Box 2)
     * @param {string} text Speech or text phrase
     */
    speak(avIndex = 0, text) {
      if (!text || !text.trim()) return;

      const av = this.avatars[avIndex];
      if (!av) return;

      av.lastText = text;
      this.notifyStateChange(avIndex, 'PROCESSING', { text, avatar: av.id });

      const sequence = this.langManager.generateSequence(text);

      if (!sequence.sigmlXml) {
        console.warn(`[AvatarAnimationEngine] No sign animation sequence available for phrase: "${text}"`);
        this.notifyStateChange(avIndex, 'ERROR', {
          text,
          message: 'Sign animation unavailable for this phrase.',
          missingTokens: sequence.missingTokens,
          avatar: av.id
        });
        setTimeout(() => {
          this.notifyStateChange(avIndex, 'IDLE', { avatar: av.id });
        }, 3000);
        return sequence;
      }

      // Add to playback queue
      av.queue.push(sequence);
      this.processQueue(avIndex);
      return sequence;
    }

    /**
     * Replay last spoken sign phrase
     */
    replay(avIndex = 0) {
      const av = this.avatars[avIndex];
      if (av && av.lastText) {
        return this.speak(avIndex, av.lastText);
      }
    }

    processQueue(avIndex = 0) {
      const av = this.avatars[avIndex];
      if (!av || av.state === 'SIGNING') return;
      if (av.queue.length === 0) {
        if (av.ready || this.isMeshReady) {
          this.notifyStateChange(avIndex, 'IDLE', { avatar: av.id });
        }
        return;
      }

      // Guard: If 3D mesh is still binding in WebGL, hold in queue until avatarready hook fires
      if (!av.ready && !this.isMeshReady) {
        console.log(`[AvatarAnimationEngine] 3D mesh av${avIndex} still binding, queued sign for avatarready event…`);
        return;
      }

      const item = av.queue.shift();
      av.currentItem = item;

      this.notifyStateChange(avIndex, 'SIGNING', {
        text: item.rawText,
        sequence: item,
        lang: item.lang,
        avatar: av.id
      });

      if (window.CWASA && (this.isMeshReady || av.ready)) {
        try {
          if (typeof window.CWASA.stopSiGML === 'function') {
            window.CWASA.stopSiGML(avIndex);
          }
        } catch (_e) {}
        try {
          window.CWASA.playSiGMLText(item.sigmlXml, avIndex);
        } catch (e) {
          console.error(`[AvatarAnimationEngine] playSiGMLText error for av${avIndex}:`, e);
        }
      }

      // Estimate animation playback duration (approx 850ms per sign block)
      const tokenCount = item.wordDetails.length || 1;
      const durationMs = Math.max(2500, tokenCount * 900);

      if (av.fallbackTimer) clearTimeout(av.fallbackTimer);
      av.fallbackTimer = setTimeout(() => {
        if (av.state === 'SIGNING') {
          av.currentItem = null;
          if (av.queue.length > 0) {
            av.state = 'IDLE';
            this.processQueue(avIndex);
          } else {
            av.state = 'IDLE';
            this.notifyStateChange(avIndex, 'IDLE', { text: item.rawText, avatar: av.id });
          }
        }
      }, durationMs);
    }
  }

  // Create singleton instance
  window.SignAvatarEngine = new AvatarAnimationEngine();

})(window);
