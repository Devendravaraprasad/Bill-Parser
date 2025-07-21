import streamlit as st
from PIL import Image
import pytesseract
import cv2
import numpy as np
import pandas as pd

from parser import extract_receipt_data
from db import init_db, insert_receipt, fetch_all_receipts

# Tesseract path (adjust as needed)
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r'C:\Users\devevara\OneDrive - Magna\DevaProjects\8-byte\Tesseract-OCR\tesseract.exe'


# Streamlit setup
st.set_page_config(page_title="Receipt OCR App", layout="wide")
st.title("🧾 Receipt OCR & Insights App")

# Initialize DB
init_db()

# Tabs
upload_tab, visualize_tab, search_tab = st.tabs(["📤 Upload & View", "📊 Visualize", "🔍 Search"])

# Updated column schema
COLUMNS = [
    "ID", "Invoice Number", "Invoice Date", "Vendor Name",
    "Subtotal Amount", "Tax Amount", "Total Amount", "Payment Method"
]


import cv2
import numpy as np
from PIL import Image
import pytesseract
import pandas as pd
import streamlit as st

def enhance_image(pil_img):
    # Convert to OpenCV grayscale
    img = np.array(pil_img.convert("RGB"))
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Resize to make small fonts OCR-friendly
    img = cv2.resize(img, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC)

    # Reduce noise
    img = cv2.GaussianBlur(img, (5, 5), 0)

    # Adaptive threshold for better contrast
    img = cv2.adaptiveThreshold(img, 255,
                                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY,
                                11, 2)
    return img

# --- Upload Tab ---
with upload_tab:
    uploaded_file = st.file_uploader("📤 Upload receipt image", type=["png", "jpg", "jpeg"])

    if uploaded_file:
        pil_img = Image.open(uploaded_file)

        # Display original
        st.image(pil_img, caption="🖼️ Uploaded Image", use_container_width=False, width=600)

        try:
            # Step 1: Enhance
            enhanced_img = enhance_image(pil_img)

            # Step 2: Show enhanced image for reference
            st.image(enhanced_img, caption="✨ Enhanced for OCR", use_container_width=False, width=600, channels="GRAY")

            # Step 3: OCR on enhanced image
            text = pytesseract.image_to_string(enhanced_img, config="--psm 6")

            st.subheader("📄 Raw OCR Text")
            st.text(text)

            # Step 4: Extract structured data
            structured_data = extract_receipt_data(text)

            st.subheader("📦 Structured Data")
            st.json(structured_data)

            # Step 5: Insert to DB if valid
            if "Error" not in structured_data:
                insert_receipt(structured_data)
                st.success("✅ Receipt stored successfully.")
            else:
                st.error(structured_data["Error"])

        except Exception as e:
            st.error(f"❌ OCR failed: {e}")

    # --- Show stored receipts ---
    st.markdown("---")
    st.subheader("📂 All Stored Receipts")

    records = fetch_all_receipts()
    if records:
        try:
            df = pd.DataFrame(records, columns=COLUMNS)
            st.dataframe(df, use_container_width=True)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download CSV", csv, "receipts.csv", "text/csv")
        except Exception as e:
            st.error(f"❌ Error displaying receipts: {e}")
    else:
        st.info("ℹ️ No receipts found yet.")


