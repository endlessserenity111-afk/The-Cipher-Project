import json
import os
import pandas as pd
import numpy as np
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import groq

load_dotenv()
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
groq_client = groq.Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# In-memory cache for explanations
explanation_cache = {}
app = FastAPI(title="MPLADS API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base directory for data
DATA_DIR = os.path.join(os.path.dirname(__file__), "data", "outputs")

def get_file_path(filename: str) -> str:
    return os.path.join(DATA_DIR, filename)

def read_json(filename: str):
    path = get_file_path(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found. Pipeline may not have been run.")
    with open(path, "r") as f:
        return json.load(f)

def read_csv(filename: str) -> pd.DataFrame:
    path = get_file_path(filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail=f"File {filename} not found. Pipeline may not have been run.")
    try:
        df = pd.read_csv(path)
        # Replace NaN/NaT values with None for JSON serialization
        df = df.replace({np.nan: None})
        return df
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading {filename}: {str(e)}") from e

@app.get("/")
def root():
    return {"status": "ok", "message": "MPLADS API running"}

@app.get("/api/dashboard")
def get_dashboard():
    return read_json("pipeline_summary.json")

@app.get("/api/projects")
def get_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000),
    risk_level: Optional[str] = None,
    state: Optional[str] = None,
    category: Optional[str] = None,
    sort_by: Optional[str] = "risk_score",
    order: Optional[str] = "desc"
):
    df = read_csv("project_risk_scores.csv")
    
    # Filter
    if risk_level:
        df = df[df['risk_level'] == risk_level]
    if state:
        df = df[df['state'] == state]
    if category:
        df = df[df['category'] == category]
        
    # Sort
    if sort_by in df.columns:
        ascending = (order.lower() == "asc")
        df = df.sort_values(by=sort_by, ascending=ascending)
        
    # Select key fields
    key_fields = [
        "recommendation_row_id", "recommendation_work_id", "completion_work_id", "mp_name", 
        "constituency", "state", "category", "recommended_amount", "final_amount", 
        "match_score", "match_tier", "risk_score", "risk_level"
    ]
    
    # Only select columns that exist in the dataframe to avoid errors
    available_fields = [col for col in key_fields if col in df.columns]
    df = df[available_fields]
    
    # Pagination
    total = len(df)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_df = df.iloc[start_idx:end_idx]
    
    return {
        "items": paginated_df.to_dict(orient="records"),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@app.get("/api/projects/{recommendation_row_id}")
def get_project_detail(recommendation_row_id: str):
    df = read_csv("project_risk_scores.csv")
    
    # The ID might be an int or string depending on the CSV, try to match robustly
    df['recommendation_row_id_str'] = df['recommendation_row_id'].astype(str)
    
    project = df[df['recommendation_row_id_str'] == str(recommendation_row_id)]
    
    if project.empty:
        raise HTTPException(status_code=404, detail=f"Project with recommendation_row_id {recommendation_row_id} not found.")
        
    # Drop the temporary column and return the first matched row
    project = project.drop(columns=['recommendation_row_id_str'])
    return project.iloc[0].to_dict()

@app.get("/api/mp-indicators")
def get_mp_indicators(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=1000)
):
    df = read_csv("mp_risk_indicators.csv")
    
    total = len(df)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    paginated_df = df.iloc[start_idx:end_idx]
    
    return {
        "items": paginated_df.to_dict(orient="records"),
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": (total + page_size - 1) // page_size
    }

@app.get("/api/review")
def get_review_samples():
    df = read_csv("review/match_review.csv")
    return df.to_dict(orient="records")

@app.get("/api/rollups/state")
def get_state_rollup():
    df = read_csv("state_rollup.csv")
    return df.to_dict(orient="records")

@app.get("/api/rollups/category")
def get_category_rollup():
    df = read_csv("category_rollup.csv")
    return df.to_dict(orient="records")

@app.get("/api/projects/{recommendation_row_id}/explain")
def get_project_explanation(recommendation_row_id: str):
    if recommendation_row_id in explanation_cache:
        return {"recommendation_row_id": recommendation_row_id, "explanation": explanation_cache[recommendation_row_id]}

    if not groq_client:
        return {"recommendation_row_id": recommendation_row_id, "explanation": "Explanation temporarily unavailable — see risk factors above (API key not configured)."}
    
    # Get the project row
    try:
        project = get_project_detail(recommendation_row_id)
    except HTTPException as exc:
        raise HTTPException(status_code=404, detail=f"Project with recommendation_row_id {recommendation_row_id} not found.") from exc

    # Build prompt with ONLY already-computed fields
    prompt = f"""You are explaining an already-computed risk assessment for a government project to a non-technical official. Do NOT invent any new risk factors or numbers — only explain and contextualize the ones given below. Write 2-4 sentences in plain English.

Project Details:
- Work Description: {project.get('work_description', 'N/A')}
- MP Name: {project.get('mp_name', 'N/A')}
- State: {project.get('state', 'N/A')}
- Category: {project.get('category', 'N/A')}
- Recommended Amount: {project.get('recommended_amount', 'N/A')}
- Final Amount: {project.get('final_amount', 'N/A')}
- Amount Difference %: {project.get('amount_difference_pct', 'N/A')}
- Days to Completion: {project.get('days_to_completion', 'N/A')}
- Has Images: {project.get('has_images', False)}

Risk Assessment:
- Risk Score: {project.get('risk_score', 'N/A')}
- Risk Level: {project.get('risk_level', 'N/A')}
- ML Anomaly Flag: {project.get('ml_anomaly_flag', False)}
- Risk Reasons (Evidence): {project.get('risk_reasons', 'None')}

Please provide the 2-4 sentence explanation now:
"""

    try:
        completion = groq_client.chat.completions.create(
            model="groq/compound",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=150,
        )
        explanation = completion.choices[0].message.content.strip()
        explanation_cache[recommendation_row_id] = explanation
        return {"recommendation_row_id": recommendation_row_id, "explanation": explanation}
    except Exception as e:
        print(f"Groq API Error: {e}")
        return {"recommendation_row_id": recommendation_row_id, "explanation": "Explanation temporarily unavailable — see risk factors above."}
