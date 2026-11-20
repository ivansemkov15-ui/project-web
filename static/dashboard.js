import { api, bindLogout, hasSession, showMessage } from './api.js';

const total = document.getElementById('contact-total');

async function loadStatistics() {
    const stats = await api('/api/stats');
    total.textContent = `Всего контактов: ${stats.total_contacts}`;
    if (stats.total_contacts === 0) {
        document.getElementById('empty-chart').hidden = false;
        return;
    }
    if (!window.Chart) {
        showMessage('Библиотека Chart.js не загрузилась.');
        return;
    }

    const labels = stats.groups.map(group => group.name);
    const counts = stats.groups.map(group => group.count);
    if (stats.without_group > 0) {
        labels.push('Без группы');
        counts.push(stats.without_group);
    }

    const chartBox = document.getElementById('chart-box');
    chartBox.style.height = `${Math.max(240, labels.length * 32 + 48)}px`;
    chartBox.hidden = false;
    const canvas = document.getElementById('group-chart');
    canvas.setAttribute('aria-label', labels.map((label, index) => `${label}: ${counts[index]}`).join(', '));

    new window.Chart(canvas, {
        type: 'bar',
        data: {
            labels,
            datasets: [{ label: 'Контакты', data: counts, backgroundColor: '#0d6efd' }]
        },
        options: {
            indexAxis: 'y',
            maintainAspectRatio: false,
            plugins: { legend: { display: false } },
            scales: { x: { beginAtZero: true, ticks: { precision: 0 } } }
        }
    });
}

if (hasSession()) {
    document.getElementById('dashboard-area').hidden = false;
    bindLogout();
    loadStatistics().catch(error => {
        total.textContent = '';
        showMessage(error.message);
    });
} else {
    window.location.replace('/');
}
