# emergency_firstaid_knowledge.py - Emergency and first aid knowledge base for Weslr
"""
Emergency response and first aid knowledge for Weslr to assist in medical
and disaster scenarios. Includes trauma care, medical emergencies, and
disaster response protocols with agency contact information.
"""
from __future__ import annotations

from typing import List, Dict, Any, Optional


# ============================================================================
# EMERGENCY AND FIRST AID CONCEPTS
# ============================================================================

EMERGENCY_CONCEPTS = {
    # Trauma categories
    "trauma_types": [
        "blunt trauma", "penetrating trauma", "burns", "chemical injuries",
        "electrical injuries", "drowning", "choking", "fractures"
    ],
    
    # Medical emergencies
    "medical_emergencies": [
        "cardiac arrest", "heart attack", "stroke", "severe allergic reaction",
        "diabetic emergency", "seizure", "hypothermia", "heat stroke"
    ],
    
    # First aid procedures
    "first_aid_procedures": [
        "CPR (cardiopulmonary resuscitation)",
        "Choking relief (Heimlich maneuver)",
        "Bleeding control",
        "Burn treatment",
        "Fracture stabilization",
        "Shock management",
        "Wound cleaning",
        "Splinting"
    ],
    
    # Disaster categories
    "disaster_types": [
        "earthquake", "fire", "flood", "hurricane", "tornado",
        "chemical spill", "active shooter", "mass casualty incident"
    ],
    
    # First responder categories
    "first_responders": [
        "EMS (Emergency Medical Services)",
        "Fire department",
        "Police department",
        "Search and rescue",
        "Hazmat team",
        "Disaster medical assistance team (DMAT)",
        "Red Cross",
        "Coast guard (maritime)"
    ],
    
    # US emergency agencies
    "emergency_agencies": [
        {
            "name": "National Response Framework (NRF)",
            "description": "National template for all-disaster response",
            "website": "https://www.fema.gov/national-response-framework",
            "phone": None
        },
        {
            "name": "Disaster Medical Assistance Teams (DMAT)",
            "description": "Federal medical teams for disaster response",
            "website": "https://www.flash.navy.mil/DMAT/",
            "phone": "1-800-621-3362"
        },
        {
            "name": "American Red Cross",
            "description": "Disaster relief, shelter, and blood donation",
            "website": "https://www.redcross.org",
            "phone": "1-800-733-2767"
        },
        {
            "name": "FEMA Disaster Assistance",
            "description": "Individual assistance programs for disasters",
            "website": "https://www.fema.gov/assistance",
            "phone": "1-800-621-3362"
        },
        {
            "name": "National Weather Service",
            "description": "Weather warnings and forecasts",
            "website": "https://www.weather.gov",
            "phone": None
        },
        {
            "name": "Coast Guard Emergency Services",
            "description": "Maritime search and rescue",
            "website": "https://www.uscg.mil/rescue",
            "phone": "1-800-424-8802"
        },
        {
            "name": "Poison Control",
            "description": "24/7 poisoning emergency assistance",
            "website": "https://www.poison.org",
            "phone": "1-800-222-1222"
        },
        {
            "name": "National Suicide & Crisis Lifeline",
            "description": "Crisis counseling and suicide prevention",
            "website": "https://988lifeline.org",
            "phone": "988"
        }
    ],
    
    # International emergency contacts by country
    "international_emergency_numbers": {
        # Africa
        "ZA": "112",  # South Africa
        "NG": "767",  # Nigeria
        "EG": "123",  # Egypt
        "KE": "999",  # Kenya
        "ET": "999",  # Ethiopia
        
        # Asia
        "CN": "120",  # China (ambulance), 119 (fire), 110 (police)
        "JP": "119",  # Japan (ambulance/fire)
        "IN": "112",  # India (unified emergency)
        "SG": "995",  # Singapore (police), 997 (fire), 999 (ambulance)
        "KR": "119",  # South Korea (fire/ambulance)
        "TH": "191",  # Thailand (all services)
        
        # Europe
        "DE": "112",  # Germany (all services)
        "FR": "15",   # France (ambulance), 17 (police), 18 (fire)
        "IT": "118",  # Italy (ambulance), 113 (police), 115 (fire)
        "ES": "112",  # Spain (all services)
        "NL": "112",  # Netherlands (all services)
        "BE": "112",  # Belgium (all services)
        "SE": "112",  # Sweden (all services)
        "NO": "113",  # Norway (ambulance), 112 (emergency)
        "DK": "112",  # Denmark (all services)
        "PL": "999",  # Poland (ambulance), 998 (fire), 997 (police)
        "CZ": "155",  # Czech Republic (ambulance), 158 (police), 150 (fire)
        "HU": "104",  # Hungary (ambulance), 105 (police), 105 (fire)
        "RO": "112",  # Romania (all services)
        
        # Oceania
        "AU": "000",  # Australia
        "NZ": "111",  # New Zealand
        
        # Americas
        "US": "911",  # United States
        "CA": "911",  # Canada
        "MX": "911",  # Mexico (all services since 2017)
        "BR": "192",  # Brazil (ambulance), 193 (fire), 190 (police)
        "AR": "107",  # Argentina (ambulance), 101 (police)
        "CL": "131",  # Chile (ambulance), 133 (police)
        "CO": "123",  # Colombia (all services)
        "PE": "115",  # Peru (ambulance), 105 (police), 103 (fire)
        "VE": "911",  # Venezuela (all services)
        "CU": "104",  # Cuba (ambulance), 106 (police), 105 (fire)
        
        # Middle East
        "AE": "999",  # UAE (all services)
        "SA": "997",  # Saudi Arabia (police), 993 (ambulance), 998 (fire)
        "IL": "101",  # Israel (ambulance), 100 (police), 102 (fire)
        "TR": "112",  # Turkey (all services)
        "IR": "125",  # Iran (police), 115 (ambulance)
    },
    
    # Emergency services by country
    "emergency_services_by_country": {
        "US": {
            "ambulance": "911",
            "police": "911",
            "fire": "911",
            "coast_guard": "1-800-424-8802",
            "poison_control": "1-800-222-1222"
        },
        "CA": {
            "ambulance": "911",
            "police": "911",
            "fire": "911",
            "coast_guard": "1-800-565-1633",
            "poison_control": "1-800-332-1414"
        },
        "UK": {
            "ambulance": "999",
            "police": "999",
            "fire": "999",
            "non_emergency": "101",
            "coast_guard": "155000",
            "poison_control": "111"
        },
        "AU": {
            "ambulance": "000",
            "police": "000",
            "fire": "000",
            "non_emergency": "131 444",
            "coast_guard": "1800 800 000",
            "poison_info": "131 126"
        },
        "DE": {
            "ambulance": "112",
            "police": "112",
            "fire": "112",
            "non_emergency_police": "116 111"
        },
        "FR": {
            "ambulance": "15",
            "police": "17",
            "fire": "18",
            "coordinated_emergency": "112"
        },
        "JP": {
            "ambulance/fire": "119",
            "police": "110",
            "coast_guard": "118"
        },
        "BR": {
            "ambulance": "192",
            "police": "190",
            "fire": "193",
            "civil_defense": "199"
        },
        "ZA": {
            "ambulance": "10177",
            "police": "10111",
            "fire": "10177",
            "emergency": "112"
        },
        "IN": {
            "ambulance": "102",
            "police": "100",
            "fire": "101",
            "disaster": "108"
        },
        "EG": {
            "ambulance": "123",
            "police": "122",
            "fire": "180"
        },
        "NG": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "AE": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "SA": {
            "ambulance": "993",
            "police": "997",
            "fire": "998"
        },
        "IL": {
            "ambulance": "101",
            "police": "100",
            "fire": "102"
        },
        "TR": {
            "ambulance": "112",
            "police": "155",
            "fire": "110"
        },
        "NL": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "ES": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "IT": {
            "ambulance": "118",
            "police": "113",
            "fire": "115",
            "coast_guard": "1533"
        },
        "SE": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "NO": {
            "ambulance": "113",
            "police": "112",
            "fire": "110"
        },
        "DK": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "PL": {
            "ambulance": "999",
            "police": "997",
            "fire": "998"
        },
        "CZ": {
            "ambulance": "155",
            "police": "158",
            "fire": "150"
        },
        "RO": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "NZ": {
            "ambulance": "111",
            "police": "111",
            "fire": "111"
        },
        "MX": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "AR": {
            "ambulance": "107",
            "police": "101",
            "fire": "100"
        },
        "CL": {
            "ambulance": "131",
            "police": "133",
            "fire": "132"
        },
        "CO": {
            "ambulance": "123",
            "police": "112",
            "fire": "119"
        },
        "PE": {
            "ambulance": "115",
            "police": "105",
            "fire": "103"
        },
        "CU": {
            "ambulance": "104",
            "police": "106",
            "fire": "105"
        },
        "PT": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "GR": {
            "ambulance": "166",
            "police": "166",
            "fire": "199"
        },
        "BE": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "AT": {
            "ambulance": "144",
            "police": "133",
            "fire": "122"
        },
        "CH": {
            "ambulance": "144",
            "police": "117",
            "fire": "118"
        },
        "FI": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "SK": {
            "ambulance": "155",
            "police": "158",
            "fire": "150"
        },
        "SI": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "HR": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "UA": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "BY": {
            "ambulance": "03",
            "police": "02",
            "fire": "01"
        },
        "KZ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "UZ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "MD": {
            "ambulance": "903",
            "police": "902",
            "fire": "901"
        },
        "LV": {
            "ambulance": "113",
            "police": "116",
            "fire": "112"
        },
        "EE": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "LT": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "BG": {
            "ambulance": "150",
            "police": "150",
            "fire": "150"
        },
        "HU": {
            "ambulance": "104",
            "police": "105",
            "fire": "105"
        },
        "RS": {
            "ambulance": "194",
            "police": "192",
            "fire": "193"
        },
        "BA": {
            "ambulance": "194",
            "police": "192",
            "fire": "193"
        },
        "MK": {
            "ambulance": "194",
            "police": "192",
            "fire": "193"
        },
        "AL": {
            "ambulance": "192",
            "police": "193",
            "fire": "194"
        },
        "GR": {
            "ambulance": "166",
            "police": "166",
            "fire": "199"
        },
        "CY": {
            "ambulance": "199",
            "police": "199",
            "fire": "199"
        },
        "MT": {
            "ambulance": "199",
            "police": "199",
            "fire": "199"
        },
        "LU": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "IE": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "IS": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "LI": {
            "ambulance": "144",
            "police": "117",
            "fire": "118"
        },
        "MC": {
            "ambulance": "15",
            "police": "17",
            "fire": "18"
        },
        "AD": {
            "ambulance": "116",
            "police": "117",
            "fire": "118"
        },
        "SM": {
            "ambulance": "118",
            "police": "113",
            "fire": "115"
        },
        "VA": {
            "ambulance": "112",
            "police": "113",
            "fire": "115"
        },
        "GE": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "AM": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "AZ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "MD": {
            "ambulance": "903",
            "police": "902",
            "fire": "901"
        },
        "KG": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "TJ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "TM": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "BD": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "PK": {
            "ambulance": "115",
            "police": "15",
            "fire": "16"
        },
        "LK": {
            "ambulance": "119",
            "police": "118",
            "fire": "118"
        },
        "MM": {
            "ambulance": "192",
            "police": "191",
            "fire": "191"
        },
        "KH": {
            "ambulance": "119",
            "police": "117",
            "fire": "118"
        },
        "LA": {
            "ambulance": "190",
            "police": "191",
            "fire": "192"
        },
        "VN": {
            "ambulance": "115",
            "police": "113",
            "fire": "114"
        },
        "PH": {
            "ambulance": "117",
            "police": "117",
            "fire": "117"
        },
        "MY": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "ID": {
            "ambulance": "118",
            "police": "110",
            "fire": "119"
        },
        "TW": {
            "ambulance": "119",
            "police": "110",
            "fire": "119"
        },
        "HK": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "MO": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "NP": {
            "ambulance": "102",
            "police": "101",
            "fire": "101"
        },
        "BT": {
            "ambulance": "112",
            "police": "113",
            "fire": "110"
        },
        "MV": {
            "ambulance": "102",
            "police": "100",
            "fire": "101"
        },
        "BT": {
            "ambulance": "112",
            "police": "113",
            "fire": "110"
        },
        "MV": {
            "ambulance": "102",
            "police": "100",
            "fire": "101"
        },
        "KZ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "UZ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "KG": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "TJ": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "TM": {
            "ambulance": "103",
            "police": "102",
            "fire": "101"
        },
        "AF": {
            "ambulance": "102",
            "police": "119",
            "fire": "101"
        },
        "IQ": {
            "ambulance": "123",
            "police": "130",
            "fire": "115"
        },
        "SY": {
            "ambulance": "110",
            "police": "112",
            "fire": "113"
        },
        "JO": {
            "ambulance": "191",
            "police": "191",
            "fire": "193"
        },
        "LB": {
            "ambulance": "193",
            "police": "191",
            "fire": "192"
        },
        "PS": {
            "ambulance": "101",
            "police": "100",
            "fire": "102"
        },
        "YE": {
            "ambulance": "191",
            "police": "191",
            "fire": "191"
        },
        "OM": {
            "ambulance": "1999",
            "police": "1122",
            "fire": "1999"
        },
        "QA": {
            "ambulance": "101",
            "police": "100",
            "fire": "102"
        },
        "KW": {
            "ambulance": "192",
            "police": "191",
            "fire": "193"
        },
        "BH": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "SA": {
            "ambulance": "997",
            "police": "997",
            "fire": "998"
        },
        "LY": {
            "ambulance": "193",
            "police": "194",
            "fire": "195"
        },
        "TN": {
            "ambulance": "198",
            "police": "197",
            "fire": "196"
        },
        "MA": {
            "ambulance": "15",
            "police": "19",
            "fire": "15"
        },
        "DZ": {
            "ambulance": "14",
            "police": "17",
            "fire": "14"
        },
        "EG": {
            "ambulance": "123",
            "police": "122",
            "fire": "180"
        },
        "SD": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "SS": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "ET": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "ER": {
            "ambulance": "2222",
            "police": "2222",
            "fire": "2222"
        },
        "DJ": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "KM": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "MG": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "MU": {
            "ambulance": "114",
            "police": "114",
            "fire": "114"
        },
        "SC": {
            "ambulance": "111",
            "police": "111",
            "fire": "111"
        },
        "MZ": {
            "ambulance": "198",
            "police": "191",
            "fire": "193"
        },
        "ZA": {
            "ambulance": "10177",
            "police": "10111",
            "fire": "10177"
        },
        "ZM": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "ZW": {
            "ambulance": "717",
            "police": "717",
            "fire": "717"
        },
        "BW": {
            "ambulance": "997",
            "police": "997",
            "fire": "997"
        },
        "NA": {
            "ambulance": "10114",
            "police": "10111",
            "fire": "10114"
        },
        "SZ": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "LS": {
            "ambulance": "121",
            "police": "121",
            "fire": "121"
        },
        "MW": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "TZ": {
            "ambulance": "999",
            "police": "112",
            "fire": "999"
        },
        "UG": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "RW": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "BI": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "CD": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "CF": {
            "ambulance": "125",
            "police": "124",
            "fire": "123"
        },
        "TD": {
            "ambulance": "125",
            "police": "124",
            "fire": "123"
        },
        "NE": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "ML": {
            "ambulance": "15",
            "police": "17",
            "fire": "15"
        },
        "SN": {
            "ambulance": "115",
            "police": "117",
            "fire": "115"
        },
        "MR": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "GM": {
            "ambulance": "2182182",
            "police": "2182182",
            "fire": "2182182"
        },
        "GN": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "CI": {
            "ambulance": "15",
            "police": "17",
            "fire": "15"
        },
        "BF": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "TG": {
            "ambulance": "117",
            "police": "117",
            "fire": "117"
        },
        "BJ": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "SL": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "LR": {
            "ambulance": "222",
            "police": "222",
            "fire": "222"
        },
        "NG": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "GH": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "TG": {
            "ambulance": "117",
            "police": "117",
            "fire": "117"
        },
        "BJ": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "CM": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "GA": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "CG": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "AO": {
            "ambulance": "115",
            "police": "113",
            "fire": "114"
        },
        "ZM": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "MW": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "MV": {
            "ambulance": "102",
            "police": "100",
            "fire": "101"
        },
        "PK": {
            "ambulance": "115",
            "police": "15",
            "fire": "16"
        },
        "LK": {
            "ambulance": "119",
            "police": "118",
            "fire": "118"
        },
        "BD": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "MM": {
            "ambulance": "192",
            "police": "191",
            "fire": "191"
        },
        "KH": {
            "ambulance": "119",
            "police": "117",
            "fire": "118"
        },
        "LA": {
            "ambulance": "190",
            "police": "191",
            "fire": "192"
        },
        "VN": {
            "ambulance": "115",
            "police": "113",
            "fire": "114"
        },
        "PH": {
            "ambulance": "117",
            "police": "117",
            "fire": "117"
        },
        "MY": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "ID": {
            "ambulance": "118",
            "police": "110",
            "fire": "119"
        },
        "TW": {
            "ambulance": "119",
            "police": "110",
            "fire": "119"
        },
        "HK": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "MO": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "NP": {
            "ambulance": "102",
            "police": "101",
            "fire": "101"
        },
        "BT": {
            "ambulance": "112",
            "police": "113",
            "fire": "110"
        },
        "MV": {
            "ambulance": "102",
            "police": "100",
            "fire": "101"
        },
        "AF": {
            "ambulance": "102",
            "police": "119",
            "fire": "101"
        },
        "IQ": {
            "ambulance": "123",
            "police": "130",
            "fire": "115"
        },
        "SY": {
            "ambulance": "110",
            "police": "112",
            "fire": "113"
        },
        "JO": {
            "ambulance": "191",
            "police": "191",
            "fire": "193"
        },
        "LB": {
            "ambulance": "193",
            "police": "191",
            "fire": "192"
        },
        "PS": {
            "ambulance": "101",
            "police": "100",
            "fire": "102"
        },
        "YE": {
            "ambulance": "191",
            "police": "191",
            "fire": "191"
        },
        "OM": {
            "ambulance": "1999",
            "police": "1122",
            "fire": "1999"
        },
        "QA": {
            "ambulance": "101",
            "police": "100",
            "fire": "102"
        },
        "KW": {
            "ambulance": "192",
            "police": "191",
            "fire": "193"
        },
        "BH": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "SA": {
            "ambulance": "997",
            "police": "997",
            "fire": "998"
        },
        "LY": {
            "ambulance": "193",
            "police": "194",
            "fire": "195"
        },
        "TN": {
            "ambulance": "198",
            "police": "197",
            "fire": "196"
        },
        "MA": {
            "ambulance": "15",
            "police": "19",
            "fire": "15"
        },
        "DZ": {
            "ambulance": "14",
            "police": "17",
            "fire": "14"
        },
        "EG": {
            "ambulance": "123",
            "police": "122",
            "fire": "180"
        },
        "SD": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "SS": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "ET": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "ER": {
            "ambulance": "2222",
            "police": "2222",
            "fire": "2222"
        },
        "DJ": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "KM": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "MG": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "MU": {
            "ambulance": "114",
            "police": "114",
            "fire": "114"
        },
        "SC": {
            "ambulance": "111",
            "police": "111",
            "fire": "111"
        },
        "MZ": {
            "ambulance": "198",
            "police": "191",
            "fire": "193"
        },
        "ZA": {
            "ambulance": "10177",
            "police": "10111",
            "fire": "10177"
        },
        "ZM": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "ZW": {
            "ambulance": "717",
            "police": "717",
            "fire": "717"
        },
        "BW": {
            "ambulance": "997",
            "police": "997",
            "fire": "997"
        },
        "NA": {
            "ambulance": "10114",
            "police": "10111",
            "fire": "10114"
        },
        "SZ": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "LS": {
            "ambulance": "121",
            "police": "121",
            "fire": "121"
        },
        "MW": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "TZ": {
            "ambulance": "999",
            "police": "112",
            "fire": "999"
        },
        "UG": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "RW": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "BI": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "CD": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        },
        "CF": {
            "ambulance": "125",
            "police": "124",
            "fire": "123"
        },
        "TD": {
            "ambulance": "125",
            "police": "124",
            "fire": "123"
        },
        "NE": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "ML": {
            "ambulance": "15",
            "police": "17",
            "fire": "15"
        },
        "SN": {
            "ambulance": "115",
            "police": "117",
            "fire": "115"
        },
        "MR": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "GM": {
            "ambulance": "2182182",
            "police": "2182182",
            "fire": "2182182"
        },
        "GN": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "CI": {
            "ambulance": "15",
            "police": "17",
            "fire": "15"
        },
        "BF": {
            "ambulance": "13",
            "police": "13",
            "fire": "13"
        },
        "TG": {
            "ambulance": "117",
            "police": "117",
            "fire": "117"
        },
        "BJ": {
            "ambulance": "17",
            "police": "17",
            "fire": "17"
        },
        "SL": {
            "ambulance": "999",
            "police": "999",
            "fire": "999"
        },
        "LR": {
            "ambulance": "222",
            "police": "222",
            "fire": "222"
        },
        "NG": {
            "ambulance": "112",
            "police": "112",
            "fire": "112"
        },
        "GH": {
            "ambulance": "911",
            "police": "911",
            "fire": "911"
        }
    },
    
    # "Do NOT" emergency actions
    "do_not_do": [
        "Do not move a person with suspected spinal injury",
        "Do not give food or drink to an unconscious person",
        "Do not apply ice directly to burns",
        "Do not remove objects embedded in wounds",
        "Do not use alcohol-based products on burns",
        "Do not leave a seizure victim unattended",
        "Do not restrain a person during seizure",
        "Do not attempt CPR without proper training"
    ],
    
    # "DO" emergency actions
    "do_commands": [
        "CALL EMERGENCY SERVICES FIRST in life-threatening situations",
        "Maintain calm and speak clearly to responders",
        "Follow dispatcher instructions exactly",
        "Stay with the victim until help arrives",
        "Use personal protective equipment when available",
        "Know your location and give precise directions",
        "Perform CPR if trained and necessary",
        "Control bleeding with direct pressure"
    ],
    
    # Trauma care protocols
    "trauma_triage": [
        "Assess airway, breathing, circulation (ABC)",
        "Control life-threatening bleeding first",
        "Treat shock before other injuries",
        "Immobilize suspected fractures",
        "Monitor vital signs continuously",
        "Document injuries and interventions"
    ],
    
    # Disaster response phases
    "disaster_phases": [
        "Preparedness", "Warning", "Impact", "Emergency",
        "Recovery", "Restoration", "Long-term recovery"
    ]
}


