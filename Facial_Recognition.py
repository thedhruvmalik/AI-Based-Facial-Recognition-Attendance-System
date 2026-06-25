import streamlit as st
import google.generativeai as genai
import pandas as pd
import json
import os
import io

# --- Configuration and Setup ---

# Set your Gemini API key directly in the code.
# Note: It's often recommended to use environment variables for keys in production.
API_KEY = "AIzaSyD_WWpfEdXu-7PAmSL9pI67IqTQ67Pa9yk"
genai.configure(api_key=API_KEY)

# Initialize the Gemini model for image and text understanding
model = genai.GenerativeModel("gemini-2.5-flash-preview-05-20")

# --- App UI and Logic ---

st.title("Document Data Extractor")
st.markdown("Upload a PDF, image, or bill to extract key information.")

# File Uploader component - now accepts multiple files
uploaded_files = st.file_uploader(
    "Choose files...",
    type=["pdf", "jpg", "jpeg", "png"],
    accept_multiple_files=True,
    help="Supported formats: PDF, JPG, PNG"
)

# Main logic to process the files and extract data
if uploaded_files:
    st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")
    
    # List to hold the extracted data from all files
    all_extracted_data = []

    for file_index, uploaded_file in enumerate(uploaded_files):
        # Display a subheader for each file being processed
        st.subheader(f"Processing: {uploaded_file.name}")
        
        # Display the uploaded document (image or PDF preview)
        file_type = uploaded_file.type
        if "image" in file_type:
            st.image(uploaded_file, caption=f"Uploaded Image: {uploaded_file.name}")
        else: # It's a PDF
            st.write(f"PDF file uploaded: {uploaded_file.name}. The content will be processed.")

        st.write("Extracting data... Please wait.")
        
        # Use a loading spinner while processing
        with st.spinner(f"Processing {uploaded_file.name} ..."):
            try:
                # The prompt is critical for structured data extraction.
                # It instructs the model to provide a precise JSON output.
                prompt = """
                Extract the following four fields from the document provided.
                Provide the output as a JSON object only, with no other text or explanation.

                Fields to extract:
                1.  "date": The date of the document. Format as YYYY-MM-DD if possible.
                2.  "invoice_number": The bill, invoice, or challan number.
                3.  "total_amount": The total amount, including currency symbol if available.
                4.  "company_name": The name of the company that issued the document.

                If a field is not found, use "N/A".
                """
                
                uploaded_file_part = genai.upload_file(uploaded_file, mime_type=uploaded_file.type)
                
                response = model.generate_content([
                    prompt,
                    uploaded_file_part
                ])

                # Parse the JSON from the response text
                extracted_json_text = response.text.strip()
                
                # The model might return a markdown code block, so we clean it.
                if extracted_json_text.startswith("```json"):
                    extracted_json_text = extracted_json_text.removeprefix("```json").removesuffix("```").strip()
                
                # Check if the extracted content is valid JSON
                try:
                    data = json.loads(extracted_json_text)
                    all_extracted_data.append(data)
                    st.success(f"Data successfully extracted from {uploaded_file.name}!")
                    
                except json.JSONDecodeError:
                    st.error(f"Error: Failed to parse JSON from the API response for {uploaded_file.name}. The response might not be in the expected format.")
                    st.text_area(f"Gemini API Response for {uploaded_file.name}:", extracted_json_text, height=100)
            
            except Exception as e:
                st.error(f"An error occurred while processing {uploaded_file.name}: {e}")

    # After processing all files, display the consolidated data and offer the download
    if all_extracted_data:
        st.subheader("Consolidated Extracted Data")
        
        # Create a single Pandas DataFrame from all extracted data
        df = pd.DataFrame(all_extracted_data)
        st.dataframe(df)
        
        # --- Export Step: Create a downloadable Excel file ---
        
        # Create an in-memory buffer to save the Excel file
        buffer = io.BytesIO()
        
        # Use openpyxl as the engine to write the DataFrame to the buffer
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Extracted Data")
        
        # Reset the buffer's position to the beginning for downloading
        buffer.seek(0)
        
        # Create a download button for the Excel file
        st.download_button(
            label="Download All Data as Excel",
            data=buffer,
            file_name="consolidated_extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            help="Click to download all extracted data as a single Excel file."
        )
