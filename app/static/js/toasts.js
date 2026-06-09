(function() {
    'use strict';

    var ICONS = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-circle-fill',
        info: 'bi-info-circle-fill'
    };

    function normalizeType(type) {
        if (type === 'error') return 'danger';
        return ICONS[type] ? type : 'info';
    }

    function dismissToast(toast) {
        if (!toast || toast.classList.contains('toast-out')) return;
        toast.classList.add('toast-out');
        setTimeout(function() {
            toast.remove();
            var stack = document.getElementById('toastStack');
            if (stack && !stack.children.length) {
                stack.remove();
            }
        }, 320);
    }

    function bindToast(toast, autoDelay) {
        var closeBtn = toast.querySelector('.toast-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', function() {
                dismissToast(toast);
            });
        }
        if (autoDelay !== false) {
            setTimeout(function() {
                dismissToast(toast);
            }, autoDelay || 5000);
        }
    }

    function getOrCreateStack() {
        var stack = document.getElementById('toastStack');
        if (!stack) {
            stack = document.createElement('div');
            stack.id = 'toastStack';
            stack.className = 'toast-stack';
            if (document.querySelector('.ft-mobile-step, .fixed-action-bar')) {
                stack.classList.add('toast-stack-above-bar');
            }
            stack.setAttribute('aria-live', 'polite');
            document.body.appendChild(stack);
        }
        return stack;
    }

    window.showToast = function(message, type) {
        type = normalizeType(type || 'success');
        var stack = getOrCreateStack();
        var toast = document.createElement('div');
        toast.className = 'toast-item toast-item-' + type;
        toast.setAttribute('role', 'alert');
        toast.innerHTML =
            '<i class="bi ' + ICONS[type] + ' toast-icon" aria-hidden="true"></i>' +
            '<span class="toast-msg"></span>' +
            '<button type="button" class="toast-close" aria-label="Chiudi">' +
                '<i class="bi bi-x-lg" aria-hidden="true"></i>' +
            '</button>';
        toast.querySelector('.toast-msg').textContent = message;
        stack.appendChild(toast);
        var delay = 5000 + (stack.querySelectorAll('.toast-item').length - 1) * 400;
        bindToast(toast, delay);
    };

    window.initFlashToasts = function() {
        document.querySelectorAll('#toastStack .toast-item').forEach(function(toast, index) {
            bindToast(toast, 5000 + index * 400);
        });
    };

    document.addEventListener('DOMContentLoaded', window.initFlashToasts);
})();
