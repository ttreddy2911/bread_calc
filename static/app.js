// ---- State ----
let authToken = localStorage.getItem('jwt_token') || null;
let currentUsername = localStorage.getItem('username') || null;
let editingCalcId = null;

// ---- Boot ----
if (authToken) showDashboard();
else showAuthScreen();

// ---- Auth Screen ----
function showAuthScreen() {
    document.getElementById('auth-screen').style.display = 'flex';
    document.getElementById('dashboard').style.display = 'none';
}

function showDashboard() {
    document.getElementById('auth-screen').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    document.getElementById('logged-in-user').textContent = `Hi, ${currentUsername}`;
    loadCalculations();
}

function switchTab(tab) {
    document.getElementById('login-form').style.display = tab === 'login' ? 'block' : 'none';
    document.getElementById('register-form').style.display = tab === 'register' ? 'block' : 'none';
    document.getElementById('tab-login').className = 'tab' + (tab === 'login' ? ' active' : '');
    document.getElementById('tab-register').className = 'tab' + (tab === 'register' ? ' active' : '');
}

async function handleLogin(e) {
    e.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;
    const errEl = document.getElementById('login-error');

    try {
        const body = new URLSearchParams({ username, password });
        const res = await fetch('/api/login', { method: 'POST', body });
        const data = await res.json();

        if (!res.ok) throw new Error(data.detail || 'Login failed');

        authToken = data.access_token;
        currentUsername = username;
        localStorage.setItem('jwt_token', authToken);
        localStorage.setItem('username', username);
        showDashboard();
    } catch (err) {
        errEl.textContent = err.message;
        errEl.className = 'message error';
    }
}

async function handleRegister(e) {
    e.preventDefault();
    const username = document.getElementById('reg-username').value;
    const email = document.getElementById('reg-email').value;
    const password = document.getElementById('reg-password').value;
    const errEl = document.getElementById('register-error');

    try {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Registration failed');

        errEl.textContent = 'Account created! Please log in.';
        errEl.className = 'message success';
        setTimeout(() => switchTab('login'), 1500);
    } catch (err) {
        errEl.textContent = err.message;
        errEl.className = 'message error';
    }
}

function logout() {
    authToken = null;
    currentUsername = null;
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('username');
    showAuthScreen();
}

// ---- Authenticated API Helper ----
async function apiFetch(url, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (authToken) headers['Authorization'] = `Bearer ${authToken}`;
    const res = await fetch(url, { ...options, headers });

    if (res.status === 401) {
        logout();
        throw new Error('Session expired. Please login again.');
    }
    return res;
}

// ---- Calculations ----
async function loadCalculations() {
    try {
        const res = await apiFetch('/api/calculations');
        const calcs = await res.json();
        renderCalculations(calcs);
    } catch (err) {
        showMessage(document.getElementById('list-message'), err.message, true);
    }
}

function getOpSymbol(op) {
    return { add: '+', subtract: '−', multiply: '×', divide: '÷' }[op] || op;
}

function renderCalculations(calcs) {
    const tbody = document.getElementById('calc-tbody');
    tbody.innerHTML = '';
    if (calcs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="color:var(--text-muted);text-align:center;padding:2rem;">No calculations yet. Add one!</td></tr>';
        return;
    }
    calcs.forEach(c => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>#${c.id}</td>
            <td>${c.operand1}</td>
            <td>${getOpSymbol(c.operation)}</td>
            <td>${c.operand2}</td>
            <td style="font-weight:600;color:var(--primary)">${c.result}</td>
            <td class="actions">
                <button class="btn secondary small" onclick="startEdit(${c.id})">Edit</button>
                <button class="btn danger small" onclick="deleteCalc(${c.id})">Delete</button>
            </td>`;
        tbody.appendChild(tr);
    });
}

async function handleCalcSubmit(e) {
    e.preventDefault();
    const op = document.getElementById('operation').value;
    const a = parseFloat(document.getElementById('operand1').value);
    const b = parseFloat(document.getElementById('operand2').value);
    const msgEl = document.getElementById('form-message');

    try {
        let res;
        if (editingCalcId) {
            res = await apiFetch(`/api/calculations/${editingCalcId}`, {
                method: 'PUT',
                body: JSON.stringify({ operation: op, operand1: a, operand2: b })
            });
        } else {
            res = await apiFetch('/api/calculations', {
                method: 'POST',
                body: JSON.stringify({ operation: op, operand1: a, operand2: b })
            });
        }
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Error');

        showMessage(msgEl, editingCalcId ? 'Calculation updated!' : 'Calculation added!');
        resetForm();
        loadCalculations();
    } catch (err) {
        showMessage(msgEl, err.message, true);
    }
}

async function startEdit(id) {
    try {
        const res = await apiFetch(`/api/calculations/${id}`);
        const calc = await res.json();
        document.getElementById('calc-id').value = calc.id;
        document.getElementById('operand1').value = calc.operand1;
        document.getElementById('operand2').value = calc.operand2;
        document.getElementById('operation').value = calc.operation;
        editingCalcId = calc.id;
        document.getElementById('form-title').textContent = 'Edit Calculation';
        document.getElementById('submit-btn').textContent = 'Update';
        document.getElementById('cancel-btn').style.display = 'block';
    } catch (err) { alert(err.message); }
}

async function deleteCalc(id) {
    if (!confirm('Delete this calculation?')) return;
    try {
        await apiFetch(`/api/calculations/${id}`, { method: 'DELETE' });
        loadCalculations();
    } catch (err) { alert(err.message); }
}

function resetForm() {
    document.getElementById('calc-form').reset();
    editingCalcId = null;
    document.getElementById('calc-id').value = '';
    document.getElementById('form-title').textContent = 'New Calculation';
    document.getElementById('submit-btn').textContent = 'Calculate';
    document.getElementById('cancel-btn').style.display = 'none';
}

function showMessage(el, msg, isError = false) {
    el.textContent = msg;
    el.className = `message ${isError ? 'error' : 'success'}`;
    setTimeout(() => { el.className = 'message'; }, 5000);
}
