"""
Priority Engine - Creates clusters and generates insights
"""

from typing import List, Dict
from collections import defaultdict
from datetime import datetime, timedelta
import re

class PriorityEngine:
    def __init__(self):
        self.cluster_threshold = 3  # Minimum complaints to form a cluster
    
    def create_clusters(self, complaints: List[Dict]) -> List[Dict]:
        """Create complaint clusters by location and category"""
        
        # Group by category and location
        cluster_map = defaultdict(list)
        
        for complaint in complaints:
            if complaint["status"] in ["resolved", "closed"]:
                continue
            
            category = complaint.get("category", "other")
            location = self._extract_location(complaint.get("location", ""))
            
            key = f"{category}_{location}"
            cluster_map[key].append(complaint)
        
        # Create cluster objects
        clusters = []
        
        for key, items in cluster_map.items():
            if len(items) < self.cluster_threshold:
                continue
            
            category, location = key.split("_", 1)
            
            # Calculate cluster priority
            high_priority_count = sum(1 for c in items if c.get("aiAnalysis", {}).get("priority") == "high")
            avg_priority_score = sum(c.get("aiAnalysis", {}).get("priorityScore", 50) for c in items) / len(items)
            
            # Determine cluster priority
            if high_priority_count >= len(items) * 0.5 or avg_priority_score >= 75:
                cluster_priority = "HIGH"
            elif avg_priority_score >= 50:
                cluster_priority = "MEDIUM"
            else:
                cluster_priority = "LOW"
            
            # Calculate total impact
            total_impact = sum(c.get("aiAnalysis", {}).get("estimatedImpact", 10) for c in items)
            
            # Resource allocation suggestion
            resources = self._suggest_resources(category, len(items), cluster_priority)
            
            clusters.append({
                "id": key,
                "name": f"{category.title()} - {location}",
                "category": category,
                "location": location,
                "count": len(items),
                "priority": cluster_priority,
                "priorityScore": round(avg_priority_score, 1),
                "totalImpact": total_impact,
                "resources": resources,
                "complaintIds": [c["id"] for c in items]
            })
        
        # Sort by priority score
        clusters.sort(key=lambda x: x["priorityScore"], reverse=True)
        
        return clusters[:10]  # Return top 10 clusters
    
    def _extract_location(self, location_text: str) -> str:
        """Extract area/neighborhood from location text"""
        # Common Bangalore areas (can be expanded)
        areas = [
            "Whitefield", "Koramangala", "Indiranagar", "HSR Layout",
            "Marathahalli", "Jayanagar", "BTM", "Bellandur", "Sarjapur",
            "Electronic City", "JP Nagar", "Banashankari", "Malleshwaram",
            "Yelahanka", "Hebbal", "Frazer Town", "Richmond Town"
        ]
        
        location_lower = location_text.lower()
        
        for area in areas:
            if area.lower() in location_lower:
                return area
        
        # If no match, try to extract first word that looks like an area
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', location_text)
        if words:
            return words[0]
        
        return "Central Area"
    
    def _suggest_resources(self, category: str, complaint_count: int, priority: str) -> Dict:
        """Suggest resource allocation for cluster"""
        
        base_resources = {
            "garbage": {"type": "Garbage trucks", "base": 1},
            "roads": {"type": "Road repair crews", "base": 1},
            "water": {"type": "Plumbing teams", "base": 1},
            "electricity": {"type": "Electrical teams", "base": 1},
            "parks": {"type": "Maintenance crews", "base": 1},
            "noise": {"type": "Inspection officers", "base": 1},
            "streetlight": {"type": "Electrical crews", "base": 1}
        }
        
        resource_info = base_resources.get(category, {"type": "Teams", "base": 1})
        
        # Scale based on complaint count
        multiplier = 1
        if complaint_count > 20:
            multiplier = 3
        elif complaint_count > 10:
            multiplier = 2
        
        # Adjust for priority
        if priority == "HIGH":
            multiplier += 1
        
        quantity = resource_info["base"] * multiplier
        
        return {
            "type": resource_info["type"],
            "quantity": quantity,
            "suggestion": f"Deploy {quantity} {resource_info['type']}"
        }
    
    def generate_insights(self, complaints: List[Dict], clusters: List[Dict]) -> List[Dict]:
        """Generate predictive insights"""
        insights = []
        
        # Check for rapid growth in categories
        recent_complaints = [c for c in complaints 
                           if self._is_recent(c.get("timestamp", c.get("created_at")))]
        
        if len(recent_complaints) > 5:
            # Category trend analysis
            category_counts = defaultdict(int)
            for complaint in recent_complaints:
                category_counts[complaint.get("category", "other")] += 1
            
            for category, count in category_counts.items():
                if count >= 5:
                    # Check if increasing
                    older_count = len([c for c in complaints 
                                     if c.get("category") == category 
                                     and not self._is_recent(c.get("timestamp", c.get("created_at")))])
                    
                    if count > older_count * 0.5:  # 50% growth
                        insights.append({
                            "type": "trend_alert",
                            "severity": "high" if count >= 10 else "medium",
                            "title": f"{category.title()} complaints increasing rapidly",
                            "description": f"{count} new {category} complaints in last 24 hours. {self._get_prediction(category)}",
                            "recommendation": self._get_recommendation(category, count)
                        })
        
        # High priority cluster alerts
        for cluster in clusters[:3]:  # Top 3 clusters
            if cluster["priority"] == "HIGH":
                insights.append({
                    "type": "cluster_alert",
                    "severity": "high",
                    "title": f"Critical cluster: {cluster['name']}",
                    "description": f"{cluster['count']} active complaints with {cluster['totalImpact']} citizens affected",
                    "recommendation": cluster["resources"]["suggestion"]
                })
        
        # Reopened complaints pattern
        reopened_count = len([c for c in complaints if c.get("reraise_count", 0) > 0])
        if reopened_count > 3:
            insights.append({
                "type": "quality_alert",
                "severity": "medium",
                "title": "Multiple complaints being re-raised",
                "description": f"{reopened_count} complaints were reopened by citizens",
                "recommendation": "Review resolution quality and follow-up procedures"
            })
        
        return insights
    
    def _is_recent(self, timestamp_str: str, hours: int = 24) -> bool:
        """Check if timestamp is within last N hours"""
        if not timestamp_str:
            return False
        
        try:
            # Handle both ISO format and SQLite format
            if 'T' in timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = datetime.fromisoformat(timestamp_str)
            
            return datetime.now() - timestamp < timedelta(hours=hours)
        except:
            return False
    
    def _get_prediction(self, category: str) -> str:
        """Get category-specific prediction"""
        predictions = {
            "garbage": "Potential sanitation crisis if not addressed within 72 hours.",
            "roads": "Risk of accidents increasing. Immediate attention required.",
            "water": "Water shortage may affect more areas. Urgent intervention needed.",
            "electricity": "Power disruption pattern detected. Grid check recommended.",
            "noise": "Continuous complaints indicate persistent source. Investigation needed."
        }
        return predictions.get(category, "Pattern requires monitoring.")
    
    def _get_recommendation(self, category: str, count: int) -> str:
        """Get actionable recommendation"""
        if count >= 15:
            return f"Emergency response required. Deploy maximum {category} management resources."
        elif count >= 8:
            return f"Urgent action needed. Increase {category} team allocation by 50%."
        else:
            return f"Monitor situation closely and prepare additional resources."