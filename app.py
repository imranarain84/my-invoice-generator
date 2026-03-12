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
    
    # 1. Extract Order Metadata
    order_no = re.search(r"Order no\. (\d+)", full_text)
    order_date = re.search(r"Date of order: ([\d/]+)", full_text)
    
    # 2. Elegant Address Extraction
    # We look for the block between "Shipping address" and "Billing address"
    ship_match = re.search(r"Shipping address\n(.*?)\nBilling address", full_text, re.DOTALL)
    address_block = ship_match.group(1).strip() if ship_match else "Address Not Found"
    
    # 3. Product Table Logic
    product_desc, qty, unit_price, total_price = "Item", "0", "£0.00", "£0.00"
    if tables and len(tables[0]) > 1:
        for row in tables[0]:
            if any("Back Market" in str(cell) for cell in row):
                product_desc = row[1].replace('\n', ' ')
                qty = row[2]
                unit_price = row[4]
                total_price = row[7]
                break

    return {
        'order_no': order_no.group(1) if order_no else "N/A",
        'order_date': order_date.group(1) if order_date else "N/A",
        'address_block': address_block,
        'item_desc': product_desc,
        'qty': qty,
        'unit_price': unit_price,
        'total': total_price
    }

def create_invoice_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # LOGO & SENDER INFO
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 40)
        pdf.set_y(40)
    else:
        pdf.set_y(10)
        
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 7, MY_COMPANY_NAME, ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 4, f"{MY_COMPANY_ADDRESS}\n{MY_COMPANY_ID}")
    
    pdf.ln(12)
    
    # ADDRESS SECTION (ELEGANT COLUMNS)
    pdf.set_font("Arial", 'B', 9)
    pdf.set_text_color(100, 100, 100) # Professional Gray
    pdf.cell(95, 5, "BILLED TO", 0, 0)
    pdf.cell(95, 5, "DELIVERED TO", 0, 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    curr_y = pdf.get_y()
    pdf.multi_cell(90, 5, data['address_block'])
    pdf.set_xy(105, curr_y)
    pdf.multi_cell(90, 5, data['address_block'])
    
    pdf.ln(12)

    # INVOICE DETAILS BAR
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"  Invoice: #INV-{data['order_no']}           Date: {data['order_date']}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # TABLE
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(110, 10, " Description", 1, 0, 'L', True)
    pdf.cell(15, 10, " QTY", 1, 0, 'C', True)
    pdf.cell(30, 10, " PRICE", 1, 0, 'C', True)
    pdf.cell(35, 10, " TOTAL (TTC)", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=8)
    
    x, y = pdf.get_x(), pdf.get_y()
    pdf.multi_cell(110, 6, data['item_desc'], 1)
    h = pdf.get_y() - y
    pdf.set_xy(x + 110, y)
    pdf.cell(15, h, data['qty'], 1, 0, 'C')
    pdf.cell(30, h, data['unit_price'], 1, 0, 'C')
    pdf.cell(35, h, data['total'], 1, 1, 'C')
    
    # TOTAL
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(155, 10, "GRAND TOTAL (TTC): ", 0, 0, 'R')
    pdf.cell(35, 10, data['total'], 1, 1, 'C')
    
    # FOOTER
    pdf.set_y(-40)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(0, 4, "Note: VAT paid at import. Price inclusive of all taxes.\nLate payment subject to 40 Euro indemnity (L.441-3 Commercial Code).", align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- STREAMLIT UI ---
st.set_page_config(page_title="Invoice Generator", layout="centered")
st.title("📄 Professional Invoice Generator")

uploaded_file = st.file_uploader("Upload Back Market Delivery Slip", type="pdf")

if uploaded_file:
    with st.spinner("Reading PDF..."):
        data = extract_backmarket_data(uploaded_file)
    
    # Display elegant preview
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Order Info")
        st.write(f"**Order:** {data['order_no']}")
        st.write(f"**Date:** {data['order_date']}")
    with col2:
        st.subheader("Customer")
        st.text(data['address_block'])
        
    st.divider()
    
    pdf_bytes = create_invoice_pdf(data)
    st.download_button(
        label="⬇️ Download PDF Invoice",
        data=pdf_bytes,
        file_name=f"Invoice_{data['order_no']}.pdf",
        mime="application/pdf",
        use_container_width=True
    )
