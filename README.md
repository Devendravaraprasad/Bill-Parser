

**Receipt Parser – Intelligent Bill Data Extractor**


**Features:**

* Upload scanned receipt or invoice images.
* Automatically extract key fields:

  * Invoice Number
  * Invoice Date
  * Vendor Name
  * Subtotal Amount
  * Tax Amount
  * Total Amount
  * Payment Method
* Visualize:

  * Total spends
  * Top vendors
  * Billing trends
* Search and filter through uploaded and parsed receipts.

**Project Architecture:**

* Backend: Python, with rule-based logic using regex and date parsing.
* OCR: Uses pytesseract by default; PaddleOCR optionally for better layout recognition.
* Frontend: Built using Streamlit for interactive UI.
* Data Storage: In-memory (can extend to CSV, SQLite, or JSON).

**Setup Steps:**

* Install Python 3.x and clone the repository.
* Create a virtual environment and activate it.
* Run `pip install -r requirements.txt`.
* Launch the app using `streamlit run app.py`.
* Upload receipt images and get structured data output.

**Design Choices:**

* Rule-based extraction for speed and interpretability.
* Vendor name detected using:

  * Context keywords (e.g., hospital, D-Mart, medical)
  * Domain inference (from email or website lines)
* Date formats handled flexibly with multiple regex patterns.
* OCR engine is modular—can swap between pytesseract and PaddleOCR.

**Limitations:**

* OCR quality depends on image clarity.
* Free-form or poorly formatted receipts may not be fully parsed.
* Does not extract line items like product names or quantities yet.
* Only English-language receipts are supported.
* Payment method detection is basic.

**Assumptions:**

* Receipts follow standard formats (dates, currency).
* Vendor names are either keyword-matched or inferred from domain/email.
* User uploads one image per receipt at a time.

**Future Enhancements:**

* Add support for PDF files.
* Include item-wise breakdown with quantity and unit prices.
* Integrate with Excel/CSV export or accounting APIs.
* Add multi-language OCR support.
* Improve vendor classification using ML/NLP if needed.

**Author Details:**

* Name: Devendravaraprasad R
* Email: [devendravaraprasadr@gmail.com]
* Phone: +91-9392878526

