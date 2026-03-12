import streamlit as st
import pdfplumber
from fpdf import FPDF
import io
import re
import os

# --- YOUR BUSINESS DETAILS ---
MY_COMPANY_NAME = "Vertical Passage LTD"
MY_COMPANY_ADDRESS = "Unit 2 More Plus Central Park\nHudson Ave, Severn Beach\nBRISTOL, BS35 4EL"
MY_COMPANY_ID = "Company ID: 12345678"

def extract_backmarket_data(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages])
        tables = pdf.pages[0].extract_tables()
    
    # 1. Metadata Extraction
    order_no = re.search(r"Order no\. (\d+)", full_text)
    order_date = re.search(r"Date of order: ([\d/]+)", full_text)
    
    # 2. Address Extraction (Improved for elegant display)
    # Extracting the block specifically between Shipping and Billing headers
    addr_search = re.search(r"Shipping address\s*\n(.*?)\nBilling address", full_text, re.DOTALL)
    address_raw = addr_search.group(1).strip() if addr_search else "Address Not Found"
    
    # 3. Table Extraction with Safety Checks (Prevents IndexError)
    product_desc, qty, unit_price, total_price = "Product", "1", "£0.00", "£0.00"
    
    if tables:
        for row in tables[0]:
            # Look for rows containing item descriptions
            if any("Back Market" in str(cell) for cell in row if cell):
                # We use 'min' and length checks to ensure we don't grab a column that doesn't exist
                product_desc = row[1].replace('\n', ' ') if len(row) > 1 else "Item"
                qty = row[2] if len(row) > 2 else "1"
                # If column 4 (unit price) is missing, we calculate it or check column 7
                unit_price = row[4] if len(row) > 4 else "£0.00"
                total_price = row[-1] if len(row) > 0 else "£0.00" # Grab the last column for total
                break

    return {
        'order_no': order_no.group(1) if order_no else "N/A",
        'order_date': order_date.group(1) if order_date else "10/03/26",
        'address_block': address_raw,
        'item_desc': product_desc,
        'qty': qty,
        'unit_price': unit_price,
        'total': total_price
    }

def create_invoice_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # LOGO & SENDER
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 40)
        pdf.set_y(40)
    else:
        pdf.set_y(10)
        
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 7, MY_COMPANY_NAME, ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 5, f"{MY_COMPANY_ADDRESS}\n{MY_COMPANY_ID}")
    
    pdf.ln(12)
    
    # ELEGANT ADDRESS DISPLAY
    pdf.set_font("Arial", 'B', 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(95, 5, "BILLED TO", 0, 0)
    pdf.cell(95, 5, "DELIVERED TO", 0, 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    y_start = pdf.get_y()
    # Billing Side
    pdf.multi_cell(90, 5, data['address_block'])
    # Delivery Side (Mirrored)
    pdf.set_xy(105, y_start)
    pdf.multi_cell(90, 5, data['address_block'])
    
    pdf.ln(12)

    # INVOICE INFO BAR
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"  Invoice: #INV-{data['order_no']}           Date: {data['order_date']}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # TABLE
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(115, 10, " Description", 1, 0, 'L', True)
    pdf.cell(15, 10, " QTY", 1, 0, 'C', True)
    pdf.cell(30, 10, " UNIT", 1, 0, 'C', True)
    pdf.cell(30, 10, " TOTAL", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=8)
    
    # Handle multi-line product descriptions elegantly
    x, y = pdf.get_x(), pdf.get_y()
    pdf.multi_cell(115, 6, data['item_desc'], 1)
    new_y = pdf.get_y()
    h = new_y - y
    
    pdf.set_xy(x + 115, y)
    pdf.cell(15, h, data['qty'], 1, 0, 'C')
    pdf.cell(30, h, data['unit_price'], 1, 0, 'C')
    pdf.cell(30, h, data['total'], 1, 1, 'C')
    
    # TOTAL
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(160, 10, "TOTAL TTC: ", 0, 0, 'R')
    pdf.cell(30, 10, data['total'], 1, 1, 'C')
    
    # FOOTER
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "VAT inclusive at import. No additional tax charged to customer.", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- APP INTERFACE ---
st.set_page_config(page_title="Back Market Invoice Generator")
st.title("💼 Professional Invoice Generator")

f = st.file_uploader("Upload Delivery Slip", type="pdf")

if f:
    # Use a try/except block just in case of unexpected PDF weirdness
    try:
        data = extract_backmarket_data(f)
        st.success(f"Successfully read Order #{data['order_no']}")
        
        # Download Button
        pdf_out = create_invoice_pdf(data)
        st.download_button("⬇️ Download Elegant Invoice", pdf_out, f"Invoice_{data['order_no']}.pdf", use_container_width=True)
        
    except Exception as e:
        st.error(f"Something went wrong reading this PDF. Please ensure it is a standard Back Market delivery slip.")
