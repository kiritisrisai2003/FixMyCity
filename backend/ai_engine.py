"""
AI Engine using Groq API for complaint analysis
Optimized for free tier usage with caching and mock mode
"""

import os
import json
import hashlib
from typing import Dict, Optional
from datetime import datetime
import httpx

class AIEngine:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.model = "llama-3.1-8b-instant"  # Faster, cheaper model for free tier
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.cache = {}  # Simple in-memory cache
        self.mock_mode = not self.api_key  # Auto-enable mock if no API key
        
    def is_available(self):
        """Check if AI engine is available"""
        return bool(self.api_key) or self.mock_mode
    
    def get_followup_questions(self, category: str) -> list:
        """Get category-specific follow-up questions"""
        questions_map = {
            "garbage": [
                {"q": "How many days has garbage not been collected?", "type": "number"},
                {"q": "Is there a bad smell?", "type": "boolean"},
                {"q": "Is it near a residential area?", "type": "boolean"},
                {"q": "Approximate quantity (in bags/bins)?", "type": "text"}
            ],
            "roads": [
                {"q": "Is the pothole causing accidents?", "type": "boolean"},
                {"q": "How deep is the pothole (approx)?", "type": "select", "options": ["Small (<3 inches)", "Medium (3-6 inches)", "Deep (>6 inches)"]},
                {"q": "Is it on a main road or residential street?", "type": "select", "options": ["Main Road", "Residential Street", "Highway"]},
                {"q": "Has it been reported before?", "type": "boolean"}
            ],
            "water": [
                {"q": "Is there complete water shortage or low pressure?", "type": "select", "options": ["Complete shortage", "Low pressure", "Contaminated water"]},
                {"q": "How many days has this been happening?", "type": "number"},
                {"q": "Number of households affected (approx)?", "type": "number"}
            ],
            "electricity": [
                {"q": "Is it a complete power outage or fluctuation?", "type": "select", "options": ["Complete outage", "Voltage fluctuation", "Frequent trips"]},
                {"q": "Duration of issue (in hours)?", "type": "number"},
                {"q": "Is it affecting the entire area?", "type": "boolean"}
            ],
            "streetlight": [
                {"q": "How many streetlights are not working?", "type": "select", "options": ["1-2", "3-5", "More than 5", "Entire street"]},
                {"q": "Is it a dark area/accident-prone zone?", "type": "boolean"}
            ],
            "noise": [
                {"q": "Type of noise pollution?", "type": "select", "options": ["Construction", "Loud music/events", "Traffic", "Industrial", "Other"]},
                {"q": "Time of occurrence?", "type": "select", "options": ["Morning (6AM-12PM)", "Afternoon (12PM-6PM)", "Evening (6PM-10PM)", "Night (10PM-6AM)"]},
                {"q": "Is it continuous or intermittent?", "type": "select", "options": ["Continuous", "Intermittent"]}
            ],
            "parks": [
                {"q": "What is the issue?", "type": "select", "options": ["Not maintained", "Broken equipment", "Safety concern", "Cleanliness", "Other"]},
                {"q": "Is it affecting children's safety?", "type": "boolean"}
            ]
        }
        
        return questions_map.get(category.lower(), [])
    
    def _get_cache_key(self, description: str, category: str) -> str:
        """Generate cache key for complaint"""
        content = f"{description}_{category}".lower()
        return hashlib.md5(content.encode()).hexdigest()
    
    async def analyze_complaint(
        self,
        description: str,
        category: str,
        location: str,
        additional_data: Optional[Dict] = None,
        image_validation: Optional[Dict] = None
    ) -> Dict:
        """Analyze complaint and return structured output"""
        
        # Check cache first
        cache_key = self._get_cache_key(description, category)
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        # Use mock mode if no API key
        if self.mock_mode:
            result = self._mock_analysis(description, category, additional_data)
        else:
            try:
                result = await self._groq_analysis(description, category, location, additional_data, image_validation)
            except Exception as e:
                print(f"Groq API error: {e}, falling back to mock mode")
                result = self._mock_analysis(description, category, additional_data)
        
        # Cache result
        self.cache[cache_key] = result
        return result
    
    def _mock_analysis(self, description: str, category: str, additional_data: Optional[Dict]) -> Dict:
        """Mock AI analysis for demo mode"""
        
        # Smart category detection
        desc_lower = description.lower()
        if category == "other":
            if any(word in desc_lower for word in ["garbage", "waste", "trash", "dump"]):
                category = "garbage"
            elif any(word in desc_lower for word in ["road", "pothole", "crater", "street"]):
                category = "roads"
            elif any(word in desc_lower for word in ["water", "tap", "pipeline", "supply"]):
                category = "water"
            elif any(word in desc_lower for word in ["electricity", "power", "light", "outage"]):
                category = "electricity"
            elif any(word in desc_lower for word in ["park", "garden", "playground"]):
                category = "parks"
            elif any(word in desc_lower for word in ["noise", "loud", "sound"]):
                category = "noise"
        
        # Priority and severity detection
        urgent_keywords = ["urgent", "emergency", "critical", "danger", "accident", "overflow", "burst"]
        high_keywords = ["many days", "week", "severe", "major", "multiple"]
        
        is_urgent = any(word in desc_lower for word in urgent_keywords)
        is_high = any(word in desc_lower for word in high_keywords)
        
        if is_urgent:
            priority = "high"
            severity = "critical"
            priority_score = 85 + (len(description) // 20)
        elif is_high:
            priority = "high"
            severity = "moderate"
            priority_score = 70 + (len(description) // 30)
        else:
            priority = "medium"
            severity = "moderate"
            priority_score = 50 + (len(description) // 40)
        
        # Estimate impact based on additional data
        estimated_impact = 10
        if additional_data:
            if additional_data.get("near_residential") == "yes":
                estimated_impact += 50
            if additional_data.get("households_affected"):
                try:
                    estimated_impact = int(additional_data["households_affected"])
                except:
                    pass
        
        # Generate cluster name
        cluster = f"{category.title()} Issues - {self._extract_area(description)}"
        
        # Generate AI message
        ai_message = self._generate_acknowledgment(category, priority, severity)
        
        return {
            "category": category,
            "priority": priority,
            "priorityScore": min(priority_score, 100),
            "severity": severity,
            "estimatedImpact": estimated_impact,
            "cluster": cluster,
            "aiMessage": ai_message,
            "suggestedDepartment": self._get_department(category),
            "estimatedResolutionTime": self._estimate_resolution_time(category, severity)
        }
    
    async def _groq_analysis(
        self,
        description: str,
        category: str,
        location: str,
        additional_data: Optional[Dict],
        image_validation: Optional[Dict]
    ) -> Dict:
        """Use Groq API for analysis"""
        
        # Build context
        context = f"Complaint: {description}\nLocation: {location}\n"
        if additional_data:
            context += f"Additional info: {json.dumps(additional_data)}\n"
        if image_validation:
            context += f"Image analysis: {image_validation.get('summary', 'No image')}\n"
        
        prompt = f"""You are an AI assistant for a civic complaint management system. Analyze this complaint and return ONLY a valid JSON object with no additional text.

{context}

Return JSON with exactly these fields:
{{
  "category": "garbage|roads|water|electricity|parks|noise|streetlight|other",
  "priority": "high|medium|low",
  "priorityScore": <number 1-100>,
  "severity": "critical|moderate|minor",
  "estimatedImpact": <number of citizens affected>,
  "cluster": "<area name> - <issue type>",
  "aiMessage": "<acknowledgment message for citizen>",
  "suggestedDepartment": "<department name>",
  "estimatedResolutionTime": "<time estimate>"
}}

Rules:
- Use 'high' priority for urgent/dangerous issues
- estimatedImpact should be realistic (10-500)
- cluster should group similar nearby issues
- aiMessage should be empathetic and reassuring
"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a civic complaint analysis AI. Return only valid JSON."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 500
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse JSON from response
                    # Sometimes the model adds markdown code blocks
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    return json.loads(content)
                else:
                    raise Exception(f"API error: {response.status_code}")
                    
        except Exception as e:
            print(f"Groq API call failed: {e}")
            # Fallback to mock
            return self._mock_analysis(description, category, additional_data)
    
    def _extract_area(self, text: str) -> str:
        """Extract area name from text"""
        common_areas = ["Whitefield", "Koramangala", "Indiranagar", "HSR Layout", 
                       "Marathahalli", "Jayanagar", "BTM", "Bellandur", "Sarjapur"]
        
        for area in common_areas:
            if area.lower() in text.lower():
                return area
        
        return "Central Area"
    
    def _get_department(self, category: str) -> str:
        """Map category to department"""
        dept_map = {
            "garbage": "Solid Waste Management",
            "roads": "Public Works Department",
            "water": "Water Supply Department",
            "electricity": "Electricity Board",
            "parks": "Parks & Gardens Department",
            "noise": "Pollution Control Board",
            "streetlight": "Street Lighting Department"
        }
        return dept_map.get(category, "General Administration")
    
    def _estimate_resolution_time(self, category: str, severity: str) -> str:
        """Estimate resolution time"""
        if severity == "critical":
            return "24-48 hours"
        elif severity == "moderate":
            return "3-5 days"
        else:
            return "5-7 days"
    
    def _generate_acknowledgment(self, category: str, priority: str, severity: str) -> str:
        """Generate personalized acknowledgment message"""
        messages = {
            "garbage": "Thank you for reporting the garbage issue. We understand the inconvenience and health concerns. Our sanitation team will address this promptly.",
            "roads": "We've received your road complaint. Safety is our priority. Our road maintenance team will inspect and resolve this issue soon.",
            "water": "Your water supply complaint has been registered. We know how essential clean water is. Our team is working to restore normal supply.",
            "electricity": "Thank you for reporting the power issue. We're coordinating with the electricity department for immediate resolution.",
            "parks": "Your concern about the park has been noted. We'll ensure it's safe and well-maintained for everyone to enjoy.",
            "noise": "We've logged your noise complaint. Peace and quiet matter. We'll investigate and take necessary action.",
            "streetlight": "Thank you for reporting the streetlight issue. Safety is important. Our team will fix this promptly."
        }
        
        base_msg = messages.get(category, "Thank you for your complaint. We're on it and will resolve this soon.")
        
        if priority == "high":
            base_msg += " This has been marked as high priority."
        
        return base_msg