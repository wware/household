"use strict";

// API client
const api = {
    async get(endpoint) {
        const response = await fetch(endpoint);
        if (!response.ok)
            throw new Error(`API error: ${response.statusText}`);
        return response.json();
    },
    async post(endpoint, data) {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!response.ok)
            throw new Error(`API error: ${response.statusText}`);
        return response.json();
    },
    async put(endpoint, data) {
        const response = await fetch(endpoint, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });
        if (!response.ok)
            throw new Error(`API error: ${response.statusText}`);
        return response.json();
    },
    async delete(endpoint) {
        const response = await fetch(endpoint, { method: "DELETE" });
        if (!response.ok)
            throw new Error(`API error: ${response.statusText}`);
        return response.ok;
    },
};

// State management
const state = {
    tasks: [],
    appointments: [],
    grocery: [],
    items: [], // Available grocery items catalog
    stores: [], // Available stores
    storeFilter: null, // Currently selected store filter
    weather: null,
    templates: [],
    currentUser: 1, // Default to user 1
    lastUpdate: new Date(),
};

// Functional helpers
const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
    });
};

const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
        hour: "2-digit",
        minute: "2-digit",
    });
};

// FullCalendar instance
let calendar = null;

// Render functions
const renderTasks = () => {
    const list = document.getElementById("tasks-list");
    if (!list) return;

    list.innerHTML = state.tasks
        .map((task) => `
            <div class="item ${task.completed ? "completed" : ""}">
                <div class="item-content">
                    <div class="item-title">${escapeHtml(task.title)}</div>
                    <div class="item-meta">
                        ${escapeHtml(task.category || "other")}${task.due_date ? ` • Due: ${formatDate(task.due_date)}` : ""}
                    </div>
                </div>
                <div class="item-actions">
                    <button class="btn-complete" onclick="toggleTask(${task.id}, ${!task.completed})">
                        ${task.completed ? "Undo" : "Done"}
                    </button>
                    <button class="btn-delete" onclick="deleteTask(${task.id})">Delete</button>
                </div>
            </div>
        `)
        .join("");
};

const renderAppointments = () => {
    const list = document.getElementById("appointments-list");
    if (!list) return;

    list.innerHTML = state.appointments
        .map((apt) => `
            <div class="item">
                <div class="item-content">
                    <div class="item-title">${escapeHtml(apt.title)}</div>
                    <div class="item-meta">
                        ${escapeHtml(apt.type || "other")} • ${formatDateTime(apt.date)}${apt.notes ? ` • ${escapeHtml(apt.notes)}` : ""}${apt.patient_name ? ` • Patient: ${escapeHtml(apt.patient_name)}` : ""}
                    </div>
                </div>
                <div class="item-actions">
                    <button class="btn-delete" onclick="deleteAppointment(${apt.id})">Delete</button>
                </div>
            </div>
        `)
        .join("");
};

const renderGrocery = () => {
    const list = document.getElementById("grocery-list");
    if (!list) return;

    // Filter grocery items based on selected store
    let filteredGrocery = state.grocery;
    if (state.storeFilter) {
        filteredGrocery = state.grocery.filter(gi => {
            // Show item if it's available at the selected store OR has no stores assigned
            const itemStores = gi.item?.stores || [];
            return itemStores.length === 0 ||
                   itemStores.some(s => s.id === state.storeFilter);
        });
    }

    if (filteredGrocery.length === 0) {
        const filterMsg = state.storeFilter
            ? "No items for this store."
            : "Your grocery list is empty.";
        list.innerHTML = `<p style="color: #7f8c8d; padding: 20px;">${filterMsg}</p>`;
        return;
    }

    list.innerHTML = filteredGrocery
        .map((gi) => {
            const itemName = gi.item?.name || "Unknown";
            const quantity = gi.quantity || gi.int_quantity || "";
            const section = gi.item?.section || "";
            const stores = gi.item?.stores?.map(s => s.name).join(", ") || "Any store";

            return `
                <div class="item ${gi.purchased ? "completed" : ""}">
                    <div class="item-content">
                        <div class="item-title">${escapeHtml(itemName)}</div>
                        <div class="item-meta">
                            ${quantity ? escapeHtml(quantity.toString()) : "no quantity"}
                            ${section ? ` • ${escapeHtml(section)}` : ""}
                            ${stores ? ` • ${escapeHtml(stores)}` : ""}
                        </div>
                    </div>
                    <div class="item-actions">
                        <button class="btn-complete" onclick="toggleGrocery(${gi.id}, ${!gi.purchased})">
                            ${gi.purchased ? "Undo" : "Bought"}
                        </button>
                        <button class="btn-delete" onclick="deleteGrocery(${gi.id})">Delete</button>
                    </div>
                </div>
            `;
        })
        .join("");
};

