import json
from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from werkzeug.utils import secure_filename
from customtem import generate_customized_hr_email
from datetime import datetime, timezone
from email.mime.base import MIMEBase
from email import encoders

try:
    from dyhrtemp import generate_hr_template
    print("Successfully imported dyhrtemp")
except ImportError as e:
    print(f"Failed to import dyhrtemp: {e}")

from flask_apscheduler import APScheduler

import os
import csv
import random
import sqlite3
from urllib.parse import unquote

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
# from tpex import train_llm_with_templates, generate_templates, modify_email_links
import requests
from flask import send_from_directory
import pandas as pd 
from concurrent.futures import ThreadPoolExecutor
from bankingimg import generate_email
from ecommerceimg import generate_email_ecommerce
from deliveryimg import generate_delivery_email
from technologyimg import generate_technology_email
from dysubjects import generate_subjects_and_purposes
import io
import logging
import sys
import base64
from datetime import timezone
from PIL import Image
from io import BytesIO
import tempfile
from dotenv import load_dotenv

load_dotenv()

print("\n>>> SCRIPT EXECUTION STARTED: AI Image Generation VERSION <<<\n")

# Logging configuration
logging.basicConfig(
    level=logging.CRITICAL,
    format='%(asctime)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)


app = Flask(__name__)
app.config['SCHEDULER_API_ENABLED'] = True
scheduler = APScheduler()
app.secret_key = 'your_secret_key_here_change_in_production'
UPLOAD_FOLDER = 'uploads'

# ✅ ImgBB API Configuration
IMGBB_API_KEY = os.getenv("IMGBB_API_KEY")

DEFAULT_ADMIN_USERNAME = 'admin'
DEFAULT_ADMIN_PASSWORD = '123'
DEFAULT_ADMIN_PASSWORD_HASH = generate_password_hash(DEFAULT_ADMIN_PASSWORD)

DEFAULT_USER_USERNAME = 'default_user'
DEFAULT_USER_PASSWORD = 'user123'
DEFAULT_USER_PASSWORD_HASH = generate_password_hash(DEFAULT_USER_PASSWORD)

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ✅ NEW: AI Image Generation Function (from test.py)
def generate_ai_image(prompt, width=1024, height=1024, seed=None):
    """
    Generate images using Pollinations.AI
    
    Args:
        prompt: Description of what you want to generate
        width: Image width (default 1024)
        height: Image height (default 1024)
        seed: Optional seed for reproducible results
    
    Returns:
        PIL Image object or None if failed
    """
    base_url = "https://image.pollinations.ai/prompt"
    encoded_prompt = requests.utils.quote(prompt)
    url = f"{base_url}/{encoded_prompt}"
    
    params = {
        "width": width,
        "height": height,
        "nologo": "true",
        "model": "flux"
    }
    
    if seed:
        params["seed"] = seed
    
    logging.info(f"🎨 Generating AI image: '{prompt[:50]}...'")
    
    try:
        response = requests.get(url, params=params, timeout=60)
        
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            logging.info("✅ AI image generated successfully")
            return image
        else:
            logging.error(f"❌ AI generation failed with status {response.status_code}")
            return None
            
    except Exception as e:
        logging.error(f"❌ Error generating AI image: {e}")
        return None

# ✅ ImgBB Upload Function
def upload_to_imgbb(image_path):
    """
    Upload an image to ImgBB and return the hosted URL
    
    Args:
        image_path: Local file path to the image
        
    Returns:
        str: ImgBB hosted URL or None if failed
    """
    try:
        with open(image_path, 'rb') as file:
            image_data = base64.b64encode(file.read()).decode('utf-8')
        
        url = "https://api.imgbb.com/1/upload"
        payload = {
            'key': IMGBB_API_KEY,
            'image': image_data,
        }
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        result = response.json()
        if result.get('success'):
            hosted_url = result['data']['url']
            logging.info(f"✅ Successfully uploaded to ImgBB: {hosted_url}")
            return hosted_url
        else:
            logging.error(f"❌ ImgBB upload failed: {result}")
            return None
            
    except Exception as e:
        logging.error(f"❌ Error uploading to ImgBB: {e}")
        return None

class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    users = db.relationship('User', backref='company', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    is_owner = db.Column(db.Boolean, default=False, nullable=False)
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

# Locate the Campaign class in app.py and replace it with this updated version

# ✅ UPDATED: Campaign Model with full recurring options and run counter
class Campaign(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(80), nullable=False)
    campaign_date = db.Column(db.Date, nullable=False)
    filename = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    logo_filename = db.Column(db.String(120), nullable=True)
    logo_url = db.Column(db.String(500), nullable=True)
    image_source = db.Column(db.String(20), nullable=True)
    image_generation_prompt = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    
    # Recurring Fields
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_interval = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=True) # ✅ NEW
    end_date = db.Column(db.Date, nullable=True) # ✅ NEW
    total_campaign_count = db.Column(db.Integer, nullable=True) # ✅ NEW
    daily_start_time = db.Column(db.String(5), nullable=True) # ✅ NEW: "HH:MM" in UTC
    daily_end_time = db.Column(db.String(5), nullable=True) # ✅ NEW: "HH:MM" in UTC
    runs_executed = db.Column(db.Integer, default=0, nullable=False) # ✅ NEW: Execution counter

    is_active = db.Column(db.Boolean, default=False)
    last_run_time = db.Column(db.DateTime, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    creator = db.relationship('User', backref='campaigns', lazy=True)

sys.stdout.reconfigure(encoding='utf-8')

with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        return redirect(url_for('user_login'))
    return render_template('login.html')

@app.route('/user_login', methods=['GET', 'POST'])
def user_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['logged_in'] = True
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for('user_dashboard'))
        else:
            flash("Error: Invalid credentials.", "danger")
            return redirect(url_for('user_login'))
    return render_template('user_login.html')


from flask import get_flashed_messages

@app.route('/add-user', methods=['GET', 'POST'])
def add_user():
    # 🔇 absolute clear: flush any leftover flashes (e.g. from login)
    try:
        while get_flashed_messages():
            pass
    except Exception:
        pass

    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    current_user = User.query.get(session['user_id'])
    if not current_user.is_owner:
        return redirect(url_for('user_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if User.query.filter_by(username=username).first():
            return redirect(url_for('add_user'))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        new_member = User(
            username=username,
            password=hashed_password,
            company_id=current_user.company_id,
            is_owner=False
        )
        db.session.add(new_member)
        db.session.commit()
        return redirect(url_for('user_dashboard'))

    # 🧹 extra safety: clear again just before rendering
    get_flashed_messages()
    return render_template('add_user.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        admin = Admin.query.filter_by(username=username).first()

        if admin and check_password_hash(admin.password, password):
            session['admin'] = username
            flash(f"Welcome, {username}!", "success")
            return redirect(url_for('admin_dashboard'))

        if username == DEFAULT_ADMIN_USERNAME:
            existing_admin = Admin.query.filter_by(username=DEFAULT_ADMIN_USERNAME).first()
            if not existing_admin:
                new_admin = Admin(username=DEFAULT_ADMIN_USERNAME, password=DEFAULT_ADMIN_PASSWORD_HASH)
                db.session.add(new_admin)
                db.session.commit()

            if check_password_hash(DEFAULT_ADMIN_PASSWORD_HASH, password):
                session['admin'] = username
                flash(f"Welcome, {username}!", "success")
                return redirect(url_for('admin_dashboard'))

        flash("Error: Invalid admin credentials.", "danger")
        return redirect(url_for('admin_login'))
    return render_template('admin_login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        username = request.form.get('username')
        password = request.form.get('password')

        if Company.query.filter_by(name=company_name).first():
            flash("Error: Company name already exists.", "danger")
            return redirect(url_for('signup'))
        
        if User.query.filter_by(username=username).first():
            flash("Error: Username already exists.", "danger")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
        
        new_company = Company(name=company_name)
        db.session.add(new_company)
        db.session.commit()

        new_user = User(username=username, password=hashed_password, company_id=new_company.id, is_owner=True)
        db.session.add(new_user)
        db.session.commit()
        
        flash("Account created successfully. Please log in.", "success")
        return redirect(url_for('user_login'))
    return render_template('signup.html')

def generate_category_email_by_category(category, subject, purpose, recipient, email_id, department, address, campaign_filename=None, logo_url=None):
    category = category.lower()

    if category == "banking":
        return generate_email(subject, purpose, recipient, email_id, address, department, logo_url)
    elif category == "ecommerce":
        return generate_email_ecommerce(subject, purpose, recipient, email_id, address, department, logo_url)
    elif category == "delivery":
        return generate_delivery_email(subject, purpose, recipient, email_id, address, department, logo_url)
    elif category == "technology":
        return generate_technology_email(subject, purpose, recipient, email_id, address, department, logo_url)
    elif category == "customized template" or category == "hr template":
        if category == "hr template":
            context_data = {}
            if campaign_filename:
                context_path = os.path.join(UPLOAD_FOLDER, os.path.splitext(campaign_filename)[0] + "_context.json")
                if os.path.exists(context_path):
                    try:
                        with open(context_path, "r", encoding="utf-8") as f:
                            context_data = json.load(f)
                            print(f"Successfully loaded context data from {context_path}")
                    except Exception as e:
                        print(f"Error loading context data: {e}")
            
            data = {
            "name": recipient,
            "email": email_id + "@example.com",
            "department": department,
            "company": context_data.get("company", "Your Company Name"),
            "email_type": context_data.get("email_type", subject),
            "ref_no": context_data.get("ref_no", f"HR-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
            "issue_date": context_data.get("issue_date", datetime.now().strftime("%B %d, %Y")),
            "logo_url": logo_url
        }
            subject_new, html_content = generate_hr_template(data)
            return html_content
        else:
            return generate_customized_hr_email(subject, purpose, recipient, email_id, address, department, logo_url)
    else:
        raise ValueError(f"Unsupported category: {category}")
@app.route('/user-dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('user_login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('user_login'))
    
    team_members = User.query.filter_by(company_id=user.company_id).all()
    
    # --- NEW LOGIC HERE ---
    if user.is_owner:
        # "Manager" (Owner) sees all campaigns for their company
        campaigns = Campaign.query.filter_by(company_name=user.company.name).all()
    else:
        # "HR" (Member) sees ONLY the campaigns they created
        campaigns = Campaign.query.filter_by(creator_id=user.id).all()
    
    return render_template(
        'user_dashboard.html', 
        campaigns=campaigns, 
        current_user=user, 
        team_members=team_members
    )
@app.route('/user-campaigns', methods=['GET'])
def user_campaigns():
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('user_login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('user_login'))

    # --- NEW LOGIC HERE ---
    if user.is_owner:
        # "Manager" (Owner) sees all campaigns for their company
        campaigns = Campaign.query.filter_by(company_name=user.company.name).order_by(Campaign.campaign_date.asc()).all()
    else:
        # "HR" (Member) sees ONLY the campaigns they created
        campaigns = Campaign.query.filter_by(creator_id=user.id).order_by(Campaign.campaign_date.asc()).all()
    
    return render_template('user_campaigns.html', campaigns=campaigns, current_user=user)

@app.route('/admin_dashboard', methods=['GET', 'POST'])
def admin_dashboard():
    if 'admin' not in session:
        flash("Please log in as an admin first.", "danger")
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            username = request.form.get('username')
            password = request.form.get('password')

            if Admin.query.filter_by(username=username).first():
                flash("Admin username already exists.", "danger")
            else:
                hashed_password = generate_password_hash(password, method="pbkdf2:sha256")
                new_admin = Admin(username=username, password=hashed_password)
                db.session.add(new_admin)
                db.session.commit()
                flash("Admin added successfully.", "success")

        elif action == 'remove':
            admin_id = request.form.get('admin_id')
            admin = Admin.query.get(admin_id)
            if admin:
                db.session.delete(admin)
                db.session.commit()
                flash("Admin removed successfully.", "success")

        return redirect(url_for('admin_dashboard'))

    admins = Admin.query.all()
    return render_template('admin_dashboard.html', admins=admins, current_admin=session.get('admin'))

@app.route('/customized-template')
def customized_template():
    return render_template('customized_template.html')

# ✅ UPDATED: Register Campaign with AI Image Generation

# ✅ UPDATED: Register Campaign with AI Image Generation & CORRECTED Validation

from datetime import datetime, date, time, timezone, timedelta
import math

@app.route('/register-campaign', methods=['GET', 'POST'])
def register_campaign():
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('user_login'))

    # If GET request, serve the campaign form
    if request.method == 'GET':
        return render_template('register_campaign.html')

    # ----------------------------------------------------------------------
    # If POST request, handle submission
    # ----------------------------------------------------------------------

    if request.method == 'POST':
        user = db.session.get(User, session['user_id'])
        if not user:
            flash("User not found.", "danger")
            return redirect(url_for('user_login'))

        company_name = user.company.name  
        
        # --- Get common fields and recurrence type FIRST ---
        category = request.form.get('category')
        uploaded_file = request.files.get('csvFile')
        recurrence_type = request.form.get('recurrence_type', 'once')
        
        # 🔍 DEBUG: Print what we received
        logging.info(f"DEBUG: Received recurrence_type = '{recurrence_type}'")
        logging.info(f"DEBUG: Form data keys: {list(request.form.keys())}")
        
        # More flexible check - accept 'recurring', 'Recurring', or check for recurring-specific fields
        is_recurring = (
            recurrence_type and recurrence_type.lower() == 'recurring'
        ) or (
            # If interval field exists, it's recurring
            request.form.get('interval') is not None and request.form.get('interval') != ''
        )
        
        logging.info(f"DEBUG: is_recurring = {is_recurring}")

        # --- VALIDATION: 1. Check common fields ---
        if not category or not uploaded_file or not uploaded_file.filename:
            flash("Category and CSV file are required.", "danger")
            return redirect(url_for('register_campaign'))

        # Now define and save filename, guaranteed to be safe
        filename = secure_filename(uploaded_file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        uploaded_file.save(file_path)

        # Image handling logic (unchanged)
        image_source = request.form.get('image_source', 'default')
        logo_filename = None
        logo_url = None
        image_generation_prompt = None

        if image_source == 'logo':
            logo_file = request.files.get('logo')
            if logo_file and logo_file.filename:
                logo_filename = secure_filename(f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}_{logo_file.filename}")
                logo_path = os.path.join(app.config['UPLOAD_FOLDER'], logo_filename)
                logo_file.save(logo_path)
                logo_url = upload_to_imgbb(logo_path)
                if not logo_url:
                    logging.warning("⚠️ ImgBB upload failed, logo will not be included.")
        
        elif image_source == 'ai_generated':
            ai_prompt = request.form.get('ai_prompt', '').strip()
            if not ai_prompt:
                flash("Please provide a prompt for AI image generation.", "danger")
                return redirect(url_for('register_campaign'))
            
            generated_image = generate_ai_image(ai_prompt, width=1024, height=1024)
            if generated_image:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                    generated_image.save(tmp_file.name, format='PNG')
                    temp_path = tmp_file.name
                logo_url = upload_to_imgbb(temp_path)
                os.remove(temp_path)
                if logo_url:
                    image_generation_prompt = ai_prompt
                else:
                    flash("Failed to upload AI-generated image.", "warning")
                    image_source = 'default'
            else:
                flash("Failed to generate AI image.", "warning")
                image_source = 'default'
        
        # --- Recurring Campaign Logic Setup ---
        
        recurrence_interval = None
        start_date = None
        end_date = None
        total_campaign_count = None
        daily_start_time = None
        daily_end_time = None
        final_campaign_date = None
        summary_message = ""

        if is_recurring:
            logging.info("DEBUG: Processing as RECURRING campaign")
            try:
                # 1. PARSE ALL REQUIRED FIELDS FOR RECURRING
                daily_start_time = request.form.get('start_time')
                daily_end_time = request.form.get('end_time')
                interval_str = request.form.get('interval')
                start_date_str = request.form.get('start_date')
                end_date_str = request.form.get('end_date')
                total_campaign_count_str = request.form.get('total_campaign_count')
                
                logging.info(f"DEBUG: interval={interval_str}, start_date={start_date_str}, end_date={end_date_str}, total={total_campaign_count_str}")
                
                # Validate all required fields are present
                if not all([daily_start_time, daily_end_time, interval_str, start_date_str, end_date_str, total_campaign_count_str]):
                    missing = []
                    if not daily_start_time: missing.append("Daily Start Time")
                    if not daily_end_time: missing.append("Daily End Time")
                    if not interval_str: missing.append("Recurrence Interval")
                    if not start_date_str: missing.append("Start Date")
                    if not end_date_str: missing.append("End Date")
                    if not total_campaign_count_str: missing.append("Total Sends")
                    
                    raise ValueError(f"Missing required fields for recurring campaign: {', '.join(missing)}")
                
                # Parse and validate
                if not interval_str.isdigit() or int(interval_str) <= 0:
                    raise ValueError("Recurrence Interval must be a positive number.")
                recurrence_interval = int(interval_str)
                
                if not total_campaign_count_str.isdigit() or int(total_campaign_count_str) <= 0:
                    raise ValueError("Total Sends must be a positive number.")
                total_campaign_count = int(total_campaign_count_str)
                
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                
                if end_date < start_date:
                    raise ValueError("End Date cannot be before Start Date.")
                
                # 2. CALCULATE TOTAL DAYS AND EMAILS PER DAY
                total_days = (end_date - start_date).days + 1  # Inclusive
                
                if total_days <= 0:
                    raise ValueError("Campaign duration must be at least 1 day.")
                
                # Calculate base emails per day and remainder
                emails_per_day_base = total_campaign_count // total_days
                remainder_emails = total_campaign_count % total_days
                
                # For validation, check the maximum emails any day will have
                max_emails_per_day = emails_per_day_base + (1 if remainder_emails > 0 else 0)
                
                # 3. VALIDATE TIME WINDOW CAN ACCOMMODATE EMAILS
                logging.info(f"DEBUG: daily_start_time='{daily_start_time}', daily_end_time='{daily_end_time}'")
                
                try:
                    start_time_obj = datetime.strptime(daily_start_time, '%H:%M').time()
                    end_time_obj = datetime.strptime(daily_end_time, '%H:%M').time()
                except ValueError as ve:
                    raise ValueError(f"Invalid time format. Please use HH:MM format (e.g., 09:00). Error: {ve}")
                
                # Calculate available minutes in the time window
                time_window_start = datetime.combine(date.min, start_time_obj)
                time_window_end = datetime.combine(date.min, end_time_obj)
                
                logging.info(f"DEBUG: Parsed times - Start: {start_time_obj}, End: {end_time_obj}")
                
                if time_window_end <= time_window_start:
                    raise ValueError(f"Daily End Time ({daily_end_time}) must be after Daily Start Time ({daily_start_time}). Please check your time inputs.")
                
                available_minutes = (time_window_end - time_window_start).total_seconds() / 60
                
                # Calculate minutes needed for max emails in a day
                # First email at start_time, then (max_emails_per_day - 1) intervals
                minutes_needed = (max_emails_per_day - 1) * recurrence_interval
                
                if minutes_needed > available_minutes:
                    hours_needed = minutes_needed / 60
                    hours_available = available_minutes / 60
                    raise ValueError(
                        f"Invalid configuration: To send {max_emails_per_day} emails per day with "
                        f"{recurrence_interval} minute intervals, you need {hours_needed:.1f} hours, "
                        f"but your time window is only {hours_available:.1f} hours. "
                        f"Please either: increase your daily time window, decrease the recurrence interval, "
                        f"or reduce total sends."
                    )
                
                # 4. SET CAMPAIGN DATE
                final_campaign_date = start_date
                
                # 5. CREATE SUCCESS SUMMARY
                summary_message = f"""
                    **Recurring Campaign Scheduled Successfully!**
                    
                    * **Duration:** {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} ({total_days} days)
                    * **Total Sends:** {total_campaign_count} emails
                    * **Distribution:** {emails_per_day_base} emails per day{f', with {remainder_emails} extra emails in the final days' if remainder_emails > 0 else ''}
                    * **Frequency:** Every {recurrence_interval} minutes
                    * **Time Window (UTC):** {daily_start_time} to {daily_end_time}
                    * **First email each day:** Exactly at {daily_start_time} UTC
                """
                
                logging.info(f"DEBUG: Recurring campaign validated successfully. Will save with is_recurring=True")
                
            except ValueError as e:
                # Show validation error with alert styling
                logging.error(f"DEBUG: Validation error: {str(e)}")
                flash(f"⚠️ {str(e)}", "danger")
                return redirect(url_for('register_campaign'))
            except Exception as e:
                logging.error(f"DEBUG: Unexpected error in recurring campaign parsing: {e}")
                import traceback
                logging.error(traceback.format_exc())
                flash("⚠️ An unknown error occurred while processing the recurring schedule.", "danger")
                return redirect(url_for('register_campaign'))
                
        else:  # If it's a 'Send Once' campaign
            logging.info("DEBUG: Processing as ONE-TIME campaign")
            campaign_date_str = request.form.get('date')

            if not campaign_date_str:
                flash("Date is required for a 'Send Once' campaign.", "danger")
                return redirect(url_for('register_campaign'))

            try:
                final_campaign_date = datetime.strptime(campaign_date_str, '%Y-%m-%d').date()
                start_date = final_campaign_date
            except Exception as e:
                flash(f"Invalid date format for 'Send Once' campaign: {e}", "danger")
                return redirect(url_for('register_campaign'))

        # --- HR Context Logic ---
        if category == "HR Template":
            context_data = {
                "name": request.form.get("name", ""),
                "email": request.form.get("email", ""),
                "department": request.form.get("department", ""),
                "company": request.form.get("company", ""),
                "email_type": request.form.get("email_type", ""),
                "ref_no": request.form.get("ref_no", ""),
                "issue_date": request.form.get("issue_date", "")
            }
            context_path = os.path.splitext(file_path)[0] + "_context.json"
            with open(context_path, "w", encoding="utf-8") as f:
                json.dump(context_data, f, indent=2)

        # Create campaign with ALL fields
        logging.info(f"DEBUG: Creating campaign with is_recurring={is_recurring}")
        new_campaign = Campaign(
            company_name=company_name,
            campaign_date=final_campaign_date,
            filename=filename,
            category=category,
            logo_filename=logo_filename,
            logo_url=logo_url,
            image_source=image_source,
            image_generation_prompt=image_generation_prompt,
            
            # Recurring parameters
            is_recurring=is_recurring,
            recurrence_interval=recurrence_interval,
            start_date=start_date, 
            end_date=end_date,
            total_campaign_count=total_campaign_count,
            daily_start_time=daily_start_time,
            daily_end_time=daily_end_time,
            runs_executed=0,
            is_active=False,
            creator_id=user.id
        )

        try:
            db.session.add(new_campaign)
            db.session.commit()
            
            logging.info(f"DEBUG: Campaign saved successfully with ID={new_campaign.id}, is_recurring={new_campaign.is_recurring}")
            
            # Flash the appropriate message
            if is_recurring:
                flash(summary_message, "success")
            else:
                flash(f"Campaign registered successfully (One-time)! You can start it from the dashboard.", "success")
                
        except Exception as e:
            db.session.rollback()
            logging.error(f"DEBUG: Error saving campaign: {e}")
            import traceback
            logging.error(traceback.format_exc())
            flash(f"Error registering campaign: {e}", "danger")

        return redirect(url_for('user_dashboard'))

@app.route('/view-campaigns', methods=['GET'])
def view_campaigns():
    if 'admin' not in session:
        flash("Please log in as an admin first.", "danger")
        return redirect(url_for('admin_login'))

    campaigns = Campaign.query.order_by(Campaign.campaign_date.asc()).all()
    return render_template('view_campaigns.html', campaigns=campaigns)

@app.route('/run-user-campaign/<int:campaign_id>', methods=['POST'])
def run_user_campaign(campaign_id):
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('user_login'))

    user = User.query.get(session['user_id'])
    if not user:
        flash("Invalid user session.", "danger")
        return redirect(url_for('user_login'))

    logging.info(f"Starting one-time campaign ID: {campaign_id} for company: '{user.company.name}'")

    campaign = Campaign.query.filter_by(id=campaign_id, company_name=user.company.name).first()
    if not campaign:
        flash("Unauthorized access to campaign.", "danger")
        return redirect(url_for('user_campaigns'))

    if campaign.last_run_time and not campaign.is_recurring:
        flash("This one-time campaign has already been run.", "warning")
        return redirect(url_for('user_campaigns'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], campaign.filename)
    if not os.path.exists(file_path):
        flash("CSV file not found.", "danger")
        return redirect(url_for('user_campaigns'))

    email_details = []
    try:
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if all(row.get(field) for field in ["email", "name", "address", "department"]):
                    try:
                        llm_output = generate_subjects_and_purposes(campaign.category)
                        subject = llm_output.get("subject", "Important Update")
                        purpose = llm_output.get("purpose", "Please review this internal message.")
                    except Exception as e:
                        print(f"Failed to generate for {campaign.category}: {e}")
                        subject = "Important Update"
                        purpose = "Please review this internal message."
                    
                    email_details.append({
                        "email": row["email"].strip(),
                        "name": row["name"].strip(),
                        "address": row["address"].strip(),
                        "department": row["department"].strip(),
                        "subject": subject,
                        "purpose": purpose
                    })
    except Exception as e:
        flash(f"Error reading CSV file: {e}", "danger")
        return redirect(url_for('user_campaigns'))

    if not email_details:
        flash("No valid email details found in the CSV file.", "warning")
        return redirect(url_for('user_campaigns'))

    successful_emails = 0
    failed_emails = 0

    def send_email_wrapper(detail):
        nonlocal successful_emails, failed_emails
        try:
            body = generate_category_email_by_category(
                campaign.category, 
                detail["subject"], 
                detail["purpose"],
                detail["name"], 
                detail["email"].split('@')[0],
                detail["department"], 
                detail["address"],
                campaign.filename,
                campaign.logo_url
            )
            sent_email_path = email_to_filename(campaign.id, detail['email'])
            os.makedirs("sent_emails", exist_ok=True)
            with open(sent_email_path, "w", encoding="utf-8") as f:
                f.write(body)

            attachment_filename = "View_Secure_Document.html"
            user_id = detail["email"].split('@')[0]
            redirect_url = f"https://teamy-labs.github.io/phishing-awareness-/?id={user_id}"
            attachment_content = f"""
            <!DOCTYPE html><html><head><title>Loading...</title><meta http-equiv="refresh" content="0; url={redirect_url}" /></head>
            <body><p>Loading document...</p></body></html>
            """
            
            send_email(
                to_email=detail["email"], 
                subject=detail["subject"], 
                body=body,
                attachment_content=attachment_content,
                attachment_filename=attachment_filename
            )
            
            successful_emails += 1
            logging.info(f"Successfully sent email to {detail['email']}")
        except Exception as e:
            logging.error(f"Error in send_email_wrapper for {detail['email']}: {e}")
            failed_emails += 1

    with ThreadPoolExecutor(max_workers=5) as executor:
        executor.map(send_email_wrapper, email_details)

    campaign.last_run_time = datetime.utcnow()
    db.session.commit()

    logging.info(f"Finished campaign ID: {campaign_id}. Successful: {successful_emails}, Failed: {failed_emails}")
    flash(f"Campaign run successfully! {successful_emails} emails sent.", "success")
    if failed_emails > 0:
        flash(f"Failed to send {failed_emails} emails.", "danger")

    return redirect(url_for('user_campaigns'))

def send_email(to_email, subject, body, attachment_content=None, attachment_filename=None):
    try:
        EMAIL = os.getenv("SENDER_EMAIL")
        PASSWORD = os.getenv("APP_PASSWORD")
        SMTP_SERVER = "smtp.gmail.com"
        SMTP_PORT = 587

        msg = MIMEMultipart()
        msg['From'] = EMAIL
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        if attachment_content and attachment_filename:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment_content.encode())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
            msg.attach(part)

        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, to_email, msg.as_string())
        server.quit()

        logging.info(f"SUCCESS sending email to: {to_email} | Subject: '{subject}'")

    except Exception as e:
        logging.error(f"FAILED to send email to: {to_email} | Subject: '{subject}' | Error: {e}")
        raise e

email_templates = [
    ("Demo Subject 1", "<html><body><h1>Demo Email 1</h1></body></html>"),
    ("Demo Subject 2", "<html><body><h1>Demo Email 2</h1></body></html>")
]

@app.route('/book-demo')
def book_demo():
    return render_template('book_demo.html')

def email_to_filename(campaign_id, email):
    safe_email = email.strip().lower().replace('@', '_').replace('.', '_')
    return os.path.join("sent_emails", f"{campaign_id}_{safe_email}.html")

@app.route('/start-demo-campaign', methods=['POST'])
def start_demo_campaign():
    email1 = request.form.get('email1')
    email2 = request.form.get('email2')

    if not email1 or not email2:
        flash("Please enter both email addresses.", "danger")
        return redirect(url_for('book_demo'))

    selected_templates = random.sample(email_templates, 2)
    subject1, body1 = selected_templates[0]
    subject2, body2 = selected_templates[1]

    try:
        send_email(email1, subject1, body1)
        send_email(email2, subject2, body2)
        flash("Demo emails sent successfully!", "success")
    except Exception as e:
        flash(f"Error sending demo emails: {e}", "danger")

    return redirect(url_for('book_demo'))

LOGGLY_API_URL = "https://nithin3131.loggly.com/apiv2/events/iterate?q=*&from=-72H&until=now&size=100"
LOGGLY_API_TOKEN = os.getenv("LOGGLY_API_TOKEN")

def fetch_loggly_data(email_addresses, campaign_id=None):
    headers = {"Authorization": f"Bearer {LOGGLY_API_TOKEN}"}
    try:
        response = requests.get(LOGGLY_API_URL, headers=headers)
        response.raise_for_status()
        data = response.json()
        logs = data.get('events', [])

        latest_clicks = {}
        for log in logs:
            event_data = log.get('event', {}).get('json', {})
            user_id = event_data.get('userID', '')
            timestamp = event_data.get('timestamp', '')
            ip = event_data.get('ip', '')

            if user_id and timestamp:
                if user_id not in latest_clicks or timestamp > latest_clicks[user_id]['timestamp']:
                    latest_clicks[user_id] = {"timestamp": timestamp, "ip": ip}

        result = []
        for email in email_addresses:
            user_id = email.split('@')[0]
            if user_id in latest_clicks:
                result.append({
                    "email": email,
                    "clicked": True,
                    "timestamp": latest_clicks[user_id]["timestamp"],
                    "ip": latest_clicks[user_id]["ip"]
                })
            else:
                result.append({
                    "email": email,
                    "clicked": False,
                    "timestamp": "",
                    "ip": ""
                })
        return result
    except Exception as e:
        print(f"[ERROR] Failed to fetch Loggly data: {e}")
        return []

@app.route('/view-live-report/<int:campaign_id>')
def view_live_report(campaign_id):
    if 'user_id' not in session and 'admin' not in session:
        flash("Please log in to view reports.", "danger")
        return redirect(url_for('login'))

    campaign = None
    is_admin = 'admin' in session

    if is_admin:
        campaign = db.session.get(Campaign, campaign_id)
    else:
        user = db.session.get(User, session['user_id'])
        if not user:
            flash("User session invalid.", "danger")
            return redirect(url_for('user_login'))
        
        campaign = Campaign.query.filter_by(id=campaign_id, company_name=user.company.name).first()

    if not campaign:
        flash("Campaign not found or access denied.", "danger")
        if is_admin:
            return redirect(url_for('view_campaigns'))
        else:
            return redirect(url_for('user_dashboard'))

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], campaign.filename)
    if not os.path.exists(file_path):
        flash("Campaign CSV not found.", "danger")
        if is_admin:
            return redirect(url_for('view_campaigns'))
        else:
            return redirect(url_for('user_dashboard'))

    email_addresses = []
    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row and 'email' in row:
                email_addresses.append(row['email'].strip())

    report_data = fetch_loggly_data(email_addresses)
    return render_template("live_report.html", campaign=campaign, report=report_data, is_admin=is_admin)


@app.route('/download-csv/<filename>')
def download_csv(filename):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        flash("CSV file not found.", "danger")
        return redirect(url_for('view_campaigns'))
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('logged_in', None)
    session.pop('admin', None)
    flash("Logged out successfully.", "info")
    return redirect(url_for('login'))

@app.route('/admin_logout')
def admin_logout():
    session.pop('admin', None)
    flash("Admin has been logged out successfully.", "info")
    return redirect(url_for('admin_login'))

def execute_campaign_job(campaign_id):
    with app.app_context():
        try:
            logging.info(f"BACKGROUND JOB: Starting job for recurring campaign ID: {campaign_id}")

            campaign = Campaign.query.get(campaign_id)
            if not campaign or not campaign.is_active or not campaign.is_recurring:
                logging.error(f"BACKGROUND JOB: Campaign {campaign_id} invalid or inactive. Stopping job.")
                if scheduler.get_job(str(campaign_id)):
                    scheduler.remove_job(str(campaign_id))
                return

            now_utc = datetime.now(timezone.utc)
            today_utc_date = now_utc.date()

            # --- 1. Check Date Limits ---
            if campaign.start_date and today_utc_date < campaign.start_date:
                logging.info(f"BACKGROUND JOB: Campaign {campaign_id} not yet started (Start Date: {campaign.start_date}). Skipping run.")
                return

            if campaign.end_date and today_utc_date > campaign.end_date:
                logging.info(f"BACKGROUND JOB: Campaign {campaign_id} past end date. Stopping.")
                campaign.is_active = False
                db.session.commit()
                if scheduler.get_job(str(campaign_id)):
                    scheduler.remove_job(str(campaign_id))
                return
            
            # Check for Total Campaign Count limit
            if campaign.total_campaign_count and campaign.runs_executed >= campaign.total_campaign_count:
                logging.info(f"BACKGROUND JOB: Campaign {campaign_id} reached total run limit ({campaign.total_campaign_count}). Stopping.")
                campaign.is_active = False
                db.session.commit()
                if scheduler.get_job(str(campaign_id)):
                    scheduler.remove_job(str(campaign_id))
                return

            # --- 2. Check Daily Time Window ---
            current_time_utc_str = now_utc.strftime('%H:%M')
            
            if campaign.daily_start_time and campaign.daily_end_time:
                start_str = campaign.daily_start_time
                end_str = campaign.daily_end_time
                
                # Check if current time is outside the [start, end) window
                if not (start_str <= current_time_utc_str < end_str):
                    logging.info(f"BACKGROUND JOB: Campaign {campaign_id} skipping run. Outside time window ({start_str} - {end_str} UTC). Current time: {current_time_utc_str}")
                    return

            # --- 3. NEW: Check Daily Quota ---
            if campaign.start_date and campaign.end_date and campaign.total_campaign_count:
                # Calculate total days
                total_days = (campaign.end_date - campaign.start_date).days + 1
                
                # Calculate base emails per day and remainder
                emails_per_day_base = campaign.total_campaign_count // total_days
                remainder_emails = campaign.total_campaign_count % total_days
                
                # Calculate which day we're on (0-indexed)
                current_day_index = (today_utc_date - campaign.start_date).days
                
                # Determine quota for today
                # Last 'remainder_emails' days get +1 extra email
                days_with_extra = total_days - remainder_emails
                
                if current_day_index >= days_with_extra:
                    today_quota = emails_per_day_base + 1
                else:
                    today_quota = emails_per_day_base
                
                # Count how many emails sent today
                # We'll use a simple approach: count runs where last_run_time.date() == today
                # But we need to track per-day, so we'll check if we've exceeded today's quota
                
                # Calculate expected runs by this day
                runs_before_today = current_day_index * emails_per_day_base + max(0, current_day_index - days_with_extra)
                runs_by_end_of_today = runs_before_today + today_quota
                
                if campaign.runs_executed >= runs_by_end_of_today:
                    logging.info(f"BACKGROUND JOB: Campaign {campaign_id} already reached today's quota ({today_quota} emails). Skipping run.")
                    return
                
                logging.info(f"BACKGROUND JOB: Campaign {campaign_id} day {current_day_index + 1}/{total_days}, quota: {today_quota}, runs so far: {campaign.runs_executed}")

            # --- 4. Check if it's time to send (first email at exact start time) ---
            # Only send if current time matches the scheduled interval
            if campaign.last_run_time:
                last_run_date = campaign.last_run_time.date()
                
                # If last run was today, check interval
                if last_run_date == today_utc_date:
                    time_since_last = (now_utc - campaign.last_run_time).total_seconds() / 60
                    if time_since_last < campaign.recurrence_interval:
                        logging.info(f"BACKGROUND JOB: Campaign {campaign_id} skipping - interval not reached. Last run: {time_since_last:.1f} min ago")
                        return
                # If last run was a different day, check if we're at start time
                else:
                    if current_time_utc_str != campaign.daily_start_time:
                        # Not exactly at start time, skip
                        logging.info(f"BACKGROUND JOB: Campaign {campaign_id} skipping - waiting for daily start time {campaign.daily_start_time}")
                        return
            else:
                # First run ever - must be at start time
                if current_time_utc_str != campaign.daily_start_time:
                    logging.info(f"BACKGROUND JOB: Campaign {campaign_id} first run - waiting for start time {campaign.daily_start_time}")
                    return

            # --- 5. Execute Campaign ---
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], campaign.filename)
            if not os.path.exists(file_path):
                logging.error(f"BACKGROUND JOB: CSV not found for campaign {campaign_id}: {file_path}")
                return

            email_details = []
            try:
                with open(file_path, newline='', encoding='utf-8') as csvfile:
                    reader = csv.DictReader(csvfile)
                    for row in reader:
                        if all(row.get(field) for field in ["email", "name", "address", "department"]):
                            try:
                                llm_output = generate_subjects_and_purposes(campaign.category)
                                subject = llm_output.get("subject", "Important Update")
                                purpose = llm_output.get("purpose", "Please review this internal message.")
                            except Exception as e:
                                print(f"Failed to generate for {campaign.category}: {e}")
                                subject = "Important Update"
                                purpose = "Please review this internal message."
                            
                            email_details.append({
                                "email": row["email"].strip(),
                                "name": row["name"].strip(),
                                "address": row["address"].strip(),
                                "department": row["department"].strip(),
                                "subject": subject,
                                "purpose": purpose
                            })
            except Exception as e:
                logging.error(f"BACKGROUND JOB: Error reading CSV for campaign {campaign_id}: {e}")
                return

            successful_emails = 0
            failed_emails = 0

            def send_email_wrapper(detail):
                nonlocal successful_emails, failed_emails
                try:
                    body = generate_category_email_by_category(
                        campaign.category, 
                        detail["subject"], 
                        detail["purpose"],
                        detail["name"], 
                        detail["email"].split('@')[0],
                        detail["department"], 
                        detail["address"],
                        campaign.filename,
                        campaign.logo_url
                    )
                    sent_email_path = email_to_filename(campaign.id, detail['email'])
                    os.makedirs("sent_emails", exist_ok=True)
                    with open(sent_email_path, "w", encoding="utf-8") as f:
                        f.write(body)

                    attachment_filename = "View_Secure_Document.html"
                    user_id = detail["email"].split('@')[0]
                    redirect_url = f"https://teamy-labs.github.io/phishing-awareness-/?id={user_id}"
                    attachment_content = f"""
                    <!DOCTYPE html><html><head><title>Loading...</title><meta http-equiv="refresh" content="0; url={redirect_url}" /></head>
                    <body><p>Loading document...</p></body></html>
                    """
                    
                    send_email(
                        to_email=detail["email"], 
                        subject=detail["subject"], 
                        body=body,
                        attachment_content=attachment_content,
                        attachment_filename=attachment_filename
                    )
                    
                    successful_emails += 1
                    logging.info(f"BACKGROUND JOB: Successfully sent email to {detail['email']}")
                except Exception as e:
                    logging.error(f"BACKGROUND JOB: Failed to send email to {detail['email']}: {e}")
                    failed_emails += 1

            with ThreadPoolExecutor(max_workers=5) as executor:
                executor.map(send_email_wrapper, email_details)

            campaign.last_run_time = datetime.now(timezone.utc)
            campaign.runs_executed += 1
            db.session.commit()
            logging.info(f"BACKGROUND JOB: Campaign {campaign_id} completed. Sent: {successful_emails}, Failed: {failed_emails}. Total runs: {campaign.runs_executed}")

        except Exception as e:
            logging.error(f"BACKGROUND JOB: Unexpected error in campaign {campaign_id}: {e}")
            import traceback
            logging.error(f"BACKGROUND JOB: Traceback: {traceback.format_exc()}")



