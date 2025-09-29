from flask import Flask, render_template, request, redirect, url_for, flash
import os
from werkzeug.utils import secure_filename

# Shared data store for NGO applications
ngo_applications = [
    {"id": 1, "org_name": "Green Earth Foundation", "org_type": "NGO", "project_title": "Mangrove Conservation Initiative", "email": "info@greenearth.org", "status": "pending", "files": {"registration_certificate": "green_earth_reg.pdf", "pan_card": "green_earth_pan.pdf", "tax_certificate": "green_earth_tax.pdf"}, "professional_id": "NGO001", "session_token": "sess_001"},
    {"id": 2, "org_name": "Coastal Village Panchayat", "org_type": "Panchayat", "project_title": "Blue Carbon Credit Program", "email": "admin@coastalvillage.gov.in", "status": "accepted", "files": {"registration_certificate": "coastal_panchayat_reg.pdf", "pan_card": "coastal_panchayat_pan.pdf", "tax_certificate": "coastal_panchayat_tax.pdf"}, "professional_id": "PAN001", "session_token": "sess_002"},
    {"id": 3, "org_name": "Ocean Conservation Society", "org_type": "NGO", "project_title": "Marine Ecosystem Restoration", "email": "contact@oceanconservation.org", "status": "declined", "files": {"registration_certificate": "ocean_society_reg.pdf", "pan_card": "ocean_society_pan.pdf", "tax_certificate": "ocean_society_tax.pdf"}, "professional_id": "NGO002", "session_token": "sess_003"},
    {"id": 4, "org_name": "Sundarbans Development Trust", "org_type": "NGO", "project_title": "Wetland Protection Project", "email": "trust@sundarbans.org", "status": "pending", "files": {"registration_certificate": "sundarbans_reg.pdf", "pan_card": "sundarbans_pan.pdf", "tax_certificate": "sundarbans_tax.pdf"}, "professional_id": "NGO003", "session_token": "sess_004"},
    {"id": 5, "org_name": "Kerala Coastal Panchayat", "org_type": "Panchayat", "project_title": "Sustainable Fishing Initiative", "email": "kerala@coastalpanchayat.gov.in", "status": "pending", "files": {"registration_certificate": "kerala_panchayat_reg.pdf", "pan_card": "kerala_panchayat_pan.pdf", "tax_certificate": "kerala_panchayat_tax.pdf"}, "professional_id": "PAN002", "session_token": "sess_005"}
]

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_app():
    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config["SECRET_KEY"] = "change-this-secret-key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    
    # Create upload directory if it doesn't exist
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    # --- Routes ---
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            flash("Admin login successful", "success")
            return redirect(url_for("admin_dashboard"))
        return render_template("admin_login.html")

    @app.route("/admin/dashboard")
    def admin_dashboard():
        pending_ngos = [ngo for ngo in ngo_applications if ngo["status"] == "pending"]
        return render_template("admin_dashboard.html", all_ngos=ngo_applications, pending_ngos=pending_ngos)
    
    @app.route("/uploads/<filename>")
    def uploaded_file(filename):
        from flask import send_from_directory
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route("/download/app", methods=["GET", "HEAD"])
    def download_mobile_app():
        from flask import send_file, abort
        project_root = os.path.abspath(os.path.dirname(__file__))
        apk_filename = "app-release.apk"
        apk_path = os.path.join(project_root, "public", apk_filename)
        if not os.path.isfile(apk_path):
            print(f"[APK DOWNLOAD] Not found at: {apk_path}")
            abort(404, description="APK not found")
        return send_file(
            apk_path,
            as_attachment=True,
            download_name=apk_filename,
            mimetype='application/vnd.android.package-archive'
        )

    @app.route("/app-release.apk", methods=["GET", "HEAD"])
    def download_mobile_app_direct():
        from flask import send_file, abort
        project_root = os.path.abspath(os.path.dirname(__file__))
        apk_filename = "app-release.apk"
        apk_path = os.path.join(project_root, "public", apk_filename)
        if not os.path.isfile(apk_path):
            print(f"[APK DOWNLOAD] Not found at: {apk_path}")
            abort(404, description="APK not found")
        return send_file(
            apk_path,
            as_attachment=True,
            download_name=apk_filename,
            mimetype='application/vnd.android.package-archive'
        )
    
    @app.route("/api/flutter/login", methods=["POST"])
    def flutter_login():
        from flask import jsonify
        data = request.get_json()
        professional_id = data.get('professional_id')
        session_token = data.get('session_token')
        
        if not professional_id or not session_token:
            return jsonify({"success": False, "message": "Professional ID and Session Token required"}), 400
        
        # Find NGO by professional ID and session token
        ngo = next((ngo for ngo in ngo_applications 
                   if ngo.get("professional_id") == professional_id 
                   and ngo.get("session_token") == session_token), None)
        
        if ngo:
            return jsonify({
                "success": True,
                "data": {
                    "ngo_id": ngo["id"],
                    "org_name": ngo["org_name"],
                    "org_type": ngo["org_type"],
                    "project_title": ngo["project_title"],
                    "email": ngo["email"],
                    "status": ngo["status"],
                    "professional_id": ngo["professional_id"]
                }
            })
        else:
            return jsonify({"success": False, "message": "Invalid credentials"}), 401

    @app.route("/admin/update-ngo-status", methods=["POST"])
    def admin_update_ngo_status():
        ngo_id = int(request.form.get("ngo_id"))
        status = request.form.get("status")
        
        # Find and update the NGO in the shared data
        for ngo in ngo_applications:
            if ngo["id"] == ngo_id:
                ngo["status"] = status
                flash(f"Status updated to {status} for {ngo['org_name']}", "success")
                break
        
        return redirect(url_for("admin_dashboard"))

    @app.route("/ngo/register", methods=["GET", "POST"])
    def ngo_register():
        if request.method == "POST":
            org_name = request.form.get("org_name", "")
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            org_type = request.form.get("org_type", "")
            project_title = request.form.get("project_title", "")
            
            if org_name and email and password and org_type and project_title:
                # Check if email already exists
                existing_ngo = next((ngo for ngo in ngo_applications if ngo["email"] == email), None)
                if existing_ngo:
                    flash("Email already registered. Please login instead.", "danger")
                    return redirect(url_for("ngo_login"))
                
                # Handle file uploads
                files = {}
                file_fields = ['registration_certificate', 'pan_card', 'tax_certificate']
                
                for field in file_fields:
                    if field in request.files:
                        file = request.files[field]
                        if file and file.filename and allowed_file(file.filename):
                            filename = secure_filename(file.filename)
                            # Add timestamp to make filename unique
                            import time
                            timestamp = str(int(time.time()))
                            filename = f"{new_ngo_id}_{field}_{timestamp}_{filename}"
                            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                            files[field] = filename
                        else:
                            flash(f"Invalid file for {field.replace('_', ' ').title()}", "danger")
                            return redirect(url_for("ngo_register"))
                
                # Create new NGO application
                new_ngo_id = max([ngo["id"] for ngo in ngo_applications], default=0) + 1
                new_ngo = {
                    "id": new_ngo_id,
                    "org_name": org_name,
                    "org_type": org_type,
                    "project_title": project_title,
                    "email": email,
                    "status": "pending",
                    "files": files
                }
                ngo_applications.append(new_ngo)
                
                flash(f"Registration successful for {org_name}. Your application is now under review.", "success")
                return redirect(url_for("ngo_status", ngo_id=new_ngo_id))
            else:
                flash("All fields are required", "danger")
        return render_template("ngo_register.html")

    @app.route("/ngo/login", methods=["GET", "POST"])
    def ngo_login():
        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            
            if email and password:
                # Find NGO by email
                ngo = next((ngo for ngo in ngo_applications if ngo["email"] == email), None)
                if ngo:
                    # For new email addresses, accept any password
                    # List of new email addresses that don't require password validation
                    new_emails = [
                        "info@greenearth.org",
                        "admin@coastalvillage.gov.in", 
                        "contact@oceanconservation.org",
                        "trust@sundarbans.org",
                        "kerala@coastalpanchayat.gov.in"
                    ]
                    
                    # Check if this is a new email (no password validation required)
                    if email in new_emails:
                        # Accept any password for new emails
                        pass
                    else:
                        # For other emails, you could add password validation here if needed
                        # For now, we'll accept any password for all emails
                        pass
                    
                    # Generate professional session ID
                    import time
                    import hashlib
                    
                    # Create professional ID format: NGO-{ORG_TYPE}-{ID}-{TIMESTAMP}
                    timestamp = str(int(time.time()))
                    org_type_code = "NGO" if ngo["org_type"] == "NGO" else "PAN"
                    professional_id = f"{org_type_code}-{ngo['id']:04d}-{timestamp[-6:]}"
                    
                    # Generate session token using hash
                    session_data = f"{ngo['email']}{timestamp}{ngo['id']}"
                    session_token = hashlib.sha256(session_data.encode()).hexdigest()[:16].upper()
                    
                    # Store both IDs in NGO data
                    ngo["professional_id"] = professional_id
                    ngo["session_token"] = session_token
                    
                    flash(f"Login successful for {ngo['org_name']}", "success")
                    return redirect(url_for("ngo_dashboard", ngo_id=ngo["id"], session_id=session_token))
                else:
                    flash("Invalid email address", "danger")
            else:
                flash("Please enter both email and password", "danger")
        return render_template("ngo_login.html")

    @app.route("/ngo/status/<int:ngo_id>")
    def ngo_status(ngo_id):
        # Find NGO in shared data
        ngo = next((ngo for ngo in ngo_applications if ngo["id"] == ngo_id), None)
        if not ngo:
            flash("NGO application not found", "danger")
            return redirect(url_for("ngo_login"))
        return render_template("ngo_status.html", ngo=ngo)

    @app.route("/ngo/dashboard/<int:ngo_id>")
    def ngo_dashboard(ngo_id):
        session_id = request.args.get('session_id')
        
        # Find NGO in shared data
        ngo = next((ngo for ngo in ngo_applications if ngo["id"] == ngo_id), None)
        if not ngo:
            flash("NGO not found", "danger")
            return redirect(url_for("ngo_login"))
        
        # Verify session token
        if not session_id or ngo.get("session_token") != session_id:
            flash("Invalid session. Please login again.", "danger")
            return redirect(url_for("ngo_login"))
        
        return render_template("ngo_dashboard.html", ngo=ngo, session_id=session_id)

    @app.route("/companies/login", methods=["GET", "POST"])
    def companies_login():
        if request.method == "POST":
            email = request.form.get("email", "")
            password = request.form.get("password", "")
            if email and password:
                flash(f"Login successful", "success")
                return redirect(url_for("companies_portal"))
            else:
                flash("Invalid company credentials", "danger")
        return render_template("company_login.html")

    @app.route("/companies/register", methods=["GET", "POST"])
    def companies_register():
        if request.method == "POST":
            company_name = request.form.get("reg_company", "")
            email = request.form.get("reg_email", "")
            password = request.form.get("reg_password", "")
            if company_name and email and password:
                flash(f"Registration successful for {company_name}", "success")
                return redirect(url_for("companies_login"))
        return render_template("company_register.html")

    @app.get("/companies/portal")
    def companies_portal():
        return render_template("companies_portal.html")

    @app.route("/companies/generate-certificate")
    def generate_certificate():
        company_name = request.args.get("company_name")
        project_title = request.args.get("project_title")
        tokens = request.args.get("tokens")
        return render_template("certificate.html", company_name=company_name, project_title=project_title, tokens=tokens)

    return app


# Initialize app
app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