const renderWeather = () => {
    const container = document.getElementById("weather-container");
    if (!container) return;

    if (!state.weather) {
        container.innerHTML = "<p>Weather information not available yet.</p>";
        return;
    }

    const weather = state.weather;
    container.innerHTML = `
        <div class="weather-header">
            <h3>${escapeHtml(weather.location)}</h3>
            <p class="weather-updated">Updated: ${new Date(weather.updated).toLocaleTimeString()}</p>
        </div>
        <div class="weather-periods">
            ${weather.periods
                .map((period) => `
                    <div class="weather-period">
                        <div class="period-name">${escapeHtml(period.name)}</div>
                        <div class="period-temp">${period.temperature}°${period.temperatureUnit}</div>
                        <div class="period-forecast">${escapeHtml(period.shortForecast)}</div>
                        <div class="period-wind">${escapeHtml(period.windDirection)} ${escapeHtml(period.windSpeed)}</div>
                    </div>
                `)
                .join("")}
        </div>
    `;
};

const renderTemplates = () => {
    const select = document.getElementById("template-select");
    if (!select) return;

    const selectedValue = select.value;
    select.innerHTML = '<option value="">-- Select a template --</option>';

    state.templates.forEach((template) => {
        const option = document.createElement("option");
        option.value = template.id.toString();
        option.textContent = `${template.name} (${template.items ? template.items.length : 0} items)`;
        select.appendChild(option);
    });

    if (selectedValue && Array.from(select.options).some(o => o.value === selectedValue)) {
        select.value = selectedValue;
    }
};

const renderItemsDropdown = () => {
    const select = document.getElementById("grocery-item-select");
    if (!select) return;

    const selectedValue = select.value;
    select.innerHTML = '<option value="">-- Select an item --</option>';

    // Sort items alphabetically
    const sortedItems = [...state.items].sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    sortedItems.forEach((item) => {
        const option = document.createElement("option");
        option.value = item.id.toString();
        option.textContent = item.name;
        // Store default quantity as data attribute
        option.dataset.defaultQuantity = item.default_quantity || "";
        select.appendChild(option);
    });

    if (selectedValue && Array.from(select.options).some(o => o.value === selectedValue)) {
        select.value = selectedValue;
    }
};

const renderStoreFilter = () => {
    const select = document.getElementById("store-filter");
    if (!select) return;

    select.innerHTML = '<option value="">All Stores</option>';

    // Sort stores alphabetically
    const sortedStores = [...state.stores].sort((a, b) =>
        a.name.localeCompare(b.name)
    );

    sortedStores.forEach((store) => {
        const option = document.createElement("option");
        option.value = store.id.toString();
        option.textContent = store.name;
        select.appendChild(option);
    });

    // Restore filter state
    if (state.storeFilter) {
        select.value = state.storeFilter.toString();
    }
};

const initializeCalendar = () => {
    const calendarEl = document.getElementById("calendar");
    if (!calendarEl || calendar) return;

    const events = state.appointments.map((apt) => ({
        id: apt.id.toString(),
        title: apt.title,
        start: apt.date,
        extendedProps: {
            type: apt.type,
            notes: apt.notes,
        },
    }));

    calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: "dayGridMonth",
        headerToolbar: {
            left: "prev,next today",
            center: "title",
            right: "dayGridMonth,timeGridWeek,timeGridDay",
        },
        events: events,
        eventClick: (info) => {
            const notes = info.event.extendedProps.notes
                ? `\n\nNotes: ${info.event.extendedProps.notes}`
                : "";
            alert(`${info.event.title}\nType: ${info.event.extendedProps.type}${notes}`);
        },
    });

    calendar.render();
};

const updateCalendarEvents = () => {
    if (!calendar) return;

    calendar.getEvents().forEach((event) => event.remove());

    state.appointments.forEach((apt) => {
        calendar.addEvent({
            id: apt.id.toString(),
            title: apt.title,
            start: apt.date,
            extendedProps: {
                type: apt.type,
                notes: apt.notes,
            },
        });
    });
};

const updateLastUpdate = () => {
    const now = new Date();
    state.lastUpdate = now;
    const el = document.getElementById("last-update");
    if (el) {
        el.textContent = now.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
        });
    }
};

const escapeHtml = (text) => {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
};

