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

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    full_text = " ".join(lines)

    # ---- 1. Structured Field Line Extraction ----
    for i in range(len(lines) - 1):
        if ("invoice number" in lines[i].lower() and
            "date" in lines[i].lower()):

            values = re.findall(r"(\d{2}/\d{2}/\d{2,4}|\d+|\$[\d,]+\.\d{2})", lines[i+1])
            if len(values) >= 2:
                try:
                    data["invoice_number"] = re.sub(r"[^\d]", "", values[0])
                    dt = datetime.strptime(values[1], "%d/%m/%Y")
                    data["invoice_date"] = dt.strftime("%Y-%m-%d")
                except:
                    pass

    # ---- 2. Backup Invoice Number ----
    if data["invoice_number"] == "NA":
        match = re.search(r"(Invoice|Bill|Receipt)[^\d]{0,10}(\d{3,})", full_text, re.IGNORECASE)
        if match:
            data["invoice_number"] = match.group(2)

    # ---- 3. Backup Invoice Date ----
    if data["invoice_date"] == "NA":
        date_patterns = [
            r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[01])[/-](\d{2,4})\b",  # MM/DD/YYYY
            r"\b(0?[1-9]|[12][0-9]|3[01])[/-](0?[1-9]|1[0-2])[/-](\d{2,4})\b",  # DD/MM/YYYY
            r"\b\d{4}[/-](0?[1-9]|1[0-2])[/-](0?[1-9]|[12][0-9]|3[01])\b"       # YYYY-MM-DD
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
                break

    # ---- 4. Vendor Name Extraction ----
    vendor_keywords = r"(hospital|dmart|store|center|mart|medical|electricity|power|board|energy|bescom|mseb|tneb|tangedco|bills?|supermarket|bazaar|pharmacy|clinic|institute|solutions|services|technologies|systems|telecom|broadband)"
    company_indicators = r"(pvt|private|ltd|limited|inc|llp|corp|corporation|technologies|solutions|services|company|enterprise|industries|office|your company|group)"

    # Primary: Uppercase header
    for line in lines[:10]:
        if line.strip().isupper() and len(line.strip()) > 4 and len(line.strip().split()) <= 6:
            data["vendor_name"] = line.strip().title()
            break

    # Backup 1: Keyword match (top or bottom)
    if data["vendor_name"] == "NA":
        for line in reversed(lines[-10:] + lines[:10]):
            if re.search(vendor_keywords, line, re.IGNORECASE):
                data["vendor_name"] = re.sub(r"[^\w\s&]", "", line).strip().title()
                break

    # Backup 2: After "Billed To" / "Invoice To"
    if data["vendor_name"] == "NA":
        for idx, line in enumerate(lines):
            if "billed to" in line.lower() or "invoice to" in line.lower():
                if idx + 1 < len(lines):
                    next_line = lines[idx + 1]
                    if re.search(company_indicators, next_line, re.IGNORECASE):
                        data["vendor_name"] = re.sub(r"[^\w\s&]", "", next_line).strip().title()
                        break

    # Backup 3: Email / Domain inference
    if data["vendor_name"] == "NA":
        for line in lines:
            if ".com" in line or "@" in line or "www." in line:
                domain_match = re.search(r"[\w\-]+(?:\.com|\.in|\.org)", line)
                if domain_match:
                    domain = domain_match.group(0)
                    vendor_guess = domain.split(".")[0]
                    data["vendor_name"] = vendor_guess.capitalize() + " (inferred)"
                    break

    if data["vendor_name"] == "NA":
        data["vendor_name"] = "Unknown"

    # ---- 5. Tax Amount ----
    tax_amt_match = re.search(r"\b(Tax|GST|VAT)[\s\S]{0,15}?\$?([0-9.,]{2,})", full_text, re.IGNORECASE)
    if tax_amt_match:
        try:
            data["tax_amount"] = float(tax_amt_match.group(2).replace(",", ""))
        except:
            pass

    # ---- 6. Subtotal ----
    sub_total_match = re.search(r"\b(Sub[- ]?Total)[\s:$]*\$?([0-9.,]+)", full_text, re.IGNORECASE)
    if sub_total_match:
        try:
            data["subtotal_amount"] = float(sub_total_match.group(2).replace(",", ""))
        except:
            pass

    # ---- 7. Total ----
    if data["total_amount"] == 0.0:
        grand_total_match = re.search(r"\b(Total Amount|Grand Total|Total)[\s:$]*\$?([0-9.,]+)", full_text, re.IGNORECASE)
        if grand_total_match:
            try:
                data["total_amount"] = float(grand_total_match.group(2).replace(",", ""))
            except:
                pass

    # ---- 8. Payment Method ----
    method_match = re.search(r"(Payment Method|Mode|Paid via|Payment Type)[^\w]{0,10}([A-Za-z ]+)", full_text, re.IGNORECASE)
    if method_match:
        data["payment_method"] = method_match.group(2).strip()

    return data