def get_emergency_concept(concept: str) -> dict:
    """Get a specific emergency concept."""
    if concept in EMERGENCY_CONCEPTS:
        return {
            "name": concept,
            "values": EMERGENCY_CONCEPTS[concept],
            "category": "knowledge",
            "source": "emergency_firstaid_knowledge.py"
        }
    
    # Search for concept in values
    for category, concepts in EMERGENCY_CONCEPTS.items():
        if isinstance(concepts, list):
            if concept.lower() in [c.lower() for c in concepts]:
                return {
                    "name": concept,
                    "category": category,
                    "description": f"Found in {category} emergency concepts",
                    "source": "emergency_firstaid_knowledge.py"
                }
    
    return {
        "name": concept,
        "error": "Concept not found",
        "source": "emergency_firstaid_knowledge.py"
    }


def get_all_emergency_concepts() -> list:
    """Get all available emergency concepts."""
    return list(EMERGENCY_CONCEPTS.keys())


# ============================================================================
# EMERGENCY PROCEDURES
# ============================================================================

def get_cardiac_arrest_procedure() -> dict:
    """Get CPR and cardiac arrest response procedure."""
    return {
        "name": "Cardiac Arrest Response",
        "immediate_actions": [
            "Check responsiveness - tap and shout",
            "Call 911 or local emergency number",
            "Check for normal breathing (look, listen, feel)",
            "If no breathing, begin CPR immediately",
            "Use AED if available - turn on and follow prompts"
        ],
        "cpr_steps": [
            "Position: Kneel beside victim, chest exposed",
            "Hand placement: Heel of one hand on center of chest, other hand on top",
            "Compression depth: 2-2.4 inches (5-6 cm) for adults",
            "Compression rate: 100-120 per minute",
            "Allow full chest recoil between compressions",
            "Minimize interruptions"
        ],
        "rescue_breaths": [
            "Open airway (head tilt-chin lift)",
            "Pinch nose, give 2 breaths (1 second each)",
            "Watch for chest rise",
            "Continue cycles: 30 compressions : 2 breaths"
        ],
        "source": "emergency_firstaid_knowledge.py"
    }


