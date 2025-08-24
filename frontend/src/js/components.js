/**
 * MINGUS Components Service
 * Reusable UI components, modal management, and form handling
 */

class ComponentService {
    constructor() {
        this.components = new Map();
        this.modals = new Map();
        this.activeModals = [];
        this.notifications = [];
        this.maxNotifications = 5;
        
        // Initialize
        this.init();
    }
    
    // ===== INITIALIZATION =====
    init() {
        this.registerDefaultComponents();
        this.setupEventListeners();
        this.setupNotificationSystem();
    }
    
    setupEventListeners() {
        // Listen for custom events
        window.addEventListener('showModal', (event) => {
            this.showModal(event.detail);
        });
        
        window.addEventListener('hideModal', (event) => {
            this.hideModal(event.detail);
        });
        
        window.addEventListener('showNotification', (event) => {
            this.showNotification(event.detail);
        });
        
        window.addEventListener('showLoginModal', () => {
            this.showLoginModal();
        });
        
        // Handle escape key for modals
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                this.hideTopModal();
            }
        });
        
        // Handle modal backdrop clicks
        document.addEventListener('click', (event) => {
            if (event.target.classList.contains('modal-overlay')) {
                this.hideTopModal();
            }
        });
    }
    
    registerDefaultComponents() {
        // Register common components
        this.register('Button', this.createButton);
        this.register('Modal', this.createModal);
        this.register('Form', this.createForm);
        this.register('Notification', this.createNotification);
        this.register('Loading', this.createLoading);
        this.register('Card', this.createCard);
        this.register('Input', this.createInput);
        this.register('Select', this.createSelect);
        this.register('Checkbox', this.createCheckbox);
        this.register('Radio', this.createRadio);
        this.register('Textarea', this.createTextarea);
        this.register('Alert', this.createAlert);
        this.register('Progress', this.createProgress);
        this.register('Tabs', this.createTabs);
        this.register('Accordion', this.createAccordion);
        this.register('Tooltip', this.createTooltip);
        this.register('Dropdown', this.createDropdown);
    }
    
    // ===== COMPONENT REGISTRATION =====
    register(name, factory) {
        this.components.set(name, factory);
        MINGUS.utils.logDebug('Component registered', { name });
    }
    
    get(name) {
        return this.components.get(name);
    }
    
    create(name, config = {}) {
        const factory = this.get(name);
        if (!factory) {
            throw new Error(`Component '${name}' not found`);
        }
        return factory(config);
    }
    
    // ===== BUTTON COMPONENT =====
    createButton(config = {}) {
        const {
            text = 'Button',
            type = 'button',
            variant = 'primary',
            size = 'medium',
            disabled = false,
            loading = false,
            icon = null,
            onClick = null,
            className = '',
            ...attrs
        } = config;
        
        const button = MINGUS.utils.DOM.create('button', {
            type,
            className: `btn btn-${variant} btn-${size} ${className}`,
            disabled: disabled || loading,
            ...attrs
        });
        
        if (loading) {
            button.innerHTML = `
                <span class="spinner spinner-sm"></span>
                <span>Loading...</span>
            `;
        } else {
            if (icon) {
                button.innerHTML = `<i class="icon-${icon}"></i> ${text}`;
            } else {
                button.textContent = text;
            }
        }
        
        if (onClick) {
            MINGUS.utils.DOM.on(button, 'click', onClick);
        }
        
        return button;
    }
    
    // ===== MODAL COMPONENT =====
    createModal(config = {}) {
        const {
            id = 'modal-' + Date.now(),
            title = '',
            content = '',
            size = 'medium',
            closable = true,
            backdrop = true,
            onClose = null,
            onConfirm = null,
            confirmText = 'Confirm',
            cancelText = 'Cancel',
            showCancel = true,
            className = ''
        } = config;
        
        const modal = MINGUS.utils.DOM.create('div', {
            id,
            className: `modal-container ${className}`,
            'aria-hidden': 'true'
        });
        
        modal.innerHTML = `
            ${backdrop ? '<div class="modal-overlay" tabindex="-1"></div>' : ''}
            <div class="modal-content modal-${size}" role="dialog" aria-modal="true">
                ${closable ? '<button class="modal-close" aria-label="Close modal">×</button>' : ''}
                ${title ? `<div class="modal-header"><h2>${title}</h2></div>` : ''}
                <div class="modal-body">${content}</div>
                ${onConfirm ? `
                    <div class="modal-footer">
                        ${showCancel ? `<button class="btn btn-outline" data-action="cancel">${cancelText}</button>` : ''}
                        <button class="btn btn-primary" data-action="confirm">${confirmText}</button>
                    </div>
                ` : ''}
            </div>
        `;
        
        // Add event listeners
        if (onClose) {
            MINGUS.utils.DOM.on(modal, 'close', onClose);
        }
        
        if (onConfirm) {
            const confirmBtn = modal.querySelector('[data-action="confirm"]');
            const cancelBtn = modal.querySelector('[data-action="cancel"]');
            
            if (confirmBtn) {
                MINGUS.utils.DOM.on(confirmBtn, 'click', () => {
                    onConfirm();
                    this.hideModal(id);
                });
            }
            
            if (cancelBtn) {
                MINGUS.utils.DOM.on(cancelBtn, 'click', () => {
                    this.hideModal(id);
                });
            }
        }
        
        if (closable) {
            const closeBtn = modal.querySelector('.modal-close');
            if (closeBtn) {
                MINGUS.utils.DOM.on(closeBtn, 'click', () => {
                    this.hideModal(id);
                });
            }
        }
        
        return modal;
    }
    
    // ===== FORM COMPONENT =====
    createForm(config = {}) {
        const {
            id = 'form-' + Date.now(),
            action = '',
            method = 'POST',
            fields = [],
            onSubmit = null,
            onReset = null,
            className = '',
            ...attrs
        } = config;
        
        const form = MINGUS.utils.DOM.create('form', {
            id,
            action,
            method,
            className: `form ${className}`,
            novalidate: true,
            ...attrs
        });
        
        // Add fields
        fields.forEach(fieldConfig => {
            const field = this.createFormField(fieldConfig);
            form.appendChild(field);
        });
        
        // Add submit and reset buttons
        const buttonGroup = MINGUS.utils.DOM.create('div', {
            className: 'form-actions'
        });
        
        if (onSubmit) {
            const submitBtn = this.createButton({
                type: 'submit',
                text: 'Submit',
                variant: 'primary'
            });
            buttonGroup.appendChild(submitBtn);
        }
        
        if (onReset) {
            const resetBtn = this.createButton({
                type: 'reset',
                text: 'Reset',
                variant: 'outline'
            });
            buttonGroup.appendChild(resetBtn);
        }
        
        form.appendChild(buttonGroup);
        
        // Add event listeners
        if (onSubmit) {
            MINGUS.utils.DOM.on(form, 'submit', (event) => {
                event.preventDefault();
                const formData = this.getFormData(form);
                onSubmit(formData, form);
            });
        }
        
        if (onReset) {
            MINGUS.utils.DOM.on(form, 'reset', (event) => {
                event.preventDefault();
                onReset(form);
            });
        }
        
        return form;
    }
    
    createFormField(config = {}) {
        const {
            type = 'text',
            name,
            label,
            placeholder = '',
            value = '',
            required = false,
            validation = null,
            options = [],
            className = ''
        } = config;
        
        const fieldGroup = MINGUS.utils.DOM.create('div', {
            className: `form-group ${className}`
        });
        
        if (label) {
            const labelElement = MINGUS.utils.DOM.create('label', {
                for: name,
                className: 'form-label'
            }, [label]);
            fieldGroup.appendChild(labelElement);
        }
        
        let input;
        
        switch (type) {
            case 'select':
                input = this.createSelect({ name, value, options, required, placeholder });
                break;
            case 'textarea':
                input = this.createTextarea({ name, value, required, placeholder });
                break;
            case 'checkbox':
                input = this.createCheckbox({ name, value, required });
                break;
            case 'radio':
                input = this.createRadio({ name, value, required, options });
                break;
            default:
                input = this.createInput({ type, name, value, required, placeholder });
        }
        
        fieldGroup.appendChild(input);
        
        // Add validation
        if (validation) {
            this.addFieldValidation(input, validation);
        }
        
        return fieldGroup;
    }
    
    // ===== INPUT COMPONENTS =====
    createInput(config = {}) {
        const {
            type = 'text',
            name,
            value = '',
            placeholder = '',
            required = false,
            disabled = false,
            className = '',
            ...attrs
        } = config;
        
        return MINGUS.utils.DOM.create('input', {
            type,
            name,
            value,
            placeholder,
            required,
            disabled,
            className: `form-control ${className}`,
            ...attrs
        });
    }
    
    createSelect(config = {}) {
        const {
            name,
            value = '',
            options = [],
            required = false,
            placeholder = '',
            className = '',
            ...attrs
        } = config;
        
        const select = MINGUS.utils.DOM.create('select', {
            name,
            required,
            className: `form-control ${className}`,
            ...attrs
        });
        
        if (placeholder) {
            const placeholderOption = MINGUS.utils.DOM.create('option', {
                value: '',
                disabled: true,
                selected: !value
            }, [placeholder]);
            select.appendChild(placeholderOption);
        }
        
        options.forEach(option => {
            const optionElement = MINGUS.utils.DOM.create('option', {
                value: option.value,
                selected: option.value === value
            }, [option.label]);
            select.appendChild(optionElement);
        });
        
        return select;
    }
    
    createTextarea(config = {}) {
        const {
            name,
            value = '',
            placeholder = '',
            required = false,
            rows = 4,
            className = '',
            ...attrs
        } = config;
        
        return MINGUS.utils.DOM.create('textarea', {
            name,
            placeholder,
            required,
            rows,
            className: `form-control ${className}`,
            ...attrs
        }, [value]);
    }
    
    createCheckbox(config = {}) {
        const {
            name,
            value = false,
            required = false,
            className = '',
            ...attrs
        } = config;
        
        const wrapper = MINGUS.utils.DOM.create('div', {
            className: `checkbox-wrapper ${className}`
        });
        
        const checkbox = MINGUS.utils.DOM.create('input', {
            type: 'checkbox',
            name,
            checked: value,
            required,
            className: 'form-checkbox',
            ...attrs
        });
        
        wrapper.appendChild(checkbox);
        return wrapper;
    }
    
    createRadio(config = {}) {
        const {
            name,
            value = '',
            required = false,
            options = [],
            className = '',
            ...attrs
        } = config;
        
        const wrapper = MINGUS.utils.DOM.create('div', {
            className: `radio-group ${className}`
        });
        
        options.forEach(option => {
            const radioWrapper = MINGUS.utils.DOM.create('div', {
                className: 'radio-wrapper'
            });
            
            const radio = MINGUS.utils.DOM.create('input', {
                type: 'radio',
                name,
                value: option.value,
                checked: option.value === value,
                required,
                className: 'form-radio',
                ...attrs
            });
            
            const label = MINGUS.utils.DOM.create('label', {
                for: `${name}-${option.value}`
            }, [option.label]);
            
            radioWrapper.appendChild(radio);
            radioWrapper.appendChild(label);
            wrapper.appendChild(radioWrapper);
        });
        
        return wrapper;
    }
    
    // ===== NOTIFICATION COMPONENT =====
    createNotification(config = {}) {
        const {
            message,
            type = 'info',
            duration = 5000,
            closable = true,
            action = null,
            className = ''
        } = config;
        
        const notification = MINGUS.utils.DOM.create('div', {
            className: `notification notification-${type} ${className}`,
            role: 'alert'
        });
        
        notification.innerHTML = `
            <div class="notification-content">
                <span class="notification-message">${message}</span>
                ${action ? `<button class="notification-action">${action.label}</button>` : ''}
                ${closable ? '<button class="notification-close" aria-label="Close notification">×</button>' : ''}
            </div>
        `;
        
        // Add event listeners
        if (closable) {
            const closeBtn = notification.querySelector('.notification-close');
            MINGUS.utils.DOM.on(closeBtn, 'click', () => {
                this.removeNotification(notification);
            });
        }
        
        if (action && action.handler) {
            const actionBtn = notification.querySelector('.notification-action');
            MINGUS.utils.DOM.on(actionBtn, 'click', () => {
                action.handler();
                this.removeNotification(notification);
            });
        }
        
        // Auto-remove after duration
        if (duration > 0) {
            setTimeout(() => {
                this.removeNotification(notification);
            }, duration);
        }
        
        return notification;
    }
    
    // ===== LOADING COMPONENT =====
    createLoading(config = {}) {
        const {
            text = 'Loading...',
            size = 'medium',
            className = ''
        } = config;
        
        const loading = MINGUS.utils.DOM.create('div', {
            className: `loading loading-${size} ${className}`
        });
        
        loading.innerHTML = `
            <div class="spinner"></div>
            ${text ? `<span class="loading-text">${text}</span>` : ''}
        `;
        
        return loading;
    }
    
    // ===== CARD COMPONENT =====
    createCard(config = {}) {
        const {
            title = '',
            content = '',
            footer = '',
            className = '',
            ...attrs
        } = config;
        
        const card = MINGUS.utils.DOM.create('div', {
            className: `card ${className}`,
            ...attrs
        });
        
        if (title) {
            const header = MINGUS.utils.DOM.create('div', {
                className: 'card-header'
            }, [title]);
            card.appendChild(header);
        }
        
        const body = MINGUS.utils.DOM.create('div', {
            className: 'card-body'
        }, [content]);
        card.appendChild(body);
        
        if (footer) {
            const footerElement = MINGUS.utils.DOM.create('div', {
                className: 'card-footer'
            }, [footer]);
            card.appendChild(footerElement);
        }
        
        return card;
    }
    
    // ===== ALERT COMPONENT =====
    createAlert(config = {}) {
        const {
            message,
            type = 'info',
            closable = true,
            className = ''
        } = config;
        
        const alert = MINGUS.utils.DOM.create('div', {
            className: `alert alert-${type} ${className}`,
            role: 'alert'
        });
        
        alert.innerHTML = `
            <span class="alert-message">${message}</span>
            ${closable ? '<button class="alert-close" aria-label="Close alert">×</button>' : ''}
        `;
        
        if (closable) {
            const closeBtn = alert.querySelector('.alert-close');
            MINGUS.utils.DOM.on(closeBtn, 'click', () => {
                alert.remove();
            });
        }
        
        return alert;
    }
    
    // ===== PROGRESS COMPONENT =====
    createProgress(config = {}) {
        const {
            value = 0,
            max = 100,
            text = '',
            className = ''
        } = config;
        
        const progress = MINGUS.utils.DOM.create('div', {
            className: `progress ${className}`
        });
        
        const percentage = Math.min((value / max) * 100, 100);
        
        progress.innerHTML = `
            <div class="progress-bar" style="width: ${percentage}%" role="progressbar" aria-valuenow="${value}" aria-valuemin="0" aria-valuemax="${max}">
                ${text ? `<span class="progress-text">${text}</span>` : ''}
            </div>
        `;
        
        return progress;
    }
    
    // ===== TABS COMPONENT =====
    createTabs(config = {}) {
        const {
            tabs = [],
            activeTab = 0,
            className = ''
        } = config;
        
        const tabsContainer = MINGUS.utils.DOM.create('div', {
            className: `tabs ${className}`
        });
        
        const tabList = MINGUS.utils.DOM.create('div', {
            className: 'tab-list',
            role: 'tablist'
        });
        
        const tabPanels = MINGUS.utils.DOM.create('div', {
            className: 'tab-panels'
        });
        
        tabs.forEach((tab, index) => {
            const tabButton = MINGUS.utils.DOM.create('button', {
                className: `tab-button ${index === activeTab ? 'active' : ''}`,
                role: 'tab',
                'aria-selected': index === activeTab,
                'aria-controls': `tab-panel-${index}`
            }, [tab.label]);
            
            const tabPanel = MINGUS.utils.DOM.create('div', {
                id: `tab-panel-${index}`,
                className: `tab-panel ${index === activeTab ? 'active' : ''}`,
                role: 'tabpanel',
                'aria-labelledby': `tab-${index}`
            }, [tab.content]);
            
            MINGUS.utils.DOM.on(tabButton, 'click', () => {
                this.switchTab(tabsContainer, index);
            });
            
            tabList.appendChild(tabButton);
            tabPanels.appendChild(tabPanel);
        });
        
        tabsContainer.appendChild(tabList);
        tabsContainer.appendChild(tabPanels);
        
        return tabsContainer;
    }
    
    switchTab(tabsContainer, activeIndex) {
        const tabButtons = tabsContainer.querySelectorAll('.tab-button');
        const tabPanels = tabsContainer.querySelectorAll('.tab-panel');
        
        tabButtons.forEach((button, index) => {
            MINGUS.utils.DOM.toggleClass(button, 'active', index === activeIndex);
            button.setAttribute('aria-selected', index === activeIndex);
        });
        
        tabPanels.forEach((panel, index) => {
            MINGUS.utils.DOM.toggleClass(panel, 'active', index === activeIndex);
        });
    }
    
    // ===== ACCORDION COMPONENT =====
    createAccordion(config = {}) {
        const {
            items = [],
            multiple = false,
            className = ''
        } = config;
        
        const accordion = MINGUS.utils.DOM.create('div', {
            className: `accordion ${className}`
        });
        
        items.forEach((item, index) => {
            const accordionItem = MINGUS.utils.DOM.create('div', {
                className: 'accordion-item'
            });
            
            const header = MINGUS.utils.DOM.create('button', {
                className: 'accordion-header',
                'aria-expanded': 'false',
                'aria-controls': `accordion-content-${index}`
            }, [item.title]);
            
            const content = MINGUS.utils.DOM.create('div', {
                id: `accordion-content-${index}`,
                className: 'accordion-content'
            }, [item.content]);
            
            MINGUS.utils.DOM.on(header, 'click', () => {
                this.toggleAccordionItem(accordionItem, multiple);
            });
            
            accordionItem.appendChild(header);
            accordionItem.appendChild(content);
            accordion.appendChild(accordionItem);
        });
        
        return accordion;
    }
    
    toggleAccordionItem(item, multiple) {
        const header = item.querySelector('.accordion-header');
        const content = item.querySelector('.accordion-content');
        const isExpanded = header.getAttribute('aria-expanded') === 'true';
        
        if (!multiple) {
            // Close other items
            const otherItems = item.parentElement.querySelectorAll('.accordion-item');
            otherItems.forEach(otherItem => {
                if (otherItem !== item) {
                    const otherHeader = otherItem.querySelector('.accordion-header');
                    const otherContent = otherItem.querySelector('.accordion-content');
                    otherHeader.setAttribute('aria-expanded', 'false');
                    MINGUS.utils.DOM.removeClass(otherContent, 'active');
                }
            });
        }
        
        // Toggle current item
        header.setAttribute('aria-expanded', !isExpanded);
        MINGUS.utils.DOM.toggleClass(content, 'active', !isExpanded);
    }
    
    // ===== TOOLTIP COMPONENT =====
    createTooltip(config = {}) {
        const {
            content,
            position = 'top',
            trigger = 'hover',
            className = ''
        } = config;
        
        const tooltip = MINGUS.utils.DOM.create('div', {
            className: `tooltip tooltip-${position} ${className}`,
            role: 'tooltip'
        }, [content]);
        
        return tooltip;
    }
    
    // ===== DROPDOWN COMPONENT =====
    createDropdown(config = {}) {
        const {
            trigger,
            items = [],
            position = 'bottom',
            className = ''
        } = config;
        
        const dropdown = MINGUS.utils.DOM.create('div', {
            className: `dropdown dropdown-${position} ${className}`
        });
        
        const triggerElement = MINGUS.utils.DOM.create('button', {
            className: 'dropdown-trigger',
            'aria-expanded': 'false',
            'aria-haspopup': 'true'
        }, [trigger]);
        
        const menu = MINGUS.utils.DOM.create('div', {
            className: 'dropdown-menu',
            role: 'menu'
        });
        
        items.forEach(item => {
            const menuItem = MINGUS.utils.DOM.create('button', {
                className: 'dropdown-item',
                role: 'menuitem'
            }, [item.label]);
            
            if (item.handler) {
                MINGUS.utils.DOM.on(menuItem, 'click', () => {
                    item.handler();
                    this.hideDropdown(dropdown);
                });
            }
            
            menu.appendChild(menuItem);
        });
        
        MINGUS.utils.DOM.on(triggerElement, 'click', () => {
            this.toggleDropdown(dropdown);
        });
        
        dropdown.appendChild(triggerElement);
        dropdown.appendChild(menu);
        
        return dropdown;
    }
    
    toggleDropdown(dropdown) {
        const trigger = dropdown.querySelector('.dropdown-trigger');
        const menu = dropdown.querySelector('.dropdown-menu');
        const isExpanded = trigger.getAttribute('aria-expanded') === 'true';
        
        trigger.setAttribute('aria-expanded', !isExpanded);
        MINGUS.utils.DOM.toggleClass(menu, 'active', !isExpanded);
    }
    
    hideDropdown(dropdown) {
        const trigger = dropdown.querySelector('.dropdown-trigger');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        trigger.setAttribute('aria-expanded', 'false');
        MINGUS.utils.DOM.removeClass(menu, 'active');
    }
    
    // ===== MODAL MANAGEMENT =====
    showModal(config) {
        const modal = this.createModal(config);
        document.body.appendChild(modal);
        
        // Add to active modals
        this.activeModals.push(modal);
        
        // Show modal
        MINGUS.utils.DOM.addClass(modal, 'active');
        modal.setAttribute('aria-hidden', 'false');
        
        // Focus first focusable element
        const focusable = modal.querySelector('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if (focusable) {
            focusable.focus();
        }
        
        // Prevent body scroll
        document.body.style.overflow = 'hidden';
        
        return modal;
    }
    
    hideModal(id) {
        const modal = document.getElementById(id);
        if (modal) {
            MINGUS.utils.DOM.removeClass(modal, 'active');
            modal.setAttribute('aria-hidden', 'true');
            
            // Remove from active modals
            const index = this.activeModals.indexOf(modal);
            if (index > -1) {
                this.activeModals.splice(index, 1);
            }
            
            // Remove from DOM after animation
            setTimeout(() => {
                modal.remove();
                
                // Restore body scroll if no more modals
                if (this.activeModals.length === 0) {
                    document.body.style.overflow = '';
                }
            }, 300);
        }
    }
    
    hideTopModal() {
        if (this.activeModals.length > 0) {
            const topModal = this.activeModals[this.activeModals.length - 1];
            const id = topModal.id;
            this.hideModal(id);
        }
    }
    
    // ===== NOTIFICATION SYSTEM =====
    setupNotificationSystem() {
        // Create notification container
        const container = MINGUS.utils.DOM.create('div', {
            id: 'notification-container',
            className: 'notification-container'
        });
        
        document.body.appendChild(container);
    }
    
    showNotification(config) {
        const notification = this.createNotification(config);
        const container = document.getElementById('notification-container');
        
        if (container) {
            container.appendChild(notification);
            this.notifications.push(notification);
            
            // Limit notifications
            if (this.notifications.length > this.maxNotifications) {
                const oldNotification = this.notifications.shift();
                oldNotification.remove();
            }
            
            // Animate in
            MINGUS.utils.Animation.fadeIn(notification);
        }
    }
    
    removeNotification(notification) {
        const index = this.notifications.indexOf(notification);
        if (index > -1) {
            this.notifications.splice(index, 1);
        }
        
        MINGUS.utils.Animation.fadeOut(notification, 300);
    }
    
    // ===== FORM UTILITIES =====
    getFormData(form) {
        const formData = new FormData(form);
        const data = {};
        
        for (const [key, value] of formData.entries()) {
            if (data[key]) {
                if (Array.isArray(data[key])) {
                    data[key].push(value);
                } else {
                    data[key] = [data[key], value];
                }
            } else {
                data[key] = value;
            }
        }
        
        return data;
    }
    
    addFieldValidation(field, validation) {
        const input = field.querySelector('input, select, textarea');
        if (!input) return;
        
        const validate = () => {
            const value = input.value;
            const isValid = validation(value);
            
            MINGUS.utils.DOM.toggleClass(field, 'has-error', !isValid);
            
            // Show/hide error message
            let errorElement = field.querySelector('.form-error');
            if (!isValid && !errorElement) {
                errorElement = MINGUS.utils.DOM.create('div', {
                    className: 'form-error'
                }, [validation.message || 'Invalid input']);
                field.appendChild(errorElement);
            } else if (isValid && errorElement) {
                errorElement.remove();
            }
        };
        
        MINGUS.utils.DOM.on(input, 'blur', validate);
        MINGUS.utils.DOM.on(input, 'input', MINGUS.utils.Performance.debounce(validate, 300));
    }
    
    // ===== LOGIN MODAL =====
    showLoginModal() {
        const loginForm = this.createForm({
            fields: [
                { type: 'email', name: 'email', label: 'Email', required: true },
                { type: 'password', name: 'password', label: 'Password', required: true }
            ],
            onSubmit: async (data) => {
                try {
                    await MINGUS.auth.login(data);
                    this.hideModal('login-modal');
                } catch (error) {
                    // Error handling is done in auth service
                }
            }
        });
        
        this.showModal({
            id: 'login-modal',
            title: 'Login',
            content: loginForm.outerHTML,
            size: 'small'
        });
    }
}

// ===== EXPORT COMPONENT SERVICE =====
const components = new ComponentService();

// Make available globally
window.MINGUS = window.MINGUS || {};
window.MINGUS.components = components;

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComponentService;
}
