import random
import datetime
import json
import google.generativeai as genai
import os
import re
import os
from dotenv import load_dotenv

# Configure Gemini API Key
load_dotenv() # Make sure to load the .env file
API_KEY = os.getenv("GEMINI_API_KEY") 
if not API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")
genai.configure(api_key=API_KEY)

# Use a standard model name like "gemini-1.5-flash"
model = genai.GenerativeModel("gemini-1.5-flash")

HR_MANAGER_NAMES = [
    "Ananya Sharma", "Rahul Kapoor", "Priya Singh", "Vikram Rathore",
    "Deepa Menon", "Sanjay Gupta", "Monica Verma", "Alok Kumar"
]

pseudo_data = {
    "name": ["Diya Sharma", "Karan Patel", "Sneha Reddy", "Rohit Nair"],
    "email": ["diya@company.com", "karan@company.com", "sneha@company.com", "rohit@company.com"],
    "department": ["Finance", "Engineering", "Operations", "Marketing"],
    "company": ["CyberGuard360", "Ngit Tech Pvt Ltd", "Kmit Corp Ltd"],
    "email_type": ["Performance Review Notification", "Compliance Survey Reminder", "Policy Update Notification"],
    "ref_no": ["HR-2025-09-08-001", "HR-2025-09-08-045", "HR-2025-09-08-078"],
    "issue_date": datetime.date.today().strftime("%B %d, %Y"),
}


