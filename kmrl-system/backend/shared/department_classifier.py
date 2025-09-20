"""
Department Classifier for KMRL
Classifies documents by department based on content and source
"""

import re
from typing import str, Dict, Any
import structlog

logger = structlog.get_logger()

class DepartmentClassifier:
    """Department classifier for KMRL documents"""
    
    def __init__(self):
        # Department keywords and patterns
        self.department_patterns = {
            "engineering": [
                "maintenance", "repair", "technical", "equipment", "machinery",
                "work order", "inspection", "calibration", "troubleshooting",
                "breakdown", "fault", "defect", "installation", "commissioning"
            ],
            "finance": [
                "invoice", "payment", "budget", "cost", "expense", "revenue",
                "accounting", "financial", "billing", "purchase", "procurement",
                "tender", "contract", "quotation", "price", "amount"
            ],
            "safety": [
                "safety", "incident", "accident", "hazard", "risk", "emergency",
                "compliance", "regulatory", "audit", "inspection", "violation",
                "training", "procedure", "protocol", "standard"
            ],
            "hr": [
                "personnel", "employee", "staff", "training", "recruitment",
                "attendance", "leave", "salary", "benefits", "performance",
                "appraisal", "disciplinary", "promotion", "transfer"
            ],
            "operations": [
                "operations", "schedule", "timetable", "service", "passenger",
                "station", "train", "route", "depot", "control", "dispatch"
            ],
            "executive": [
                "board", "meeting", "minutes", "policy", "decision", "approval",
                "strategy", "planning", "review", "report", "presentation"
            ]
        }
    
    def classify_department(self, text_content: str, source: str) -> str:
        """Classify document by department"""
        try:
            if not text_content:
                return "general"
            
            text_lower = text_content.lower()
            
            # Source-based classification
            if source == "maximo":
                return "engineering"
            elif source == "whatsapp":
                return "operations"
            elif source == "sharepoint":
                return self._classify_sharepoint_content(text_lower)
            elif source == "email":
                return self._classify_email_content(text_lower)
            
            # Content-based classification
            return self._classify_by_content(text_lower)
            
        except Exception as e:
            logger.error(f"Department classification failed: {e}")
            return "general"
    
    def _classify_sharepoint_content(self, text: str) -> str:
        """Classify SharePoint content"""
        if any(word in text for word in ["board", "meeting", "minutes", "policy"]):
            return "executive"
        elif any(word in text for word in ["hr", "personnel", "training", "recruitment"]):
            return "hr"
        elif any(word in text for word in ["finance", "budget", "invoice", "payment"]):
            return "finance"
        elif any(word in text for word in ["safety", "compliance", "regulatory"]):
            return "safety"
        else:
            return "general"
    
    def _classify_email_content(self, text: str) -> str:
        """Classify email content"""
        if any(word in text for word in ["maintenance", "repair", "technical"]):
            return "engineering"
        elif any(word in text for word in ["finance", "invoice", "payment", "budget"]):
            return "finance"
        elif any(word in text for word in ["safety", "incident", "accident"]):
            return "safety"
        elif any(word in text for word in ["hr", "personnel", "training"]):
            return "hr"
        else:
            return "general"
    
    def _classify_by_content(self, text: str) -> str:
        """Classify by content analysis"""
        department_scores = {}
        
        for department, keywords in self.department_patterns.items():
            score = sum(1 for keyword in keywords if keyword in text)
            department_scores[department] = score
        
        # Return department with highest score
        if department_scores:
            best_department = max(department_scores, key=department_scores.get)
            if department_scores[best_department] > 0:
                return best_department
        
        return "general"
