import requests
import json
import pandas as pd

# USAspending API Advanced Award Search Endpoint
url = "https://usaspending.gov
"

# Query payload filtering for the $39B semiconductor infrastructure grants
payload = {
    "filters": {
        "award_ids": [],
        "award_type_codes": ["02", "03", "04", "05"], # Grants & Cooperative Agreements
        "agencies": [{"type": "funding", "tier": "toptier", "name": "Department of Commerce"}],
        "keywords": ["semiconductor", "microelectronics", "cleanroom", "CHIPS Act"],
        "time_period": [{"start_date": "2022-10-01", "end_date": "2026-01-01"}]
    },
    "fields": [
        "Award ID", "Recipient Name", "Start Date", 
        "Award Amount", "Awarding Agency", "Description"
    ],
    "limit": 100,
    "page": 1
}

headers = {"Content-Type": "application/json"}

print("Connecting to USAspending API...")
response = requests.post(url, data=json.dumps(payload), headers=headers)

if response.status_code == 200:
    data = response.json()
    awards = data.get("results", [])
    
    # Convert into a structured pandas DataFrame
    df = pd.DataFrame(awards)
    print(f"Successfully pulled {len(df)} live federal awards.")
    # Show the structured data layout
    print(df.head())
else:
    print(f"API Connection Failed. Status Code: {response.status_code}")
