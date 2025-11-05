


import google.generativeai as genai
import json

import os
from dotenv import load_dotenv


API_KEY = os.getenv("GEMINI_API_KEY")

def generate_subjects_and_purposes(category: str) -> dict:
    """
    Generate a single email subject and purpose for the given category.
    
    Args:
        category (str): The selected category (e.g., 'Banking', 'Technology')
    
    Returns:
        dict: { 'subject': ..., 'purpose': ... }
    """

    # Fallback values for each category
    fallbacks = {
        "banking": {
            "subject": "Important Account Security Update Required",
            "purpose": "To inform you about important security measures for your banking account."
        },
        "ecommerce": {
            "subject": "Order Status Update - Action Required", 
            "purpose": "To provide you with updates regarding your recent purchase and next steps."
        },
        "delivery": {
            "subject": "Package Delivery Notification",
            "purpose": "To notify you about the status of your package delivery."
        },
        "technology": {
            "subject": "System Update Notification",
            "purpose": "To inform you about important system updates and security patches."
        },
        "hr template": {
            "subject": "HR Communication - Action Required",
            "purpose": "To provide you with important HR-related information requiring your attention."
        },
        "customized template": {
            "subject": "Company Communication Update",
            "purpose": "To share important company information with you."
        }
    }

    model = genai.GenerativeModel("gemini-2.0-flash-exp")

    prompt = f"""
    You are an expert in content creation and email marketing.
    Generate ONE professional email subject and ONE clear purpose for a campaign 
    related to the category: '{category}'.

    The tone should be neutral, professional, and informative.
    Return only this format:

    SUBJECT: <subject>
    PURPOSE: <purpose>
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        print(f"[DEBUG] Raw Gemini response for {category}:\n{response_text}\n")

        subject, purpose = None, None
        for line in response_text.splitlines():
            line_upper = line.upper().strip()
            if "SUBJECT:" in line_upper:
                subject = line.split(":", 1)[1].strip()
            elif "PURPOSE:" in line_upper:
                purpose = line.split(":", 1)[1].strip()

        if subject and purpose:
            return {"subject": subject, "purpose": purpose}
        else:
            raise ValueError("Could not parse Gemini response")

    except Exception as e:
        print(f"[ERROR] Failed to generate for {category}: {e}")
        category_lower = category.lower().strip()
        fallback = fallbacks.get(category_lower, fallbacks["customized template"])
        return {"subject": fallback["subject"], "purpose": fallback["purpose"]}


# Test function
if __name__ == "__main__":
    categories = ["Banking", "Ecommerce", "Delivery", "Technology", "HR Template"]
    for category in categories:
        print(f"\n=== Testing {category} ===")
        result = generate_subjects_and_purposes(category)
        print(f"Subject: {result['subject']}")
        print(f"Purpose: {result['purpose']}")
