import google.generativeai as genai
import os
import random
import datetime
import requests
from PIL import Image
from io import BytesIO
import re
import os
from dotenv import load_dotenv


API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=API_KEY)

# Model
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Get padding-top CSS value from image
def get_padding_percentage_from_image_url(url):
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        width, height = image.size
        return round((height / width) * 100, 2)
    except Exception as e:
        print(f"Error calculating padding-top: {e}")
        return 50.0

def generate_email_ecommerce(subject, purpose, recipient, email_id, address, department, logo_url=None):
    # Random sender for realism
    sender_names = ["Aarav Mehta", "Diya Sharma", "Karan Patel", "Sneha Reddy", "Rohit Nair"]
    sender_positions = ["Human Resources", "Finance", "Engineering", "Marketing", "Operations"]
    sender_name = random.choice(sender_names)
    sender_position = random.choice(sender_positions)

    # ✅ LOGIC: If logo provided, don't use banner images
    if logo_url:
        # Logo exists - generate email WITHOUT banner image
        final_prompt = f"""
You are a professional HTML email designer.

Your task is to generate a clean, professional HTML email template for an e-commerce communication. Strictly follow the structure below.

---

📌 TEMPLATE STRUCTURE & RULES

- Start the body content with this exact line: `Dear {recipient},`
- Use a full HTML document structure with a `max-width: 600px` container
- **DO NOT include any banner images, background images, or header graphics**
- Clean white background with professional styling
- Follow with:
  ✅ Two informative `<p>` paragraphs about the e-commerce update
  ✅ Key highlights or benefits in a list
  ✅ A CTA button linking to: https://teamy-labs.github.io/phishing-awareness-/?id={email_id}  
  ✅ Signature block: `Sincerely, {sender_name}, {sender_position}`
- Generate email based on {subject}, {purpose}
- Do not use ANY `<img>`, `<svg>`, background images, or branding

🎯 Output one production-ready HTML email with clean, text-focused design. Do not include anything outside the HTML.
"""
    else:
        # No logo - use default banner images
        if "new features" in subject.lower() or "new programs" in subject.lower():
            image_url = "https://i.ibb.co/yFL7FBPr/Google-AI-Studio-2025-07-10-T04-43-36-682-Z.png"
        elif "sales" in subject.lower() or "promotions" in subject.lower():
            image_url = "https://i.ibb.co/G3r3tgL4/Gemini-Generated-Image-xna5ssxna5ssxna5.png"
        elif "discounts" in subject.lower():
            image_url = "https://i.ibb.co/VYhY2NzR/Gemini-Generated-Image-xpo7m0xpo7m0xpo7.png"
        else:
            image_url = "https://i.ibb.co/JWCX1vn8/Google-AI-Studio-2025-07-14-T04-16-57-170-Z.png"

        try:
            padding_top = get_padding_percentage_from_image_url(image_url)
        except:
            padding_top = 56.25

        final_prompt = f"""
You are a professional HTML email designer.

Your task is to generate a visually realistic, standalone HTML email template that adapts dynamically to the provided **subject** and **purpose**. The visual layout must include a simulated background image (using CSS only) and maintain a professional ecommerce tone. Strictly follow the logic and constraints below.

---

📌 IMAGE SELECTION LOGIC (CSS-Only, No <img> Tags)

- Selected image URL: {image_url}
- Use this CSS for the banner:
  - `background-image: url('{image_url}')`  
  - `padding-top: {padding_top}%` based on aspect ratio

---

📌 TEMPLATE STRUCTURE

- Start content: Dear {recipient},
- Use a full HTML document structure with a `max-width: 600px` container
- Top section uses the selected background image with the padding-top value above (do not use height)
- Follow with:
  ✅ Two informative `<p>` paragraphs  
  ✅ Key highlights or benefits
  ✅ A CTA button linking to: https://teamy-labs.github.io/phishing-awareness-/?id={email_id}  
  ✅ Signature block: `Sincerely, {sender_name}, {sender_position}`
- Generate email based on {subject}, {purpose}
- Do not use `<img>`, `<svg>`, or any branding in the main content.

🎯 SUBJECT: {subject}
🎯 PURPOSE: {purpose}
📍 Department: {department}, Address: {address}

⚠️ Do NOT use additional <img> or <svg> tags. No brand names.

Generate ONLY the HTML code. Nothing else.
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
        return f"❌ Error generating email: {e}"