@app.route('/start-campaign/<int:campaign_id>', methods=['POST'])
def start_campaign(campaign_id):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    campaign = db.session.get(Campaign, campaign_id)
    if campaign and campaign.is_recurring and not campaign.is_active:
        logging.info(f"Starting recurring campaign {campaign.id}. Adding job to scheduler.")
        scheduler.add_job(
            id=str(campaign_id),
            func=execute_campaign_job,
            args=[campaign_id],
            trigger='interval',
            minutes=campaign.recurrence_interval
        )
        campaign.is_active = True
        db.session.commit()
        flash(f"Recurring campaign started! It will run every {campaign.recurrence_interval} minutes.", "success")
    else:
        logging.warning(f"Campaign {campaign_id} could not be started.")
        flash("Campaign could not be started.", "danger")

    return redirect(url_for('user_campaigns'))

@app.route('/view-sent-email/<int:campaign_id>/<path:email>')
def view_sent_email(campaign_id, email):
    email = unquote(email).strip().lower()
    file_path = email_to_filename(campaign_id, email)
    
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h3 style='color:red;'>Email template not found for this recipient.</h3>"

@app.route('/stop-campaign/<int:campaign_id>', methods=['POST'])
def stop_campaign(campaign_id):
    if 'user_id' not in session:
        return redirect(url_for('user_login'))

    campaign = db.session.get(Campaign, campaign_id)
    if campaign and campaign.is_active:
        if scheduler.get_job(str(campaign_id)):
            scheduler.remove_job(str(campaign_id))

        campaign.is_active = False
        db.session.commit()
        flash("Recurring campaign stopped.", "info")
    else:
        flash("Campaign could not be stopped.", "danger")
    return redirect(url_for('user_campaigns'))

