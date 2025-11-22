import os
import google.generativeai as genai
import re
from django.conf import settings
import base64

class AbuseDetector:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            genai.configure(api_key=self.api_key)
        else:
            print("Warning: GEMINI_API_KEY is not set. AI detection will not work.")  
    
    def analyze_text(self, text):
        if not self.api_key:
            return self._fallback_analysis(text)
        
        try:
            model = genai.GenerativeModel("gemini-2.5-flash")  # Use flash for faster responses
            
            prompt = f"""
            Analyze the following text for digital abuse. Your task is to detect abusive or harmful behavior and provide a clear, structured safety report.

            Evaluate the text across these categories:
            - Cyberbullying / Harassment
            - Sexual Harassment
            - Threats of Violence
            - Hate Speech
            - Coercion / Manipulation
            - Stalking Behavior
            - Sextortion Attempts

            TEXT TO ANALYZE:
            "{text}"

            RESPONSE FORMAT (must follow exactly):
            RISK_LEVEL: [LOW | MEDIUM | HIGH | CRITICAL]
            CATEGORY: [Primary identified category]
            CONFIDENCE: [0-100]
            EXPLANATION: [Short explanation of why the text is abusive or harmful]
            IMMEDIATE_ACTIONS: Action 1, Action 2, Action 3, Action 4

            RULES:
            - Always infer the language of the text and write IMMEDIATE_ACTIONS in that same language.
            - IMMEDIATE_ACTIONS must be short, clear, and actionable (no long paragraphs).
            - Keep the explanation concise and focused on the harmful behavior detected.
            - If multiple categories apply, choose the one with the strongest risk as the primary category.
            
            If no abusive content is detected, set RISK_LEVEL to LOW and explain.

            """      
            
            response = model.generate_content(prompt)
            return self._parse_response(response.text)
            
        except Exception as e:
            print(f"AI analysis error: {e}")
            return self._fallback_analysis(text)
    
    def analyze_image(self, image_file):
        """Analyze image directly using Gemini Vision"""
        if not self.api_key:
            return self._fallback_analysis("")
        
        try:
            # Read image file
            image_bytes = image_file.read()
            
            # Create the vision model
            model = genai.GenerativeModel("gemini-2.5-flash")
            
            prompt = """
            Analyze this image for any digital abuse content. Look for:
            - Threatening messages or text
            - Harassing content
            - Sexual harassment
            - Hate speech
            - Coercive or manipulative content
            - Stalking behavior indicators
            - Sextortion attempts
            
            Provide response in this exact format:
            RISK_LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
            CATEGORY: [Primary category]
            CONFIDENCE: [0-100]
            EXPLANATION: [Brief explanation of what was found in the image]
            IMMEDIATE_ACTIONS: [Action 1], [Action 2], [Action 3], [Action 4]
            
            RULES:
            - Always infer the language of the text and write IMMEDIATE_ACTIONS in that same language.
            - IMMEDIATE_ACTIONS must be short, clear, and actionable (no long paragraphs).
            - Keep the explanation concise and focused on the harmful behavior detected.
            - If multiple categories apply, choose the one with the strongest risk as the primary category.

            If no abusive content is detected, set RISK_LEVEL to LOW and explain.
            
            """
            
            # Prepare image for Gemini
            image_part = {
                "mime_type": image_file.content_type,
                "data": image_bytes
            }
            
            response = model.generate_content([prompt, image_part])
            return self._parse_response(response.text)
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            return self._fallback_analysis("")
    
    def _parse_response(self, response_text):
        try:
            
            
            lines = response_text.split('\n')
            result = {
                "risk_level": "UNKNOWN",
                "category": "Unknown",
                "confidence": 0,
                "explanation": "Analysis unavailable",
                "immediate_actions": [
                    "Document all messages and evidence",
                    "Block the sender immediately", 
                    "Report to platform authorities",
                    "Contact local support services"
                ],
            }        
            
            for line in lines:
                line = line.strip()
                if line.startswith("RISK_LEVEL:"):
                    result['risk_level'] = line.split(":", 1)[1].strip()
                elif line.startswith("CATEGORY:"):
                    result["category"] = line.split(":", 1)[1].strip()
                elif line.startswith("CONFIDENCE:"):
                    try:
                        confidence_str = line.split(":", 1)[1].strip()
                        result['confidence'] = int(confidence_str)
                    except (ValueError, IndexError):
                        result['confidence'] = 50
                elif line.startswith("EXPLANATION:"):
                    result['explanation'] = line.split(':', 1)[1].strip()
                elif line.startswith('IMMEDIATE_ACTIONS:'):
                    actions_text = line.split(':', 1)[1].strip()
                    # Handle different action separators
                    actions = []
                    
                    # Try comma-separated first
                    if ',' in actions_text:
                        actions = [action.strip() for action in actions_text.split(',') if action.strip()]
                    # Try numbered actions (1. Action, 2. Action, etc.)
                    elif any(char.isdigit() for char in actions_text):
                        actions = re.split(r'\d+\.', actions_text)
                        actions = [action.strip() for action in actions if action.strip()]
                    # Fallback: split by any obvious delimiter
                    else:
                        actions = re.split(r'[,•\-]', actions_text)
                        actions = [action.strip() for action in actions if action.strip()]
                    
                    # Filter out empty actions and ensure we have at least 3
                    actions = [action for action in actions if action and action not in ['', '.']]
                    
                    if actions:
                        result['immediate_actions'] = actions[:4]
                    else:
                        result['immediate_actions'] = self._get_fallback_actions(result.get('risk_level', 'UNKNOWN'))
            
            # Validate and ensure we have proper actions
            if not result['immediate_actions'] or all(action == '' for action in result['immediate_actions']):
                result['immediate_actions'] = self._get_fallback_actions(result['risk_level'])
            
            return result
        
        except Exception as e:
            print(f"Response parsing error: {e}")
            return self._fallback_analysis("")
    
    def _get_fallback_actions(self, risk_level):
        """Provide fallback actions based on risk level"""
        base_actions = [
            "Document all messages and take screenshots",
            "Block the sender on all platforms",
            "Report the content to platform moderators"
        ]
        
        if risk_level in ['HIGH', 'CRITICAL']:
            base_actions.extend([
                "Contact local authorities or emergency services",
                "Inform trusted friends or family members",
                "Seek support from local GBV organizations"
            ])
        else:
            base_actions.extend([
                "Consider limiting online interactions",
                "Review and strengthen privacy settings",
                "Save evidence for future reference"
            ])
        
        return base_actions[:4]
        
    def _fallback_analysis(self, text):
        text_lower = text.lower() if text else ""
        
        high_risk_keywords = ["kill you", "hurt you", "rape", "die", "suicide", "murder", "harm you"]
        medium_risk_keywords = ["ugly", "stupid", "fat", "worthless", "nobody likes you", "hate you"]
        sexual_keywords = ["nude", "naked", "sex", "body", "private", "sleep with"]
        
        risk_level = "LOW"
        category = "Unknown"
        confidence = 30
        
        if any(keyword in text_lower for keyword in high_risk_keywords):
            risk_level = "HIGH"
            category = 'Threats of Violence'
            confidence = 85
        elif any(keyword in text_lower for keyword in sexual_keywords):
            risk_level = 'MEDIUM'
            category = 'Sexual Harassment'
            confidence = 70
        elif any(keyword in text_lower for keyword in medium_risk_keywords):
            risk_level = 'MEDIUM'
            category = 'Cyberbullying'
            confidence = 65
            
        return {
            'risk_level': risk_level,
            'category': category,
            'confidence': confidence,
            'explanation': 'Basic pattern detection: This content may contain harmful language.',
            'immediate_actions': self._get_fallback_actions(risk_level)
        }


