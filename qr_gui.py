#!/usr/bin/env python3
"""
Generador de Códigos QR — Interfaz Gráfica
Dependencias: pip install customtkinter pillow qrcode[pil]
"""

import customtkinter as ctk
from PIL import Image, ImageTk
import qrcode
import os
import io
import threading

# ── Tema ──────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT     = "#00C896"
BG_DARK    = "#0F1117"
BG_CARD    = "#1A1D27"
BG_INPUT   = "#22263A"
TEXT_MAIN  = "#F0F2FF"
TEXT_MUTED = "#7B8099"
BORDER     = "#2E3248"

NIVELES = {
    "L — 7%":  qrcode.constants.ERROR_CORRECT_L,
    "M — 15%": qrcode.constants.ERROR_CORRECT_M,
    "Q — 25%": qrcode.constants.ERROR_CORRECT_Q,
    "H — 30%": qrcode.constants.ERROR_CORRECT_H,
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def hex_to_rgb(h: str):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def generar_pil(url, size, ec, color_qr, color_bg):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ec,
        box_size=size,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color=color_qr, back_color=color_bg)


# ── Ventana principal ─────────────────────────────────────────────────────────
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Generador de QR")
        self.geometry("860x620")
        self.minsize(760, 560)
        self.configure(fg_color=BG_DARK)
        self.resizable(True, True)

        self._pil_img   = None   # imagen PIL actual
        self._preview   = None   # ImageTk actual
        self._color_qr  = "#000000"
        self._color_bg  = "#ffffff"

        self._build_ui()

    # ── Construcción de UI ────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=0, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr, text="⬛ QR Generator",
            font=ctk.CTkFont("Courier", 18, "bold"),
            text_color=ACCENT
        ).pack(side="left", padx=24, pady=14)
        ctk.CTkLabel(
            hdr, text="genera · personaliza · descarga",
            font=ctk.CTkFont("Courier", 11),
            text_color=TEXT_MUTED
        ).pack(side="left")

        # Tabs
        self.tabs = ctk.CTkTabview(
            self,
            fg_color=BG_DARK,
            segmented_button_fg_color=BG_CARD,
            segmented_button_selected_color=ACCENT,
            segmented_button_selected_hover_color="#00A87E",
            segmented_button_unselected_color=BG_CARD,
            segmented_button_unselected_hover_color=BG_INPUT,
            text_color=TEXT_MAIN,
            corner_radius=0,
        )
        self.tabs.pack(fill="both", expand=True, padx=0, pady=0)

        self.tabs.add("  Simple  ")
        self.tabs.add("  Personalizado  ")
        self.tabs.add("  Masivo  ")

        self._tab_simple()
        self._tab_personalizado()
        self._tab_masivo()

    # ── Tab 1: Simple ─────────────────────────────────────────────────────────
    def _tab_simple(self):
        tab = self.tabs.tab("  Simple  ")
        tab.configure(fg_color=BG_DARK)

        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=16)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # Columna izquierda — controles
        left = ctk.CTkFrame(main, fg_color=BG_CARD, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._label(left, "URL o texto").pack(anchor="w", padx=20, pady=(20, 4))
        self.s_url = self._entry(left, "https://ejemplo.com")
        self.s_url.pack(fill="x", padx=20)

        self._label(left, "Nombre del archivo").pack(anchor="w", padx=20, pady=(14, 4))
        self.s_nombre = self._entry(left, "mi_qr")
        self.s_nombre.pack(fill="x", padx=20)

        self._label(left, "Carpeta de destino").pack(anchor="w", padx=20, pady=(14, 4))
        folder_row = ctk.CTkFrame(left, fg_color="transparent")
        folder_row.pack(fill="x", padx=20)
        self.s_carpeta = self._entry(folder_row, "qr_codigos")
        self.s_carpeta.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            folder_row, text="📁", width=36, height=36,
            fg_color=BG_INPUT, hover_color=BORDER,
            command=lambda: self._elegir_carpeta(self.s_carpeta)
        ).pack(side="left", padx=(6, 0))

        ctk.CTkButton(
            left, text="Generar QR",
            font=ctk.CTkFont("Courier", 13, "bold"),
            fg_color=ACCENT, hover_color="#00A87E", text_color=BG_DARK,
            height=42, corner_radius=8,
            command=self._generar_simple
        ).pack(fill="x", padx=20, pady=(24, 20))

        self.s_status = ctk.CTkLabel(left, text="", font=ctk.CTkFont("Courier", 11), text_color=ACCENT)
        self.s_status.pack(pady=(0, 16))

        # Columna derecha — preview
        right = ctk.CTkFrame(main, fg_color=BG_CARD, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._label(right, "Vista previa").pack(anchor="w", padx=20, pady=(20, 0))
        self.s_preview_frame = ctk.CTkFrame(right, fg_color=BG_INPUT, corner_radius=8)
        self.s_preview_frame.pack(fill="both", expand=True, padx=20, pady=16)
        self.s_canvas = ctk.CTkLabel(self.s_preview_frame, text="← genera un QR", text_color=TEXT_MUTED, font=ctk.CTkFont("Courier", 12))
        self.s_canvas.pack(expand=True)

        ctk.CTkButton(
            right, text="Descargar PNG",
            font=ctk.CTkFont("Courier", 12),
            fg_color="transparent", border_width=1, border_color=ACCENT,
            text_color=ACCENT, hover_color=BG_INPUT, height=36, corner_radius=8,
            command=lambda: self._guardar_png(self.s_carpeta, self.s_nombre)
        ).pack(fill="x", padx=20, pady=(0, 20))

    # ── Tab 2: Personalizado ──────────────────────────────────────────────────
    def _tab_personalizado(self):
        tab = self.tabs.tab("  Personalizado  ")
        tab.configure(fg_color=BG_DARK)

        main = ctk.CTkFrame(tab, fg_color="transparent")
        main.pack(fill="both", expand=True, padx=24, pady=16)
        main.columnconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)

        # Controles
        left = ctk.CTkFrame(main, fg_color=BG_CARD, corner_radius=12)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        self._label(left, "URL o texto").pack(anchor="w", padx=20, pady=(20, 4))
        self.p_url = self._entry(left, "https://ejemplo.com")
        self.p_url.pack(fill="x", padx=20)

        self._label(left, "Nombre del archivo").pack(anchor="w", padx=20, pady=(12, 4))
        self.p_nombre = self._entry(left, "mi_qr")
        self.p_nombre.pack(fill="x", padx=20)

        # Tamaño del módulo
        self._label(left, "Tamaño del módulo (px)").pack(anchor="w", padx=20, pady=(12, 4))
        size_row = ctk.CTkFrame(left, fg_color="transparent")
        size_row.pack(fill="x", padx=20)
        self.p_size_val = ctk.CTkLabel(size_row, text="10", text_color=ACCENT, font=ctk.CTkFont("Courier", 13, "bold"), width=30)
        self.p_size_val.pack(side="right")
        self.p_size = ctk.CTkSlider(size_row, from_=2, to=30, number_of_steps=28,
                                    button_color=ACCENT, button_hover_color="#00A87E",
                                    progress_color=ACCENT,
                                    command=lambda v: self.p_size_val.configure(text=str(int(v))))
        self.p_size.set(10)
        self.p_size.pack(fill="x", expand=True, side="left", padx=(0, 8))

        # Corrección de errores
        self._label(left, "Corrección de errores").pack(anchor="w", padx=20, pady=(12, 4))
        self.p_ec = ctk.CTkOptionMenu(
            left, values=list(NIVELES.keys()),
            fg_color=BG_INPUT, button_color=BORDER, button_hover_color=ACCENT,
            dropdown_fg_color=BG_CARD, text_color=TEXT_MAIN,
            font=ctk.CTkFont("Courier", 12)
        )
        self.p_ec.set("M — 15%")
        self.p_ec.pack(fill="x", padx=20)

        # Colores
        col_row = ctk.CTkFrame(left, fg_color="transparent")
        col_row.pack(fill="x", padx=20, pady=(12, 0))

        # color QR
        c1 = ctk.CTkFrame(col_row, fg_color="transparent")
        c1.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._label(c1, "Color QR").pack(anchor="w")
        qr_row = ctk.CTkFrame(c1, fg_color="transparent")
        qr_row.pack(fill="x")
        self.p_qr_hex = self._entry(qr_row, "#000000")
        self.p_qr_hex.pack(side="left", fill="x", expand=True)
        self.p_qr_swatch = ctk.CTkFrame(qr_row, width=30, height=30, fg_color="#000000", corner_radius=4)
        self.p_qr_swatch.pack(side="left", padx=(6, 0))
        self.p_qr_hex.bind("<FocusOut>", lambda e: self._update_swatch(self.p_qr_hex, self.p_qr_swatch, "qr"))
        self.p_qr_hex.bind("<Return>",   lambda e: self._update_swatch(self.p_qr_hex, self.p_qr_swatch, "qr"))

        # color fondo
        c2 = ctk.CTkFrame(col_row, fg_color="transparent")
        c2.pack(side="left", fill="x", expand=True, padx=(6, 0))
        self._label(c2, "Color fondo").pack(anchor="w")
        bg_row = ctk.CTkFrame(c2, fg_color="transparent")
        bg_row.pack(fill="x")
        self.p_bg_hex = self._entry(bg_row, "#ffffff")
        self.p_bg_hex.pack(side="left", fill="x", expand=True)
        self.p_bg_swatch = ctk.CTkFrame(bg_row, width=30, height=30, fg_color="#ffffff", corner_radius=4)
        self.p_bg_swatch.pack(side="left", padx=(6, 0))
        self.p_bg_hex.bind("<FocusOut>", lambda e: self._update_swatch(self.p_bg_hex, self.p_bg_swatch, "bg"))
        self.p_bg_hex.bind("<Return>",   lambda e: self._update_swatch(self.p_bg_hex, self.p_bg_swatch, "bg"))

        ctk.CTkButton(
            left, text="Generar QR",
            font=ctk.CTkFont("Courier", 13, "bold"),
            fg_color=ACCENT, hover_color="#00A87E", text_color=BG_DARK,
            height=42, corner_radius=8,
            command=self._generar_personalizado
        ).pack(fill="x", padx=20, pady=(18, 8))

        self.p_status = ctk.CTkLabel(left, text="", font=ctk.CTkFont("Courier", 11), text_color=ACCENT)
        self.p_status.pack(pady=(0, 16))

        # Preview
        right = ctk.CTkFrame(main, fg_color=BG_CARD, corner_radius=12)
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0))

        self._label(right, "Vista previa").pack(anchor="w", padx=20, pady=(20, 0))
        self.p_preview_frame = ctk.CTkFrame(right, fg_color=BG_INPUT, corner_radius=8)
        self.p_preview_frame.pack(fill="both", expand=True, padx=20, pady=12)
        self.p_canvas = ctk.CTkLabel(self.p_preview_frame, text="← genera un QR", text_color=TEXT_MUTED, font=ctk.CTkFont("Courier", 12))
        self.p_canvas.pack(expand=True)

        btn_row = ctk.CTkFrame(right, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(0, 20))

        carpeta_row = ctk.CTkFrame(right, fg_color="transparent")
        carpeta_row.pack(fill="x", padx=20, pady=(0, 8))
        self.p_carpeta = self._entry(carpeta_row, "qr_codigos")
        self.p_carpeta.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(
            carpeta_row, text="📁", width=36, height=36,
            fg_color=BG_INPUT, hover_color=BORDER,
            command=lambda: self._elegir_carpeta(self.p_carpeta)
        ).pack(side="left", padx=(6, 0))

        ctk.CTkButton(
            right, text="Descargar PNG",
            font=ctk.CTkFont("Courier", 12),
            fg_color="transparent", border_width=1, border_color=ACCENT,
            text_color=ACCENT, hover_color=BG_INPUT, height=36, corner_radius=8,
            command=lambda: self._guardar_png(self.p_carpeta, self.p_nombre)
        ).pack(fill="x", padx=20, pady=(0, 20))

    # ── Tab 3: Masivo ─────────────────────────────────────────────────────────
    def _tab_masivo(self):
        tab = self.tabs.tab("  Masivo  ")
        tab.configure(fg_color=BG_DARK)

        wrap = ctk.CTkFrame(tab, fg_color=BG_CARD, corner_radius=12)
        wrap.pack(fill="both", expand=True, padx=24, pady=16)

        self._label(wrap, "Pega tus links (uno por línea)").pack(anchor="w", padx=20, pady=(20, 6))
        self.m_text = ctk.CTkTextbox(
            wrap, font=ctk.CTkFont("Courier", 12),
            fg_color=BG_INPUT, text_color=TEXT_MAIN,
            border_color=BORDER, border_width=1,
            corner_radius=8, height=200
        )
        self.m_text.pack(fill="x", padx=20)
        self.m_text.insert("end", "https://google.com\nhttps://github.com\nhttps://claude.ai")

        row2 = ctk.CTkFrame(wrap, fg_color="transparent")
        row2.pack(fill="x", padx=20, pady=(14, 0))

        c1 = ctk.CTkFrame(row2, fg_color="transparent")
        c1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._label(c1, "Carpeta de salida").pack(anchor="w")
        self.m_carpeta = self._entry(c1, "qr_masivo")
        self.m_carpeta.pack(fill="x")

        c2 = ctk.CTkFrame(row2, fg_color="transparent")
        c2.pack(side="left", fill="x", expand=True)
        self._label(c2, "Prefijo de archivos").pack(anchor="w")
        self.m_prefijo = self._entry(c2, "qr_")
        self.m_prefijo.pack(fill="x")

        ctk.CTkButton(
            wrap, text="Generar todos",
            font=ctk.CTkFont("Courier", 13, "bold"),
            fg_color=ACCENT, hover_color="#00A87E", text_color=BG_DARK,
            height=42, corner_radius=8,
            command=self._generar_masivo
        ).pack(fill="x", padx=20, pady=(18, 0))

        self.m_progress = ctk.CTkProgressBar(wrap, progress_color=ACCENT, corner_radius=4)
        self.m_progress.pack(fill="x", padx=20, pady=(12, 0))
        self.m_progress.set(0)

        self.m_log = ctk.CTkTextbox(
            wrap, font=ctk.CTkFont("Courier", 11),
            fg_color=BG_INPUT, text_color=TEXT_MUTED,
            border_color=BORDER, border_width=1,
            corner_radius=8, height=120, state="disabled"
        )
        self.m_log.pack(fill="x", padx=20, pady=(10, 20))

    # ── Widgets helpers ───────────────────────────────────────────────────────
    def _label(self, parent, text):
        return ctk.CTkLabel(
            parent, text=text,
            font=ctk.CTkFont("Courier", 11),
            text_color=TEXT_MUTED
        )

    def _entry(self, parent, placeholder=""):
        return ctk.CTkEntry(
            parent, placeholder_text=placeholder,
            font=ctk.CTkFont("Courier", 12),
            fg_color=BG_INPUT, text_color=TEXT_MAIN,
            border_color=BORDER, border_width=1,
            placeholder_text_color=TEXT_MUTED,
            corner_radius=6, height=36
        )

    # ── Lógica ────────────────────────────────────────────────────────────────
    def _update_swatch(self, entry_widget, swatch, target):
        val = entry_widget.get().strip()
        try:
            hex_to_rgb(val)
            swatch.configure(fg_color=val)
            if target == "qr":
                self._color_qr = val
            else:
                self._color_bg = val
        except Exception:
            pass

    def _elegir_carpeta(self, entry_widget):
        from tkinter import filedialog
        path = filedialog.askdirectory()
        if path:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, path)

    def _show_preview(self, pil_img, canvas_label, frame):
        self._pil_img = pil_img
        w = frame.winfo_width() - 32 or 240
        h = frame.winfo_height() - 32 or 240
        size = min(w, h, 300)
        img_resized = pil_img.resize((size, size), Image.NEAREST)
        self._preview = ImageTk.PhotoImage(img_resized)
        canvas_label.configure(image=self._preview, text="")

    def _generar_simple(self):
        url    = self.s_url.get().strip()
        nombre = self.s_nombre.get().strip() or "qrcode"
        if not url:
            self.s_status.configure(text="⚠ Ingresa una URL", text_color="#FF6B6B")
            return
        try:
            img = generar_pil(url, 10, qrcode.constants.ERROR_CORRECT_M, "black", "white")
            self.after(10, lambda: self._show_preview(img, self.s_canvas, self.s_preview_frame))
            self.s_status.configure(text="✓ QR generado", text_color=ACCENT)
        except Exception as e:
            self.s_status.configure(text=f"✗ Error: {e}", text_color="#FF6B6B")

    def _generar_personalizado(self):
        url    = self.p_url.get().strip()
        if not url:
            self.p_status.configure(text="⚠ Ingresa una URL", text_color="#FF6B6B")
            return
        try:
            size  = int(self.p_size.get())
            ec    = NIVELES[self.p_ec.get()]
            c_qr  = self.p_qr_hex.get().strip() or "#000000"
            c_bg  = self.p_bg_hex.get().strip() or "#ffffff"
            img   = generar_pil(url, size, ec, c_qr, c_bg)
            self.after(10, lambda: self._show_preview(img, self.p_canvas, self.p_preview_frame))
            self.p_status.configure(text="✓ QR generado", text_color=ACCENT)
        except Exception as e:
            self.p_status.configure(text=f"✗ Error: {e}", text_color="#FF6B6B")

    def _guardar_png(self, carpeta_widget, nombre_widget):
        if self._pil_img is None:
            return
        carpeta = carpeta_widget.get().strip() or "qr_codigos"
        nombre  = nombre_widget.get().strip() or "qrcode"
        os.makedirs(carpeta, exist_ok=True)
        ruta = os.path.join(carpeta, f"{nombre}.png")
        self._pil_img.save(ruta)
        from tkinter import messagebox
        messagebox.showinfo("Guardado", f"QR guardado en:\n{os.path.abspath(ruta)}")

    def _generar_masivo(self):
        texto   = self.m_text.get("1.0", "end").strip()
        links   = [l.strip() for l in texto.splitlines() if l.strip()]
        carpeta = self.m_carpeta.get().strip() or "qr_masivo"
        prefijo = self.m_prefijo.get().strip() or "qr_"

        if not links:
            return

        self._log_clear()
        self.m_progress.set(0)

        def worker():
            os.makedirs(carpeta, exist_ok=True)
            total = len(links)
            for i, link in enumerate(links, 1):
                nombre = f"{prefijo}{i:03d}"
                try:
                    img = generar_pil(link, 10, qrcode.constants.ERROR_CORRECT_M, "black", "white")
                    ruta = os.path.join(carpeta, f"{nombre}.png")
                    img.save(ruta)
                    self.after(0, lambda n=nombre, l=link: self._log(f"✓ {n}.png  ←  {l}"))
                except Exception as e:
                    self.after(0, lambda l=link, err=e: self._log(f"✗ Error '{l}': {err}"))
                self.after(0, lambda p=i/total: self.m_progress.set(p))
            self.after(0, lambda: self._log(f"\n✓ Listo. {total} QR(s) en '{carpeta}/'"))

        threading.Thread(target=worker, daemon=True).start()

    def _log(self, msg):
        self.m_log.configure(state="normal")
        self.m_log.insert("end", msg + "\n")
        self.m_log.see("end")
        self.m_log.configure(state="disabled")

    def _log_clear(self):
        self.m_log.configure(state="normal")
        self.m_log.delete("1.0", "end")
        self.m_log.configure(state="disabled")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()