def get_bleeding_control_procedure() -> dict:
    """Get severe bleeding control procedure."""
    return {
        "name": "Severe Bleeding Control",
        "immediate_actions": [
            "Call emergency services",
            "Remove or cut away clothing covering the wound",
            "Apply direct pressure with clean cloth or gauze",
            "If bleeding continues, add more cloth and keep pressure",
            "If bleeding stops, bandage in place - do not remove"
        ],
        "tourniquet": [
            "Only for life-threatening extremity bleeding",
            "Apply 2-3 inches above wound",
            "Tighten until bleeding stops",
            "Record time applied",
            "Do not remove once applied"
        ],
        "source": "emergency_firstaid_knowledge.py"
    }


def get_choking_procedure() -> dict:
    """Get choking relief (Heimlich maneuver) procedure."""
    return {
        "name": "Choking Relief",
        "conscious_adult_child": {
            "steps": [
                "Ask 'Are you choking?' - if they nod yes, proceed",
                "Stand behind, wrap arms around waist",
                "Make fist, place thumb side against abdomen above navel",
                "Grasp fist with other hand",
                "Quick upward thrusts until object dislodged"
            ],
            "self_help": [
                "Place upper abdomen on edge of chair/table",
                "Press inward and upward forcefully"
            ]
        },
        "conscious_infant": {
            "steps": [
                "Hold infant face down on forearm, head lower than body",
                "Give 5 back blows between shoulder blades",
                "Turn infant face up, give 5 chest thrusts",
                "Repeat until object dislodged"
            ]
        },
        "unconscious_victim": {
            "steps": [
                "Call 911",
                "Begin CPR - after 30 compressions, check mouth for object",
                "If visible, remove object; if not, continue CPR"
            ]
        },
        "source": "emergency_firstaid_knowledge.py"
    }


