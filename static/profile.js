import { api, bindLogout, hasSession, refreshAccessToken, showMessage } from './api.js';

const refreshButton = document.getElementById('refresh-token');

async function loadProfile() {
    const user = await api('/api/users/me');
    document.getElementById('profile-name').textContent = user.user_name;
    document.getElementById('profile-id').textContent = user.id;
}

if (hasSession()) {
    document.getElementById('profile-area').hidden = false;
    bindLogout();
    loadProfile().catch(error => showMessage(error.message));
} else {
    window.location.replace('/');
}

refreshButton.addEventListener('click', async () => {
    refreshButton.disabled = true;
    showMessage('');
    try {
        await refreshAccessToken();
        await loadProfile();
        showMessage('Токен обновлён.', 'success');
    } catch (error) {
        showMessage(error.message);
    } finally {
        refreshButton.disabled = false;
    }
});