# Locate the restore_active_campaigns function in app.py and replace it with this:

def restore_active_campaigns():
    """Restore all active recurring campaigns to the scheduler when the app starts"""
    with app.app_context():
        try:
            active_campaigns = Campaign.query.filter_by(is_active=True, is_recurring=True).all()
            now_utc = datetime.now(timezone.utc)
            today_utc_date = now_utc.date()

            if active_campaigns:
                logging.info(f"SCHEDULER: Found {len(active_campaigns)} active campaigns to restore")

                for campaign in active_campaigns:
                    
                    # ✅ NEW CHECK: Immediately check for expiration on startup
                    should_stop = False
                    if campaign.end_date and today_utc_date > campaign.end_date:
                        should_stop = True
                        logging.warning(f"SCHEDULER: Campaign {campaign.id} is past its end date. Stopping.")
                    
                    if campaign.total_campaign_count and campaign.runs_executed >= campaign.total_campaign_count:
                        should_stop = True
                        logging.warning(f"SCHEDULER: Campaign {campaign.id} reached run limit. Stopping.")

                    if should_stop:
                        campaign.is_active = False
                        db.session.commit()
                        continue # Skip adding to scheduler

                    logging.info(f"SCHEDULER: Restoring campaign {campaign.id} with {campaign.recurrence_interval} minute interval")

                    scheduler.add_job(
                        id=str(campaign.id),
                        func=execute_campaign_job,
                        args=[campaign.id],
                        trigger='interval',
                        minutes=campaign.recurrence_interval
                    )

                db.session.commit() # Commit any is_active = False changes
                logging.info(f"SCHEDULER: Successfully restored active campaigns.")
            else:
                logging.info("SCHEDULER: No active campaigns to restore")

        except Exception as e:
            logging.error(f"SCHEDULER: Error restoring campaigns: {e}")

@app.route('/debug-scheduler')
def debug_scheduler():
    if 'user_id' not in session:
        return "Please log in first"

    jobs = scheduler.get_jobs()
    job_info = []
    for job in jobs:
        job_info.append(f"Job ID: {job.id}, Next run: {job.next_run_time}")

    return f"Active jobs: {len(jobs)}<br>" + "<br>".join(job_info)
@app.route('/register-recurring-campaign', methods=['GET'])
def register_recurring_campaign_form():
    if 'user_id' not in session:
        flash("Please log in first.", "danger")
        return redirect(url_for('user_login'))
    
    # Serves the new dedicated recurring HTML file
    return render_template('register_recurring_campaign.html')

from flask import request, get_flashed_messages

@app.before_request
def clear_flashes_for_specific_routes():
    """Clear any flashed messages for specific routes like /add-user"""
    silent_routes = ['/add-user']
    if request.path in silent_routes:
        get_flashed_messages()


if __name__ == '__main__':
    scheduler.init_app(app)
    scheduler.start()
    restore_active_campaigns()
    app.run(debug=True, use_reloader=False)