def get_stroke_recognition() -> dict:
    """Get FAST stroke recognition and response."""
    return {
        "name": "Stroke Recognition (FAST)",
        "symptoms": {
            "Face drooping": "Ask person to smile - one side droops?",
            "Arm weakness": "Ask to raise both arms - one drifts down?",
            "Speech difficulty": "Ask a simple sentence - slurred or strange?",
            "Time to call": "If ANY of these, call emergency IMMEDIATELY"
        },
        "other_symptoms": [
            "Sudden confusion, trouble speaking",
            "Sudden numbness or weakness (face/arm/leg, especially one side)",
            "Sudden trouble seeing (eyes)",
            "Sudden trouble walking, dizziness, loss of balance",
            "Sudden severe headache with no known cause"
        ],
        "actions": [
            "Note time when symptoms started",
            "Do NOT give food, drink, or medication",
            "Do NOT let person sleep - keep them awake",
            "Stay with person until help arrives",
            "Report symptoms and time to responders"
        ],
        "source": "emergency_firstaid_knowledge.py"
    }


def get_allergy_reaction_procedure() -> dict:
    """Get severe allergic reaction (anaphylaxis) procedure."""
    return {
        "name": "Severe Allergic Reaction",
        "symptoms": [
            "Hives, swelling (lips, face, throat)",
            "Difficulty breathing, wheezing",
            "Rapid pulse, dizziness",
            "Nausea, vomiting",
            "Sense of impending doom"
        ],
        "immediate_actions": [
            "Call 911 immediately",
            "If epinephrine auto-injector available, use it NOW",
            "Lay person flat (elevate legs if no breathing difficulty)",
            "Do NOT give oral medication if breathing impaired",
            "Monitor until help arrives"
        ],
        "epinephrine_injection": [
            "Remove safety cap",
            "Inject into outer thigh (through clothing if needed)",
            "Hold for 3 seconds",
            "Massage injection site for 10 seconds",
            "Call 911 even if symptoms improve (may rebound)"
        ],
        "source": "emergency_firstaid_knowledge.py"
    }


