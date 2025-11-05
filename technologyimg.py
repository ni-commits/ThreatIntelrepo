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
model = genai.GenerativeModel("gemini-2.0-flash-exp")

# Get image padding-top percentage
def get_padding_percentage_from_image_url(url):
    try:
        response = requests.get(url)
        image = Image.open(BytesIO(response.content))
        width, height = image.size
        return round((height / width) * 100, 2)
    except Exception as e:
        print(f"⚠️ Error calculating padding-top: {e}")
        return 50.0

def generate_technology_email(subject, purpose, recipient, email_id, address, department, logo_url=None):
    # Random sender details
    sender_name = random.choice(["Aarav Mehta", "Diya Sharma", "Karan Patel", "Sneha Reddy", "Rohit Nair"])
    sender_position = random.choice(["Tech Lead", "Engineer", "Product Manager", "Support Specialist", "Data Analyst"])

    # Redirection link
    redirect_link = f"https://teamy-labs.github.io/phishing-awareness-/?id={email_id}"

    # ✅ LOGIC: If logo provided, don't use banner images
    if logo_url:
        # Logo exists - generate email WITHOUT banner image
        final_prompt = f"""
You are a professional HTML email designer.

Generate a complete standalone HTML email with:
- Subject: {subject}
- Purpose: {purpose}
- Recipient: {recipient}
- Department: {department}
- Location: {address}
- Email ID: {email_id}
- CTA Link: {redirect_link}
- Sender: {sender_name}, {sender_position}

The email must follow these rules:

---

📌 STRUCTURE:
- Use full HTML with <html>, <head>, and <style>
- Container with max-width: 600px
- **DO NOT include any banner images, background images, or header graphics**
- Clean white background with professional styling
- Body starts with: Dear {recipient},
- Two <p> paragraphs based on subject and purpose
- <ul> block with 3 tech-relevant highlights
- CTA button to: {redirect_link}
- Closing: Sincerely, {sender_name}, {sender_position}

---

📌 CONSTRAINTS:
- ❌ No <img>, <svg>, logos, banners, or branding images
- ✅ Responsive layout
- ✅ Neutral and professional tone
- ✅ Output ONLY valid HTML (no comments outside <html>)

Now generate the full email.
"""
    else:
        # No logo - use default banner images
        subject_lower = subject.lower()
        if "new software update" in subject_lower or "new features" in subject_lower:
            image_url = "https://i.ibb.co/yFL7FBPr/Google-AI-Studio-2025-07-10-T04-43-36-682-Z.png"
        elif "webinar" in subject_lower or "online events" in subject_lower:
            image_url = "https://i.ibb.co/CKkwc9Q6/Gemini-Generated-Image-8w0k1u8w0k1u8w0k.png"
        elif "advancements" in subject_lower:
            image_url = "https://i.ibb.co/bM0PsYhq/Gemini-Generated-Image-mu585vmu585vmu58.png"
        elif "sales" in subject_lower or "promotions" in subject_lower:
            image_url = "https://i.ibb.co/yFL7FBPr/Google-AI-Studio-2025-07-10-T04-43-36-682-Z.png"
        else:
            image_url = "https://i.ibb.co/nsQwyFmG/Gemini-Generated-Image-qnpcbiqnpcbiqnpc.png"

        try:
            padding_top = get_padding_percentage_from_image_url(image_url)
        except:
            padding_top = 56.25  # Default 16:9 aspect ratio fallback

        final_prompt = f"""
You are a professional HTML email designer.

Generate a complete standalone HTML email with:
- Subject: {subject}
- Purpose: {purpose}
- Recipient: {recipient}
- Department: {department}
- Location: {address}
- Email ID: {email_id}
- CTA Link: {redirect_link}
- Sender: {sender_name}, {sender_position}

The email must follow these rules:

---

📌 IMAGE LOGIC (CSS Background):
- Image URL: {image_url}
- Padding-top: {padding_top}%

---

📌 STRUCTURE:
- Use full HTML with <html>, <head>, and <style>
- Container with max-width: 600px
- First section: CSS background-image div using {image_url} with padding-top: {padding_top}%
- Body starts with: Dear {recipient},
- Two <p> paragraphs based on subject and purpose
- <ul> block with 3 tech-relevant highlights
- CTA button to: {redirect_link}
- Closing: Sincerely, {sender_name}, {sender_position}

---

📌 CONSTRAINTS:
- ❌ No additional <img>, <svg>, logos, or branding (CSS banner only)
- ✅ Responsive layout using only padding-top
- ✅ Neutral and professional tone
- ✅ Output ONLY valid HTML (no comments outside <html>)

Now generate the full email.
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