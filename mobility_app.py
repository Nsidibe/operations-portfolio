import os
import streamlit as st
import pandas as pd
from anthropic import Anthropic
from dotenv import load_dotenv

# --- SETUP ---
load_dotenv()
client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

st.set_page_config(page_title="Internal Mobility Engine", page_icon="🧭", layout="wide")
st.title("🧭 Internal Mobility & Skills Gap Mapper")
st.markdown("Map internal talent to open roles and generate AI-driven upskilling roadmaps.")

# --- HR DATABASE ---
employee_data = {
"Employee_ID": ["EMP-001", "EMP-002", "EMP-003"],
"Name": ["Sarah Connor", "John Smith", "Emily Chen"],
"Current_Role": ["Junior Data Analyst", "Customer Support Rep", "Marketing Coordinator"],
"Current_Skills": [
    "Excel, Basic SQL, Tableau, Data Cleaning", 
    "Zendesk, Communication, Conflict Resolution, Empathy", 
    "SEO, Copywriting, Google Analytics, A/B Testing"
]
}
df_employees = pd.DataFrame(employee_data)

# --- SIDEBAR ---
with st.sidebar:
    st.header("🎯 Target Role")
    target_role = st.text_input("Open Role Title", "Data Engineer")
    target_skills = st.text_area("Required Skills", "Advanced SQL, Python, ETL Pipelines, Snowflake, AWS")

# --- MAIN UI ---
st.subheader("Current Talent Pool")
st.dataframe(df_employees, hide_index=True, width='stretch')

st.subheader("Map an Employee")
selected_name = st.selectbox("Select an employee to evaluate:", df_employees["Name"])
employee_skills = df_employees.loc[df_employees["Name"] == selected_name, "Current_Skills"].values[0]
employee_role = df_employees.loc[df_employees["Name"] == selected_name, "Current_Role"].values[0]

if st.button("Calculate Skills Gap & Generate Roadmap", type="primary"):
    with st.spinner(f"Analyzing gap for {selected_name}..."):
        
        prompt = f"""
        You are an expert HR Talent Engineer and Career Coach. 
        Analyze the gap between this employee's current skills and their target role.
        
        Employee: {selected_name}
        Current Role: {employee_role}
        Current Skills: {employee_skills}
        
        Target Role: {target_role}
        Target Skills Required: {target_skills}
        
        Provide your response in exactly two sections using Markdown formatting:
        
        ### 📊 The Skills Gap
        Write 2-3 sentences summarizing what they already know and exactly what they are missing.
        
        ### 🗺️ 4-Week Upskilling Syllabus
        Provide a bulleted 4-week learning plan detailing exactly what they should study each week to bridge the gap.
        """

        try:
            response = client.messages.create(
                model="claude-haiku-5-5",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = next((block.text for block in response.content if block.type == "text"), None)
            
            if result:
                st.success("Roadmap Generated!")
                st.markdown(result)
            else:
                st.error("Failed to generate roadmap.")
                
        except Exception as e:
            st.error(f"API Error: {e}")