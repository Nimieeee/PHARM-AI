"""
Drug Database - Comprehensive pharmaceutical information
"""

import json
from typing import Dict, List, Optional

class DrugDatabase:
    """Drug information database with search capabilities."""
    
    def __init__(self):
        self.drugs = self._initialize_drug_data()
    
    def _initialize_drug_data(self) -> Dict:
        """Initialize comprehensive drug database."""
        return {
            # ACE Inhibitors
            "lisinopril": {
                "name": "Lisinopril",
                "class": "ACE Inhibitor",
                "mechanism": "Inhibits angiotensin-converting enzyme, reducing angiotensin II formation",
                "indications": ["Hypertension", "Heart failure", "Post-MI cardioprotection"],
                "contraindications": ["Pregnancy", "Angioedema history", "Bilateral renal artery stenosis"],
                "side_effects": ["Dry cough", "Hyperkalemia", "Angioedema", "Hypotension"],
                "interactions": ["NSAIDs", "Potassium supplements", "Diuretics"],
                "monitoring": ["Blood pressure", "Serum creatinine", "Potassium levels"]
            },
            
            "enalapril": {
                "name": "Enalapril",
                "class": "ACE Inhibitor",
                "mechanism": "Prodrug converted to enalaprilat; inhibits ACE",
                "indications": ["Hypertension", "Heart failure"],
                "contraindications": ["Pregnancy", "Angioedema history"],
                "side_effects": ["Dry cough", "Hyperkalemia", "Dizziness"],
                "interactions": ["NSAIDs", "Lithium", "Potassium-sparing diuretics"],
                "monitoring": ["Renal function", "Electrolytes", "Blood pressure"]
            },
            
            # Beta Blockers
            "metoprolol": {
                "name": "Metoprolol",
                "class": "Beta-1 Selective Blocker",
                "mechanism": "Selective beta-1 adrenergic receptor antagonist",
                "indications": ["Hypertension", "Angina", "Heart failure", "Post-MI"],
                "contraindications": ["Severe bradycardia", "Heart block", "Cardiogenic shock"],
                "side_effects": ["Bradycardia", "Fatigue", "Cold extremities", "Depression"],
                "interactions": ["Calcium channel blockers", "Digoxin", "Insulin"],
                "monitoring": ["Heart rate", "Blood pressure", "Signs of heart failure"]
            },
            
            "propranolol": {
                "name": "Propranolol",
                "class": "Non-selective Beta Blocker",
                "mechanism": "Non-selective beta-1 and beta-2 adrenergic receptor antagonist",
                "indications": ["Hypertension", "Migraine prophylaxis", "Anxiety", "Hyperthyroidism"],
                "contraindications": ["Asthma", "COPD", "Severe heart failure"],
                "side_effects": ["Bronchospasm", "Bradycardia", "Hypoglycemia masking"],
                "interactions": ["Calcium channel blockers", "Antidiabetic drugs", "Theophylline"],
                "monitoring": ["Respiratory function", "Heart rate", "Blood glucose"]
            },
            
            # NSAIDs
            "ibuprofen": {
                "name": "Ibuprofen",
                "class": "NSAID (Non-selective COX inhibitor)",
                "mechanism": "Inhibits cyclooxygenase-1 and -2, reducing prostaglandin synthesis",
                "indications": ["Pain", "Inflammation", "Fever", "Arthritis"],
                "contraindications": ["Active GI bleeding", "Severe heart failure", "Severe renal impairment"],
                "side_effects": ["GI upset", "Renal impairment", "Cardiovascular risk", "Fluid retention"],
                "interactions": ["Warfarin", "ACE inhibitors", "Lithium", "Methotrexate"],
                "monitoring": ["Renal function", "GI symptoms", "Blood pressure"]
            },
            
            "celecoxib": {
                "name": "Celecoxib",
                "class": "NSAID (Selective COX-2 inhibitor)",
                "mechanism": "Selective cyclooxygenase-2 inhibitor",
                "indications": ["Osteoarthritis", "Rheumatoid arthritis", "Acute pain"],
                "contraindications": ["Sulfonamide allergy", "Severe heart failure", "Active GI bleeding"],
                "side_effects": ["Cardiovascular risk", "Renal impairment", "Fluid retention"],
                "interactions": ["Warfarin", "ACE inhibitors", "Fluconazole"],
                "monitoring": ["Cardiovascular status", "Renal function", "Blood pressure"]
            },
            
            # Anticoagulants
            "warfarin": {
                "name": "Warfarin",
                "class": "Vitamin K Antagonist",
                "mechanism": "Inhibits vitamin K epoxide reductase, reducing clotting factor synthesis",
                "indications": ["Atrial fibrillation", "DVT/PE", "Mechanical heart valves"],
                "contraindications": ["Active bleeding", "Pregnancy", "Severe liver disease"],
                "side_effects": ["Bleeding", "Skin necrosis", "Purple toe syndrome"],
                "interactions": ["Antibiotics", "Amiodarone", "NSAIDs", "Alcohol"],
                "monitoring": ["INR", "Signs of bleeding", "Drug interactions"]
            },
            
            "rivaroxaban": {
                "name": "Rivaroxaban",
                "class": "Direct Factor Xa Inhibitor",
                "mechanism": "Direct, selective factor Xa inhibitor",
                "indications": ["Atrial fibrillation", "DVT/PE prevention and treatment"],
                "contraindications": ["Active bleeding", "Severe renal impairment"],
                "side_effects": ["Bleeding", "Nausea", "Dizziness"],
                "interactions": ["Strong CYP3A4 inhibitors", "P-glycoprotein inhibitors"],
                "monitoring": ["Renal function", "Signs of bleeding", "Drug interactions"]
            },
            
            # Cardiac Glycosides
            "digoxin": {
                "name": "Digoxin",
                "class": "Cardiac Glycoside",
                "mechanism": "Inhibits Na+/K+-ATPase pump, increases intracellular calcium",
                "indications": ["Heart failure", "Atrial fibrillation rate control"],
                "contraindications": ["Ventricular fibrillation", "Hypertrophic cardiomyopathy"],
                "side_effects": ["Arrhythmias", "Nausea", "Visual disturbances", "Confusion"],
                "interactions": ["Diuretics", "Amiodarone", "Quinidine", "Verapamil"],
                "monitoring": ["Digoxin levels", "Electrolytes", "Renal function", "ECG"]
            },
            
            # Diuretics
            "furosemide": {
                "name": "Furosemide",
                "class": "Loop Diuretic",
                "mechanism": "Inhibits Na+/K+/2Cl- cotransporter in ascending limb of Henle",
                "indications": ["Heart failure", "Edema", "Hypertension"],
                "contraindications": ["Anuria", "Severe electrolyte depletion"],
                "side_effects": ["Hypokalemia", "Hyponatremia", "Ototoxicity", "Hyperuricemia"],
                "interactions": ["Digoxin", "Lithium", "NSAIDs", "Aminoglycosides"],
                "monitoring": ["Electrolytes", "Renal function", "Hearing", "Blood pressure"]
            },
            
            "hydrochlorothiazide": {
                "name": "Hydrochlorothiazide",
                "class": "Thiazide Diuretic",
                "mechanism": "Inhibits Na+/Cl- cotransporter in distal convoluted tubule",
                "indications": ["Hypertension", "Mild heart failure", "Edema"],
                "contraindications": ["Anuria", "Severe renal impairment"],
                "side_effects": ["Hypokalemia", "Hyperuricemia", "Hyperglycemia", "Hyperlipidemia"],
                "interactions": ["Digoxin", "Lithium", "NSAIDs", "Antidiabetic drugs"],
                "monitoring": ["Electrolytes", "Glucose", "Uric acid", "Lipids"]
            },
            
            # Antibiotics
            "amoxicillin": {
                "name": "Amoxicillin",
                "class": "Beta-lactam Antibiotic (Penicillin)",
                "mechanism": "Inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins",
                "indications": ["Respiratory infections", "UTIs", "Skin infections", "H. pylori"],
                "contraindications": ["Penicillin allergy", "Infectious mononucleosis"],
                "side_effects": ["Allergic reactions", "GI upset", "C. diff colitis"],
                "interactions": ["Warfarin", "Methotrexate", "Oral contraceptives"],
                "monitoring": ["Allergic reactions", "GI symptoms", "Superinfections"]
            },
            
            "ciprofloxacin": {
                "name": "Ciprofloxacin",
                "class": "Fluoroquinolone Antibiotic",
                "mechanism": "Inhibits bacterial DNA gyrase and topoisomerase IV",
                "indications": ["UTIs", "Respiratory infections", "GI infections", "Anthrax"],
                "contraindications": ["Pregnancy", "Children", "Tendon disorders"],
                "side_effects": ["Tendon rupture", "QT prolongation", "CNS effects", "Photosensitivity"],
                "interactions": ["Warfarin", "Theophylline", "Antacids", "Iron supplements"],
                "monitoring": ["Tendon pain", "ECG", "CNS symptoms", "Drug interactions"]
            }
        }
    
    def search_drug(self, drug_name: str) -> Optional[Dict]:
        """Search for drug information by name."""
        drug_name_lower = drug_name.lower().strip()
        
        # Direct match
        if drug_name_lower in self.drugs:
            return self.drugs[drug_name_lower]
        
        # Partial match
        for key, drug_info in self.drugs.items():
            if drug_name_lower in key or drug_name_lower in drug_info["name"].lower():
                return drug_info
        
        return None
    
    def search_by_class(self, drug_class: str) -> List[Dict]:
        """Search for drugs by therapeutic class."""
        class_lower = drug_class.lower()
        results = []
        
        for drug_info in self.drugs.values():
            if class_lower in drug_info["class"].lower():
                results.append(drug_info)
        
        return results
    
    def get_drug_interactions(self, drug_name: str) -> List[str]:
        """Get drug interactions for a specific drug."""
        drug_info = self.search_drug(drug_name)
        if drug_info:
            return drug_info.get("interactions", [])
        return []
    
    def get_all_drug_names(self) -> List[str]:
        """Get list of all drug names in database."""
        return [drug_info["name"] for drug_info in self.drugs.values()]
    
    def get_drug_classes(self) -> List[str]:
        """Get list of all drug classes."""
        classes = set()
        for drug_info in self.drugs.values():
            classes.add(drug_info["class"])
        return sorted(list(classes))

# Global instance
drug_db = DrugDatabase()

def search_drug_info(drug_name: str) -> Optional[Dict]:
    """Search for drug information."""
    return drug_db.search_drug(drug_name)

def get_drug_interactions(drug_name: str) -> List[str]:
    """Get drug interactions."""
    return drug_db.get_drug_interactions(drug_name)

def search_drugs_by_class(drug_class: str) -> List[Dict]:
    """Search drugs by therapeutic class."""
    return drug_db.search_by_class(drug_class)