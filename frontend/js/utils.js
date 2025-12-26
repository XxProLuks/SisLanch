/**
 * Common JavaScript Utility Functions
 * Shared helper functions used throughout the frontend
 * @module utils/common
 */

/**
 * Format a number as Brazilian currency
 * @param {number} value - The numeric value to format
 * @returns {string} Formatted currency string (e.g., 'R$ 1.234,56')
 * @example
 * formatCurrency(1234.56); // Returns 'R$ 1.234,56'
 */
function formatCurrency(value) {
    if (value === null || value === undefined) return 'R$ 0,00';

    const formatted = value.toFixed(2)
        .replace(/\d(?=(\d{3})+\.)/g, '$&,')
        .replace('.', 'TEMP')
        .replace(/,/g, '.')
        .replace('TEMP', ',');

    return `R$ ${formatted}`;
}

/**
 * Format a date to Brazilian format (DD/MM/YYYY)
 * @param {Date|string} date - Date object or ISO string
 * @returns {string} Formatted date string
 * @example
 * formatDate(new Date()); // Returns '26/12/2025'
 */
function formatDate(date) {
    if (!date) return '';

    const d = date instanceof Date ? date : new Date(date);
    const day = String(d.getDate()).padStart(2, '0');
    const month = String(d.getMonth() + 1).padStart(2, '0');
    const year = d.getFullYear();

    return `${day}/${month}/${year}`;
}

/**
 * Format a date to Brazilian datetime format
 * @param {Date|string} date - Date object or ISO string
 * @returns {string} Formatted datetime string
 * @example
 * formatDateTime(new Date()); // Returns '26/12/2025 11:30'
 */
function formatDateTime(date) {
    if (!date) return '';

    const d = date instanceof Date ? date : new Date(date);
    const dateStr = formatDate(d);
    const hours = String(d.getHours()).padStart(2, '0');
    const minutes = String(d.getMinutes()).padStart(2, '0');

    return `${dateStr} ${hours}:${minutes}`;
}

/**
 * Debounce a function call
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
 * @example
 * const search = debounce(() => fetchResults(), 300);
 * input.addEventListener('input', search);
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle a function call
 * @param {Function} func - Function to throttle
 * @param {number} limit - Minimum time between calls in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function executedFunction(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Deep clone an object
 * @param {Object} obj - Object to clone
 * @returns {Object} Cloned object
 * @example
 * const clone = deepClone(original);
 */
function deepClone(obj) {
    return JSON.parse(JSON.stringify(obj));
}

/**
 * Check if object is empty
 * @param {Object} obj - Object to check
 * @returns {boolean} True if empty
 * @example
 * isEmpty({}); // Returns true
 * isEmpty({a: 1}); // Returns false
 */
function isEmpty(obj) {
    return Object.keys(obj).length === 0;
}

/**
 * Capitalize first letter of string
 * @param {string} str - String to capitalize
 * @returns {string} Capitalized string
 * @example
 * capitalize('hello'); // Returns 'Hello'
 */
function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
}

/**
 * Truncate string to maximum length
 * @param {string} str - String to truncate
 * @param {number} maxLength - Maximum length
 * @param {string} [suffix='...'] - Suffix to add if truncated
 * @returns {string} Truncated string
 * @example
 * truncate('Hello World', 8); // Returns 'Hello...'
 */
function truncate(str, maxLength, suffix = '...') {
    if (str.length <= maxLength) return str;
    return str.slice(0, maxLength - suffix.length) + suffix;
}

/**
 * Generate a random ID
 * @param {number} [length=8] - Length of ID
 * @returns {string} Random ID
 * @example
 * generateId(); // Returns 'a3f8d2e1'
 */
function generateId(length = 8) {
    return Math.random().toString(36).substring(2, 2 + length);
}

/**
 * Sleep for specified milliseconds
 * @param {number} ms - Milliseconds to sleep
 * @returns {Promise<void>} Promise that resolves after delay
 * @example
 * await sleep(1000); // Wait 1 second
 */
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Get URL query parameter
 * @param {string} param - Parameter name
 * @returns {string|null} Parameter value or null
 * @example
 * getQueryParam('id'); // Returns value of ?id=...
 */
function getQueryParam(param) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(param);
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<void>} Promise that resolves when copied
 * @example
 * await copyToClipboard('Hello World');
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
    } catch (err) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'absolute';
        textarea.style.left = '-9999px';
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);
    }
}

/**
 * Format file size in human-readable format
 * @param {number} bytes - Size in bytes
 * @returns {string} Formatted size string
 * @example
 * formatFileSize(1536); // Returns '1.5 KB'
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));

    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

/**
 * Group array items by key
 * @param {Array} array - Array to group
 * @param {string|Function} key - Key or function to group by
 * @returns {Object} Grouped object
 * @example
 * groupBy([{type: 'a', val: 1}, {type: 'b', val: 2}], 'type');
 * // Returns {a: [{type: 'a', val: 1}], b: [{type: 'b', val: 2}]}
 */
function groupBy(array, key) {
    return array.reduce((result, item) => {
        const group = typeof key === 'function' ? key(item) : item[key];
        (result[group] = result[group] || []).push(item);
        return result;
    }, {});
}

/**
 * Remove duplicates from array
 * @param {Array} array - Array with duplicates
 * @param {string} [key] - Optional key for objects
 * @returns {Array} Array without duplicates
 * @example
 * unique([1, 2, 2, 3]); // Returns [1, 2, 3]
 */
function unique(array, key) {
    if (!key) {
        return [...new Set(array)];
    }

    const seen = new Set();
    return array.filter(item => {
        const k = item[key];
        if (seen.has(k)) return false;
        seen.add(k);
        return true;
    });
}

// Export functions if module system is available
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        formatCurrency,
        formatDate,
        formatDateTime,
        debounce,
        throttle,
        deepClone,
        isEmpty,
        capitalize,
        truncate,
        generateId,
        sleep,
        getQueryParam,
        copyToClipboard,
        formatFileSize,
        groupBy,
        unique
    };
}
