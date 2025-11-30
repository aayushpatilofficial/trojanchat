/**
 * TrojanChat - Theme Toggle System
 * Location: static/js/theme.js
 * 
 * Handles light/dark mode switching with persistence
 */

document.addEventListener('DOMContentLoaded', function() {
    initializeTheme();
});

/**
 * Initialize theme on page load
 */
function initializeTheme() {
    const savedTheme = localStorage.getItem('trojan-theme') || 'light';
    applyTheme(savedTheme);
    updateThemeButton();
}

/**
 * Apply theme to document
 * @param {string} theme - 'light' or 'dark'
 */
function applyTheme(theme) {
    const html = document.documentElement;

    if (theme === 'dark') {
        html.setAttribute('data-theme', 'dark');
    } else {
        html.removeAttribute('data-theme');
    }

    // Save preference
    localStorage.setItem('trojan-theme', theme);
}

/**
 * Toggle between light and dark themes
 */
function toggleTheme() {
    const html = document.documentElement;
    const isDark = html.getAttribute('data-theme') === 'dark';
    const newTheme = isDark ? 'light' : 'dark';

    applyTheme(newTheme);
    updateThemeButton(newTheme);
}

/**
 * Update theme button icon
 * @param {string} theme - optional theme to display
 */
function updateThemeButton(theme) {
    const themeBtns = document.querySelectorAll('#themeBtn');
    const html = document.documentElement;
    const currentTheme = theme || (html.getAttribute('data-theme') === 'dark' ? 'dark' : 'light');

    themeBtns.forEach(btn => {
        const icon = btn.querySelector('.theme-icon');
        if (icon) {
            icon.textContent = currentTheme === 'dark' ? '☀️' : '🌙';
        }
    });
}

/**
 * System preference detection (optional enhancement)
 */
function detectSystemPreference() {
    if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
        return 'dark';
    }
    return 'light';
}

/**
 * Listen for system theme changes (optional)
 */
if (window.matchMedia) {
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', (e) => {
        // Optional: Auto-apply system preference changes
        // Uncomment to enable:
        // applyTheme(e.matches ? 'dark' : 'light');
        // updateThemeButton();
    });
}