// Data loading
const loadData = async () => {
    try {
        state.tasks = await api.get("/api/tasks");
        state.appointments = await api.get("/api/appointments");

        // Load items catalog and stores
        state.items = await api.get("/api/items");
        state.stores = await api.get("/api/stores");

        // Grocery items require user_id parameter
        state.grocery = await api.get(`/api/grocery-items?user_id=${state.currentUser}`);

        // Templates endpoint
        try {
            state.templates = await api.get(`/api/grocery-templates?user_id=${state.currentUser}`);
        } catch (e) {
            console.log("Templates not available:", e);
            state.templates = [];
        }

        // Weather might not be implemented yet
        try {
            state.weather = await api.get("/api/weather");
        } catch (e) {
            console.log("Weather not available:", e);
            state.weather = null;
        }

        renderTasks();
        renderAppointments();
        renderGrocery();
        renderWeather();
        renderTemplates();
        renderItemsDropdown();
        renderStoreFilter();

        if (!calendar) {
            initializeCalendar();
        } else {
            updateCalendarEvents();
        }

        updateLastUpdate();
    } catch (error) {
        console.error("Failed to load data:", error);
    }
};

// Event handlers - attach to window for HTML onclick handlers
const toggleTask = async (id, completed) => {
    try {
        await api.put(`/api/tasks/${id}`, { completed });
        await loadData();
    } catch (error) {
        console.error("Failed to toggle task:", error);
    }
};

