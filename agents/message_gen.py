import google.generativeai as genai
from config import GEMINI_API_KEY, GEMINI_MODEL
import logging

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def generate_message(profile, goal, company_info):
    """
    Uses Gemini to generate a personalized outreach message
    """
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)
        
        # Build profile context
        profile_context = f"Name: {profile.get('name', 'Unknown')}"
        if profile.get('title'):
            profile_context += f", Title: {profile['title']}"
        if profile.get('company'):
            profile_context += f", Company: {profile['company']}"
        
        prompt = f"""
Write a brief, professional, and personalized outreach message for B2B networking/sales.

MY COMPANY: {company_info}
MY GOAL: {goal}
TARGET PERSON: {profile_context}

Requirements:
- Keep it under 50 words
- Be genuine and specific
- Mention why you're reaching out
- Include a clear but soft call-to-action
- Don't be pushy or salesy
- Make it feel personal, not templated

Write just the message text, no subject line or extra formatting.
"""

        response = model.generate_content(prompt)
        message = response.text.strip()
        
        # Clean up any unwanted formatting
        message = message.replace('"', '').replace("'", "'")
        
        # Fallback if message is too long or seems off
        if len(message) > 300 or len(message) < 10:
            return generate_fallback_message(profile, goal, company_info)
        
        return message
        
    except Exception as e:
        logging.error(f"Error generating message with Gemini: {e}")
        return generate_fallback_message(profile, goal, company_info)

def generate_fallback_message(profile, goal, company_info):
    """
    Generate a simple fallback message if Gemini fails
    """
    name = profile.get('name', 'there')
    company = profile.get('company', '')
    
    if company:
        return f"Hi {name}, I noticed you're at {company}. We're working on {goal} at {company_info}. Would love to connect and share ideas!"
    else:
        return f"Hi {name}, I came across your profile and thought you might be interested in {goal}. We're at {company_info} - would love to connect!" 