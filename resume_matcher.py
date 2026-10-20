import os
import json
import glob
import pdfplumber
from anthropic import Anthropic
from dotenv import load_dotenv

# 1. Load the secret API key from your .env file
load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# 2. Define the Job Description
JOB_DESCRIPTION = """
We are looking for a Mid-Level Data Analyst. 
Requirements: 
- 3+ years of experience with Python (Pandas, NumPy) and SQL.
- Experience building dashboards in Tableau or PowerBI.
- Strong communication skills and ability to present findings to non-technical stakeholders.
"""

def extract_text_from_pdf(pdf_path):
    """Safely extracts text from a PDF file using pdfplumber."""
    text = ""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text.strip()
    except Exception as e:
        print(f"Error reading {pdf_path}: {e}")
        return None

def evaluate_candidate(resume_text, job_desc):
    """Sends the resume and job description to Claude and requests a JSON response."""
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
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        raw_json = next((block.text for block in response.content if block.type == "text"), None)
        
        if not raw_json:
            print("Error: Claude did not return any text.")
            return None
            
        result_dict = json.loads(raw_json)
        return result_dict

    except json.JSONDecodeError:
        print("Error: Claude did not return valid JSON.")
        return None
    except Exception as e:
        print(f"API Error: {e}")
        return None

def main():
    resume_folder = "resumes"
    if not os.path.exists(resume_folder):
        print(f"Please create a folder named '{resume_folder}' and add some PDFs.")
        return

    pdf_files = glob.glob(os.path.join(resume_folder, "*.pdf"))
    
    if not pdf_files:
        print("No PDFs found in the 'resumes' folder.")
        return

    print(f"Found {len(pdf_files)} resume(s). Starting evaluation...\n")

    for pdf_path in pdf_files:
        file_name = os.path.basename(pdf_path)
        print(f"--- Evaluating: {file_name} ---")
        
        text = extract_text_from_pdf(pdf_path)
        
        if not text:
            print("Could not extract text. Skipping...\n")
            continue
            
        if len(text) < 50:
            print("PDF appears to be an image or scanned document. Skipping...\n")
            continue

        print("Analyzing fit...")
        evaluation = evaluate_candidate(text, JOB_DESCRIPTION)
        
        if evaluation:
            print(f"Fit Score: {evaluation.get('Fit Score')}/100")
            print("Rationale:")
            for bullet in evaluation.get('Rationale', []):
                print(f" - {bullet}")
        print("\n")

if __name__ == "__main__":
    main()