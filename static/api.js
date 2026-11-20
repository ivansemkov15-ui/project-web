export async function api(path, { method = 'GET', data, token = sessionStorage.getItem('access_token') } = {}) {
    const headers = { Accept: 'application/json' };
    if (token) {
        headers.Authorization = `Bearer ${token}`;
    }
    if (data !== undefined) {
        headers['Content-Type'] = 'application/json';
    }

    let response;
    try {
        response = await fetch(path, { method, headers, body: JSON.stringify(data) });
    } catch {
        throw new Error('Не удалось связаться с сервером.');
    }

    const result = response.status === 204 ? null : await response.json().catch(() => null);
    if (!response.ok) {
        if (response.status === 401 && token && path !== '/api/auth/refresh') {
            throw new Error('Срок действия токена истёк. Обновите его в профиле.');
        }
        throw new Error(result?.error || `Ошибка запроса (${response.status}).`);
    }
    return result;
}

export function hasSession() {
    return Boolean(sessionStorage.getItem('access_token'));
}

export function saveTokens(tokens) {
    if (!tokens?.access_token || !tokens.refresh_token) {
        throw new Error('Сервер не вернул токены для входа.');
    }
    sessionStorage.setItem('access_token', tokens.access_token);
    sessionStorage.setItem('refresh_token', tokens.refresh_token);
}

export async function refreshAccessToken() {
    const token = sessionStorage.getItem('refresh_token');
    if (!token) {
        throw new Error('Войдите в справочник снова.');
    }
    const result = await api('/api/auth/refresh', { method: 'POST', token });
    if (!result?.access_token) {
        throw new Error('Сервер не вернул новый токен.');
    }
    sessionStorage.setItem('access_token', result.access_token);
}

export function bindLogout() {
    document.getElementById('logout').addEventListener('click', () => {
        sessionStorage.removeItem('access_token');
        sessionStorage.removeItem('refresh_token');
        window.location.replace('/');
    });
}

export function showMessage(text, type = 'danger') {
    const message = document.getElementById('message');
    message.textContent = text;
    message.className = `alert alert-${type}`;
    message.hidden = !text;
}
