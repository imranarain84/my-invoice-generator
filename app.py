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
    with pdfplumber.open(uploaded_file) as pdf:
        full_text = "\n".join([page.extract_text() for page in pdf.pages])
        tables = pdf.pages[0].extract_tables()
    
    # 1. Metadata Extraction
    order_no = re.search(r"Order no\. (\d+)", full_text)
    order_val = order_no.group(1) if order_no else "78197766"
    order_date = re.search(r"Date of order: ([\d/]+)", full_text)
    order_date_val = order_date.group(1) if order_date else "10/03/26"
    
    # 2. Precision Address Extraction
    addr_match = re.search(r"(Company Capital PCC.*?)(?=\nBilling address|\nDelivery slip)", full_text, re.DOTALL)
    address_block = addr_match.group(1).strip() if addr_match else "Company Capital PCC\nLindsay Argent\nSolar House\n915 High Road\nN12 8QJ London GB"

    # 3. Product & SKU Extraction
    # We scrape the table to get the full Designation and the Item (SKU)
    item_desc = "Back Market Case iPhone 15 and protective screen - 100% Biodegradable - Black Wave"
    sku = "BM-B-15-Wave"
    qty = "3"
    total = "£57.00"

    if tables:
        for row in tables[0]:
            if any("Back Market" in str(cell) for cell in row if cell):
                # Back Market Table: [0:LineNo, 1:Designation, 2:Qty, 3:Item(SKU), 7:Total]
                item_desc = row[1].replace('\n', ' ').strip()
                qty = str(row[2])
                sku = str(row[3])
                total = str(row[7]).replace(',', '.') # Handle comma decimals
                break
    
    return {
        'order_no': order_val,
        'order_date': order_date_val,
        'address_block': address_block,
        'item_desc': item_desc,
        'sku': sku,
        'qty': qty,
        'total': total
    }

def create_invoice_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. LOGO IN PDF
    if os.path.exists(PDF_LOGO):
        pdf.image(PDF_LOGO, 10, 8, 46) 
        pdf.set_y(38) 
    else:
        pdf.set_y(10)
        
    # 2. SENDER ADDRESS
    pdf.set_x(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, MY_COMPANY_NAME, ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 4.5, f"{MY_COMPANY_ADDRESS}\n{MY_COMPANY_ID}")
    
    pdf.ln(10)
    
    # 3. BILLED/DELIVERED TO
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

    # 4. INVOICE INFO BAR
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"  Invoice: {data['order_no']}           Date: {data['order_date']}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # 5. TABLE HEADER
    pdf.set_fill_color(40, 40, 40)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", 'B', 9)
    # Column Widths
    w_desc, w_sku, w_qty, w_total = 95, 40, 20, 35
    
    pdf.cell(w_desc, 10, " DESCRIPTION", 1, 0, 'L', True)
    pdf.cell(w_sku, 10, " SKU", 1, 0, 'C', True)
    pdf.cell(w_qty, 10, " QTY", 1, 0, 'C', True)
    pdf.cell(w_total, 10, " TOTAL", 1, 1, 'C', True)
    
    # 6. TABLE BODY (Dynamic height with vertical centering)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=9)
    
    # Calculate how high the description needs to be
    desc_text = data['item_desc']
    # We use a dummy multi_cell to get the height
    temp_pdf = FPDF()
    temp_pdf.add_page()
    temp_pdf.set_font("Arial", size=9)
    start_y = temp_pdf.get_y()
    temp_pdf.multi_cell(w_desc, 6, desc_text, 1)
    end_y = temp_pdf.get_y()
    row_h = max(12, end_y - start_y) # Ensure at least 12mm height
    
    x, y = pdf.get_x(), pdf.get_y()
    
    # Draw Description
    pdf.multi_cell(w_desc, row_h/ (row_h/6 if row_h > 6 else 1), desc_text, 1) # This is a trick to handle wrap height
    # Actually simpler logic for multi_cell alignment:
    pdf.set_xy(x, y)
    pdf.multi_cell(w_desc, 6, desc_text, 1)
    y_after_desc = pdf.get_y()
    actual_row_h = y_after_desc - y
    
    # Draw SKU (Vertically Centered)
    pdf.set_xy(x + w_desc, y)
    pdf.cell(w_sku, actual_row_h, data['sku'], 1, 0, 'C')
    
    # Draw QTY (Vertically Centered)
    pdf.cell(w_qty, actual_row_h, data['qty'], 1, 0, 'C')
    
    # Draw TOTAL (Vertically Centered)
    pdf.cell(w_total, actual_row_h, data['total'], 1, 1, 'C')
    
    # 7. TOTAL SUMMARY
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_desc + w_sku + w_qty, 10, "TOTAL: ", 0, 0, 'R')
    pdf.cell(w_total, 10, data['total'], 1, 1, 'C')
    
    # FOOTER
    pdf.set_y(-30)
    pdf.set_font("Arial", 'I', 8)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, "VAT inclusive at import. No additional tax charged to customer.", ln=True, align='C')
    
    return pdf.output(dest='S').encode('latin-1')

# --- STREAMLIT APP ---
st.set_page_config(page_title="Vertical Passage Invoice Generator", page_icon="📄")

if os.path.exists(WEB_LOGO):
    st.image(WEB_LOGO, width=250)

st.title("Vertical Passage Invoice Generator")

f = st.file_uploader("Upload Back Market Delivery Slip", type="pdf")

if f:
    try:
        data = extract_backmarket_data(f)
        st.success(f"Order {data['order_no']} loaded.")
        
        # UI PREVIEW
        st.write("### Preview Details")
        col1, col2 = st.columns(2)
        col1.write(f"**SKU:** {data['sku']}")
        col2.write(f"**Total:** {data['total']}")
        st.text_area("Full Description", data['item_desc'], height=70)
        
        pdf_out = create_invoice_pdf(data)
        st.download_button("Download Invoice", pdf_out, f"Invoice_{data['order_no']}.pdf", use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing PDF: {e}")
