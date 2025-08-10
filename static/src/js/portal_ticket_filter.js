/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { loadWysiwygFromTextarea } from "@web_editor/js/frontend/loadWysiwygFromTextarea";

publicWidget.registry.PGITicketForm = publicWidget.Widget.extend({
  selector: "#pgi-ticket-form",

  start() {
    this._initFilters();
    this._initAttachments();
    this._initSubmitGuard();
    this._initWysiwyg();
    return this._super(...arguments);
  },

  // =========================
  // FILTROS (Equipo / Categorías)
  // =========================
  _initFilters() {
    const form = this.el;
    const teamSelect   = form.querySelector("#team");
    const parentSelect = form.querySelector("#category_parent");
    const childSelect  = form.querySelector("#category");

    // Equipo → recarga con ?team=
    if (teamSelect) {
      teamSelect.addEventListener("change", function () {
        const url = new URL(window.location.href);
        url.searchParams.set("team", this.value || "");
        window.location.href = url.toString();
      });
    }

    // Categoría padre → Subcategoría (usa data-parent en <option>)
    const filterSubcategories = () => {
      if (!parentSelect || !childSelect) return;
      const parentId = parentSelect.value || "";
      Array.from(childSelect.options).forEach(opt => {
        if (!opt.value) return;
        const visible = (opt.dataset.parent || "") === parentId;
        opt.hidden = !visible;
      });
      // Si la seleccionada quedó oculta, limpiamos
      if (childSelect.selectedOptions.length && childSelect.selectedOptions[0].hidden) {
        childSelect.value = "";
      }
    };

    if (parentSelect && childSelect) {
      filterSubcategories(); // inicial
      parentSelect.addEventListener("change", filterSubcategories);
    }
  },

  // =========================
  // ADJUNTOS (dropzone + deduplicación + fix doble apertura)
  // =========================
  _initAttachments() {
    const form       = this.el;
    const fileInput  = form.querySelector("#attachment");
    const dropzone   = form.querySelector("#pgi-dropzone");
    const previewUL  = form.querySelector("#pgi-files-preview");
    const selectLink = dropzone ? dropzone.querySelector(".pgi-select-link") : null;

    if (!fileInput || !dropzone) return;

    const MAX_MB   = 5;
    const ACCEPTED = /\.(jpg|jpeg|png|pdf|doc|docx)$/i;
    const fileKey  = f => `${f.name}|${f.size}|${f.lastModified || 0}`;

    const setFiles = (list) => {
      const dt = new DataTransfer();
      list.forEach(f => dt.items.add(f));
      fileInput.files = dt.files;
    };

    const refreshPreview = () => {
      if (!previewUL) return;
      previewUL.innerHTML = "";
      Array.from(fileInput.files || []).forEach(f => {
        const li = document.createElement("li");
        li.textContent = `${f.name} (${(f.size/1024/1024).toFixed(2)} MB)`;
        previewUL.appendChild(li);
      });
    };

    const replaceWithSelected = (files) => {
      if (!files || !files.length) return;
      const kept = [];
      const seen = new Set();
      Array.from(files).forEach(f => {
        const okType = ACCEPTED.test(f.name);
        const okSize = f.size <= MAX_MB * 1024 * 1024;
        const k = fileKey(f);
        if (okType && okSize && !seen.has(k)) { seen.add(k); kept.push(f); }
      });
      setFiles(kept); refreshPreview();
    };

    const addFiles = (files) => {
      if (!files || !files.length) return;
      const current = Array.from(fileInput.files || []);
      const seen = new Set(current.map(fileKey));
      const merged = [...current];
      Array.from(files).forEach(f => {
        const okType = ACCEPTED.test(f.name);
        const okSize = f.size <= MAX_MB * 1024 * 1024;
        const k = fileKey(f);
        if (okType && okSize && !seen.has(k)) { seen.add(k); merged.push(f); }
      });
      setFiles(merged); refreshPreview();
    };

    // --- Apertura segura del diálogo (evita doble apertura) ---
    let opening = false;
    const openDialog = (e) => {
      e.preventDefault();
      e.stopPropagation(); // clave para frenar burbuja
      if (opening) return;
      opening = true;

      // Reset si el usuario cierra el diálogo sin seleccionar (sin 'change')
      const resetOnFocus = () => {
        opening = false;
        window.removeEventListener("focus", resetOnFocus, true);
      };
      window.addEventListener("focus", resetOnFocus, true);

      fileInput.click();
    };

    // Reset del flag al seleccionar archivos (con vista previa)
    fileInput.addEventListener("change", () => {
      opening = false;
      replaceWithSelected(fileInput.files);
    });

    // Click en la caja general: solo si NO es el link interno
    dropzone.addEventListener("click", (e) => {
      if (e.target && e.target.closest(".pgi-select-link")) return;
      openDialog(e);
    });

    // Click en el link: cortar burbuja y abrir
    if (selectLink) {
      selectLink.addEventListener("click", openDialog);
    }

    // Accesibilidad por teclado
    dropzone.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") openDialog(e);
    });

    // Drag & Drop
    ["dragenter", "dragover"].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault(); e.stopPropagation();
        dropzone.classList.add("pgi-dropzone--drag");
      });
    });
    ["dragleave", "drop"].forEach(evt => {
      dropzone.addEventListener(evt, (e) => {
        e.preventDefault(); e.stopPropagation();
        dropzone.classList.remove("pgi-dropzone--drag");
      });
    });
    dropzone.addEventListener("drop", (e) => addFiles(e.dataTransfer && e.dataTransfer.files));
  },

  // =========================
  // SUBMIT GUARD (anti doble-click)
  // =========================
  _initSubmitGuard() {
    const form = this.el;
    const submitBtn = form.querySelector("#pgi-submit");
    if (!submitBtn) return;
    form.addEventListener("submit", () => {
      if (form.checkValidity()) {
        submitBtn.disabled = true;
        submitBtn.innerText = "Enviando…";
      }
    });
  },

  // =========================
  // WYSIWYG (web_editor)
  // =========================
  _initWysiwyg() {
    const textareas = this.el.querySelectorAll("textarea.o_wysiwyg_loader");
    textareas.forEach((ta) => {
      loadWysiwygFromTextarea(this, ta, {
        height: 180,
        resizable: true,
        userGeneratedContent: true,
      });
    });
  },
});
