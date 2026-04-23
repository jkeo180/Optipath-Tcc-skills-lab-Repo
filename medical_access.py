import requests
import pandas as pd

# Load ZCTA data once at module level
df_zcta = pd.read_csv(
    "PLACES__Local_Data_for_Better_Health,_ZCTA_Data,_2025_release_20260330.csv"
)

PRIMARY_CARE_CODES = [
    '207Q00000X',  # Family Medicine
    '207R00000X',  # Internal Medicine
    '207QA0505X',  # Adult Medicine
    '208D00000X',  # General Practice
    '207RG0300X',  # Internal Medicine, Geriatric
    '363LF0000X',  # Nurse Practitioner, Family
    '363LA2200X',  # Nurse Practitioner, Adult
]

def get_doctor_count(zip_code: str) -> int:
    """Returns number of primary care providers in a ZIP code."""
    try:
        url = "https://npiregistry.cms.hhs.gov/api/"
        params = {
            "version": "2.1",
            "postal_code": zip_code,
            "enumeration_type": "NPI-1",
            "limit": 200
        }
        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        count = 0
        for provider in data.get('results', []):
            location_zip = None
            for addr in provider.get('addresses', []):
                if addr.get('address_purpose') == 'LOCATION':
                    location_zip = addr.get('postal_code', '')[:5]
                    break
            if location_zip != zip_code:
                continue
            for tax in provider.get('taxonomies', []):
                if tax.get('code') in PRIMARY_CARE_CODES:
                    count += 1
                    break
        return count
    except Exception:
        return 0

def get_places_measures(zip_code: str) -> dict:
    """Returns health measures for a ZIP from CDC PLACES ZCTA data."""
    zip_int = int(zip_code) if zip_code.isdigit() else None
    if zip_int is None:
        return {}

    df_zip = df_zcta[df_zcta['LocationName'] == zip_int]
    measures = {}
    for _, row in df_zip.iterrows():
        measures[row['Short_Question_Text']] = row['Data_Value']
    return measures

def get_medical_access(zip_code: str) -> dict:
    """
    Returns full medical access report for a ZIP code.
    Includes doctor count, checkup rate, insurance rate, and 0-100 score.
    """
    measures = get_places_measures(zip_code)
    doctor_count = get_doctor_count(zip_code)

    checkup_rate = measures.get('Annual Checkup')
    uninsured_rate = measures.get('Health Insurance')

    if checkup_rate is not None and uninsured_rate is not None:
        doctor_score = min(doctor_count / 20 * 100, 100)
        combined = (
            doctor_score * 0.35 +
            checkup_rate * 0.35 +
            (100 - uninsured_rate) * 0.30
        )
        return {
            "zip_code": zip_code,
            "doctor_count": doctor_count,
            "checkup_rate": checkup_rate,
            "uninsured_rate": uninsured_rate,
            "access_score": round(combined, 1),
            "interpretation": (
                "High Access" if combined >= 70
                else "Moderate Access" if combined >= 40
                else "Low Access"
            )
        }
    return {
        "zip_code": zip_code,
        "doctor_count": doctor_count,
        "checkup_rate": None,
        "uninsured_rate": None,
        "access_score": None,
        "interpretation": "Insufficient data"
    }

# TEST
if __name__ == "__main__":
    result = get_medical_access("77030")
    for k, v in result.items():
        print(f"  {k}: {v}")