# ============================================================================
# DISASTER RESPONSE
# ============================================================================

def get_disaster_response_protocol(disaster_type: str) -> dict:
    """Get disaster response protocol for specific type."""
    protocols = {
        "earthquake": {
            "immediate": [
                "DROP, COVER, and HOLD ON",
                "Stay inside until shaking stops",
                "Do NOT use elevators",
                "Be prepared for aftershocks"
            ],
            "after_shaking": [
                "Check for injuries and damage",
                "Evacuate if building is unsafe",
                "Avoid downed power lines",
                "Expect aftershocks - drop and cover again"
            ],
            "communication": [
                "Use text messages (phone lines may be overloaded)",
                "Check on neighbors (especially elderly/disabled)"
            ]
        },
        "fire": {
            "immediate": [
                "Get out immediately - don't stop for possessions",
                "Stay low under smoke",
                "Test doors with back of hand before opening",
                "If door hot, stay in room, seal gaps, signal for help"
            ],
            "if_trapped": [
                "Stay low where smoke is less dense",
                "Signal at window - wave bright cloth or flash light"
            ],
            "after_escape": [
                "Call 911 from safe location",
                "Do NOT re-enter under any circumstances",
                "Meet at pre-arranged meeting place"
            ]
        },
        "flood": {
            "before": [
                "Know flood risk in area",
                "Have evacuation plan",
                "Prepare emergency kit"
            ],
            "during": [
                "Move to higher ground immediately",
                "Do NOT walk, swim, or drive through flood waters",
                "6 inches of water can knock you down",
                "12 inches of water can carry away vehicles"
            ],
            "after": [
                "Wait for official all-clear before returning",
                "Avoid standing water (electrocution, contamination)",
                "Disinfect everything that got wet"
            ]
        },
        "hurricane": {
            "before": [
                "Know evacuation routes",
                "Stock emergency supplies",
                "Secure property (board windows, tie down objects)"
            ],
            "during": [
                "Stay indoors, away from windows",
                "Go to upper floor if flooded",
                "Turn off electricity if flooding"
            ],
            "after": [
                "Avoid downed power lines",
                "Stay out of floodwaters",
                "Document damage for insurance"
            ]
        }
    }
    
    return {
        "disaster_type": disaster_type,
        "protocol": protocols.get(disaster_type, {
            "error": "Protocol not found - contact emergency services"
        }),
        "source": "emergency_firstaid_knowledge.py"
    }


