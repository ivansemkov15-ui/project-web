import { api, bindLogout, hasSession, saveTokens, showMessage } from './api.js';

const loginForm = document.getElementById('login-form');
const registerForm = document.getElementById('register-form');
const signedIn = hasSession();

document.getElementById('auth-area').hidden = signedIn;
document.getElementById('contacts-area').hidden = !signedIn;
document.getElementById('account-nav').hidden = !signedIn;
bindLogout();

async function submitAuth(event, action) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector('button[type="submit"]');
    const data = {
        user_name: form.elements.user_name.value.trim(),
        password: form.elements.password.value
    };

    button.disabled = true;
    showMessage('');
    try {
        if (!data.user_name) {
            throw new Error('Введите имя пользователя.');
        }
        const result = await api(`/api/auth/${action}`, { method: 'POST', data, token: null });
        if (action === 'login') {
            saveTokens(result);
            window.location.replace('/');
        } else {
            form.reset();
            loginForm.elements.user_name.value = data.user_name;
            loginForm.elements.password.focus();
            showMessage('Аккаунт создан. Теперь можно войти.', 'success');
        }
    } catch (error) {
        showMessage(error.message);
    } finally {
        button.disabled = false;
    }
}

loginForm.addEventListener('submit', event => submitAuth(event, 'login'));
registerForm.addEventListener('submit', event => submitAuth(event, 'register'));
