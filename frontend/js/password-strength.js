/**
 * Password Strength Indicator
 * Visual feedback for password strength with real-time validation
 */

class PasswordStrengthIndicator {
    constructor(passwordInput, options = {}) {
        this.input = passwordInput;
        this.options = {
            showRequirements: options.showRequirements !== false,
            minLength: options.minLength || 8,
            ...options
        };

        this.createIndicator();
        this.attachListeners();
    }

    createIndicator() {
        // Create strength meter container
        const container = document.createElement('div');
        container.className = 'password-strength-container';

        // Strength meter
        const meter = document.createElement('div');
        meter.className = 'password-strength-meter';
        meter.innerHTML = `
            <div class="strength-bar">
                <div class="strength-bar-fill" data-strength="0"></div>
            </div>
            <span class="strength-label">Digite uma senha</span>
        `;

        // Requirements list
        if (this.options.showRequirements) {
            const requirements = document.createElement('div');
            requirements.className = 'password-requirements';
            requirements.innerHTML = `
                <div class="requirement" data-req="length">
                    <span class="req-icon">○</span>
                    <span class="req-text">Mínimo ${this.options.minLength} caracteres</span>
                </div>
                <div class="requirement" data-req="uppercase">
                    <span class="req-icon">○</span>
                    <span class="req-text">Uma letra maiúscula</span>
                </div>
                <div class="requirement" data-req="lowercase">
                    <span class="req-icon">○</span>
                    <span class="req-text">Uma letra minúscula</span>
                </div>
                <div class="requirement" data-req="number">
                    <span class="req-icon">○</span>
                    <span class="req-text">Um número</span>
                </div>
            `;
            meter.appendChild(requirements);
        }

        container.appendChild(meter);

        // Insert after password input
        this.input.parentNode.insertBefore(container, this.input.nextSibling);

        this.container = container;
        this.strengthBar = container.querySelector('.strength-bar-fill');
        this.strengthLabel = container.querySelector('.strength-label');
        this.requirements = container.querySelectorAll('.requirement');
    }

    attachListeners() {
        this.input.addEventListener('input', () => this.updateStrength());
        this.input.addEventListener('focus', () => this.container.classList.add('focused'));
        this.input.addEventListener('blur', () => this.container.classList.remove('focused'));
    }

    updateStrength() {
        const password = this.input.value;

        if (!password) {
            this.setStrength(0, 'Digite uma senha');
            this.updateRequirements(password);
            return;
        }

        const checks = {
            length: password.length >= this.options.minLength,
            uppercase: /[A-Z]/.test(password),
            lowercase: /[a-z]/.test(password),
            number: /\d/.test(password)
        };

        // Calculate strength (0-4)
        const score = Object.values(checks).filter(Boolean).length;

        // Update strength display
        const strengthLevels = [
            { threshold: 0, label: 'Digite uma senha', class: 'none' },
            { threshold: 1, label: 'Muito fraca', class: 'weak' },
            { threshold: 2, label: 'Fraca', class: 'fair' },
            { threshold: 3, label: 'Boa', class: 'good' },
            { threshold: 4, label: 'Forte', class: 'strong' }
        ];

        const level = strengthLevels[score];
        this.setStrength(score, level.label, level.class);

        // Update requirements
        this.updateRequirements(password, checks);
    }

    setStrength(score, label, className = 'none') {
        this.strengthBar.setAttribute('data-strength', score);
        this.strengthBar.className = `strength-bar-fill strength-${className}`;
        this.strengthLabel.textContent = label;
        this.strengthLabel.className = `strength-label strength-${className}`;
    }

    updateRequirements(password, checks = null) {
        if (!this.options.showRequirements) return;

        if (!checks) {
            checks = {
                length: password.length >= this.options.minLength,
                uppercase: /[A-Z]/.test(password),
                lowercase: /[a-z]/.test(password),
                number: /\d/.test(password)
            };
        }

        this.requirements.forEach(req => {
            const type = req.getAttribute('data-req');
            const icon = req.querySelector('.req-icon');

            if (checks[type]) {
                req.classList.add('met');
                icon.textContent = '✓';
            } else {
                req.classList.remove('met');
                icon.textContent = '○';
            }
        });
    }

    isValid() {
        return Validators.validatePassword(this.input.value).valid;
    }
}

// Auto-initialize for password inputs with data-strength attribute
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('input[type="password"][data-strength]').forEach(input => {
        new PasswordStrengthIndicator(input);
    });
});
