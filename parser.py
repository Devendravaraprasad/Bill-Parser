import re
from datetime import datetime

def extract_receipt_data(text: str) -> dict:
    data = {
        "invoice_number": "NA",
        "invoice_date": "NA",
        "vendor_name": "NA",
        "subtotal_amount": 0.0,
        "tax_amount": 0.0,
        "total_amount": 0.0,
        "payment_method": "NA",
    }

    # Normalize and clean lines
    lines = [line.strip() for line in re.split(r'[\r\n]+', text) if line.strip()]
    full_text = " ".join(lines)

    # ---- 1. Handle structured line with multiple fields (invoice no, date, due, amount) ----
    for i in range(len(lines) - 1):
        if ("invoice number" in lines[i].lower() and
            "date" in lines[i].lower() and
            "due" in lines[i].lower()):
            values = re.findall(r"(\d{2}/\d{2}/\d{2,4}|\d+|\$[\d,]+\.\d{2})", lines[i+1])
            if len(values) >= 4:
                try:
                    data["invoice_number"] = re.sub(r"[^\d]", "", values[0])
                    dt = datetime.strptime(values[1], "%m/%d/%y")
                    data["invoice_date"] = dt.strftime("%Y-%m-%d")
                    data["total_amount"] = float(values[3].replace("$", "").replace(",", ""))
                except:
                    pass

    # ---- 2. Backup: Invoice number ----
    if data["invoice_number"] == "NA":
        match = re.search(r"(Invoice|Bill|Receipt)[^\d]{0,10}(\d{3,})", full_text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(2)

    # ---- 3. Backup: Invoice date in various formats ----
    if data["invoice_date"] == "NA":
        date_patterns = [
            r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[01])[/-](\d{2,4})\b",  # MM/DD/YYYY
            r"\b(0?[1-9]|[12][0-9]|3[01])[/-](0?[1-9]|1[0-2])[/-](\d{2,4})\b",  # DD/MM/YYYY
            r"\b\d{4}[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[01])\b"      # YYYY-MM-DD
        ]
        for pattern in date_patterns:
            match = re.search(pattern, full_text)
            if match:
                for fmt in ["%m/%d/%Y", "%d/%m/%Y", "%Y-%m-%d", "%m/%d/%y", "%d/%m/%y"]:
                    try:
                        parsed_date = datetime.strptime(match.group(0), fmt)
                        data["invoice_date"] = parsed_date.strftime("%Y-%m-%d")
                        break
                    except:
                        continue
                else:
                    data["invoice_date"] = match.group(0)
                break

    # ---- 4. Vendor Name Extraction ----
    vendor_keywords = r"(hospital|dmart|store|center|mart|medical|electricity|power|board|energy|bescom|mseb|tneb|tangedco|bills?)"

    # Step 1: Keywords in last lines
    for line in reversed(lines[-10:]):
        if re.search(vendor_keywords, line, re.IGNORECASE):
            data["vendor_name"] = re.sub(r"[^\w\s&]", "", line).strip()
            break

    # Step 2: Look near labels like "Billed To" or "From"
    if data["vendor_name"] == "NA":
        for i, line in enumerate(lines):
            if re.search(r"(billed\s*to|vendor|from|invoice\s*by)", line, re.IGNORECASE):
                for j in range(1, 3):
                    if i + j < len(lines):
                        name_line = lines[i + j].strip()
                        if name_line and not re.search(r"@|\.com|\d{1,2}/\d{1,2}/\d{2,4}", name_line):
                            data["vendor_name"] = re.sub(r"[^\w\s&]", "", name_line).strip()
                            break
                if data["vendor_name"] != "NA":
                    break

    # Step 3: Fallback from domain/email
    if data["vendor_name"] == "NA":
        for line in lines:
            if ".com" in line or "@" in line or "www." in line:
                domain_match = re.search(r"[\w\-]+(?:\.com|\.in|\.org)", line)
                if domain_match:
                    domain = domain_match.group(0)
                    vendor_guess = domain.split(".")[0]
                    data["vendor_name"] = vendor_guess.capitalize() + " (inferred)"
                    break

    # Step 4: Post-clean vendor name (remove leading junk)
    if data["vendor_name"] != "NA":
        data["vendor_name"] = re.sub(r"^[^A-Za-z]*(\w.+)", r"\1", data["vendor_name"]).strip()

    # ---- 5. Tax Amount ----
    tax_amt_match = re.search(r"\b(Tax|GST|VAT)[\s\S]{0,15}?\$?([0-9.,]{2,})", full_text, re.IGNORECASE)
    if tax_amt_match:
        try:
            data["tax_amount"] = float(tax_amt_match.group(2).replace(",", ""))
        except:
            pass

    # ---- 6. Subtotal Amount ----
    sub_total_match = re.search(r"\b(Sub[- ]?Total)[\s:$]*\$?([0-9.,]+)", full_text, re.IGNORECASE)
    if sub_total_match:
        try:
            data["subtotal_amount"] = float(sub_total_match.group(2).replace(",", ""))
        except:
            pass

    # ---- 7. Grand Total (fallback if not captured) ----
    if data["total_amount"] == 0.0:
        grand_total_match = re.search(r"\b(Total Amount|Grand Total|Total)[\s:$]*\$?([0-9.,]+)", full_text, re.IGNORECASE)
        if grand_total_match:
            try:
                data["total_amount"] = float(grand_total_match.group(2).replace(",", ""))
            except:
                pass

    # ---- 8. Total Amount Correction if mismatch ----
    if data["subtotal_amount"] > 0 and data["tax_amount"] > 0:
        expected_total = round(data["subtotal_amount"] + data["tax_amount"], 2)
        if abs(expected_total - data["total_amount"]) > 1:
            data["total_amount"] = expected_total

    # ---- 9. Payment Method ----
    method_match = re.search(r"(Payment Method|Mode|Paid via|Payment Type)[^\w]{0,10}([A-Za-z ]+)", full_text, re.IGNORECASE)
    if method_match:
        data["payment_method"] = method_match.group(2).strip()

    # ---- 10. Round all amounts ----
    data["subtotal_amount"] = round(data["subtotal_amount"], 2)
    data["tax_amount"] = round(data["tax_amount"], 2)
    data["total_amount"] = round(data["total_amount"], 2)

    return data
