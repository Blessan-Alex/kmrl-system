"""
Stakeholder Manager for KMRL
Manages stakeholder information and notification preferences
"""

from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()

class StakeholderManager:
    """Stakeholder manager for KMRL notifications"""
    
    def __init__(self):
        # Stakeholder database (placeholder)
        self.stakeholders = {
            "engineering": [
                {"id": "eng_001", "name": "Chief Engineer", "email": "chief.engineer@kmrl.com", "role": "head"},
                {"id": "eng_002", "name": "Maintenance Manager", "email": "maintenance@kmrl.com", "role": "manager"},
                {"id": "eng_003", "name": "Technical Officer", "email": "technical@kmrl.com", "role": "officer"}
            ],
            "safety": [
                {"id": "safety_001", "name": "Safety Officer", "email": "safety@kmrl.com", "role": "head"},
                {"id": "safety_002", "name": "Compliance Manager", "email": "compliance@kmrl.com", "role": "manager"}
            ],
            "operations": [
                {"id": "ops_001", "name": "Operations Manager", "email": "operations@kmrl.com", "role": "head"},
                {"id": "ops_002", "name": "Station Controller", "email": "station@kmrl.com", "role": "controller"}
            ],
            "finance": [
                {"id": "fin_001", "name": "Finance Manager", "email": "finance@kmrl.com", "role": "head"},
                {"id": "fin_002", "name": "Accounts Officer", "email": "accounts@kmrl.com", "role": "officer"}
            ],
            "executive": [
                {"id": "exec_001", "name": "Managing Director", "email": "md@kmrl.com", "role": "head"},
                {"id": "exec_002", "name": "General Manager", "email": "gm@kmrl.com", "role": "manager"}
            ]
        }
    
    def get_stakeholders(self, departments: List[str], source_department: str = None) -> List[Dict[str, Any]]:
        """Get stakeholders for notification"""
        try:
            stakeholders = []
            
            for dept in departments:
                if dept == "all":
                    # Get all stakeholders
                    for dept_stakeholders in self.stakeholders.values():
                        stakeholders.extend(dept_stakeholders)
                elif dept in self.stakeholders:
                    stakeholders.extend(self.stakeholders[dept])
            
            # Add source department stakeholders if specified
            if source_department and source_department in self.stakeholders:
                stakeholders.extend(self.stakeholders[source_department])
            
            # Remove duplicates
            unique_stakeholders = []
            seen_ids = set()
            for stakeholder in stakeholders:
                if stakeholder['id'] not in seen_ids:
                    unique_stakeholders.append(stakeholder)
                    seen_ids.add(stakeholder['id'])
            
            logger.info(f"Retrieved {len(unique_stakeholders)} stakeholders for departments: {departments}")
            return unique_stakeholders
            
        except Exception as e:
            logger.error(f"Stakeholder retrieval failed: {e}")
            return []
    
    def get_stakeholder_by_id(self, stakeholder_id: str) -> Dict[str, Any]:
        """Get stakeholder by ID"""
        try:
            for dept_stakeholders in self.stakeholders.values():
                for stakeholder in dept_stakeholders:
                    if stakeholder['id'] == stakeholder_id:
                        return stakeholder
            return None
            
        except Exception as e:
            logger.error(f"Stakeholder lookup failed: {e}")
            return None
    
    def get_department_stakeholders(self, department: str) -> List[Dict[str, Any]]:
        """Get stakeholders for specific department"""
        try:
            if department in self.stakeholders:
                return self.stakeholders[department]
            return []
            
        except Exception as e:
            logger.error(f"Department stakeholder retrieval failed: {e}")
            return []
