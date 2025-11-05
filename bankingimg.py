import google.generativeai as genai
import os
import random
import datetime
import requests
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

# API Key
API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Initialize model
model = genai.GenerativeModel("gemini-2.0-flash-exp")

def get_padding_percentage_from_image_url(url):
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        width, height = image.size
        return round((height / width) * 100, 2)
    except Exception:
        return 50.0

def generate_email(subject, purpose, recipient, email_id, address, department, logo_url=None):
    import random
    import re
    
    names = ["Aarav Mehta", "Diya Sharma", "Karan Patel", "Sneha Reddy", "Rohit Nair"]
    emails = ["aarav@company.com", "diya@company.com", "karan@company.com", "sneha@company.com", "rohit@company.com"]
    departments = ["Human Resources", "Finance", "Engineering", "Marketing", "Operations"]

    sender_name = random.choice(names)
    sender_position = random.choice(departments)

    subject = "Enhance Your Banking Experience: New Feature"
    purpose = "To introduce a new online banking feature designed to enhance user experience."

    # ✅ include address and department in the context
    recipient_context = f"""
The recipient’s full details are:
- Name: {recipient}
- Department: {department}
- Address: {address}
"""

    # ✅ LOGIC: If logo provided, don't use banner images
    if logo_url:
        # Logo exists - generate email WITHOUT banner image
        final_prompt = f"""
You are a professional HTML email designer.

Your task is to generate a clean, professional HTML email template for a banking communication. Strictly follow the structure below.

---

{recipient_context}

📌 TEMPLATE STRUCTURE & RULES

- Start the body content with this exact line: `Dear {recipient},`
- Use a full HTML document structure with a `max-width: 600px` container
- Include at least one line referencing the department (“{department}”) and address (“{address}”) naturally in the message body.
- **DO NOT include any banner images, background images, or header graphics**
- Clean white background with professional styling
- Follow with:
  ✅ Two informative `<p>` paragraphs about the banking feature
  ✅ `<ul>` for account highlights  
  ✅ A CTA button linking to: https://teamy-labs.github.io/phishing-awareness-/?id={email_id}  
  ✅ Signature block: `Sincerely, {sender_name}, {sender_position}`
- Generate email based on {subject}, {purpose}
- Do not use ANY `<img>`, `<svg>`, background images, or branding

🎯 Output one production-ready HTML email with clean, text-focused design. Do not include anything outside the HTML.
"""
    else:
        # No logo - use default banner images
        if "new feature" in subject.lower() or "new updates" in subject.lower():
            image_url = "https://i.ibb.co/B5q7cTjJ/Gemini-Generated-Image-6adbns6adbns6adb.png"
        elif "annual account summary" in subject.lower() or "overview of account transactions" in subject.lower() or "monthly statement" in subject.lower():
            image_url = "https://i.ibb.co/b58xvP4S/Gemini-Generated-Image-ktzxu5ktzxu5ktzx.png"
        elif "security" in subject.lower() or "fraud alerts" in subject.lower():
            image_url = "https://i.ibb.co/wr7Y2Crc/Google-AI-Studio-2025-07-17-T05-02-57-319-Z.png"
        else:
            image_url = "https://i.ibb.co/C57qGPKT/Google-AI-Studio-2025-07-17-T05-19-41-431-Z.png"

        try:
            padding_top = get_padding_percentage_from_image_url(image_url)
        except:
            padding_top = 56.25

        final_prompt = f"""
You are a professional HTML email designer.

Your task is to generate a visually realistic, standalone HTML email template that adapts dynamically to the provided **subject** and **purpose**. The visual layout must include a simulated background image (using CSS only) and maintain a professional banking tone. Strictly follow the logic and constraints below.

---

📌 IMAGE SELECTION LOGIC (CSS-Only, No <img> Tags)

- Selected image URL: {image_url}
- Use this CSS for the banner:
  - `background-image: url('{image_url}')`  
  - `padding-top: {padding_top}%` based on aspect ratio

---

{recipient_context}

📌 TEMPLATE STRUCTURE & RULES

- Start the body with this exact line: `Dear {recipient},`
- Use a full HTML document structure with a `max-width: 600px` container
- Include at least one line referencing the department (“{department}”) or address (“{address}”) naturally in the message body.
- Top section uses the selected background image with the padding-top value above (do not use height)
- Follow with:
  ✅ Two informative `<p>` paragraphs  
  ✅ `<ul>` for account highlights  
  ✅ A CTA button linking to: https://teamy-labs.github.io/phishing-awareness-/?id={email_id}  
  ✅ Signature block: `Sincerely, {sender_name}, {sender_position}`
- Generate email based on {subject},{purpose}
- Do not use `<img>`, `<svg>`, or any branding in the main content.

🎯 Output one production-ready HTML email using these rules. Do not include anything outside the HTML.
"""

    try:
        response = model.generate_content(final_prompt)
        html_content = response.text
        
        # ✅ If logo provided, inject it at the top
        if logo_url:
            logo_html = f'''<div style="text-align: center; margin: 0 0 30px 0; padding: 20px 0; background-color: #ffffff;">
    <img src="{logo_url}" alt="Company Logo" style="max-width: 250px; height: auto; display: block; margin: 0 auto;">
</div>
'''
            
            # Strategy 1: Look for "Dear {recipient}" and insert logo before it
            dear_pattern = rf'(Dear\s+{re.escape(recipient)})'
            if re.search(dear_pattern, html_content, re.IGNORECASE):
                html_content = re.sub(dear_pattern, logo_html + r'\1', html_content, count=1, flags=re.IGNORECASE)
            else:
                # Fallback: insert after body tag
                body_pattern = r'(<body[^>]*>)'
                match = re.search(body_pattern, html_content, re.IGNORECASE)
                if match:
                    insert_position = match.end()
                    html_content = (
                        html_content[:insert_position] + 
                        '\n' + logo_html + '\n' + 
                        html_content[insert_position:]
                    )
        
        return html_content
        
    except Exception as e:
        return f"❌ Error during generation: {e}"