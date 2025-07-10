import os
import json
import pandas as pd
from datetime import datetime

# Path to previously saved JSON
RAW_JSON_PATH = "raw_apify_response.json"

# Output base directory
BASE_DIR = "leads"

# Load JSON
if not os.path.exists(RAW_JSON_PATH):
    print("❌ raw_apify_response.json not found.")
    exit()

with open(RAW_JSON_PATH, "r") as f:
    leads = json.load(f)

# Create today's folder
today = datetime.now().strftime("%Y-%m-%d")
scrape_dir = os.path.join(BASE_DIR, today)
os.makedirs(scrape_dir, exist_ok=True)

df_rows = []

for lead in leads:
    full_name = f"{lead.get('first_name', '')} {lead.get('last_name', '')}".strip().replace("/", "-")
    emp = next((e for e in lead.get("employment_history", []) if e.get("current")), {})

    phone_list = [p.get("number", "") for p in lead.get("phone_numbers", [])]

    lead_dir = os.path.join(scrape_dir, full_name)
    os.makedirs(lead_dir, exist_ok=True)

    # Save individual JSON
    with open(os.path.join(lead_dir, "lead.json"), "w") as f:
        json.dump(lead, f, indent=2)

    # Build metadata row
    row = {
        "Full Name": full_name,
        "Title": emp.get("title", ""),
        "Company": emp.get("organization_name", ""),
        "Email": lead.get("email", ""),
        "LinkedIn": lead.get("linkedin_url", ""),
        "City": lead.get("city", ""),
        "State": lead.get("state", ""),
        "Country": lead.get("country", ""),
        "Seniority": lead.get("seniority", ""),
        "Department": ', '.join(lead.get("departments", [])),
        "Industry": lead.get("industry", ""),
        "Skills": ', '.join(lead.get("skills", [])),
        "Tags": ', '.join(lead.get("tags", [])),
        "Phone Numbers": ', '.join(phone_list)
    }

    # Save CSV
    pd.DataFrame([row]).to_csv(os.path.join(lead_dir, "meta.csv"), index=False)
    df_rows.append(row)

# Save combined CSV
pd.DataFrame(df_rows).to_csv(os.path.join(scrape_dir, "combined.csv"), index=False)

print(f"✅ Saved {len(df_rows)} leads to: leads/{today}/")
