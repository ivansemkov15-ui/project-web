import { api, hasSession, showMessage } from './api.js';

const contactForm = document.getElementById('contact-form');
const contactName = document.getElementById('contact-name');
const contactPhone = document.getElementById('contact-phone');
const contactGroup = document.getElementById('contact-group');
const filterGroup = document.getElementById('filter-group');
const groupName = document.getElementById('group-name');
const previousPage = document.getElementById('previous-page');
const nextPage = document.getElementById('next-page');
const pageStatus = document.getElementById('page-status');

let page = 1;
let editingId = null;
let saving = false;
let contactsRequest = 0;
let groupsRequest = 0;

function openContactForm(contact) {
    if (saving) return;
    editingId = contact?.id ?? null;
    document.getElementById('contact-form-title').textContent = contact ? 'Изменить контакт' : 'Новый контакт';
    contactName.value = contact?.name ?? '';
    contactPhone.value = contact?.phone ?? '';
    const groupId = String(contact?.group_id ?? '');
    if (groupId && !Array.from(contactGroup.options).some(option => option.value === groupId)) {
        contactGroup.add(new Option(contact.group_name, groupId));
    }
    contactGroup.value = groupId;
    contactForm.hidden = false;
    contactName.focus();
}

function closeContactForm() {
    editingId = null;
    contactForm.hidden = true;
}

function actionButton(label, style) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `btn ${style} btn-sm`;
    button.textContent = label;
    return button;
}

function renderContacts(contacts) {
    const rows = document.getElementById('contact-rows');
    rows.replaceChildren();

    for (const contact of contacts) {
        const row = rows.insertRow();
        row.insertCell().textContent = contact.name;
        row.insertCell().textContent = contact.phone;
        row.insertCell().textContent = contact.group_name ?? 'Без группы';

        const edit = actionButton('Изменить', 'btn-outline-secondary');
        edit.classList.add('me-2');
        edit.addEventListener('click', () => openContactForm(contact));

        const remove = actionButton('Удалить', 'btn-outline-danger');
        remove.addEventListener('click', () => {
            if (saving || !window.confirm(`Удалить контакт «${contact.name}»?`)) return;
            runAction(remove, async () => {
                await api(`/api/contacts/${contact.id}`, { method: 'DELETE' });
                if (editingId === contact.id) closeContactForm();
                await loadContacts();
            });
        });

        const actions = row.insertCell();
        actions.className = 'text-nowrap';
        actions.append(edit, remove);
    }
}

async function loadContacts(requestedPage = page) {
    const request = ++contactsRequest;
    const params = new URLSearchParams({
        search: document.getElementById('search').value.trim(),
        sort_by: document.getElementById('sort-by').value,
        order: document.getElementById('sort-order').value,
        page: requestedPage,
        per_page: 10
    });
    if (filterGroup.value) params.set('group_id', filterGroup.value);

    try {
        const result = await api(`/api/contacts?${params}`);
        if (request !== contactsRequest) return;
        const lastPage = Math.max(result.pages, 1);
        if (requestedPage > lastPage) {
            await loadContacts(lastPage);
            return;
        }

        page = result.page;
        renderContacts(result.items);
        previousPage.disabled = page <= 1;
        nextPage.disabled = page >= lastPage;
        pageStatus.textContent = result.total
            ? `Страница ${page} из ${lastPage} · Всего ${result.total}`
            : 'Контакты не найдены.';
    } catch (error) {
        if (request === contactsRequest) {
            showMessage(error.message);
            pageStatus.textContent = 'Не удалось загрузить контакты.';
        }
    }
}

function fillGroupSelect(select, groups, placeholder) {
    const selected = select.value;
    const options = groups.map(group => new Option(group.name, group.id));
    select.replaceChildren(new Option(placeholder, ''), ...options);
    if (options.some(option => option.value === selected)) select.value = selected;
}

async function loadGroups() {
    const request = ++groupsRequest;
    const groups = await api('/api/groups');
    if (request !== groupsRequest) return;

    fillGroupSelect(contactGroup, groups, 'Без группы');
    fillGroupSelect(filterGroup, groups, 'Все группы');
    document.getElementById('no-groups').hidden = groups.length > 0;
    const list = document.getElementById('group-list');
    list.replaceChildren();

    for (const group of groups) {
        const item = document.createElement('li');
        item.className = 'list-group-item d-flex align-items-center justify-content-between gap-2';
        const remove = actionButton('Удалить', 'btn-outline-danger');
        remove.addEventListener('click', () => {
            if (saving || !window.confirm(`Удалить группу «${group.name}»? Контакты из неё сохранятся.`)) return;
            runAction(remove, async () => {
                await api(`/api/groups/${group.id}`, { method: 'DELETE' });
                await loadGroups();
                await loadContacts(1);
            });
        });
        item.append(group.name, remove);
        list.append(item);
    }
}

async function runAction(button, action) {
    if (saving) return;
    saving = true;
    button.disabled = true;
    showMessage('');
    try {
        await action();
    } catch (error) {
        showMessage(error.message);
    } finally {
        saving = false;
        button.disabled = false;
    }
}

document.getElementById('add-contact').addEventListener('click', () => openContactForm());
document.getElementById('cancel-contact').addEventListener('click', () => {
    if (!saving) closeContactForm();
});

contactForm.addEventListener('submit', event => {
    event.preventDefault();
    const id = editingId;
    const data = {
        name: contactName.value.trim(),
        phone: contactPhone.value.trim(),
        group_id: contactGroup.value ? Number(contactGroup.value) : null
    };

    runAction(document.getElementById('save-contact'), async () => {
        if (!data.name || !data.phone) throw new Error('Введите имя и телефон.');
        if (id === null) {
            await api('/api/contacts', { method: 'POST', data });
        } else {
            await api(`/api/contacts/${id}`, { method: 'PATCH', data });
        }
        closeContactForm();
        showMessage(id === null ? 'Контакт добавлен.' : 'Контакт обновлён.', 'success');
        await loadContacts();
    });
});

document.getElementById('group-form').addEventListener('submit', event => {
    event.preventDefault();
    const name = groupName.value.trim();
    runAction(document.getElementById('add-group'), async () => {
        if (!name) throw new Error('Введите название группы.');
        await api('/api/groups', { method: 'POST', data: { name } });
        groupName.value = '';
        await loadGroups();
    });
});

document.getElementById('filter-form').addEventListener('submit', event => {
    event.preventDefault();
    showMessage('');
    loadContacts(1);
});
previousPage.addEventListener('click', () => loadContacts(page - 1));
nextPage.addEventListener('click', () => loadContacts(page + 1));

if (hasSession()) {
    document.getElementById('groups-area').hidden = false;
    loadContacts();
    loadGroups().catch(error => showMessage(error.message));
}
