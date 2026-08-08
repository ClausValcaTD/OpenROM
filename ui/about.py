import customtkinter as ctk
import qrcode
from PIL import Image
import webbrowser

NAVY   = "#0d1b2a"
CYAN   = "#00e5ff"
CYAN2  = "#00b4cc"
DARK2  = "#112233"
DARK3  = "#0a1628"
WHITE  = "#e0f0ff"
GRAY   = "#7a8a9a"

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About OpenROM")
        self.geometry("450x520")
        self.resizable(False, False)
        self.configure(fg_color=NAVY)
        self.grab_set()

        self._build()

    def _build(self):
        # Header Info
        ctk.CTkLabel(self, text="OpenROM",
                     font=ctk.CTkFont(size=24, weight="bold"),
                     text_color=CYAN).pack(pady=(20, 2))

        ctk.CTkLabel(self, text="Universal ROM Compression Suite",
                     font=ctk.CTkFont(size=13, slant="italic"),
                     text_color=CYAN2).pack()

        info_frame = ctk.CTkFrame(self, fg_color=DARK2, corner_radius=10)
        info_frame.pack(fill="x", padx=20, pady=10)

        # Labels
        ctk.CTkLabel(info_frame, text="Version: 1.0.0",
                     font=ctk.CTkFont(size=12),
                     text_color=WHITE).pack(pady=2)
        ctk.CTkLabel(info_frame, text="Author: M5 Dev (Claus Valca)",
                     font=ctk.CTkFont(size=12),
                     text_color=WHITE).pack(pady=2)
        ctk.CTkLabel(info_frame, text="License: GPL v3",
                     font=ctk.CTkFont(size=12),
                     text_color=WHITE).pack(pady=2)

        # Support Section
        ctk.CTkLabel(self, text="Support the project via USDT (TRC20):",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=CYAN).pack(pady=(10, 2))

        wallet_address = "TWbG9smLbcyTcVod3YsRPyEtWhtQnnu7vC"

        entry = ctk.CTkEntry(self, fg_color=DARK3, border_color=CYAN2,
                             text_color=WHITE, justify="center", width=320,
                             font=ctk.CTkFont(size=10))
        entry.insert(0, wallet_address)
        entry.configure(state="readonly")
        entry.pack(pady=2)

        # Generate QR Code
        try:
            qr = qrcode.QRCode(version=1, box_size=3, border=4)
            qr.add_data(wallet_address)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            # Convert PIL image to ctk.CTkImage for CustomTkinter compatibility
            img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(img.width, img.height))
            qr_label = ctk.CTkLabel(self, image=img_ctk, text="")
            qr_label.image = img_ctk  # Keep reference
            qr_label.pack(pady=10)
        except Exception as e:
            ctk.CTkLabel(self, text=f"Could not generate QR: {e}", text_color="red").pack(pady=10)

        # GitHub Link
        ctk.CTkButton(
            self, text="View GitHub Repository",
            fg_color=DARK3, hover_color=DARK2,
            text_color=CYAN2, font=ctk.CTkFont(size=12),
            command=lambda: webbrowser.open("https://github.com/M5Devs/OpenROM")
        ).pack(fill="x", padx=40, pady=10)

        # Close Button
        ctk.CTkButton(
            self, text="Close", height=36,
            fg_color=CYAN2, hover_color=CYAN,
            text_color=NAVY, font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy,
        ).pack(pady=(5, 15), padx=40, fill="x")
