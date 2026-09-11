import re
from typing import Dict, Any, List

class FieldExtractor:
    @staticmethod
    def extract_fields(doc_type: str, text: str) -> List[Dict[str, Any]]:
        """
        Extracts structured fields from text based on document type using Regex and NLP patterns.
        """
        fields = []
        if not text:
            return fields

        if doc_type == "GST":
            gstin_match = re.search(r"\b([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})\b", text)
            if gstin_match:
                fields.append({"field_name": "gstin", "field_value": gstin_match.group(1), "confidence": 99.0, "validation_status": "VALID"})

            status_match = re.search(r"Status\s*:\s*(ACTIVE|CANCELLED|SUSPENDED)", text, re.IGNORECASE)
            if status_match:
                fields.append({"field_name": "registration_status", "field_value": status_match.group(1).upper(), "confidence": 98.0, "validation_status": "VALID"})
            
            name_match = re.search(r"Legal Name\s*:\s*([^\n,]+)", text, re.IGNORECASE) or re.search(r"Name\s*:\s*([^\n,]+)", text, re.IGNORECASE)
            if name_match:
                fields.append({"field_name": "legal_name", "field_value": name_match.group(1).strip(), "confidence": 95.0, "validation_status": "VALID"})

            addr_match = re.search(r"Address\s*:\s*([^\n]+)", text, re.IGNORECASE)
            if addr_match:
                fields.append({"field_name": "address", "field_value": addr_match.group(1).strip(), "confidence": 92.0, "validation_status": "VALID"})

        elif doc_type == "PAN":
            pan_match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b", text)
            if pan_match:
                fields.append({"field_name": "pan", "field_value": pan_match.group(1), "confidence": 99.0, "validation_status": "VALID"})

            name_match = re.search(r"Name\s*:\s*([^\n]+)", text, re.IGNORECASE) or re.search(r"Holder\s*:\s*([^\n]+)", text, re.IGNORECASE)
            if name_match:
                fields.append({"field_name": "entity_name", "field_value": name_match.group(1).strip(), "confidence": 94.0, "validation_status": "VALID"})

        elif doc_type == "UDYAM":
            udyam_match = re.search(r"\b(UDYAM-[A-Z]{2}-[0-9]{2}-[0-9]{7})\b", text)
            if udyam_match:
                fields.append({"field_name": "udyam_number", "field_value": udyam_match.group(1), "confidence": 99.0, "validation_status": "VALID"})

            ent_match = re.search(r"Enterprise Name\s*:\s*([^\n]+)", text, re.IGNORECASE) or re.search(r"Name of Enterprise\s*:\s*([^\n]+)", text, re.IGNORECASE)
            if ent_match:
                fields.append({"field_name": "enterprise_name", "field_value": ent_match.group(1).strip(), "confidence": 95.0, "validation_status": "VALID"})

            cat_match = re.search(r"Major Activity\s*:\s*(Manufacturing|Services|Trading)", text, re.IGNORECASE)
            if cat_match:
                fields.append({"field_name": "category", "field_value": cat_match.group(1).strip(), "confidence": 96.0, "validation_status": "VALID"})

            addr_match = re.search(r"Registered Address\s*:\s*([^\n]+)", text, re.IGNORECASE)
            if addr_match:
                fields.append({"field_name": "address", "field_value": addr_match.group(1).strip(), "confidence": 91.0, "validation_status": "VALID"})

        elif doc_type == "EPFO":
            epf_match = re.search(r"\b([A-Z]{2}[A-Z]{3}[0-9]{7}[0-9]{3})\b", text) or re.search(r"Code\s*:\s*([A-Z0-9/-]+)", text)
            if epf_match:
                fields.append({"field_name": "establishment_code", "field_value": epf_match.group(1), "confidence": 96.0, "validation_status": "VALID"})

            status_match = re.search(r"Status\s*:\s*(ACTIVE|INACTIVE|NOT_FOUND)", text, re.IGNORECASE)
            if status_match:
                fields.append({"field_name": "status", "field_value": status_match.group(1).upper(), "confidence": 95.0, "validation_status": "VALID"})

        elif doc_type == "FINANCIAL":
            turnover_match = re.search(r"Turnover\s*:\s*₹?\s*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE) or re.search(r"Revenue\s*:\s*₹?\s*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
            if turnover_match:
                fields.append({"field_name": "annual_turnover", "field_value": turnover_match.group(1).replace(",", ""), "confidence": 92.0, "validation_status": "VALID"})

        elif doc_type == "EXPERIENCE":
            val_match = re.search(r"Value\s*:\s*₹?\s*([0-9,]+(?:\.[0-9]+)?)", text, re.IGNORECASE)
            if val_match:
                fields.append({"field_name": "project_value", "field_value": val_match.group(1).replace(",", ""), "confidence": 90.0, "validation_status": "VALID"})

        return fields
