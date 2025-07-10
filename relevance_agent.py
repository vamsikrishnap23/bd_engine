import os
import requests
from dotenv import load_dotenv

load_dotenv()

AUTH_TOKEN = os.getenv("AUTH_TOKEN")
API_KEY = os.getenv("API_KEY")
PROJECT = os.getenv("PROJECT")

# Replace with your actual Agent ID (from the shared link or dashboard)
AGENT_ID = "99938bef-25f7-4f4b-a9ae-247b93bf5cf6"

def fetch_pain_points(company_name, website="", linkedin_url=""):
    endpoint = f"https://api-{PROJECT}.stack.tryrelevance.com/latest/agents/{PROJECT}/{AGENT_ID}/query"

    headers = {
        "Authorization": f"Bearer {AUTH_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "inputs": {
            "company_name": company_name,
            "website": website,
            "linkedin_url": linkedin_url
        }
    }

    try:
        res = requests.post(endpoint, headers=headers, json=payload, timeout=30)
        res.raise_for_status()
        data = res.json()

        # Assumes the pain point content is inside the 'output' key
        return data.get("output", "No response received.")
    except Exception as e:
        return f"Error fetching pain points: {e}"
