/**
 * TripSync V2 — Local Storage Manager
 * Encapsulates offline-first localStorage queries for user profile settings,
 * obfuscated keys, active trip items, checklists, and chat histories.
 */

const TripSyncStorage = {
    // Keys used in localStorage
    KEYS: {
        PROFILE: 'tripsync_user_profile',
        KEYS_ENCRYPTED: 'tripsync_keys_encrypted',
        CURRENT_TRIP: 'tripsync_current_trip',
        TRIP_HISTORY: 'tripsync_trip_history'
    },

    /**
     * User Profile Methods
     */
    saveProfile(email, preferences = { currency: 'CAD', travelers: 1 }) {
        const profile = {
            email: email,
            created_at: new Date().toISOString(),
            preferences: preferences
        };
        localStorage.setItem(this.KEYS.PROFILE, JSON.stringify(profile));
        return profile;
    },

    getProfile() {
        const profile = localStorage.getItem(this.KEYS.PROFILE);
        return profile ? JSON.parse(profile) : null;
    },

    hasProfile() {
        return !!this.getProfile();
    },

    /**
     * API Key Credentials Methods
     */
    saveKeys(encryptedKey, provider = 'deepseek', autoFailover = true) {
        const credentials = {
            [provider]: encryptedKey,
            active_provider: provider,
            auto_failover: autoFailover,
            updated_at: new Date().toISOString()
        };
        // Merge with existing if present
        const existing = this.getKeys();
        const merged = { ...existing, ...credentials };
        localStorage.setItem(this.KEYS.KEYS_ENCRYPTED, JSON.stringify(merged));
        return merged;
    },

    getKeys() {
        const keys = localStorage.getItem(this.KEYS.KEYS_ENCRYPTED);
        return keys ? JSON.parse(keys) : null;
    },

    clearKeys() {
        localStorage.removeItem(this.KEYS.KEYS_ENCRYPTED);
    },

    /**
     * Current Trip & Checklist Methods
     */
    saveCurrentTrip(tripData) {
        // Expects structure: { id, destination, dates, items: { flights, hotel, activities, transfers, insurance }, checklist: [], conversation_history: [] }
        localStorage.setItem(this.KEYS.CURRENT_TRIP, JSON.stringify(tripData));
        this.addTripToHistory(tripData);
        return tripData;
    },

    getCurrentTrip() {
        const trip = localStorage.getItem(this.KEYS.CURRENT_TRIP);
        return trip ? JSON.parse(trip) : null;
    },

    updateTripItem(category, status, details = null) {
        const trip = this.getCurrentTrip();
        if (!trip) return null;

        if (!trip.items) trip.items = {};
        trip.items[category] = {
            status: status, // 'pending', 'booked'
            details: details,
            updated_at: new Date().toISOString()
        };

        return this.saveCurrentTrip(trip);
    },

    /**
     * History & Sandbox Management
     */
    getTripHistory() {
        const history = localStorage.getItem(this.KEYS.TRIP_HISTORY);
        return history ? JSON.parse(history) : [];
    },

    addTripToHistory(trip) {
        if (!trip || !trip.id) return;
        const history = this.getTripHistory();
        const existingIndex = history.findIndex(t => t.id === trip.id);

        if (existingIndex > -1) {
            history[existingIndex] = trip;
        } else {
            history.unshift(trip); // add to top
        }

        localStorage.setItem(this.KEYS.TRIP_HISTORY, JSON.stringify(history));
    },

    clearAll() {
        Object.values(this.KEYS).forEach(k => localStorage.removeItem(k));
    }
};

window.TripSyncStorage = TripSyncStorage;