const deleteTask = async (id) => {
    if (confirm("Delete this task?")) {
        try {
            await api.delete(`/api/tasks/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete task:", error);
        }
    }
};

const deleteAppointment = async (id) => {
    if (confirm("Delete this appointment?")) {
        try {
            await api.delete(`/api/appointments/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete appointment:", error);
        }
    }
};

const toggleGrocery = async (id, purchased) => {
    try {
        await api.put(`/api/grocery-items/${id}`, { purchased });
        await loadData();
    } catch (error) {
        console.error("Failed to toggle grocery item:", error);
    }
};

const deleteGrocery = async (id) => {
    if (confirm("Delete this item?")) {
        try {
            await api.delete(`/api/grocery-items/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete grocery item:", error);
        }
    }
};

// Attach to window for HTML onclick handlers
const windowAny = window;
windowAny.toggleTask = toggleTask;
windowAny.deleteTask = deleteTask;
windowAny.deleteAppointment = deleteAppointment;
windowAny.toggleGrocery = toggleGrocery;
windowAny.deleteGrocery = deleteGrocery;

// Navigation
const setupNavigation = () => {
    const sections = ["tasks", "appointments", "calendar", "grocery", "weather"];

    sections.forEach((section) => {
        const btn = document.getElementById(`nav-${section}`);
        if (btn) {
            btn.addEventListener("click", () => {
                document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
                document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));

                btn.classList.add("active");
                const sectionEl = document.getElementById(`${section}-section`);
                if (sectionEl) sectionEl.classList.add("active");
            });
        }
    });
};

// Form submissions
const setupForms = () => {
    const toggleTemplatesBtn = document.getElementById("toggle-templates-btn");
    if (toggleTemplatesBtn) {
        toggleTemplatesBtn.addEventListener("click", () => {
            const panel = document.getElementById("templates-panel");
            const isHidden = panel.style.display === "none";
            panel.style.display = isHidden ? "block" : "none";
            toggleTemplatesBtn.textContent = isHidden ? "Hide Templates" : "Show Templates";
        });
    }

    const addTaskBtn = document.getElementById("add-task-btn");
    if (addTaskBtn) {
        addTaskBtn.addEventListener("click", async () => {
            const input = document.getElementById("task-input");
            const category = document.getElementById("task-category");

            if (input?.value.trim()) {
                try {
                    await api.post("/api/tasks", {
                        title: input.value,
                        category: category?.value || "other",
                        assigned_to: state.currentUser,
                    });
                    input.value = "";
                    category.value = "";
                    await loadData();
                } catch (error) {
                    console.error("Failed to add task:", error);
                }
            }
        });
    }

    const addAppointmentBtn = document.getElementById("add-appointment-btn");
    if (addAppointmentBtn) {
        addAppointmentBtn.addEventListener("click", async () => {
            const input = document.getElementById("appointment-input");
            const date = document.getElementById("appointment-date");
            const type = document.getElementById("appointment-type");

            if (input?.value.trim() && date?.value) {
                try {
                    await api.post("/api/appointments", {
                        title: input.value,
                        date: date.value,
                        type: type?.value || "other",
                        created_by: state.currentUser,
                    });
                    input.value = "";
                    date.value = "";
                    type.value = "";
                    await loadData();
                } catch (error) {
                    console.error("Failed to add appointment:", error);
                }
            }
        });
    }

    const addGroceryBtn = document.getElementById("add-grocery-btn");
    if (addGroceryBtn) {
        addGroceryBtn.addEventListener("click", async () => {
            const itemSelect = document.getElementById("grocery-item-select");
            const quantityInput = document.getElementById("grocery-quantity");

            const itemId = itemSelect?.value;
            if (!itemId) {
                alert("Please select an item from the dropdown");
                return;
            }

            try {
                // Get the selected option to access default quantity
                const selectedOption = itemSelect.options[itemSelect.selectedIndex];
                const defaultQuantity = selectedOption.dataset.defaultQuantity || null;
                const quantity = quantityInput?.value.trim() || defaultQuantity;

                await api.post("/api/grocery-items", {
                    item_id: parseInt(itemId),
                    quantity: quantity,
                    user_id: state.currentUser,
                });

                // Reset form
                itemSelect.value = "";
                quantityInput.value = "";

                await loadData();
            } catch (error) {
                console.error("Failed to add grocery item:", error);
                alert("Failed to add grocery item.");
            }
        });
    }

    // Auto-fill quantity when item is selected
    const itemSelect = document.getElementById("grocery-item-select");
    const quantityInput = document.getElementById("grocery-quantity");
    if (itemSelect && quantityInput) {
        itemSelect.addEventListener("change", () => {
            if (itemSelect.value) {
                const selectedOption = itemSelect.options[itemSelect.selectedIndex];
                const defaultQuantity = selectedOption.dataset.defaultQuantity;
                if (defaultQuantity) {
                    quantityInput.value = defaultQuantity;
                    quantityInput.placeholder = defaultQuantity;
                }
            } else {
                quantityInput.value = "";
                quantityInput.placeholder = "Quantity (optional)";
            }
        });
    }

    const applyTemplateBtn = document.getElementById("apply-template-btn");
    if (applyTemplateBtn) {
        applyTemplateBtn.addEventListener("click", async () => {
            const templateSelect = document.getElementById("template-select");
            const templateId = templateSelect?.value;

            if (!templateId) {
                alert("Please select a template");
                return;
            }

            try {
                await fetch(`/api/grocery-templates/${templateId}/apply?user_id=${state.currentUser}`, {
                    method: "POST",
                });
                templateSelect.value = "";
                await loadData();
            } catch (error) {
                console.error("Failed to apply template:", error);
            }
        });
    }

    const saveTemplateBtn = document.getElementById("save-template-btn");
    if (saveTemplateBtn) {
        saveTemplateBtn.addEventListener("click", async () => {
            const templateNameInput = document.getElementById("template-name-input");
            const templateName = templateNameInput?.value?.trim();

            if (!templateName) {
                alert("Please enter a template name");
                return;
            }

            if (state.grocery.length === 0) {
                alert("Your grocery list is empty. Add items before saving as a template.");
                return;
            }

            try {
                await api.post("/api/grocery-templates", {
                    name: templateName,
                    created_by: state.currentUser,
                    items: state.grocery.map((gi) => ({
                        item_id: gi.item_id,
                        quantity: gi.quantity,
                        int_quantity: gi.int_quantity,
                    })),
                });
                templateNameInput.value = "";
                alert("Template saved successfully!");
                await loadData();
            } catch (error) {
                console.error("Failed to save template:", error);
                alert("Failed to save template. Check the console for details.");
            }
        });
    }
};

// Settings dropdown
const setupSettings = () => {
    const settingsIcon = document.getElementById("settings-icon");
    const settingsDropdown = document.getElementById("settings-dropdown");

    if (settingsIcon && settingsDropdown) {
        settingsIcon.addEventListener("click", (e) => {
            e.stopPropagation();
            settingsDropdown.classList.toggle("active");
        });

        // Close dropdown when clicking outside
        document.addEventListener("click", () => {
            settingsDropdown.classList.remove("active");
        });

        // Prevent dropdown from closing when clicking inside it
        settingsDropdown.addEventListener("click", (e) => {
            e.stopPropagation();
        });
    }
};

// Store filter
const setupStoreFilter = () => {
    const storeFilter = document.getElementById("store-filter");
    if (storeFilter) {
        storeFilter.addEventListener("change", () => {
            const selectedValue = storeFilter.value;
            state.storeFilter = selectedValue ? parseInt(selectedValue) : null;
            renderGrocery();
        });
    }
};

// Initialize
document.addEventListener("DOMContentLoaded", () => {
    loadData();
    setupNavigation();
    setupForms();
    setupSettings();
    setupStoreFilter();

    // Poll for updates every 10 seconds when tab is active
    document.addEventListener("visibilitychange", () => {
        if (!document.hidden) {
            loadData();
        }
    });

    setInterval(() => {
        if (!document.hidden) {
            loadData();
        }
    }, 10000);
});