# ✅ UPDATED: Changed signature to accept logo_url
def generate_customized_hr_email(subject, purpose, recipient, email_id, address, department, logo_url=None):
    """
    Generate customized HR email with optional logo support
    """
    # Use provided data or fall back to pseudo data
    name = recipient if recipient else random.choice(pseudo_data['name'])
    email = f"{email_id}@company.com" if email_id else random.choice(pseudo_data['email'])
    dept = department if department else random.choice(pseudo_data['department'])
    company = random.choice(pseudo_data['company'])
    email_type = subject if subject else random.choice(pseudo_data['email_type'])
    ref_no = random.choice(pseudo_data['ref_no'])
    issue_date = pseudo_data['issue_date']

    hr_manager_name = random.choice(HR_MANAGER_NAMES)

    redirection_link = f"https://teamy-labs.github.io/phishing-awareness-/?id={email_id}"
    deadline_date = (datetime.date.today() + datetime.timedelta(days=3)).strftime("%B %d, %Y")

    subject_purpose_prompt = f"""
You are an expert in corporate Human Resources communication.
Generate a precise email subject and its corresponding one-sentence purpose for an HR email related to '{email_type}'.
Output the result as a JSON object with the keys: 'subject' and 'purpose'.
    """

    generation_config = {
        "response_mime_type": "application/json",
        "response_schema": {
            "type": "OBJECT",
            "properties": {
                "subject": {"type": "STRING"},
                "purpose": {"type": "STRING"}
            },
            "required": ["subject", "purpose"]
        }
    }
    
    # --- THIS IS THE FIX for the TypeError ---
    # 1. Convert the dictionary to the required object
    config_object = genai.GenerationConfig(**generation_config)

    # 2. Pass the new config_object to the function
    response = model.generate_content(subject_purpose_prompt, generation_config=config_object)
    
    generated = json.loads(response.text)
    final_subject = generated['subject']
    final_purpose = generated['purpose']

    # ✅ Adjust prompt based on logo presence
    header_instruction = ""
    if logo_url:
        header_instruction = "- DO NOT include any company logos, banners, or header graphics."
    else:
        header_instruction = "- No header block with the company name. The email should begin directly with the greeting."

    # --- THIS IS THE IMPROVED LOGIC ---
    # The prompt now uses 'final_purpose' to generate a matching body
    html_prompt = f"""
You are a world-class professional HTML email template designer specializing in corporate HR communications.
Your task is to generate a highly polished, clean, and fully production-ready HTML email template.

**Email Context:**
- Recipient Name: {name}
- Company: {company}
- Department: {dept}
- Subject: {final_subject}
- **Purpose of Email:** {final_purpose}
- Action Deadline: {deadline_date}
- Reference: {ref_no}
- Issue Date: {issue_date}

**Instructions:**
1️⃣ HEADER:
{header_instruction}

2️⃣ GREETING:
- Formal salutation: "Dear {name},"

3️⃣ BODY CONTENT:
- **First paragraph:** Start with a professional opening. Then, clearly elaborate on the email's purpose: **"{final_purpose}"**. Explain *why* this is important for the employee or the company.
- **Second paragraph:** Clearly state the required action the employee needs to take. Emphasize the mandatory deadline of <span style='font-weight: bold;'>{deadline_date}</span>.

- **Instructional line:** "To proceed, please click the button below:"

4️⃣ CTA BUTTON:
- **Text:** Based on the purpose, create a clear call-to-action text (e.g., "Complete Survey", "Review Policy", "Begin Evaluation").
- **Style:** Dark blue background (#0056b3), white text, square corners (border-radius: 0px), bold, visible padding.
- **Link:** "{redirection_link}"

5️⃣ KEY INFORMATION / BULLETED LIST:
- Section Title: "Key Information:"
- Bulleted list items:
    - **Item 1:** Reiterate the core message or requirement (e.g., "This {email_type} is mandatory for all {dept} employees.")
    - **Item 2:** Re-state the deadline: "Completion is required by {deadline_date}."
    - **Item 3:** Provide a backup link: "Access the platform here: <a href='{redirection_link}' style='color:#0056b3; text-decoration: none;'>Internal Platform Link</a>"

6️⃣ CONTACT INFO:
- "For any questions, please contact HR Support at <a href='mailto:hr-support@{company.lower().replace(' ', '')}.com' style='color:#0056b3; text-decoration: none;'>hr-support@{company.lower().replace(' ', '')}.com</a>."

7️⃣ CLOSING:
- "Sincerely,<br>{hr_manager_name}<br>HR Manager<br>{company}"

8️⃣ FOOTER:
- Ref No: {ref_no}
- Issue Date: {issue_date}
- Confidentiality Notice in smaller text.

🌟 Style Requirements:
- Internal CSS only.
- Light gray background (#f2f2f2).
- White content block (.container) with subtle box-shadow.
- Font: Arial, Segoe UI.
- Line height: 1.6.
- Mobile-friendly.

🚫 Restrictions:
- No logos (unless {logo_url} is used), no banners, no placeholder text.
- Generate only full, production-ready HTML code.
"""

    html_response = model.generate_content(html_prompt)
    html_content = html_response.text.strip()
    
    # Clean markdown if present
    if html_content.startswith("```html"):
        html_content = html_content[7:]
    if html_content.endswith("```"):
        html_content = html_content[:-3]
    html_content = html_content.strip()

    # ✅ Inject logo if provided
    if logo_url:
        logo_html = f'''<div style="text-align: center; margin: 0 0 30px 0; padding: 20px 0; background-color: #ffffff;">
<img src="{logo_url}" alt="Company Logo" style="max-width: 250px; height: auto; display: block; margin: 0 auto;">
</div>
'''
        # Insert logo right after the opening <body> tag (or after any <style> block in the body)
        body_pattern = r'(<body[^>]*>)'
        match = re.search(body_pattern, html_content, re.IGNORECASE)
        if match:
            insert_position = match.end()
            # Check for a style tag immediately after body, if so, insert after it
            style_match = re.search(r'(<style>.*?</style>)', html_content[insert_position:], re.IGNORECASE | re.DOTALL)
            if style_match:
                insert_position += style_match.end()
            
            html_content = html_content[:insert_position] + '\n' + logo_html + '\n' + html_content[insert_position:]
        else:
            # Fallback if <body> tag is missing (unlikely)
            html_content = logo_html + html_content

    return final_subject, final_purpose, html_content