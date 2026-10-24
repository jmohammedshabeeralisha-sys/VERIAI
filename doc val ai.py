import streamlit as st
from pypdf import PdfReader
import re
from google import genai
import os
api_key = st.secrets.get(
    "GEMINI_API_KEY",
    os.environ.get("GEMINI_API_KEY")
)

client = genai.Client(api_key=api_key)
def validate_document(text):
    results = {}

    # Check whether readable text exists
    results["Readable Text"] = bool(text.strip())

    # Check for a date
    date_pattern = r"\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b"
    results["Date Found"] = bool(
        re.search(date_pattern, text)
    )

    # Check for a possible reference or certificate number
    reference_pattern = (
        r"\b(?:certificate|reference|registration)"
        r"\s*(?:number|no\.?|id)?\s*[:#-]?\s*[A-Z0-9/-]{4,}\b"
    )

    results["Reference Number Found"] = bool(
        re.search(reference_pattern, text, re.IGNORECASE)
    )

    return results
def analyze_with_ai(document_text):
    prompt = f"""
    You are VeriAI, an AI-powered document validation assistant.

    Analyze the following document and provide:

    1. Document type and purpose.
    2. Important details, dates, and reference numbers.
    3. Missing or unclear information.
    4. Inconsistencies that require human review.
    5. A summary and recommended next steps.

    Do not claim that a document is authentic or fraudulent
    based on text alone.

    Document text:
    {document_text[:12000]}
    """

    response = client.models.generate_content(
        model="gemini-3.8-flash",
        contents=prompt
    )

    return response.text
if "applications_checked" not in st.session_state:
    st.session_state.applications_checked = 0


st.set_page_config(
    page_title="VeriAI",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 VeriAI")
st.subheader("AI-Powered Application Validation")

st.write(
    "Welcome to VeriAI! "
    "Our system helps institutions validate "
    "applications and supporting documents."
)

st.divider()

st.header("Application Dashboard")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
    "Applications Checked",
    value=st.session_state.applications_checked
)

with col2:
    st.metric("Passed Initial Checks", 0)

with col3:
    st.metric("Needs Review", 0)

st.divider()

st.header("Upload Your Document")

uploaded_file = st.file_uploader(
    "Choose a document",
    type=["pdf", "png", "jpg", "jpeg"]
)
if uploaded_file is not None:
    if uploaded_file.name.lower().endswith(".pdf"):
        try:
            pdf_reader = PdfReader(uploaded_file)

            extracted_text = ""

            for page in pdf_reader.pages:
                extracted_text += page.extract_text() or ""

            if extracted_text.strip():
                st.subheader("Extracted Document Text")
                st.text_area(
                    "PDF contents",
                    extracted_text,
                    height=250
                )
                st.success("PDF text extracted successfully!")
                st.subheader("📋 Document Validation Report")

                report = validate_document(extracted_text)
                st.subheader("🤖 AI Document Analysis")

                with st.spinner("Gemini AI is analyzing your document..."):
                    try:
                        ai_result = analyze_with_ai(extracted_text)
                        st.markdown(ai_result)
                    except Exception as error:
                        st.error(f"AI analysis failed: {error}")

                for check, passed in report.items():
                    if passed:
                        st.success(f"✅ {check}: PASS")
                    else:
                        st.warning(f"⚠️ {check}: REVIEW")
            else:
                st.warning(
                    "No readable text found. "
                    "This PDF might contain scanned images."
                )

        except Exception as error:
            st.error(f"Could not read this PDF: {error}")
