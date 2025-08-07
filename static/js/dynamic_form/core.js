// 📁 dynamic_form/core.js

import { renderFields } from './fields.js';
import { loadAssetTypes } from './asset-type.js';
import { handleStatusChange } from './status-remarks.js';
import { populateAvailableFeatureList } from './feature-list.js';
import { setupDatepickers } from './setup.js';
import { setMasterFields, getMasterFields, fieldConfigMap } from './globals.js';

export function fetchMasterFields() {
  return fetch("/get_master_fields")
    .then(res => res.json())
    .then(data => {
      if (Array.isArray(data.fields)) {
        setMasterFields(data.fields);
        console.log("✅ Master fields loaded:", data.fields);
      } else {
        console.error("❌ Invalid response from get_master_fields");
      }
    })
    .catch(err => console.error("❌ Failed to fetch master fields:", err));
}

export async function setupForm() {
  await fetchMasterFields();
  populateAvailableFeatureList();

  const createFormBtn = document.getElementById("create-form-btn");
  const form = document.getElementById("asset-form");
  const submitBtn = document.getElementById("submit-btn");
  const typeSelect = document.getElementById("asset_type");
  const newTypeWrapper = document.getElementById("new-type-wrapper");
  const featureSelectWrapper = document.getElementById("feature-select-wrapper");
  const dynamicFieldsContainer = document.getElementById("dynamic-fields");
  const statusRemarksSection = document.getElementById("status-remarks-section");

  window.form = form;

  form.addEventListener("input", () => {
    const isNewType = typeSelect.value === "add_new_type";
    if (isNewType) {
      submitBtn.disabled = !form.checkValidity() || !window.fieldsToRender || window.fieldsToRender.length === 0;
    } else {
      submitBtn.disabled = !form.checkValidity();
    }
  });

  // ✅ Main fix to ensure correct values go into hidden fields
  form.addEventListener("submit", () => {
    // Force sync selected features
    const selectedFeatures = Array.from(document.querySelectorAll("input[name='selected_features']:checked"))
      .map(cb => cb.value.trim());
    document.getElementById("selected_features").value = selectedFeatures.join(",");

    // Sync custom fields
    const customFieldInputs = Array.from(document.querySelectorAll(".custom-field"));
    const customFieldStr = customFieldInputs.map(input => {
      const label = input.dataset.label;
      const name = input.dataset.name;
      const type = input.dataset.type;
      return `${label}:${name}:${type}`;
    }).join("|");
    document.getElementById("custom_fields").value = customFieldStr;

    // Normalize currency
    form.querySelectorAll("input[data-value]").forEach(input => {
      const raw = input.getAttribute("data-value");
      input.value = raw || "0";
    });

    // Format dates
    form.querySelectorAll('input[type="date"]').forEach(input => {
      if (input.value.includes("-")) {
        const parts = input.value.split("-");
        input.value = `${parts[2]}-${parts[1]}-${parts[0]}`;
      }
    });

    // Debug
    console.log("📝 Final form values before submission:");
    const formData = new FormData(form);
    for (let [key, val] of formData.entries()) {
      console.log(`${key}: ${val}`);
    }
  });

  typeSelect.addEventListener("change", () => {
    const selectedType = typeSelect.value;
    const isAddNew = selectedType === "add_new_type";

    newTypeWrapper.hidden = !isAddNew;
    featureSelectWrapper.hidden = !isAddNew;
    createFormBtn.hidden = !isAddNew;

    if (!isAddNew) {
      if (!fieldConfigMap[selectedType] || window.renderedTypeOnce !== selectedType) {
        renderFields(selectedType, window.existingAssetData || {});
        window.renderedTypeOnce = selectedType;
      }
      statusRemarksSection.hidden = false;
    }

    form.dispatchEvent(new Event("input"));
  });

  handleStatusChange(form);
  loadAssetTypes();
  setupDatepickers();

  if (window.fieldsToRender && window.fieldsToRender.length > 0 && window.existingAssetData) {
    const selectedType = window.existingAssetData.category;
    fieldConfigMap[selectedType] = window.fieldsToRender;
    renderFields(selectedType, window.existingAssetData);
    delete window.existingAssetData;
  }

  if (createFormBtn) {
    createFormBtn.addEventListener("click", () => {
      const selectedFeatures = Array.from(document.querySelectorAll("input[name='selected_features']:checked"))
        .map(cb => cb.value);

      if (selectedFeatures.length === 0) {
        alert("Please select at least one field.");
        return;
      }

      document.getElementById("selected_features").value = selectedFeatures.join(",");

      const fieldsToInject = getMasterFields().filter(f => selectedFeatures.includes(f.name));
      window.fieldsToRender = fieldsToInject;

      const realType = document.getElementById("new-type")?.value?.trim();
      if (!realType) {
        alert("Please enter a name for the new type.");
        return;
      }

      fieldConfigMap[realType] = fieldsToInject;
      renderFields(realType);
      form.dispatchEvent(new Event("input"));

      submitBtn.disabled = false; // ✅ Enable now that form is ready
    });
  }
}
