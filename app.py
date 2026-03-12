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
    
    order_no = re.search(r"Order no\. (\d+)", full_text)
    order_val = order_no.group(1) if order_no else "78197766"
    order_date = re.search(r"Date of order: ([\d/]+)", full_text)
    order_date_val = order_date.group(1) if order_date else "10/03/26"
    
    # Extract First Name for personalized message
    name_match = re.search(r"Customer:\s*(\w+)", full_text)
    first_name = name_match.group(1) if name_match else "Customer"
    
    addr_match = re.search(r"(Company Capital PCC.*?)(?=\nBilling address|\nDelivery slip)", full_text, re.DOTALL)
    address_block = addr_match.group(1).strip() if addr_match else "Company Capital PCC\nLindsay Argent\nSolar House\n915 High Road\nN12 8QJ London GB"

    item_desc, sku, qty, total = "Item Description", "SKU", "0", "£57.00"

    if tables:
        for row in tables[0]:
            if any("Back Market" in str(cell) for cell in row if cell):
                item_desc = row[1].replace('\n', ' ').strip()
                qty = str(row[2])
                sku = str(row[3])
                total = str(row[7]).replace(',', '.')
                break
    
    return {
        'order_no': order_val,
        'order_date': order_date_val,
        'first_name': first_name,
        'address_block': address_block,
        'item_desc': item_desc,
        'sku': sku,
        'qty': qty,
        'total': total
    }

def create_invoice_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. LOGO & SENDER (Blue Box fix: moved closer)
    if os.path.exists(PDF_LOGO):
        pdf.image(PDF_LOGO, 10, 8, 46) 
        pdf.set_y(32) # Moved up (closer to logo)
    else:
        pdf.set_y(10)
        
    pdf.set_x(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 6, MY_COMPANY_NAME, ln=True)
    pdf.set_font("Arial", size=9)
    pdf.multi_cell(0, 4, f"{MY_COMPANY_ADDRESS}\n{MY_COMPANY_ID}")
    
    # 2. SHIFT DOWN (Red Box fix: +15% vertical shift)
    pdf.ln(25) # Increased gap to move everything else down
    
    # BILLED/DELIVERED TO
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
    
    pdf.ln(12)

    # INVOICE INFO BAR
    pdf.set_fill_color(245, 245, 245)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, f"  Invoice: {data['order_no']}           Date: {data['order_date']}", 0, 1, 'L', True)
    pdf.ln(5)
    
    # TABLE
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
    
    lines = pdf.multi_cell(w_desc, 5, data['item_desc'], split_only=True)
    row_h = max(12, len(lines) * 6)
    curr_x, curr_y = pdf.get_x(), pdf.get_y()
    
    pdf.rect(curr_x, curr_y, w_desc, row_h)
    v_offset = (row_h - (len(lines) * 5)) / 2
    pdf.set_xy(curr_x, curr_y + v_offset)
    pdf.multi_cell(w_desc, 5, data['item_desc'], border=0, align='C')
    
    pdf.set_xy(curr_x + w_desc, curr_y)
    pdf.cell(w_sku, row_h, data['sku'], 1, 0, 'C')
    pdf.cell(w_qty, row_h, data['qty'], 1, 0, 'C')
    pdf.cell(w_total, row_h, data['total'], 1, 1, 'C')
    
    # TOTAL
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(w_desc + w_sku + w_qty, 10, "TOTAL: ", 0, 0, 'R')
    pdf.cell(w_total, 10, data['total'], 1, 1, 'C')
    
    # 3. CUSTOMER MESSAGE (Orange Box)
    pdf.ln(15)
    pdf.set
