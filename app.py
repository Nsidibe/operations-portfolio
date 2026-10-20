import os
import json
import pdfplumber
import pandas as pd
import streamlit as st
from anthropic import Anthropic
from dotenv import load_dotenv

# Load API key
load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

def extract_text_from_upload(uploaded_file):
    """Extracts text from a Streamlit UploadedFile object."""
    text = ""
    try:
        # Streamlit files can be passed directly to pdfplumber
        with pdfplumber.open(uploaded_file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        st.error(f"Error reading {uploaded_file.name}: {e}")
        return None

def evaluate_candidate(resume_text, job_desc):
    """Sends the resume and job description to Claude and returns a JSON dict."""
    prompt = f"""
    You are an expert technical recruiter. Evaluate the following resume against the job description.
    
    Job Description:
    {job_desc}
    
    Resume Text:
    {resume_text}
    
    Respond STRICTLY in JSON format with exactly two keys:
    1. "Fit Score": An integer from 0 to 100 representing how well the candidate matches the job.
    2. "Rationale": A list of exactly 3 bullet points explaining the score (highlighting key matches or missing skills).
    
    Do not include any introductory text, markdown formatting, or explanations outside of the JSON block.
    """

    try:
        response = client.messages.create(
            model="claude-haiku-5-5",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        
        raw_json = next((block.text for block in response.content if block.type == "text"), None)
        
        if not raw_json:
            return None
            
        return json.loads(raw_json)

    except Exception as e:
        st.error(f"API Error: {e}")
        return None

# --- STREAMLIT UI ---
st.set_page_config(page_title="AI Resume Matcher", page_icon="🎯", layout="wide")

st.title("🎯 Talent Engineering: AI Resume Matcher")
st.markdown("Upload resumes and paste a job description to instantly generate a contextual leaderboard.")

# Sidebar for Inputs
with st.sidebar:
    st.header("1. Job Description")
    job_description = st.text_area(
        "Paste the job requirements here:",
        height=300,
        value="We are looking for a Mid-Level Data Analyst with 3+ years of Python and SQL experience, plus Tableau/PowerBI."
    )

# Main Area for File Upload
st.header("2. Upload Candidates")
uploaded_files = st.file_uploader("Upload PDF Resumes", type="pdf", accept_multiple_files=True)

# Run Analysis Button
if st.button("🚀 Run Analysis", type="primary"):
    if not uploaded_files:
        st.warning("Please upload at least one PDF resume.")
    elif not job_description.strip():
        st.warning("Please provide a Job Description in the sidebar.")
    else:
        results = []
        
        # Show a progress bar
        progress_text = "Analyzing candidates..."
        my_bar = st.progress(0, text=progress_text)
        
        for i, file in enumerate(uploaded_files):
            # Extract and Evaluate
            text = extract_text_from_upload(file)
            
            if text and len(text) > 50:
                evaluation = evaluate_candidate(text, job_description)
                
                if evaluation:
                    # Format bullet points for the table
                    bullets = "\n".join([f"• {b}" for b in evaluation.get('Rationale', [])])
                    
                    results.append({
                        "Candidate File": file.name,
                        "Fit Score": evaluation.get("Fit Score", 0),
                        "AI Rationale": bullets
                    })
            
            # Update progress bar
            my_bar.progress((i + 1) / len(uploaded_files), text=f"Analyzed {file.name}")
            
        # Display Results using Pandas
        if results:
            st.success("Analysis Complete!")
            
            # Convert list of dictionaries to a Pandas DataFrame
            df = pd.DataFrame(results)
            
            # Sort by Fit Score descending
            df = df.sort_values(by="Fit Score", ascending=False).reset_index(drop=True)
            
            st.subheader("🏆 Candidate Leaderboard")
            
            # Display interactive dataframe
            st.dataframe(
                df,
                column_config={
                    "Fit Score": st.column_config.ProgressColumn(
                        "Fit Score",
                        help="The contextual match score",
                        format="%d",
                        min_value=0,
                        max_value=100,
                    ),
                },
                hide_index=True,
                use_container_width=True
            )
            
            # Allow downloading the pandas dataframe as a CSV
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name='candidate_scores.csv',
                mime='text/csv',
            )