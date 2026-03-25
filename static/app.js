const equipmentForm = document.getElementById("equipment-form");
const maintenanceForm = document.getElementById("maintenance-form");
const equipmentTable = document.getElementById("equipment-table");
const maintenanceTable = document.getElementById("maintenance-table");
const maintenanceEquipment = document.getElementById("maintenance-equipment");
const equipmentSubmit = document.getElementById("equipment-submit");
const equipmentCancel = document.getElementById("equipment-cancel");
const searchInput = document.getElementById("search-input");
const statusFilter = document.getElementById("status-filter");
const typeFilter = document.getElementById("type-filter");
const dashboardCards = document.getElementById("dashboard-cards");
const dueSoonList = document.getElementById("due-soon-list");

async function api(path, options = {}) {
    const response = await fetch(path, {
        headers: {
            "Content-Type": "application/json",
            ...(options.headers || {}),
        },
        ...options,
    });

    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed");
    }
    return data;
}

function renderDashboard(summary, dueSoon) {
    dashboardCards.innerHTML = `
        <div class="stat-card"><span>Total equipment</span><strong>${summary.totalEquipment}</strong></div>
        <div class="stat-card"><span>Service due soon</span><strong>${summary.serviceDueSoon}</strong></div>
        <div class="stat-card"><span>In service</span><strong>${summary.inService}</strong></div>
        <div class="stat-card"><span>Maintenance records</span><strong>${summary.maintenanceRecords}</strong></div>
    `;

    dueSoonList.innerHTML = dueSoon.length
        ? dueSoon.map((item) => `<li>${item.name} (${item.serial_number}) due ${item.next_service_date}</li>`).join("")
        : "<li>No urgent service reminders</li>";
}

function renderEquipment(items) {
    equipmentTable.innerHTML = items.map((item) => `
        <tr>
            <td>${item.name}</td>
            <td>${item.equipment_type}</td>
            <td>${item.status}</td>
            <td>${item.serial_number}</td>
            <td>${item.location}</td>
            <td>${item.next_service_date || "-"}</td>
            <td>
                <div class="action-row">
                    <button class="ghost" onclick="editEquipment(${item.id})">Edit</button>
                    <button class="ghost" onclick="prefillMaintenance(${item.id})">Maintain</button>
                    <button class="danger" onclick="deleteEquipment(${item.id})">Delete</button>
                </div>
            </td>
        </tr>
    `).join("");

    maintenanceEquipment.innerHTML = `
        <option value="">Select equipment</option>
        ${items.map((item) => `<option value="${item.id}">${item.name} (${item.serial_number})</option>`).join("")}
    `;
}

function renderMaintenance(records) {
    maintenanceTable.innerHTML = records.map((record) => `
        <tr>
            <td>${record.equipment_name || record.equipment_id}</td>
            <td>${record.serial_number || "-"}</td>
            <td>${record.description}</td>
            <td>${record.service_date}</td>
            <td>${record.technician}</td>
            <td>${record.outcome}</td>
            <td><button class="danger" onclick="deleteMaintenance(${record.id})">Delete</button></td>
        </tr>
    `).join("");
}

async function loadDashboard() {
    const data = await api("/api/dashboard");
    renderDashboard(data.summary, data.dueSoon);
}

async function loadEquipment() {
    const params = new URLSearchParams({
        search: searchInput.value.trim(),
        status: statusFilter.value,
        type: typeFilter.value.trim(),
    });
    const items = await api(`/api/equipment?${params.toString()}`);
    renderEquipment(items);
}

async function loadMaintenance() {
    const records = await api("/api/maintenance");
    renderMaintenance(records);
}

equipmentForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(equipmentForm);
    const payload = Object.fromEntries(formData.entries());
    const equipmentId = payload.id;
    delete payload.id;

    try {
        await api(equipmentId ? `/api/equipment/${equipmentId}` : "/api/equipment", {
            method: equipmentId ? "PUT" : "POST",
            body: JSON.stringify(payload),
        });
        resetEquipmentForm();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
});

maintenanceForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const formData = new FormData(maintenanceForm);
    const payload = Object.fromEntries(formData.entries());

    try {
        await api("/api/maintenance", {
            method: "POST",
            body: JSON.stringify(payload),
        });
        maintenanceForm.reset();
        await refreshAll();
    } catch (error) {
        alert(error.message);
    }
});

searchInput.addEventListener("input", loadEquipment);
statusFilter.addEventListener("change", loadEquipment);
typeFilter.addEventListener("input", loadEquipment);

async function refreshAll() {
    await Promise.all([loadDashboard(), loadEquipment(), loadMaintenance()]);
}

function resetEquipmentForm() {
    equipmentForm.reset();
    equipmentForm.elements.id.value = "";
    equipmentSubmit.textContent = "Save Equipment";
}

window.prefillMaintenance = function prefillMaintenance(equipmentId) {
    maintenanceEquipment.value = String(equipmentId);
    maintenanceForm.scrollIntoView({ behavior: "smooth", block: "start" });
};

window.editEquipment = async function editEquipment(equipmentId) {
    const items = await api("/api/equipment");
    const item = items.find((entry) => entry.id === equipmentId);
    if (!item) {
        alert("Equipment record not found");
        return;
    }

    Object.entries(item).forEach(([key, value]) => {
        if (equipmentForm.elements[key]) {
            equipmentForm.elements[key].value = value || "";
        }
    });
    equipmentSubmit.textContent = "Update Equipment";
    equipmentForm.scrollIntoView({ behavior: "smooth", block: "start" });
};

window.deleteEquipment = async function deleteEquipment(equipmentId) {
    if (!window.confirm("Delete this equipment and its maintenance history?")) {
        return;
    }
    await api(`/api/equipment/${equipmentId}`, { method: "DELETE" });
    resetEquipmentForm();
    await refreshAll();
};

window.deleteMaintenance = async function deleteMaintenance(recordId) {
    if (!window.confirm("Delete this maintenance record?")) {
        return;
    }
    await api(`/api/maintenance/${recordId}`, { method: "DELETE" });
    await refreshAll();
};

equipmentCancel.addEventListener("click", resetEquipmentForm);

refreshAll().catch((error) => {
    alert(error.message);
});
