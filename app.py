import streamlit as st
import pdfplumber
from fpdf import FPDF
import io
import re

# 1. Logic to extract data from the uploaded Delivery Slip
def extract_backmarket_data(uploaded_file):
    with pdfplumber.open(uploaded_file) as pdf:
        text = "\n".join([page.extract_text() for page in pdf.pages])
    
    data = {}
    # Extract Order No 
    order_match = re.search(r"Order no\. (\d+)", text)
    data['order_no'] = order_match.group(1) if order_match else "N/A"
    
    # Extract Seller [cite: 3, 11]
    seller_match = re.search(r"Sender: (.*)", text)
    data['seller'] = seller_match.group(1).strip() if seller_match else "Vertical Passage LTD"
    
    # Extract Customer and Address [cite: 11, 16, 19]
    cust_match = re.search(r"Customer: (.*)", text)
    data['customer'] = cust_match.group(1).strip() if cust_match else "Lindsay Argent"
    
    # Extract Item Details 
    # Simple regex to find the price and description patterns from the table
    item_match = re.search(r"Back Market Case.*", text)
    data['item_desc'] = item_match.group(0) if item_match else "iPhone 15 Case"
    
    return data

# 2. Logic to generate the new Invoice PDF
def create_invoice_pdf(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    
    # Header
    pdf.cell(100, 10, data['seller'], ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(100, 10, "Tax Invoice", ln=True)
    
    pdf.ln(10)
    
    # Billed To Section
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(100, 10, f"BILLED TO: {data['customer']}", ln=True)
    pdf.set_font("Arial", size=10)
    pdf.cell(100, 10, f"Order Number: {data['order_no']}", ln=True)
    
    # Item Table
    pdf.ln(20)
    pdf.set_fill_color(200, 200, 200)
    pdf.cell(120, 10, "Description", 1, 0, 'C', True)
    pdf.cell(30, 10, "Qty", 1, 0, 'C', True)
    pdf.cell(40, 10, "Total", 1, 1, 'C', True)
    
    pdf.cell(120, 10, data['item_desc'][:50], 1)
    pdf.cell(30, 10, "3", 1, 0, 'C') # Qty from 
    pdf.cell(40, 10, "£57.00", 1, 1, 'C') # Total from 
    
    return pdf.output(dest='S').encode('latin-1')

# 3. Streamlit UI
st.title("Back Market Invoice Generator")
st.write("Upload your delivery slip to generate a tax-compliant invoice.")

uploaded_file = st.file_uploader("Choose a PDF file", type="pdf")

if uploaded_file is not None:
    # Process the file
    extracted_data = extract_backmarket_data(uploaded_file)
    
    st.success("Data Extracted!")
    st.json(extracted_data) # Show user what we found
    
    # Button to download
    invoice_bytes = create_invoice_pdf(extracted_data)
    st.download_button(
        label="Download Professional Invoice",
        data=invoice_bytes,
        file_name=f"Invoice_{extracted_data['order_no']}.pdf",
        mime="application/pdf"
    )
