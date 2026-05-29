/**
 * TripSync V2 — Client Obfuscation & Encryption
 * Implements a robust XOR-based obfuscation layer for saving user API keys
 * in the local browser cache, using a composite secret dynamically combined
 * with the user's registration email to raise the bar for security.
 */

const TripSyncCipher = {
    // Fallback static secret salt
    DEFAULT_SALT: 'TS-2026-FLY-Sync-Secure-0A1B2C3D',

    /**
     * XOR Encodes a string and returns a base64 encoded ciphertext
     */
    encrypt(plainText, email = '') {
        if (!plainText) return '';
        const secret = this._getCompositeSecret(email);
        let obfuscated = '';
        
        for (let i = 0; i < plainText.length; i++) {
            const charCode = plainText.charCodeAt(i);
            const saltCode = secret.charCodeAt(i % secret.length);
            // XOR operation
            obfuscated += String.fromCharCode(charCode ^ saltCode);
        }

        // Convert raw XOR string to standard base64 for safe JSON writing
        return btoa(unescape(encodeURIComponent(obfuscated)));
    },

    /**
     * Decrypts a base64 encoded ciphertext using the same email context
     */
    decrypt(base64CipherText, email = '') {
        if (!base64CipherText) return '';
        try {
            const secret = this._getCompositeSecret(email);
            // Decode from base64
            const obfuscated = decodeURIComponent(escape(atob(base64CipherText)));
            let plainText = '';

            for (let i = 0; i < obfuscated.length; i++) {
                const charCode = obfuscated.charCodeAt(i);
                const saltCode = secret.charCodeAt(i % secret.length);
                // Inverse XOR operation
                plainText += String.fromCharCode(charCode ^ saltCode);
            }

            return plainText;
        } catch (e) {
            console.error('Cipher decryption failure:', e);
            return '';
        }
    },

    /**
     * Helper to generate a dynamic composite secret
     */
    _getCompositeSecret(email = '') {
        const cleanEmail = email.trim().toLowerCase();
        return cleanEmail ? `${cleanEmail}_${this.DEFAULT_SALT}` : this.DEFAULT_SALT;
    }
};

window.TripSyncCipher = TripSyncCipher;
