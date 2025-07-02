import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
import json
import logging

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def interpret_goal(goal, company_info, emails):
    """
    Uses Gemini to interpret the user's goal and generate optimized search strategies
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        prompt = f"""
You are an expert B2B lead generation strategist. Analyze the following goal and generate optimized search strategies.

COMPANY: {company_info}
GOAL: {goal}
INPUT EMAILS: {', '.join(emails)}

Generate search queries for each platform that will find the most relevant prospects. Consider:
- Keywords that match the goal
- Industry terms and job titles
- Geographic locations if mentioned
- Company types and sizes

Return a JSON object with these exact keys:
- "linkedin_queries": [list of 2-3 LinkedIn search queries]
- "x_queries": [list of 2-3 Twitter/X search queries] 
- "internet_queries": [list of 2-3 general web search queries]

Focus on finding decision-makers and relevant professionals. Make queries specific but not too narrow.

Example format:
{{
  "linkedin_queries": ["AI startup founders Bay Area", "voice technology CEOs"],
  "x_queries": ["#AIstartup founders", "voice AI entrepreneurs"],
  "internet_queries": ["AI voice technology startups Bay Area", "conversational AI companies"]
}}
"""

        response = model.generate_content(prompt)
        
        # Try to parse JSON from response
        try:
            # Clean the response text and extract JSON
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            search_plan = json.loads(response_text.strip())
            
            # Validate the structure
            required_keys = ['linkedin_queries', 'x_queries', 'internet_queries']
            for key in required_keys:
                if key not in search_plan:
                    search_plan[key] = []
                elif not isinstance(search_plan[key], list):
                    search_plan[key] = [str(search_plan[key])]
            
            return search_plan
            
        except json.JSONDecodeError as e:
            logging.warning(f"Failed to parse Gemini JSON response: {e}")
            # Fallback to simple search plan
            return generate_fallback_plan(goal, company_info)
            
    except Exception as e:
        logging.error(f"Error calling Gemini API: {e}")
        # Fallback to simple search plan
        return generate_fallback_plan(goal, company_info)

def generate_fallback_plan(goal, company_info):
    """
    Generate a simple fallback search plan if Gemini fails
    """
    base_query = f"{goal} {company_info}".strip()
    
    return {
        "linkedin_queries": [
            f"{goal} CEO founder",
            f"{base_query} decision maker",
            goal
        ],
        "x_queries": [
            f"#{goal.replace(' ', '')} founder",
            f"{base_query} startup",
            goal
        ],
        "internet_queries": [
            f"{base_query} company",
            f"{goal} startup",
            f"{company_info} {goal}"
        ]
    } 