# ============================================================================
# AGENCY CONTACTS
# ============================================================================

def get_emergency_agencies(country: str = "US") -> dict:
    """Get emergency agency contacts for specified country."""
    if country.upper() == "US":
        return {
            "country": "United States",
            "emergency_number": "911",
            "agencies": EMERGENCY_CONCEPTS["emergency_agencies"],
            "source": "emergency_firstaid_knowledge.py"
        }
    else:
        return {
            "country": country,
            "emergency_number": EMERGENCY_CONCEPTS["international_emergency_numbers"].get(country.upper(), "Check local directory"),
            "agencies": [],
            "source": "emergency_firstaid_knowledge.py"
        }


def get_agency_info(agency_name: str) -> dict:
    """Get detailed information about a specific emergency agency."""
    agencies = EMERGENCY_CONCEPTS["emergency_agencies"]
    
    for agency in agencies:
        if agency_name.lower() in agency["name"].lower():
            return agency
    
    return {
        "error": "Agency not found",
        "suggestion": f"Try: {', '.join([a['name'] for a in agencies[:5]])}",
        "source": "emergency_firstaid_knowledge.py"
    }


# ============================================================================
# FIRST AID BY CONDITION
# ============================================================================

def get_first_aid_by_condition(condition: str) -> dict:
    """Get first aid instructions for specific medical condition."""
    conditions = {
        "cardiac_arrest": get_cardiac_arrest_procedure(),
        "bleeding": get_bleeding_control_procedure(),
        "choking": get_choking_procedure(),
        "stroke": get_stroke_recognition(),
        "allergy": get_allergy_reaction_procedure(),
    }
    
    return conditions.get(condition, {
        "error": "Condition not found",
        "suggestion": f"Available: {', '.join(conditions.keys())}",
        "source": "emergency_firstaid_knowledge.py"
    })


