"""payment_handler.py - UPI manual payment instructions (never auto-pays)."""
import json
import os
import re
import time

PAYMENT_LOG = "/var/lib/zenvx/payment_log.json"
UPI_RE = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z]+$")


class PaymentHandler:
    def __init__(self, log_path=PAYMENT_LOG):
        self.log_path = log_path

    @staticmethod
    def validate_upi(upi_id):
        return bool(UPI_RE.match(upi_id or ""))

    def show_instructions(self, vendor, product, amount, upi_id):
        if not self.validate_upi(upi_id):
            return f"Invalid UPI ID format: {upi_id}"
        panel = [
            "\u2500" * 50,
            "  PAYMENT INFORMATION (manual entry only)",
            "\u2500" * 50,
            f"  Vendor:  {vendor}",
            f"  Product: {product}",
            f"  Amount:  \u20b9{amount}",
            f"  UPI ID:  {upi_id}",
            "\u2500" * 50,
            "  Steps:",
            "   1. Open GPay / PhonePe / BHIM",
            "   2. Choose 'Pay to UPI ID'",
            f"   3. Enter {upi_id} and amount \u20b9{amount}",
            "   4. Verify the payee, then authorize with your UPI PIN",
            "",
            "  ZenvX never stores your credentials, PIN, or passwords.",
            "  ZenvX never initiates a payment automatically.",
            "\u2500" * 50,
        ]
        return "\n".join(panel)

    def record(self, vendor, product, amount, upi_id):
        entry = {"timestamp": time.time(), "vendor": vendor,
                 "product": product, "amount": amount, "upi_id": upi_id}
        log = []
        if os.path.exists(self.log_path):
            try:
                with open(self.log_path) as f:
                    log = json.load(f)
            except (OSError, ValueError):
                log = []
        log.append(entry)
        with open(self.log_path, "w") as f:
            json.dump(log, f, indent=2)
        return entry