with visualize_tab:
    st.subheader("📊 Receipt Insights")
    records = fetch_all_receipts()

    if not records:
        st.warning("⚠️ No data to visualize.")
    else:
        df = pd.DataFrame(records, columns=COLUMNS)

        df["Total Amount"] = pd.to_numeric(df["Total Amount"].astype(str).str.replace(",", ""), errors="coerce")
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], format="%Y-%m-%d", errors="coerce")
        df = df.dropna(subset=["Total Amount", "Invoice Date"])

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### 💳 Payment Method Share")
            fig_pie = df["Payment Method"].value_counts().plot.pie(autopct="%1.1f%%", figsize=(3, 3)).get_figure()
            st.pyplot(fig_pie)

        with col2:
            st.markdown("### 🏪 Vendor Frequency")
            vendor_counts = df["Vendor Name"].value_counts()
            st.bar_chart(vendor_counts)

        st.markdown("### 📈 Spend Statistics")
        col1, col2, col3 = st.columns(3)
        col1.metric("Mean", f"₹{df['Total Amount'].mean():.2f}")
        col2.metric("Median", f"₹{df['Total Amount'].median():.2f}")
        mode = df['Total Amount'].mode()
        col3.metric("Mode", f"₹{mode[0]:.2f}" if not mode.empty else "N/A")

        st.markdown("### 📅 Monthly Trend")
        df["Month"] = df["Invoice Date"].dt.to_period("M")
        trend = df.groupby("Month")["Total Amount"].sum().sort_index()
        st.line_chart(trend, use_container_width=True)

        st.markdown("### 🔄 3-Month Rolling Avg")
        df_sorted = df.sort_values("Invoice Date").set_index("Invoice Date")
        rolling = df_sorted["Total Amount"].rolling("90D").mean()
        st.line_chart(rolling, use_container_width=True)

# Search
with search_tab:
    st.subheader("🔍 Search Receipts")
    records = fetch_all_receipts()

    if not records:
        st.warning("⚠️ No data to search.")
    else:
        df = pd.DataFrame(records, columns=COLUMNS)
        df["Invoice Date"] = pd.to_datetime(df["Invoice Date"], format="%Y-%m-%d", errors="coerce")
        df["Total Amount"] = pd.to_numeric(df["Total Amount"].astype(str).str.replace(",", ""), errors="coerce")

        use_vendor = st.checkbox("Filter by Vendor")
        use_month_year = st.checkbox("Filter by Month and Year")
        use_date_range = st.checkbox("Filter by Date Range")
        use_amount_range = st.checkbox("Filter by Amount Range")

        vendor = ""
        selected_month = selected_year = None
        start_date = end_date = None
        min_amt = max_amt = None

        if use_vendor:
            vendor = st.text_input("Vendor Name")

        if use_month_year:
            col1, col2 = st.columns(2)
            with col1:
                selected_month = st.selectbox("Month", list(range(1, 13)))
            with col2:
                selected_year = st.number_input("Year", min_value=2000, max_value=2100, value=2025)

        if use_date_range:
            col3, col4 = st.columns(2)
            with col3:
                start_date = st.date_input("Start Date")
            with col4:
                end_date = st.date_input("End Date")

        if use_amount_range:
            col5, col6 = st.columns(2)
            with col5:
                min_amt = st.number_input("Min Amount", value=0.0, step=100.0)
            with col6:
                max_amt = st.number_input("Max Amount", value=10000.0, step=100.0)

        if st.button("🔎 Search"):
            filtered = df.copy()

            if use_vendor and vendor:
                filtered = filtered[filtered["Vendor Name"].str.contains(vendor, case=False, na=False)]

            if use_month_year and selected_month and selected_year:
                filtered = filtered[
                    (filtered["Invoice Date"].dt.month == selected_month) &
                    (filtered["Invoice Date"].dt.year == selected_year)
                ]

            if use_date_range and start_date and end_date:
                filtered = filtered[
                    (filtered["Invoice Date"] >= pd.to_datetime(start_date)) &
                    (filtered["Invoice Date"] <= pd.to_datetime(end_date))
                ]

            if use_amount_range and min_amt is not None and max_amt is not None:
                filtered = filtered[
                    (filtered["Total Amount"] >= min_amt) &
                    (filtered["Total Amount"] <= max_amt)
                ]

            if not filtered.empty:
                st.success(f"{len(filtered)} result(s) found.")
                st.dataframe(filtered, use_container_width=True)
            else:
                st.info("No matching records found.")