# ============================================================================
# "DO NOT" COMMANDS
# ============================================================================

def get_do_not_commands() -> dict:
    """Get list of things NOT to do in emergencies."""
    return {
        "title": "Emergency DO NOTs",
        "commands": EMERGENCY_CONCEPTS["do_not_do"],
        "source": "emergency_firstaid_knowledge.py"
    }


def get_do_commands() -> dict:
    """Get list of things TO DO in emergencies."""
    return {
        "title": "Emergency DO commands",
        "commands": EMERGENCY_CONCEPTS["do_commands"],
        "source": "emergency_firstaid_knowledge.py"
    }


# ============================================================================
# INTEGRATION
# ============================================================================

def integrate_emergency_into_self_model(self_state: dict) -> dict:
    """
    Integrate emergency response knowledge into Weslr's self-model.
    """
    emergency_mind = self_state.setdefault("emergency_mind", {
        "procedures_available": 0,
        "agencies_tracked": 0,
        "last_training_update": 0
    })
    
    emergency_mind["procedures_available"] = sum([
        len(EMERGENCY_CONCEPTS["first_aid_procedures"]),
        len(EMERGENCY_CONCEPTS["trauma_types"]),
        len(EMERGENCY_CONCEPTS["medical_emergencies"]),
        len(EMERGENCY_CONCEPTS["disaster_types"])
    ])
    
    emergency_mind["agencies_tracked"] = len(EMERGENCY_CONCEPTS["emergency_agencies"])
    
    self_state["emergency_mind"] = emergency_mind
    
    return self_state


