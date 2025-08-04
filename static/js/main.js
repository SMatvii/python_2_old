
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    
    setTimeout(function() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
});

function initializeApp() {
    initializeTooltips();
    
    initializeLocalStorage();
    
    initializeFormValidation();
    
    initializeTheme();
}

function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeLocalStorage() {
    if (!localStorage.getItem('tasks')) {
        localStorage.setItem('tasks', JSON.stringify([]));
    }
    
    if (!localStorage.getItem('userSettings')) {
        localStorage.setItem('userSettings', JSON.stringify({
            theme: 'light',
            notifications: true,
            language: 'uk'
        }));
    }
}

function initializeFormValidation() {
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms)
        .forEach(function (form) {
            form.addEventListener('submit', function (event) {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
}

function initializeTheme() {
    const savedTheme = localStorage.getItem('theme') || 'light';
    applyTheme(savedTheme);
}

function applyTheme(theme) {
    const body = document.body;
    if (theme === 'dark') {
        body.classList.add('dark-theme');
    } else {
        body.classList.remove('dark-theme');
    }
    localStorage.setItem('theme', theme);
}

function saveTaskToLocalStorage(task) {
    const tasks = JSON.parse(localStorage.getItem('tasks') || '[]');
    tasks.push(task);
    localStorage.setItem('tasks', JSON.stringify(tasks));
}

function removeTaskFromLocalStorage(taskId) {
    const tasks = JSON.parse(localStorage.getItem('tasks') || '[]');
    const updatedTasks = tasks.filter(task => task.id !== taskId);
    localStorage.setItem('tasks', JSON.stringify(updatedTasks));
}

function getTasksFromLocalStorage() {
    return JSON.parse(localStorage.getItem('tasks') || '[]');
}

function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 3000);
}

async function makeAPIRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        showNotification('Помилка при виконанні запиту', 'danger');
        throw error;
    }
}

function formatTime(time) {
    return time.substring(0, 5);
}

function getCurrentDay() {
    const days = ['Неділя', 'Понеділок', 'Вівторок', 'Середа', 'Четвер', 'П\'ятниця', 'Субота'];
    const today = new Date();
    return days[today.getDay()];
}

function highlightCurrentDay() {
    const currentDay = getCurrentDay();
    const dayCards = document.querySelectorAll('.card-header');
    
    dayCards.forEach(card => {
        if (card.textContent.trim() === currentDay) {
            card.classList.add('bg-warning', 'text-dark');
            card.innerHTML += ' <span class="badge bg-dark">Сьогодні</span>';
        }
    });
}

function updateWeatherWidget(weatherData) {
    const weatherWidget = document.getElementById('weather-widget');
    if (!weatherWidget || !weatherData) return;
    
    const temperature = Math.round(weatherData.main.temp);
    const description = weatherData.weather[0].description;
    const icon = weatherData.weather[0].icon;
    
    weatherWidget.innerHTML = `
        <div class="d-flex align-items-center">
            <img src="http://openweathermap.org/img/w/${icon}.png" alt="${description}" class="me-2">
            <div>
                <div class="fw-bold">${temperature}°C</div>
                <small class="text-muted">${description}</small>
            </div>
        </div>
    `;
}

function getUserSettings() {
    return JSON.parse(localStorage.getItem('userSettings') || '{}');
}

function saveUserSettings(settings) {
    const currentSettings = getUserSettings();
    const updatedSettings = { ...currentSettings, ...settings };
    localStorage.setItem('userSettings', JSON.stringify(updatedSettings));
}

function validateEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

function validatePassword(password) {
    return password.length >= 6;
}

function validateForm(formData) {
    const errors = [];
    
    if (formData.email && !validateEmail(formData.email)) {
        errors.push('Невірний формат email');
    }
    
    if (formData.password && !validatePassword(formData.password)) {
        errors.push('Пароль повинен містити мінімум 6 символів');
    }
    
    return errors;
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('uk-UA', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
}

function isDateOverdue(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date < today;
}

function isDateToday(dateString) {
    const date = new Date(dateString);
    const today = new Date();
    return date.toDateString() === today.toDateString();
}

function calculateProgress(completed, total) {
    if (total === 0) return 0;
    return Math.round((completed / total) * 100);
}

function updateProgressBar(progressBar, completed, total) {
    const progress = calculateProgress(completed, total);
    progressBar.style.width = progress + '%';
    progressBar.setAttribute('aria-valuenow', progress);
    progressBar.textContent = progress + '%';
}

function fadeIn(element, duration = 300) {
    element.style.opacity = 0;
    element.style.display = 'block';
    
    let start = null;
    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        element.style.opacity = progress / duration;
        
        if (progress < duration) {
            requestAnimationFrame(animate);
        } else {
            element.style.opacity = 1;
        }
    }
    
    requestAnimationFrame(animate);
}

function fadeOut(element, duration = 300) {
    let start = null;
    function animate(timestamp) {
        if (!start) start = timestamp;
        const progress = timestamp - start;
        element.style.opacity = 1 - (progress / duration);
        
        if (progress < duration) {
            requestAnimationFrame(animate);
        } else {
            element.style.opacity = 0;
            element.style.display = 'none';
        }
    }
    
    requestAnimationFrame(animate);
}

function setCookie(name, value, days = 7) {
    const expires = new Date();
    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
    document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/`;
}

function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) === ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}

function deleteCookie(name) {
    document.cookie = `${name}=; Path=/; Expires=Thu, 01 Jan 1970 00:00:01 GMT;`;
}

window.AppUtils = {
    showNotification,
    makeAPIRequest,
    formatTime,
    getCurrentDay,
    validateEmail,
    validatePassword,
    validateForm,
    formatDate,
    isDateOverdue,
    isDateToday,
    calculateProgress,
    updateProgressBar,
    fadeIn,
    fadeOut,
    setCookie,
    getCookie,
    deleteCookie,
    saveTaskToLocalStorage,
    removeTaskFromLocalStorage,
    getTasksFromLocalStorage,
    getUserSettings,
    saveUserSettings
};

document.addEventListener('DOMContentLoaded', function() {
    setTimeout(highlightCurrentDay, 100);
});
