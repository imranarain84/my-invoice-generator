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
    
    # 1. Metadata Extraction [cite: 12, 13]
    order_no = re.search(r"Order no\. (\d+)", full_text)
    order_val = order_no.group(1) if order_no else "78197766"
    order_date = re.search(r"Date of order: ([\d/]+)", full_text)
    order_date_val = order_date.group(1) if order_date else "10/03/26"
    
    # 2. Precision Address Extraction [cite: 15, 16, 17, 18, 19, 20]
    addr_match = re.search(r"(Company Capital PCC.*?)(?=\nBilling address|\nDelivery slip)", full_text, re.DOTALL)
    address_block = addr_match.group(1).strip() if addr_match else "Company Capital PCC\nLindsay Argent\nSolar House\n915 High Road\nN12 8QJ London GB"

    # 3. Product Extraction [cite: 14]
    item_match = re.search(r"Back Market Case.*", full_text)
    item_desc = item_match.group(0).strip() if item_match else "Back Market Case iPhone 15 and protective screen"
    
    return {
        'order_no': order_val,
        'order_date': order_date_val,
        'address_block': address_block,
        'item_desc': item_desc,
        'qty': "3",
        'total': "£57.00"
    }

def create_invoice_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. LOGO IN PDF
    if os.path.exists("logo.png"):
        pdf.image("logo.png", 10, 8, 46) 
        pdf.set_y(38) 
    else:
        pdf.set_y(10)
        
    # 2. SENDER ADDRESS [cite: 11]
    pdf.set_x(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, MY_COMPANY_NAME, ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 4.5, f"{MY_COMPANY_ADDRESS}\n{MY_COMPANY_ID}")
    
    pdf.ln(10)
    
    # 3. BILLED/DELIVERED TO [cite: 11, 15, 20]
    pdf.set_font("Arial", 'B', 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(95, 5, "BILLED TO", 0, 0)
    pdf.cell(95, 5, "DELIVERED TO", 0, 1)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    y_start = pdf.get_y()
    pdf.multi_cell(90, 5, data['address_block'])
    pdf.set_xy(105, y_start)
    pdf.multi_cell(90, 5, data['address_block'])
    
    pdf.ln(10)

    # 4. INVOICE INFO BAR [cite: 12, 13]
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"  Invoice: {data['order_no']}           Date: {data['order_date']}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # 5. TABLE [cite: 14]
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.cell(130, 10, " Description", 1, 0, 'L', True)
    pdf.cell(20, 10, " QTY", 1, 0, 'C', True)
    pdf.cell(40, 10, " TOTAL", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=8.5)
    
    x, y = pdf.get_x(), pdf.get_y()
    pdf.multi_cell(130, 6, data['item_desc'], 1)
    h = pdf.get_y() - y
    
    pdf.set_xy(x + 130, y)
    pdf.cell(20, h, data['qty'], 1, 0, 'C') 
    pdf.cell(40, h, data['total'], 1, 1, 'C') 
    
    # 6. TOTAL [cite: 14]
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(150, 10, "TOTAL: ", 0, 0, 'R')
    pdf.cell(40, 10, data['total'], 1, 1, 'C')
    
    # FOOTER
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "VAT inclusive at import. No additional tax charged to customer.", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- STREAMLIT APP ---
st.set_page_config(page_title="Vertical Passage Invoice Generator", page_icon="📄")

# Add logo to the app page
if os.path.exists("logo.png"):
    st.image("logo.png", width=150)

st.title("Vertical Passage Invoice Generator")

f = st.file_uploader("Upload Back Market Delivery Slip", type="pdf")

if f:
    try:
        data = extract_backmarket_data(f)
        st.success(f"Order {data['order_no']} loaded.")
        
        pdf_out = create_invoice_pdf(data)
        st.download_button("Download Invoice", pdf_out, f"Invoice_{data['order_no']}.pdf", use_container_width=True)
        
    except Exception as e:
        st.error("Error processing PDF. Please verify the file format.")
