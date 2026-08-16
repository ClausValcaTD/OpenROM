import customtkinter as ctk
import qrcode
from PIL import Image
import webbrowser

BG_DARK     = "#1a1a2e"
CARD_BG     = "#16213e"
ACCENT_RED  = "#e94560"
BORDER_DARK = "#333333"
TEXT_WHITE  = "#ffffff"
TEXT_GRAY   = "#a0a0b0"

ABOUT_TEXT = """OpenROM is free and open-source software built to break the monopoly of proprietary ROM tools. We believe in open standards, community-driven development, and giving users full control over their game preservation workflow."""

USDT_ADDRESS = "TWbG9smLbcyTcVod3YsRPyEtWhtQnnu7vC"

class AboutWindow(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("About OpenROM")
        self.geometry("520x620")
        self.resizable(False, False)
        self.configure(fg_color=BG_DARK)
        self.grab_set()

        self._build()

    def _build(self):
        scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=16, pady=16)

        # Title Header
        ctk.CTkLabel(
            scroll_frame, text="OpenROM",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=ACCENT_RED
        ).pack(pady=(10, 2))

        ctk.CTkLabel(
            scroll_frame, text="Universal ROM Compression Suite",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_WHITE
        ).pack(pady=(0, 4))

        ctk.CTkLabel(
            scroll_frame, text="Developed by M5 Dev",
            font=ctk.CTkFont(size=12, slant="italic"),
            text_color=TEXT_GRAY
        ).pack(pady=(0, 12))

        # Text Manifesto Box
        manifesto_box = ctk.CTkFrame(scroll_frame, fg_color=CARD_BG, corner_radius=10, border_color=BORDER_DARK, border_width=1)
        manifesto_box.pack(fill="x", pady=8)

        ctk.CTkLabel(
            manifesto_box, text=ABOUT_TEXT,
            font=ctk.CTkFont(size=11), text_color=TEXT_WHITE,
            justify="left", wraplength=440
        ).pack(padx=16, pady=12)

        # License & Source
        lic_frame = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        lic_frame.pack(fill="x", pady=4)

        ctk.CTkLabel(
            lic_frame, text="License: GPL v3",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=TEXT_GRAY
        ).pack(anchor="w")

        source_btn = ctk.CTkButton(
            lic_frame, text="Source: https://github.com/M5Devs/OpenROM",
            fg_color="transparent", hover_color=CARD_BG,
            text_color=ACCENT_RED, font=ctk.CTkFont(size=11, underline=True),
            anchor="w", command=lambda: webbrowser.open("https://github.com/M5Devs/OpenROM")
        )
        source_btn.pack(anchor="w", pady=(2, 0))

        # Divider line
        ctk.CTkFrame(scroll_frame, fg_color=BORDER_DARK, height=1).pack(fill="x", pady=16)

        # Support Section Header
        ctk.CTkLabel(
            scroll_frame, text="💙 Support OpenROM",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=ACCENT_RED
        ).pack(pady=(0, 6))

        ctk.CTkLabel(
            scroll_frame,
            text="If you find this tool useful, consider donating to support development:\n\nUSDT (TRC20):",
            font=ctk.CTkFont(size=12), text_color=TEXT_WHITE, justify="center"
        ).pack(pady=(0, 6))

        # Wallet Address Entry Box
        addr_entry = ctk.CTkEntry(
            scroll_frame, fg_color=CARD_BG, border_color=BORDER_DARK,
            text_color=TEXT_WHITE, justify="center", font=ctk.CTkFont(size=11),
            width=380
        )
        addr_entry.insert(0, USDT_ADDRESS)
        addr_entry.configure(state="readonly")
        addr_entry.pack(pady=(0, 10))

        # QR Code Generation
        try:
            qr = qrcode.QRCode(version=1, box_size=4, border=2)
            qr.add_data(USDT_ADDRESS)
            qr.make(fit=True)
            img = qr.make_image(fill_color="black", back_color="white")

            img_ctk = ctk.CTkImage(light_image=img, dark_image=img, size=(160, 160))
            qr_label = ctk.CTkLabel(scroll_frame, image=img_ctk, text="")
            qr_label.image = img_ctk
            qr_label.pack(pady=4)
        except Exception as e:
            ctk.CTkLabel(scroll_frame, text=f"Could not generate QR: {e}", text_color=ACCENT_RED).pack(pady=4)

        ctk.CTkLabel(
            scroll_frame,
            text="Scan the QR code or copy the address to send USDT on TRON network.\nEvery donation helps keep OpenROM free and actively maintained!",
            font=ctk.CTkFont(size=11), text_color=TEXT_GRAY, justify="center"
        ).pack(pady=(8, 16))

        # Close Button
        ctk.CTkButton(
            scroll_frame, text="Close", height=38,
            fg_color=ACCENT_RED, hover_color="#c8344d",
            text_color=TEXT_WHITE, font=ctk.CTkFont(size=12, weight="bold"),
            command=self.destroy
        ).pack(fill="x", pady=(0, 10))
