import google.generativeai as genai
import os
import random
import datetime
import json
import re
import os
from dotenv import load_dotenv


API_KEY = os.getenv("GEMINI_API_KEY")

genai.configure(api_key=API_KEY)

# Use a standard, reliable model
model = genai.GenerativeModel("gemini-2.0-flash-exp")
subject_purpose_model = genai.GenerativeModel("gemini-2.0-flash-exp")


# This list is for the randomly chosen HR manager in the signature
HR_MANAGER_NAMES = [
    "Ananya Sharma", "Rahul Kapoor", "Priya Singh", "Vikram Rathore",
    "Deepa Menon", "Sanjay Gupta", "Monica Verma", "Alok Kumar"
]


# --- HELPER FUNCTION ---
def generate_hr_subject_and_purpose(hr_email_type: str):
    prompt = f"Generate a professional email subject for an HR email about '{hr_email_type}'. Format your response as: SUBJECT: [subject line]"
    try:
        response = subject_purpose_model.generate_content(prompt)
        for line in response.text.strip().split('\n'):
            if line.startswith('SUBJECT:'):
                return line.replace('SUBJECT:', '').strip()
        return None
    except Exception as e:
        print(f"Error generating HR subject for '{hr_email_type}': {e}")
        return None


# --- MAIN FUNCTION ---
# ✅ UPDATED: Added logo_url parameter
def generate_hr_template(email_detail):
    """
    Generates an HR template using only the exact details provided.
    """
    # Extract details
    name = email_detail["name"]
    email = email_detail["email"]
    department = email_detail["department"]
    company = email_detail["company"]
    email_type = email_detail["email_type"]
    ref_no = email_detail["ref_no"]
    issue_date = email_detail["issue_date"]
    logo_url = email_detail.get("logo_url", None)  # ✅ Get logo URL
    
    # Generate other dynamic variables
    email_id = email.split("@")[0]
    redirection_link = f"https://teamy-labs.github.io/phishing-awareness-/?id={email_id}"
    hr_manager_name = random.choice(HR_MANAGER_NAMES) # Signature is still random
    deadline_date = (datetime.date.today() + datetime.timedelta(days=3)).strftime("%B %d, %Y")

    # Safely generate the subject
    subject = f"{email_type} - Action Required" # Default subject
    try:
        generated_subject = generate_hr_subject_and_purpose(email_type)
        if generated_subject:
            subject = generated_subject
    except Exception as e:
        print(f"Using default subject. Error: {e}")

    # ✅ MODIFIED: Adjust prompt based on logo presence
    header_instruction = ""
    if logo_url:
        header_instruction = """
1️⃣ HEADER:
- DO NOT include any company logo, banner images, or header graphics in the email.
- The email should begin directly with the greeting."""
    else:
        header_instruction = """
1️⃣ HEADER:
- No header block with the company name. The email should begin directly with the greeting."""

    final_prompt = f"""
You are an expert front-end developer specializing in creating beautiful, responsive, and robust HTML emails for corporate communications. Your task is to create a complete, single-file HTML email template using the context and requirements below.

## Context for this Email
- **Recipient Name:** {name}
- **Company:** {company}
- **Recipient Department:** {department}
- **Email's Purpose/Type:** {email_type}
- **Action Deadline:** {deadline_date}
- **Reference Number:** {ref_no}
- **Date of Issue:** {issue_date}
- **Call to Action Link (CTA):** {redirection_link}
- **HR Manager Signing Off:** {hr_manager_name}

## Structure & Content Requirements
The email must follow this structure precisely:
{header_instruction}
2.  **Greeting:** A polite and professional greeting addressing the employee by their name.
3.  **Opening Paragraph:** A paragraph that clearly states the purpose of the email, based on the '{email_type}'.
4.  **Action Paragraph:** A paragraph that clearly outlines the required action and mentions the firm deadline of **{deadline_date}**.
5.  **Call to Action Button:** A prominent HTML button with the text "Complete Action" that links to the CTA URL.
6.  **Key Information Section:** A section with the title "Important Details" containing a bulleted list reinforcing the mandatory nature of the action and the deadline.
7.  **Support Information:** A line explaining who to contact for questions, including a mailto link for HR.
8.  **Closing:** A professional closing ("Sincerely,") followed by the HR manager's name, title ("HR Manager"), and the company name.
9.  **Footer:** A simple footer containing the reference number, issue date, and a standard confidentiality notice.

## Style Requirements
-   The final output must be a single, complete HTML file, including `<!DOCTYPE html>`, `<html>`, `<head>`, and `<body>`.
-   All CSS must be contained within a single `<style>` block in the `<head>`.
-   Use a professional, clean design with a light gray page background (`#f2f2f2`) and a white content area with a subtle shadow.
-   The font should be a common sans-serif choice like Arial, Helvetica, or Segoe UI.
-   Ensure the layout is responsive and mobile-friendly.
-   The CTA button must be a dark blue (`#0056b3`) with white text and have sharp, square corners (no border-radius).
-   DO NOT include any logos, images, or graphics in the email body.

Now, using all the context and requirements above, generate the complete HTML email file.
"""

    try:
        response = model.generate_content(final_prompt)
        html = response.text.strip()
        # Clean up markdown formatting from the response, if present
        if html.startswith("```html"):
            html = html[7:]
        if html.endswith("```"):
            html = html[:-3]
        html = html.strip()
        
        # ✅ Inject logo if provided
        if logo_url:
            logo_html = f'''<div style="text-align: center; margin: 0 0 30px 0; padding: 20px 0; background-color: #ffffff;">
    <img src="{logo_url}" alt="Company Logo" style="max-width: 250px; height: auto; display: block; margin: 0 auto;">
</div>
'''
            # Insert logo before "Dear {name}"
            dear_pattern = rf'(Dear\s+{re.escape(name)})'
            if re.search(dear_pattern, html, re.IGNORECASE):
                html = re.sub(dear_pattern, logo_html + r'\1', html, count=1, flags=re.IGNORECASE)
            else:
                # Fallback: insert after body tag
                body_pattern = r'(<body[^>]*>)'
                match = re.search(body_pattern, html, re.IGNORECASE)
                if match:
                    insert_position = match.end()
                    html = html[:insert_position] + '\n' + logo_html + '\n' + html[insert_position:]
        
        return subject, html
    except Exception as e:
        raise Exception(f"Gemini generation failed: {e}")