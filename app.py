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

# Logo Filenames
WEB_LOGO = "VP Logo Horizontal Transparent White Lettering.png"
PDF_LOGO = "logo.png"

def extract_backmarket_data(uploaded_file):
    items = []
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages])
        tables = pdf.pages[0].extract_tables()
    
    order_no = re.search(r"Order no\. (\d+)", full_text)
    order_val = order_no.group(1) if order_no else "N/A"
    order_date = re.search(r"Date of order: ([\d/]+)", full_text)
    order_date_val = order_date.group(1) if order_date else "10/03/26"
    
    carrier_match = re.search(r"Shipping method:\s*(.*)", full_text)
    carrier = carrier_match.group(1).strip() if carrier_match else "Standard"
    ship_cost_match = re.search(r"Shipping costs\s*(£[\d\.]+)", full_text)
    ship_cost = ship_cost_match.group(1) if ship_cost_match else "£0.00"

    name_match = re.search(r"Hi\s+([A-Za-z]+),", full_text)
    first_name = name_match.group(1).strip() if name_match else "Lindsay"
    
    full_name_match = re.search(r"Company Capital PCC\n([A-Za-z]+\s+[A-Za-z]+)", full_text)
    full_name = full_name_match.group(1).strip() if full_name_match else f"{first_name} Argent"
    
    addr_match = re.search(r"(Company Capital PCC.*?)(?=\nBilling address|\nDelivery slip)", full_text, re.DOTALL)
    address_block = addr_match.group(1).strip() if addr_match else "Company Capital PCC\nLindsay Argent\nSolar House\n915 High Road\nN12 8QJ London GB"

    grand_total = "£0.00"
    if tables:
        for row in tables[0]:
            if len(row) > 7 and row[0] and row[0].isdigit():
                items.append({
                    'desc': row[1].replace('\n', ' ').strip(),
                    'qty': str(row[2]),
                    'sku': str(row[3]),
                    'total': str(row[7]).replace(',', '.')
                })
            if "TOTAL" in str(row).upper():
                grand_total = str(row[-1]).replace(',', '.')

    return {
        'order_no': order_val,
        'order_date': order_date_val,
        'carrier': carrier,
        'ship_cost': ship_cost,
        'first_name': first_name,
        'full_name': full_name,
        'address_block': address_block,
        'items': items,
        'total': grand_total
    }

def create_invoice_pdf(data):
    pdf = FPDF(unit='mm', format='A4')
    pdf.set_auto_page_break(auto=False) 
    pdf.add_page()
    
    if os.path.exists(PDF_LOGO):
        pdf.image(PDF_LOGO, 10, 8, 46) 
        pdf.set_y(32) 
    else:
        pdf.set_y(10)
        
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, MY_COMPANY_NAME, ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 4.5, f"{MY_COMPANY_ADDRESS}\n{MY_COMPANY_ID}")
    
    pdf.ln(6) 
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
    
    pdf.ln(6) 
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    info_text = f"  Invoice: {data['order_no']}           Date: {data['order_date']}           Shipping Method: {data['carrier']}"
    pdf.cell(0, 10, info_text, 0, 1, 'L', True)
    pdf.ln(4)
    
    w_desc, w_sku, w_qty, w_total = 95, 40, 20, 35
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 9)
    pdf.cell(w_desc, 10, " DESCRIPTION", 1, 0, 'C', True)
    pdf.cell(w_sku, 10, " SKU", 1, 0, 'C', True)
    pdf.cell(w_qty, 10, " QTY", 1, 0, 'C', True)
    pdf.cell(w_total, 10, " TOTAL", 1, 1, 'C', True)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9)
    
    for item in data['items']:
        lines = pdf.multi_cell(w_desc, 5, item['desc'], split_only=True)
        row_h = max(12, len(lines) * 6)
        curr_x, curr_y = pdf.get_x(), pdf.get_y()
        pdf.rect(curr_x, curr_y, w_desc, row_h)
        v_offset = (row_h - (len(lines) * 5)) / 2
        pdf.set_xy(curr_x, curr_y + v_offset)
        pdf.multi_cell(w_desc, 5, item['desc'], border=0, align='C')
        pdf.set_xy(curr_x + w_desc, curr_y)
        pdf.cell(w_sku, row_h, item['sku'], 1, 0, 'C')
        pdf.cell(w_qty, row_h, item['qty'], 1, 0, 'C')
        pdf.cell(w_total, row_h, item['total'], 1, 1, 'C')
    
    pdf.ln(3)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(w_desc + w_sku + w_qty, 8, "Shipping Cost: ", 0, 0, 'R')
    pdf.cell(w_total, 8, data['ship_cost'], 1, 1, 'C')
    
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_desc + w_sku + w_qty, 10, "TOTAL: ", 0, 0, 'R')
    pdf.cell(w_total, 10, data['total'], 1, 1, 'C')
    
    pdf.ln(6)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 6, f"Hi {data['first_name']},", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.ln(2)
    msg1 = f"We hope you enjoy your order #{data['order_no']} from Vertical Passage LTD.".strip()
    msg2 = "Looks like your phone just found its new favorite case.".strip()
    pdf.multi_cell(0, 5, msg1 + "\n" + msg2, align='C')
    pdf.ln(3)
    help_msg = 'Need help? Just log in to your Back Market account, go to Orders, and click "Get Help."'.strip()
    pdf.multi_cell(0, 5, help_msg, align='C')
    pdf.ln(5)
    pdf.cell(0, 5, "Enjoy your new case,", ln=True, align='C')
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, "Vertical Passage", ln=True, align='C')
    pdf.set_y(-12) 
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(150, 150, 150)
    pdf.cell(0, 5, "VAT inclusive at import. No additional tax charged to customer.", ln=True, align='C')
    return pdf.output(dest='S').encode('latin-1')

# --- STREAMLIT APP ---
st.set_page_config(page_title="Invoice Generator", page_icon="📄")

# CUSTOM CSS FOR POSITIONING
st.markdown("""
    <style>
    /* Gemini look: logo closer to top */
    .logo-container {
        padding-top: 10px !important; /* SIGNIFICANTLY REDUCED */
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
    }
    .stTitle {
        text-align: center;
        width: 100%;
        font-weight: 300 !important;
        letter-spacing: -1px;
        padding-top: 10px !important; 
        padding-bottom: 30px !important;
    }
    .stFileUploader {
        padding-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# Centered Logo pushed toward the top
if os.path.exists(WEB_LOGO):
    st.markdown('<div class="logo-container">', unsafe_allow_html=True)
    st.image(WEB_LOGO, width=400)
    st.markdown('</div>', unsafe_allow_html=True)

# Title immediately below logo
st.title("Invoice Generator", anchor=False)

if 'uploader_key' not in st.session_state:
    st.session_state.uploader_key = 0

f = st.file_uploader("Upload Back Market Delivery Slip", type="pdf", key=f"uploader_{st.session_state.uploader_key}")

if f:
    try:
        data = extract_backmarket_data(f)
        st.success(f"Order {data['order_no']} loaded.")
        pdf_out = create_invoice_pdf(data)
        download_filename = f"{data['full_name']}_{data['order_no']}.pdf"
        
        col_dl, col_rs = st.columns([3, 1])
        with col_dl:
            st.download_button("Download Invoice", pdf_out, download_filename, use_container_width=True)
        with col_rs:
            if st.button("Reset", use_container_width=True):
                st.session_state.uploader_key += 1
                st.rerun()
                
    except Exception as e:
        st.error(f"Error: {e}")
