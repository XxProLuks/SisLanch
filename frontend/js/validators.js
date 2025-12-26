/**
 * LANCH - Input Validators
 * Client-side validation utilities
 */

const Validators = {
    /**
     * Validate CPF (Brazilian tax ID)
     * @param {string} cpf - CPF to validate
     * @returns {boolean} true if valid
     */
    validateCPF(cpf) {
        // Remove non-digits
        cpf = cpf.replace(/\D/g, '');

        // Check length
        if (cpf.length !== 11) return false;

        // Check if all digits are the same
        if (/^(\d)\1+$/.test(cpf)) return false;

        // Validate check digits
        let sum = 0;
        for (let i = 0; i < 9; i++) {
            sum += parseInt(cpf.charAt(i)) * (10 - i);
        }
        let checkDigit = 11 - (sum % 11);
        if (checkDigit >= 10) checkDigit = 0;
        if (checkDigit !== parseInt(cpf.charAt(9))) return false;

        sum = 0;
        for (let i = 0; i < 10; i++) {
            sum += parseInt(cpf.charAt(i)) * (11 - i);
        }
        checkDigit = 11 - (sum % 11);
        if (checkDigit >= 10) checkDigit = 0;
        if (checkDigit !== parseInt(cpf.charAt(10))) return false;

        return true;
    },

    /**
     * Format CPF with mask
     * @param {string} cpf - CPF to format
     * @returns {string} formatted CPF (xxx.xxx.xxx-xx)
     */
    formatCPF(cpf) {
        cpf = cpf.replace(/\D/g, '');
        return cpf.replace(/(\d{3})(\d{3})(\d{3})(\d{2})/, '$1.$2.$3-$4');
    },

    /**
     * Validate numeric input
     * @param {string} value - Value to validate
     * @param {number} min - Minimum value (optional)
     * @param {number} max - Maximum value (optional)
     * @returns {boolean} true if valid
     */
    validateNumber(value, min = null, max = null) {
        const num = parseFloat(value);
        if (isNaN(num)) return false;
        if (min !== null && num < min) return false;
        if (max !== null && num > max) return false;
        return true;
    },

    /**
     * Validate decimal with  2 places
     * @param {string} value - Value to validate
     * @returns {boolean} true if valid
     */
    validateDecimal(value) {
        return /^\d+(\.\d{1,2})?$/.test(value);
    },

    /**
     * Validate required field
     * @param {string} value - Value to validate
     * @returns {boolean} true if not empty
     */
    validateRequired(value) {
        return value && value.trim() !== '';
    },

    /**
     * Validate email
     * @param {string} email - Email to validate
     * @returns {boolean} true if valid
     */
    validateEmail(email) {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    },

    /**
     * Validate password strength
     * @param {string} password - Password to validate
     * @returns {object} { valid: boolean, message: string }
     */
    validatePassword(password) {
        if (password.length < 8) {
            return { valid: false, message: 'A senha deve ter no mínimo 8 caracteres' };
        }
        if (!/[A-Z]/.test(password)) {
            return { valid: false, message: 'A senha deve conter pelo menos uma letra maiúscula' };
        }
        if (!/[a-z]/.test(password)) {
            return { valid: false, message: 'A senha deve conter pelo menos uma letra minúscula' };
        }
        if (!/\d/.test(password)) {
            return { valid: false, message: 'A senha deve conter pelo menos um número' };
        }
        return { valid: true, message: 'Senha forte' };
    },

    /**
     * Sanitize HTML input
     * @param {string} input - Input to sanitize
     * @returns {string} sanitized input
     */
    sanitizeHTML(input) {
        const div = document.createElement('div');
        div.textContent = input;
        return div.innerHTML;
    },

    /**
     * Validate matricula (employee ID)
     * @param {string} matricula - Matricula to validate
     * @returns {boolean} true if valid (numeric, 1-10 digits)
     */
    validateMatricula(matricula) {
        const cleaned = matricula.replace(/\D/g, '');
        return cleaned.length >= 1 && cleaned.length <= 10;
    },

    /**
     * Add real-time validation to an input field
     * @param {HTMLElement} input - Input element
     * @param {Function} validator - Validation function
     * @param {string} errorMessage - Error message to display
     */
    addValidation(input, validator, errorMessage) {
        input.addEventListener('blur', () => {
            const isValid = validator(input.value);
            if (!isValid) {
                input.classList.add('error');
                this.showError(input, errorMessage);
            } else {
                input.classList.remove('error');
                this.clearError(input);
            }
        });

        input.addEventListener('input', () => {
            if (input.classList.contains('error')) {
                const isValid = validator(input.value);
                if (isValid) {
                    input.classList.remove('error');
                    this.clearError(input);
                }
            }
        });
    },

    /**
     * Show error message for input
     * @param {HTMLElement} input - Input element
     * @param {string} message - Error message
     */
    showError(input, message) {
        let errorDiv = input.parentElement.querySelector('.field-error');
        if (!errorDiv) {
            errorDiv = document.createElement('div');
            errorDiv.className = 'field-error';
            input.parentElement.appendChild(errorDiv);
        }
        errorDiv.textContent = message;
    },

    /**
     * Clear error message for input
     * @param {HTMLElement} input - Input element
     */
    clearError(input) {
        const errorDiv = input.parentElement.querySelector('.field-error');
        if (errorDiv) {
            errorDiv.remove();
        }
    }
};