# import os
# import google.generativeai as genai
# import re
# from django.conf import settings

# class AbuseDetector:
#     def __init__(self):
#         self.api_key = settings.GEMINI_API_KEY
#         if self.api_key:
#             genai.configure(api_key=self.api_key)
#         else:
#             print("Warning: GEMINI_API_KEY is not set. AI detection will not work.")  
    
#     def analyze_text(self, text):
#         if not self.api_key:
#             return self._fallback_analysis(text)
        
#         try:
#             model = genai.GenerativeModel("gemini-2.0-flash")  
            
#             prompt = f"""
#             Analyze the following text for digital abuse. Your task is to detect abusive or harmful behavior and provide a clear, structured safety report.

#             Evaluate the text across these categories:
#             - Cyberbullying / Harassment
#             - Sexual Harassment
#             - Threats of Violence
#             - Hate Speech
#             - Coercion / Manipulation
#             - Stalking Behavior
#             - Sextortion Attempts

#             TEXT TO ANALYZE:
#             "{text}"

#             RESPONSE FORMAT (must follow exactly):
#             RISK_LEVEL: [LOW | MEDIUM | HIGH | CRITICAL]
#             CATEGORY: [Primary identified category]
#             CONFIDENCE: [0-100]
#             EXPLANATION: [Short explanation of why the text is abusive or harmful]
#             IMMEDIATE_ACTIONS: Action 1, Action 2, Action 3, Action 4

