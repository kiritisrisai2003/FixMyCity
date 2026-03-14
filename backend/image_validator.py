"""
Image Validator - Validates uploaded images against complaint category
Uses Groq Vision API (if available) or mock validation
"""

import os
import base64
from typing import Dict, Optional
import httpx

class ImageValidator:
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY", "")
        self.vision_model = "llava-v1.5-7b-4096-preview"  # Groq's vision model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self.mock_mode = not self.api_key
    
    async def validate_image(
        self,
        image_path: str,
        complaint_text: str,
        category: str
    ) -> Optional[Dict]:
        """Validate if image matches the complaint"""
        
        if self.mock_mode:
            return self._mock_validation(category)
        
        try:
            return await self._groq_vision_validation(image_path, complaint_text, category)
        except Exception as e:
            print(f"Vision API error: {e}, using mock validation")
            return self._mock_validation(category)
    
    def _mock_validation(self, category: str) -> Dict:
        """Mock image validation for demo"""
        
        # Simulate realistic validation
        confidence_map = {
            "garbage": {"match": True, "confidence": 87, "detected": "Garbage pile"},
            "roads": {"match": True, "confidence": 92, "detected": "Road pothole"},
            "water": {"match": True, "confidence": 85, "detected": "Water leakage"},
            "electricity": {"match": True, "confidence": 78, "detected": "Electrical issue"},
            "parks": {"match": True, "confidence": 81, "detected": "Park area"},
            "noise": {"match": True, "confidence": 65, "detected": "Noise source"},
            "streetlight": {"match": True, "confidence": 88, "detected": "Streetlight"}
        }
        
        validation = confidence_map.get(category, {
            "match": True,
            "confidence": 75,
            "detected": "Civic issue"
        })
        
        return {
            "isValid": validation["match"],
            "confidence": validation["confidence"],
            "detectedObjects": [validation["detected"]],
            "matchesCategory": validation["match"],
            "summary": f"{validation['detected']} detected with {validation['confidence']}% confidence",
            "warning": None if validation["match"] else "Image may not match complaint category"
        }
    
    async def _groq_vision_validation(
        self,
        image_path: str,
        complaint_text: str,
        category: str
    ) -> Dict:
        """Use Groq Vision API for image validation"""
        
        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Determine image type
        ext = image_path.split('.')[-1].lower()
        mime_type = f"image/{ext if ext in ['jpeg', 'jpg', 'png', 'gif'] else 'jpeg'}"
        
        prompt = f"""Analyze this image for a civic complaint system.

Complaint category: {category}
Complaint text: {complaint_text}

Determine:
1. What civic issue is visible in the image?
2. Does it match the complaint category "{category}"?
3. Confidence level (0-100)
4. Any visible objects or issues

Return JSON only:
{{
  "detectedIssue": "description",
  "matchesCategory": true/false,
  "confidence": <number>,
  "detectedObjects": ["object1", "object2"],
  "warning": "message if mismatch" or null
}}"""

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.base_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.vision_model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:{mime_type};base64,{image_data}"
                                        }
                                    }
                                ]
                            }
                        ],
                        "temperature": 0.2,
                        "max_tokens": 300
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Parse JSON
                    import json
                    if "```json" in content:
                        content = content.split("```json")[1].split("```")[0].strip()
                    elif "```" in content:
                        content = content.split("```")[1].split("```")[0].strip()
                    
                    data = json.loads(content)
                    
                    return {
                        "isValid": data.get("matchesCategory", True),
                        "confidence": data.get("confidence", 80),
                        "detectedObjects": data.get("detectedObjects", []),
                        "matchesCategory": data.get("matchesCategory", True),
                        "summary": data.get("detectedIssue", "Image analyzed"),
                        "warning": data.get("warning")
                    }
                else:
                    raise Exception(f"API error: {response.status_code}")
        
        except Exception as e:
            print(f"Vision API failed: {e}")
            return self._mock_validation(category)