def generate_emergency_self_description(self_state: dict) -> str:
    """Generate emergency response self-description for Weslr."""
    emergency_mind = self_state.get("emergency_mind", {})
    
    capabilities = [
        "First aid procedures (CPR, bleeding control, choking relief)",
        "Emergency medical condition response (stroke, cardiac arrest, allergy)",
        "Disaster response protocols (earthquake, fire, flood, hurricane)",
        "Agency contact information and emergency procedures"
    ]
    
    return (
        f"I can assist with emergency response including: "
        f"{', '.join(capabilities[:3])}. "
        f"I've tracked {emergency_mind.get('procedures_available', 0)} emergency procedures "
        f"and {emergency_mind.get('agencies_tracked', 0) } emergency agencies."
    )


# ============================================================================
# SPIRAL EXPANSION
# ============================================================================

def get_spiral_expansion(base_knowledge: dict) -> dict:
    """Expand emergency knowledge into related domains."""
    return {
        "trauma_care": [
            "Wound assessment and cleaning",
            "Fracture and dislocation management",
            "Burn classification and treatment",
            "Shock management",
            "Spinal injury immobilization"
        ],
        "medical_emergencies": [
            "Diabetic emergency response",
            "Seizure management",
            "Asthma attack response",
            "High blood pressure emergency",
            "Sepsis recognition"
        ],
        "disaster_response": [
            "Mass casualty incident triage (START method)",
            "Search and rescue coordination",
            "Shelter management",
            "Resource allocation",
            "Incident command system (ICS)"
        ],
        "public_health": [
            "Pandemic response protocols",
            "Infection control",
            "Vaccination program coordination",
            "Disease outbreak reporting"
        ]
    }


# ============================================================================
# INTEGRATION WITH EXISTING MODULES
# ============================================================================

from psychology_knowledge import (
    integrate_psychology_into_self_model,
    get_psychology_concept,
    get_all_concepts as get_all_psychology_concepts
)


def get_emergency_psychology_concept(concept: str) -> dict:
    """Get psychology concept with emergency context."""
    # First try as emergency concept
    result = get_emergency_concept(concept)
    if "error" not in result:
        return result
    
    # Then try as psychology concept
    psych_result = get_psychology_concept(concept)
    if "error" not in psych_result:
        return {
            **psych_result,
            "emergency_context": "Applicable to emergency psychology"
        }
    
    return psych_result


# ============================================================================
# END OF EMERGENCY FIRST AID KNOWLEDGE MODULE
# ============================================================================
