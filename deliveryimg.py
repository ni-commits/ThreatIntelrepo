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

# Model
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Calculate padding-top for CSS from image aspect ratio
def get_padding_percentage_from_image_url(url):
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        width, height = image.size
        return round((height / width) * 100, 2)
    except Exception as e:
        print(f"⚠️ Error calculating padding-top: {e}")
        return 50.0  # fallback

# 📩 Generate delivery email
def generate_delivery_email(subject, purpose, recipient, email_id, address, department, logo_url=None):
    # Random sender
    sender_name = random.choice(["Aarav Mehta", "Diya Sharma", "Karan Patel", "Sneha Reddy", "Rohit Nair"])
    sender_position = random.choice(["Marketing", "Finance", "Engineering", "Sales", "Support"])

    # ✅ LOGIC: If logo provided, don't use banner images
    if logo_url:
        # Logo exists - generate email WITHOUT banner image
        final_prompt = f"""
You are a top-tier HTML email designer.  
Design a beautiful, production-ready HTML email for a delivery/e-commerce order update with the following goals and restrictions:

---

### Strict Rules

- **NO harmful, alarmist, emergency, or urgent-sounding words.**
  - Do not use "urgent", "immediately", "emergency", "act now", "alert", "warning", or similar language.
- **Tone:** Friendly, calm, professional, and reassuring.
- **Visual:** Attractive layout, clear sectioning, and a welcoming vibe.
- **DO NOT include any banner images, background images, or header graphics**
- Clean white background with professional styling

---

### STRUCTURE

- Outer container: max-width 600px, white background, subtle drop-shadow and rounded corners.
- Greeting: "Dear {recipient},"
- Inside:  
    - 2 informative, personalized paragraphs (avoid any urgency!)
    - <ul> or <ol> with 2-4 recent order highlights or tips (friendly, not alarming!)
    - 1 centered CTA button:
        - Text: "View Your Dashboard"
        - Link: https://teamy-labs.github.io/phishing-awareness-/?id={email_id}
    - Signature:  
        Sincerely, {sender_name}, {sender_position}

---

### CONTENT GUIDELINES

- DO NOT include:
    - Any company logos, banners, background images, or graphics
    - Extra buttons, links, or secondary actions
    - Any language implying emergency, danger, or time pressure
- MAKE IT visually attractive:
    - Use colors, fonts, padding, and spacing elegantly.
    - Responsive layout.
- Use recipient name ({recipient}), City/Region ({address}), and Department ({department}) naturally in the body.

---

### DATA FOR THIS EMAIL

- Subject: {subject}
- Purpose: {purpose}
- Address: {address}
- Department: {department}

---

**Return ONLY a full standalone HTML email (including meta/head/style), no explanations.**
"""
    else:
        # No logo - use default banner images
        subject_lower = subject.lower()
        if "new features" in subject_lower or "new programs" in subject_lower:
            image_url = "https://i.ibb.co/yFL7FBPr/Google-AI-Studio-2025-07-10-T04-43-36-682-Z.png"
        elif "sales" in subject_lower or "promotions" in subject_lower:
            image_url = "https://i.ibb.co/G3r3tgL4/Gemini-Generated-Image-xna5ssxna5ssxna5.png"
        elif "discounts" in subject_lower:
            image_url = "https://i.ibb.co/VYhY2NzR/Gemini-Generated-Image-xpo7m0xpo7m0xpo7.png"
        else:
            image_url = "https://i.ibb.co/HLWzkWJ/fallback.png"

        try:
            padding_top = get_padding_percentage_from_image_url(image_url)
        except:
            padding_top = 56.25

        final_prompt = f"""
You are a top-tier HTML email designer.  
Design a beautiful, production-ready HTML email for an e-commerce order update with the following goals and restrictions:

---

### Strict Rules

- **NO harmful, alarmist, emergency, or urgent-sounding words.**
  - Do not use "urgent", "immediately", "emergency", "act now", "alert", "warning", or similar language.
- **Tone:** Friendly, calm, professional, and reassuring.
- **Visual:** Attractive layout, clear sectioning, and a welcoming vibe.

---

### IMAGE BANNER (CSS-Only):

- Use this for the main hero/banner:
    - background-image: url('{image_url}')
    - padding-top: {padding_top}%
    - No <img> or <svg>; CSS only.

---

### STRUCTURE

- Outer container: max-width 600px, white background, subtle drop-shadow and rounded corners.
- Top: Banner as above.
- Greeting: "Dear {recipient},"
- Inside:  
    - 2 informative, personalized paragraphs (avoid any urgency!)
    - <ul> or <ol> with 2-4 recent order highlights or tips (friendly, not alarming!)
    - 1 centered CTA button:
        - Text: "View Your Dashboard"
        - Link: https://teamy-labs.github.io/phishing-awareness-/?id={email_id}
    - Signature:  
        Sincerely, {sender_name}, {sender_position}

---

### CONTENT GUIDELINES

- DO NOT include:
    - Extra company logos, actual branding, or additional images (CSS banner only)
    - Extra buttons, links, or secondary actions
    - Any language implying emergency, danger, or time pressure
- MAKE IT visually attractive:
    - Use colors, fonts, padding, and spacing elegantly.
    - Responsive layout.
- Use recipient name ({recipient}), City/Region ({address}), and Department ({department}) naturally in the body.

---

### DATA FOR THIS EMAIL

- Subject: {subject}
- Purpose: {purpose}
- Address: {address}
- Department: {department}

---

**Return ONLY a full standalone HTML email (including meta/head/style), no explanations.**
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