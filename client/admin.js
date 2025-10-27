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
    stores: [],
    items: [],
    providers: [],
    templates: [],
    currentUser: 1, // Default to user 1
};

// Utility functions
const escapeHtml = (text) => {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
};

// ============================================================================
// STORES
// ============================================================================

const renderStores = () => {
    const list = document.getElementById("stores-list");
    if (!list) return;

    if (state.stores.length === 0) {
        list.innerHTML = '<p style="color: #7f8c8d; padding: 20px;">No stores yet. Add one above!</p>';
        return;
    }

    list.innerHTML = state.stores
        .map((store) => `
            <div class="item">
                <div class="item-header">
                    <div class="item-title">${escapeHtml(store.name)}</div>
                    <div class="item-actions">
                        <button class="btn-danger" onclick="deleteStore(${store.id})">Delete</button>
                    </div>
                </div>
            </div>
        `)
        .join("");
};

const deleteStore = async (id) => {
    if (confirm("Delete this store? This will remove it from all items.")) {
        try {
            await api.delete(`/api/stores/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete store:", error);
            alert("Failed to delete store. It may be in use.");
        }
    }
};

// Attach to window
window.deleteStore = deleteStore;

// ============================================================================
// ITEMS
// ============================================================================

const renderItemStoresCheckboxes = () => {
    const container = document.getElementById("item-stores-checkboxes");
    if (!container) return;

    if (state.stores.length === 0) {
        container.innerHTML = '<p style="color: #7f8c8d;">Add stores first to assign them to items.</p>';
        return;
    }

    container.innerHTML = state.stores
        .map((store) => `
            <label>
                <input type="checkbox" name="store-checkbox" value="${store.id}">
                ${escapeHtml(store.name)}
            </label>
        `)
        .join("");
};

const renderItems = () => {
    const list = document.getElementById("items-list");
    if (!list) return;

    if (state.items.length === 0) {
        list.innerHTML = '<p style="color: #7f8c8d; padding: 20px;">No items yet. Add one above!</p>';
        return;
    }

    list.innerHTML = state.items
        .map((item) => {
            const stores = item.stores?.map(s => s.name).join(", ") || "No stores";
            const quantity = item.default_quantity || "none";
            const section = item.section || "none";

            return `
                <div class="item">
                    <div class="item-header">
                        <div>
                            <div class="item-title">${escapeHtml(item.name)}</div>
                            <div class="item-meta">
                                Default quantity: ${escapeHtml(quantity)} •
                                Section: ${escapeHtml(section)} •
                                ${item.quantity_is_int ? "Integer only" : "Any quantity"}
                            </div>
                            <div class="item-meta">Stores: ${escapeHtml(stores)}</div>
                        </div>
                        <div class="item-actions">
                            <button class="btn-danger" onclick="deleteItem(${item.id})">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        })
        .join("");
};

const deleteItem = async (id) => {
    if (confirm("Delete this item? This will remove it from all lists and templates.")) {
        try {
            await api.delete(`/api/items/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete item:", error);
            alert("Failed to delete item. It may be in use.");
        }
    }
};

// Attach to window
window.deleteItem = deleteItem;

// ============================================================================
// PROVIDERS
// ============================================================================

const renderProviders = () => {
    const list = document.getElementById("providers-list");
    if (!list) return;

    if (state.providers.length === 0) {
        list.innerHTML = '<p style="color: #7f8c8d; padding: 20px;">No providers yet. Add one above!</p>';
        return;
    }

    list.innerHTML = state.providers
        .map((provider) => {
            const phone = provider.phone || "N/A";
            const email = provider.email || "N/A";
            const website = provider.website || "N/A";
            const address = provider.address || "N/A";

            return `
                <div class="item">
                    <div class="item-header">
                        <div>
                            <div class="item-title">${escapeHtml(provider.name)}</div>
                            <div class="item-meta">Phone: ${escapeHtml(phone)}</div>
                            <div class="item-meta">Email: ${escapeHtml(email)}</div>
                            ${provider.website ? `<div class="item-meta">Website: <a href="${escapeHtml(website)}" target="_blank">${escapeHtml(website)}</a></div>` : ''}
                            ${provider.address ? `<div class="item-meta">Address: ${escapeHtml(address)}</div>` : ''}
                            ${provider.info ? `<div class="item-meta">Info: ${escapeHtml(provider.info)}</div>` : ''}
                        </div>
                        <div class="item-actions">
                            <button class="btn-danger" onclick="deleteProvider(${provider.id})">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        })
        .join("");
};

const deleteProvider = async (id) => {
    if (confirm("Delete this provider?")) {
        try {
            await api.delete(`/api/providers/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete provider:", error);
            alert("Failed to delete provider. It may be in use.");
        }
    }
};

// Attach to window
window.deleteProvider = deleteProvider;

// ============================================================================
// TEMPLATES
// ============================================================================

const renderTemplates = () => {
    const list = document.getElementById("templates-list");
    if (!list) return;

    if (state.templates.length === 0) {
        list.innerHTML = '<p style="color: #7f8c8d; padding: 20px;">No templates yet. Create one from the main grocery list.</p>';
        return;
    }

    list.innerHTML = state.templates
        .map((template) => {
            const itemCount = template.items?.length || 0;

            return `
                <div class="item">
                    <div class="item-header">
                        <div>
                            <div class="item-title">${escapeHtml(template.name)}</div>
                            <div class="item-meta">${itemCount} items</div>
                        </div>
                        <div class="item-actions">
                            <button class="btn-danger" onclick="deleteTemplate(${template.id})">Delete</button>
                        </div>
                    </div>
                </div>
            `;
        })
        .join("");
};

const deleteTemplate = async (id) => {
    if (confirm("Delete this template?")) {
        try {
            await api.delete(`/api/grocery-templates/${id}`);
            await loadData();
        } catch (error) {
            console.error("Failed to delete template:", error);
            alert("Failed to delete template.");
        }
    }
};

// Attach to window
window.deleteTemplate = deleteTemplate;

// ============================================================================
// DATA LOADING
// ============================================================================

const loadData = async () => {
    try {
        state.stores = await api.get("/api/stores");
        state.items = await api.get("/api/items");
        state.providers = await api.get("/api/providers");

        try {
            state.templates = await api.get(`/api/grocery-templates?user_id=${state.currentUser}`);
        } catch (e) {
            console.log("Templates not available:", e);
            state.templates = [];
        }

        renderStores();
        renderItems();
        renderProviders();
        renderTemplates();
        renderItemStoresCheckboxes();
    } catch (error) {
        console.error("Failed to load data:", error);
    }
};

// ============================================================================
// NAVIGATION
// ============================================================================

const setupNavigation = () => {
    const sections = ["stores", "items", "providers", "templates"];

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

// ============================================================================
// FORM SUBMISSIONS
// ============================================================================

const setupForms = () => {
    // Store form
    const storeForm = document.getElementById("store-form");
    if (storeForm) {
        storeForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            const nameInput = document.getElementById("store-name");

            try {
                await api.post("/api/stores", {
                    name: nameInput.value.trim(),
                });
                nameInput.value = "";
                await loadData();
            } catch (error) {
                console.error("Failed to add store:", error);
                alert("Failed to add store.");
            }
        });
    }

    // Item form
    const itemForm = document.getElementById("item-form");
    if (itemForm) {
        itemForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const nameInput = document.getElementById("item-name");
            const quantityInput = document.getElementById("item-default-quantity");
            const sectionSelect = document.getElementById("item-section");
            const quantityIsIntCheckbox = document.getElementById("item-quantity-is-int");

            // Get selected stores
            const storeCheckboxes = document.querySelectorAll('input[name="store-checkbox"]:checked');
            const storeIds = Array.from(storeCheckboxes).map(cb => parseInt(cb.value));

            try {
                await api.post("/api/items", {
                    name: nameInput.value.trim(),
                    default_quantity: quantityInput.value.trim() || null,
                    section: sectionSelect.value || null,
                    quantity_is_int: quantityIsIntCheckbox.checked,
                    store_ids: storeIds,
                });

                nameInput.value = "";
                quantityInput.value = "";
                sectionSelect.value = "";
                quantityIsIntCheckbox.checked = false;
                storeCheckboxes.forEach(cb => cb.checked = false);

                await loadData();
            } catch (error) {
                console.error("Failed to add item:", error);
                alert("Failed to add item.");
            }
        });
    }

    // Provider form
    const providerForm = document.getElementById("provider-form");
    if (providerForm) {
        providerForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const nameInput = document.getElementById("provider-name");
            const phoneInput = document.getElementById("provider-phone");
            const emailInput = document.getElementById("provider-email");
            const websiteInput = document.getElementById("provider-website");
            const addressInput = document.getElementById("provider-address");
            const infoInput = document.getElementById("provider-info");

            try {
                await api.post("/api/providers", {
                    name: nameInput.value.trim(),
                    phone: phoneInput.value.trim() || null,
                    email: emailInput.value.trim() || null,
                    website: websiteInput.value.trim() || null,
                    address: addressInput.value.trim() || null,
                    info: infoInput.value.trim() || null,
                });

                nameInput.value = "";
                phoneInput.value = "";
                emailInput.value = "";
                websiteInput.value = "";
                addressInput.value = "";
                infoInput.value = "";

                await loadData();
            } catch (error) {
                console.error("Failed to add provider:", error);
                alert("Failed to add provider.");
            }
        });
    }
};

// ============================================================================
// INITIALIZE
// ============================================================================

document.addEventListener("DOMContentLoaded", () => {
    loadData();
    setupNavigation();
    setupForms();
});
