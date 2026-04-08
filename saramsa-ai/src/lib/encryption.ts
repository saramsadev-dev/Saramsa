import CryptoJS from 'crypto-js';

// Note: NEXT_PUBLIC_ vars are embedded in the client bundle — this is URL obfuscation, not security.
// The env var must be set; do not commit a fallback key.
const SECRET_KEY = process.env.NEXT_PUBLIC_ENCRYPTION_KEY;
if (!SECRET_KEY) {
  throw new Error('NEXT_PUBLIC_ENCRYPTION_KEY is not set');
}

/**
 * Encrypts a project ID for use in URLs
 * @param projectId - The plain project ID to encrypt
 * @returns Encrypted and URL-safe string
 */
export function encryptProjectId(projectId: string): string {
  try {
    const encrypted = CryptoJS.AES.encrypt(projectId, SECRET_KEY).toString();
    // Make URL-safe by replacing problematic characters
    return encrypted
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=/g, '');
  } catch (error) {
    console.error('Error encrypting project ID:', error);
    throw new Error('Failed to encrypt project ID');
  }
}

/**
 * Decrypts a project ID from URL
 * @param encryptedId - The encrypted project ID from URL
 * @returns Decrypted project ID
 */
export function decryptProjectId(encryptedId: string): string {
  try {
    // Restore original base64 format
    let restored = encryptedId
      .replace(/-/g, '+')
      .replace(/_/g, '/');
    
    // Add padding if needed
    while (restored.length % 4) {
      restored += '=';
    }
    
    const decrypted = CryptoJS.AES.decrypt(restored, SECRET_KEY);
    const projectId = decrypted.toString(CryptoJS.enc.Utf8);
    
    if (!projectId) {
      throw new Error('Invalid encrypted project ID');
    }
    
    return projectId;
  } catch (error) {
    console.error('Error decrypting project ID:', error);
    throw new Error('Failed to decrypt project ID');
  }
}

/**
 * Validates if an encrypted project ID can be decrypted
 * @param encryptedId - The encrypted project ID to validate
 * @returns boolean indicating if the ID is valid
 */
export function isValidEncryptedId(encryptedId: string): boolean {
  try {
    const decrypted = decryptProjectId(encryptedId);
    return decrypted.length > 0;
  } catch {
    return false;
  }
}
