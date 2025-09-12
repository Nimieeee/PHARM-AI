"""
Simple drug database for quick reference in the pharmacology chatbot.
"""

DRUG_CATEGORIES = {
    "Cardiovascular": [
        "ACE Inhibitors", "ARBs", "Beta-blockers", "Calcium Channel Blockers",
        "Diuretics", "Statins", "Anticoagulants", "Antiplatelets"
    ],
    "CNS": [
        "Antidepressants", "Antipsychotics", "Anxiolytics", "Anticonvulsants",
        "Opioids", "Local Anesthetics", "General Anesthetics"
    ],
    "Antimicrobials": [
        "Penicillins", "Cephalosporins", "Fluoroquinolones", "Macrolides",
        "Antivirals", "Antifungals", "Antiparasitics"
    ],
    "Endocrine": [
        "Insulin", "Oral Hypoglycemics", "Thyroid Hormones", "Corticosteroids",
        "Sex Hormones", "Growth Hormones"
    ],
    "Respiratory": [
        "Bronchodilators", "Corticosteroids", "Antihistamines", "Decongestants",
        "Antitussives", "Mucolytics"
    ],
    "GI": [
        "PPIs", "H2 Blockers", "Antacids", "Antiemetics", "Laxatives",
        "Antidiarrheals", "IBD Medications"
    ]
}

COMMON_DRUGS = {
    "aspirin": {
        "class": "NSAID/Antiplatelet",
        "mechanism": "Irreversible COX inhibition",
        "uses": ["Pain relief", "Fever reduction", "Cardiovascular protection"],
        "contraindications": ["Bleeding disorders", "Peptic ulcer", "Children with viral infections"]
    },
    "metformin": {
        "class": "Biguanide",
        "mechanism": "Decreases hepatic glucose production, increases insulin sensitivity",
        "uses": ["Type 2 diabetes", "PCOS", "Prediabetes"],
        "contraindications": ["Severe kidney disease", "Metabolic acidosis", "Severe heart failure"]
    },
    "lisinopril": {
        "class": "ACE Inhibitor",
        "mechanism": "Inhibits angiotensin-converting enzyme",
        "uses": ["Hypertension", "Heart failure", "Post-MI cardioprotection"],
        "contraindications": ["Pregnancy", "Angioedema history", "Bilateral renal artery stenosis"]
    },
    "warfarin": {
        "class": "Anticoagulant",
        "mechanism": "Vitamin K antagonist",
        "uses": ["Atrial fibrillation", "DVT/PE", "Mechanical heart valves"],
        "contraindications": ["Active bleeding", "Pregnancy", "Severe liver disease"]
    }
}

def get_drug_info(drug_name: str) -> dict:
    """Get basic information about a drug."""
    return COMMON_DRUGS.get(drug_name.lower(), None)

def get_drug_categories() -> dict:
    """Get all drug categories."""
    return DRUG_CATEGORIES