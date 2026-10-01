/**
 * Signify Dynamic Account-Specific Data Store & Isolation Manager
 * Handles dynamic API syncing and account isolation per user ID.
 */
(function(window) {
  'use strict';

  const STORAGE_PREFIX = 'signify_user_data_';

  const SignifyUserStore = {
    
    // Get currently authenticated or active user identity
    getLoggedInUser: function() {
      try {
        const stored = sessionStorage.getItem('signify_logged_user');
        if (stored) return JSON.parse(stored);
      } catch (e) {}

      // Fallback default identity
      const defaultUser = {
        id: 'usr_charu',
        name: 'Charu',
        email: 'charu@signify.ai',
        phone: '6382472844',
        role: 'Sign Language User'
      };
      sessionStorage.setItem('signify_logged_user', JSON.stringify(defaultUser));
      return defaultUser;
    },

    // Switch active user account (Account Isolation)
    switchUser: function(userObj) {
      if (!userObj || !userObj.name) return;
      
      const cleanUser = {
        id: userObj.id || 'usr_' + userObj.name.toLowerCase(),
        name: userObj.name,
        email: userObj.email || `${userObj.name.toLowerCase()}@signify.ai`,
        phone: userObj.phone || '9876543210',
        role: userObj.role || 'Sign Language User'
      };

      sessionStorage.setItem('signify_logged_user', JSON.stringify(cleanUser));
      localStorage.setItem('signify_last_assigned_role', cleanUser.name);
      
      window.dispatchEvent(new CustomEvent('signify:user_switched', { detail: cleanUser }));
      this.loadUserData(); // Reload isolated dataset
    },

    // Get user-specific localStorage key
    getStorageKey: function() {
      const u = this.getLoggedInUser();
      const safeId = (u.id || u.email || u.name).toLowerCase().replace(/[^a-z0-9]/g, '_');
      return STORAGE_PREFIX + safeId;
    },

    // Load dynamic dataset for the currently logged-in account
    loadUserData: async function() {
      const u = this.getLoggedInUser();
      const localKey = this.getStorageKey();

      // Try fetching from backend API
      try {
        const token = localStorage.getItem('signify_auth_token') || '';
        const res = await fetch(`/api/user/data?user_id=${encodeURIComponent(u.id || u.email)}`, {
          headers: { 'Authorization': token ? `Bearer ${token}` : '' }
        });
        if (res.ok) {
          const json = await res.json();
          if (json && json.data) {
            localStorage.setItem(localKey, JSON.stringify(json.data));
            window.dispatchEvent(new CustomEvent('signify:user_data_loaded', { detail: json.data }));
            return json.data;
          }
        }
      } catch (err) {
        console.warn('Network fetch error for user data, using isolated local cache:', err);
      }

      // Fallback to local user store
      let data = null;
      try {
        const raw = localStorage.getItem(localKey);
        if (raw) data = JSON.parse(raw);
      } catch (e) {}

      if (!data) {
        data = this.generateDefaultDataForUser(u);
        localStorage.setItem(localKey, JSON.stringify(data));
      }

      window.dispatchEvent(new CustomEvent('signify:user_data_loaded', { detail: data }));
      return data;
    },

    // Save or update user data for the active account
    saveUserData: async function(fullData) {
      const u = this.getLoggedInUser();
      const localKey = this.getStorageKey();

      localStorage.setItem(localKey, JSON.stringify(fullData));

      // Sync asynchronously to backend
      try {
        const token = localStorage.getItem('signify_auth_token') || '';
        await fetch('/api/user/data', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({
            user_id: u.id || u.email,
            ...fullData
          })
        });
      } catch (err) {
        console.warn('Failed to sync user data to backend:', err);
      }

      window.dispatchEvent(new CustomEvent('signify:user_data_updated', { detail: fullData }));
      return fullData;
    },

    // Partial update helper
    updateField: async function(field, val) {
      const current = await this.loadUserData();
      current[field] = val;
      return await this.saveUserData(current);
    },

    // Initial seed generator for new accounts
    generateDefaultDataForUser: function(u) {
      const isCharu = (u.name || '').toLowerCase().includes('charu');
      const isKeerthi = (u.name || '').toLowerCase().includes('keerthi');

      const defaultContacts = [
        { id: 'c_luna', name: 'Luna (Signify AI)', phone: '+1 (800) 555-LUNA', avatar: '/images/luna_3d.jpg', isFav: true, isBlocked: false }
      ];

      if (isCharu) {
        defaultContacts.push(
          { id: 'usr_keerthi', name: 'Keerthi', phone: '9834567290', avatar: null, isFav: true, isBlocked: false },
          { id: 'usr_alex', name: 'Alex Rivers', phone: '+1 (555) 019-2834', avatar: null, isFav: true, isBlocked: false },
          { id: 'usr_priya', name: 'Priya', phone: '9876543210', avatar: null, isFav: false, isBlocked: false },
          { id: 'usr_sanjay', name: 'Sanjay', phone: '9123456780', avatar: null, isFav: false, isBlocked: false },
          { id: 'usr_meena', name: 'Meena', phone: '9887766554', avatar: null, isFav: false, isBlocked: false },
          { id: 'usr_ravi', name: 'Ravi Kumar', phone: '9876012345', avatar: null, isFav: false, isBlocked: true },
          { id: 'usr_spam', name: 'Spam Caller', phone: '+1 (444) 222-9999', avatar: null, isFav: false, isBlocked: true }
        );
      } else if (isKeerthi) {
        defaultContacts.push(
          { id: 'usr_charu', name: 'Charu', phone: '6382472844', avatar: null, isFav: true, isBlocked: false },
          { id: 'usr_alex', name: 'Alex Rivers', phone: '+1 (555) 019-2834', avatar: null, isFav: true, isBlocked: false },
          { id: 'usr_sanjay', name: 'Sanjay', phone: '9123456780', avatar: null, isFav: false, isBlocked: false }
        );
      }

      return {
        user_id: u.id,
        profile: {
          name: u.name,
          email: u.email,
          phone: u.phone,
          role: u.role || 'Sign Language User',
          avatar: isCharu ? '/images/luna_3d.jpg' : '/images/anna_3d.jpg'
        },
        contacts: defaultContacts,
        callHistory: [
          { id: 'h1', name: 'Priya', phone: '9876543210', time: 'Today, 10:45 AM', type: 'missed', avatar: null },
          { id: 'h2', name: isCharu ? 'Keerthi' : 'Charu', phone: isCharu ? '9834567290' : '6382472844', time: 'Today, 09:12 AM', type: 'incoming', avatar: null },
          { id: 'h3', name: 'Luna (Signify AI)', phone: '+1 (800) 555-LUNA', time: 'Yesterday, 06:30 PM', type: 'outgoing', avatar: '/images/luna_3d.jpg' }
        ],
        notifications: [
          { id: 'n1', title: 'Call Connection Ready', text: `Welcome back ${u.name}. Live call service is active.`, time: '5m ago', read: false },
          { id: 'n2', title: 'Sign Language Update', text: 'New BSL and ASL gloss dataset loaded.', time: '1h ago', read: true }
        ],
        avatarSettings: {
          selectedAvatar: isCharu ? 'luna' : 'anna',
          skinTone: '#F5D6BA',
          hairStyle: 'style_1',
          hairColor: '#29231F',
          eyeColor: '#16A34A',
          outfit: 'outfit_green',
          pose: 0
        },
        preferences: {
          language: 'en',
          signLanguage: 'bsl',
          subtitles: true,
          theme: 'light'
        }
      };
    }

  };

  window.SignifyUserStore = SignifyUserStore;

})(window);