#             RULES:
#             - Always infer the language of the text and write IMMEDIATE_ACTIONS in that same language.
#             - IMMEDIATE_ACTIONS must be short, clear, and actionable (no long paragraphs).
#             - Keep the explanation concise and focused on the harmful behavior detected.
#             - If multiple categories apply, choose the one with the strongest risk as the primary category.

#             """        
            
#             response = model.generate_content(prompt)
#             return self._parse_response(response.text)
            
#         except Exception as e:
#             print(f"AI analysis error: {e}")
#             return self._fallback_analysis(text)
    
#     def _parse_response(self, response_text):
#         try:
#             lines = response_text.split('\n')
#             result = {
#                 "risk_level": "UNKNOWN",
#                 "category": "Unknown",
#                 "confidence": 0,
#                 "explanation": "Analysis unavailable",
#                 "immediate_actions": ["Document the content", "Consider blocking the sender", "Reach out to trusted support"],
#             }        
            
#             for line in lines:
#                 if line.startswith("RISK_LEVEL:"):  # Fixed typo: RISKY_LEVEL -> RISK_LEVEL
#                     result['risk_level'] = line.split(":", 1)[1].strip()
#                 elif line.startswith("CATEGORY:"):
#                     result["category"] = line.split(":", 1)[1].strip()
#                 elif line.startswith("CONFIDENCE:"):
#                     try:
#                         result['confidence'] = int(line.split(":", 1)[1].strip())
#                     except:
#                         pass
#                 elif line.startswith("EXPLANATION:"):
#                     result['explanation'] = line.split(':', 1)[1].strip()
#                 elif line.startswith('IMMEDIATE_ACTIONS:'):
#                     actions = line.split(':', 1)[1].strip()
#                     result['immediate_actions'] = [action.strip() for action in actions.split(',')]         
                    
#             return result
        
#         except Exception as e:
#             print(f"Response parsing error: {e}")
#             return self._fallback_analysis("")
        
    
#     def _fallback_analysis(self, text):
#         text_lower = text.lower()
        
#         high_risk_keywords = ["kill you", "hurt you", "rape", "die", "suicide"]
#         medium_risk_keywords = ["ugly", "stupid", "fat", "worthless", "nobody likes you"]
#         sexual_keywords = ["nude", "naked", "sex", "body", "private"]
        
#         risk_level = "LOW"  # Fixed typo: risk_leve -> risk_level
#         category = "Unknown"  # Fixed typo: Unkwown -> Unknown
#         confidence = 30
        
#         if any(keyword in text_lower for keyword in high_risk_keywords):
#             risk_level = "HIGH"  
#             category = 'Threats of Violence'  
#             confidence = 75
#         elif any(keyword in text_lower for keyword in sexual_keywords):
#             risk_level = 'MEDIUM'
#             category = 'Sexual Harassment'
#             confidence = 65
#         elif any(keyword in text_lower for keyword in medium_risk_keywords):
#             risk_level = 'MEDIUM'
#             category = 'Cyberbullying'
#             confidence = 60
            
#         return {
#             'risk_level': risk_level,
#             'category': category,
#             'confidence': confidence,
#             'explanation': 'Basic pattern detection: This content may contain harmful language.',
#             'immediate_actions': [
#                 'Take screenshots for evidence',
#                 'Do not engage with the sender',
#                 'Block the account/person',
#                 'Report to platform authorities'
#             ]
#         }