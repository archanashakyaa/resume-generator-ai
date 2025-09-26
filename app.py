from flask import Flask, render_template, request, send_file, jsonify, make_response
from flask_cors import CORS, cross_origin
from groq import Groq
from docx import Document
import os
import traceback
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# -------------------------------
# Enhanced CORS configuration (FIXED)
# -------------------------------
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000", "http://localhost:5000", "http://127.0.0.1:3000", "http://127.0.0.1:5000",
                    "*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept", "X-Requested-With"],
        "supports_credentials": True
    }
})


@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization,Accept,X-Requested-With")
        response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        return response


@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response


# -------------------------------
# Groq API Configuration (FIXED)
# -------------------------------
# FIXED: Direct API key assignment instead of using os.getenv with the key itself
GROQ_API_KEY = "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"

# FIXED: Use a known working model
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"  # Changed from the non-existent model

# Test Groq connection
client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        # Test the connection with a simple request
        test_response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5
        )
        logger.info(f"✅ Groq API connection successful with model: {GROQ_MODEL}")
        print(f"✅ Groq API Key loaded and tested successfully")
        print(f"✅ Model: {GROQ_MODEL}")
    except Exception as e:
        logger.error(f"❌ Groq API connection failed: {e}")
        print(f"❌ Groq API connection failed: {e}")
        client = None
else:
    logger.error("❌ No GROQ_API_KEY found")
    print("❌ No GROQ_API_KEY found")

# -------------------------------
# Resume Enhancement Prompts
# -------------------------------
GLOBAL_RULE = (
    "Global Resume Rules:\n"
    "1. Use professional, employer-focused tone.\n"
    "2. Do not use first-person pronouns.\n"
    "3. Be concise, quantifiable, and clear.\n"
    "4. Fix grammar, avoid redundancy.\n"
    "5. Do not invent experiences or education.\n"
)

resume_prompts = {
    "summary": "Rewrite the Professional Summary concisely (50–70 words).",
    "experience": "Rewrite Work Experience emphasizing achievements and measurable outcomes (70–120 words).",
    "skills": "Rewrite Skills as a concise, comma-separated list.",
    "education": "Rewrite Education highlighting degrees, certifications, or distinctions (50–100 words).",
    "projects": "Rewrite Projects highlighting scope, technologies, and results (50–100 words).",
    "certifications": "Rewrite Certifications to emphasize relevance (30–60 words).",
    "achievements": "Rewrite Achievements with measurable impact (40–80 words).",
    "hobbies": "Rewrite Hobbies/Interests professionally (20–50 words)."
}


# -------------------------------
# Helper Functions
# -------------------------------
def enhance_section(section_name, user_input):
    """Enhance resume section via Groq"""
    logger.debug(f"Enhancing section: {section_name}")

    if not user_input or not user_input.strip():
        logger.warning(f"Empty input for section: {section_name}")
        return f"[{section_name.title()} section not provided.]"

    if not client:
        logger.error("Groq client not available")
        return user_input.strip()

    prompt = f"{GLOBAL_RULE}\n\n{resume_prompts.get(section_name.lower(), '')}\n\nUser Input:\n{user_input}\n\nEnhanced Content:"

    try:
        logger.debug(f"Sending request to Groq for section: {section_name}")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system",
                 "content": "You are an expert resume consultant. Improve the given content while keeping it truthful and professional."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )

        enhanced_content = response.choices[0].message.content.strip()
        logger.info(f"Successfully enhanced section: {section_name}")
        return enhanced_content

    except Exception as e:
        logger.error(f"Groq API failed for section {section_name}: {e}")
        print(f"[ERROR] Groq API failed: {e}")
        traceback.print_exc()
        return user_input.strip()


def save_resume_docx(enhanced_resume, filename="Enhanced_Resume.docx"):
    """Save enhanced resume to DOCX file"""
    try:
        logger.debug(f"Creating DOCX file: {filename}")
        doc = Document()
        doc.add_heading("Enhanced Resume", 0)

        for section, text in enhanced_resume.items():
            if text and text.strip() and not text.startswith('[') and not text.endswith('not provided.]'):
                doc.add_heading(section.title(), level=1)

                # Handle multi-line content
                paragraphs = text.split('\n')
                for paragraph in paragraphs:
                    if paragraph.strip():
                        doc.add_paragraph(paragraph.strip())

        doc.save(filename)
        logger.info(f"DOCX file saved successfully: {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to create DOCX: {str(e)}")
        print(f"[ERROR] Failed to create DOCX: {str(e)}")
        raise


# -------------------------------
# Flask Routes
# -------------------------------
@app.route("/")
def index():
    logger.info("Serving index page")
    return render_template("index.html")


@app.route("/enhance", methods=["POST", "OPTIONS"])
@cross_origin()
def enhance_ajax():
    if request.method == "OPTIONS":
        logger.debug("Handling OPTIONS request for /enhance")
        return "", 200

    logger.info("Processing enhance request")

    try:
        # Log request details
        logger.debug(f"Content-Type: {request.content_type}")
        logger.debug(f"Method: {request.method}")
        logger.debug(f"Is JSON: {request.is_json}")

        if not request.is_json:
            logger.error("Request is not JSON")
            return jsonify({'success': False, 'error': 'Content-Type must be application/json'}), 400

        data = request.get_json()
        if not data:
            logger.error("No JSON data received")
            return jsonify({'success': False, 'error': 'No data received'}), 400

        logger.debug(f"Request data: {data}")

        section_name = data.get('section')
        content = data.get('content')

        if not section_name:
            logger.error("Missing section name")
            return jsonify({'success': False, 'error': 'Missing section name'}), 400

        if not client:
            logger.error("Groq client not available")
            return jsonify({'success': False,
                            'error': 'AI enhancement service not available. Please check server configuration.'}), 500

        logger.info(f"Enhancing section: {section_name}")
        enhanced_content = enhance_section(section_name, content or "")

        response_data = {
            'success': True,
            'enhanced_content': enhanced_content,
            'section': section_name
        }

        logger.info(f"Enhancement successful for section: {section_name}")
        return jsonify(response_data)

    except Exception as e:
        logger.error(f"Enhancement error: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Server error: {str(e)}'}), 500


@app.route("/generate_resume", methods=["POST", "OPTIONS"])
@cross_origin()
def generate_resume():
    if request.method == "OPTIONS":
        logger.debug("Handling OPTIONS request for /generate_resume")
        return "", 200

    logger.info("Processing generate_resume request")

    try:
        data = request.get_json()
        if not data:
            logger.error("No data received for resume generation")
            return jsonify({'success': False, 'error': 'No data received'}), 400

        logger.debug(f"Resume data received: {list(data.keys())}")
        enhanced_resume = {}

        # Personal info
        personal_info = data.get('personal', {})
        if personal_info:
            contact_info = []
            for field in ['email', 'phone', 'location', 'linkedin']:
                if personal_info.get(field):
                    contact_info.append(personal_info[field])
            if contact_info:
                enhanced_resume['Contact Information'] = ' | '.join(contact_info)

            if personal_info.get('fullName'):
                enhanced_resume['Name'] = personal_info['fullName']

            if personal_info.get('summary'):
                enhanced_resume['Professional Summary'] = enhance_section("summary", personal_info['summary'])

        # Experience
        experiences = data.get('experiences', [])
        if experiences:
            exp_content = []
            for exp in experiences:
                if any([exp.get('title'), exp.get('company'), exp.get('description')]):
                    exp_text = f"{exp.get('title', 'Position')} - {exp.get('company', 'Company')}"
                    if exp.get('startDate') or exp.get('endDate'):
                        start = exp.get('startDate', '')
                        end = exp.get('endDate', 'Present') if not exp.get('current', False) else 'Present'
                        exp_text += f" ({start} - {end})"
                    if exp.get('description'):
                        exp_text += f"\n{exp.get('description')}"
                    exp_content.append(exp_text)
            if exp_content:
                enhanced_resume['Work Experience'] = enhance_section("experience", '\n\n'.join(exp_content))

        # Education
        education = data.get('education', [])
        if education:
            edu_content = []
            for edu in education:
                if any([edu.get('degree'), edu.get('field'), edu.get('institution')]):
                    edu_text = f"{edu.get('degree', '')} in {edu.get('field', '')}"
                    if edu.get('institution'):
                        edu_text += f" - {edu.get('institution')}"
                    if edu.get('year'):
                        edu_text += f" ({edu.get('year')})"
                    if edu.get('details'):
                        edu_text += f"\n{edu.get('details')}"
                    edu_content.append(edu_text)
            if edu_content:
                enhanced_resume['Education'] = enhance_section("education", '\n\n'.join(edu_content))

        # Skills
        if data.get('skills'):
            enhanced_resume['Skills'] = enhance_section("skills", data['skills'])

        # Projects
        if data.get('projects'):
            enhanced_resume['Projects'] = enhance_section("projects", data['projects'])

        if not enhanced_resume:
            logger.warning("No content to generate resume")
            return jsonify({'success': False, 'error': 'No content provided to generate resume'}), 400

        filename = save_resume_docx(enhanced_resume)
        logger.info(f"Resume generated successfully: {filename}")

        return jsonify({
            'success': True,
            'message': 'Resume generated successfully',
            'filename': filename
        })

    except Exception as e:
        logger.error(f"Resume generation error: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': f'Failed to generate resume: {str(e)}'}), 500


@app.route("/download")
def download():
    filename = "Enhanced_Resume.docx"
    logger.info(f"Download request for: {filename}")

    if os.path.exists(filename):
        try:
            return send_file(filename, as_attachment=True, download_name=filename)
        except Exception as e:
            logger.error(f"Download error: {str(e)}")
            return jsonify({"error": f"Download failed: {str(e)}"}), 500
    else:
        logger.error(f"File not found: {filename}")
        return jsonify({"error": "File not found. Please generate a resume first."}), 404


@app.route("/health")
def health():
    logger.info("Health check requested")

    health_status = {
        'status': 'healthy',
        'groq_configured': bool(client),
        'groq_api_key_present': bool(GROQ_API_KEY),
        'model': GROQ_MODEL,
        'endpoints': ['/enhance', '/generate_resume', '/download', '/health'],
        'server_time': str(__import__('datetime').datetime.now())
    }

    # Test Groq connection
    if client:
        try:
            test_response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1
            )
            health_status['groq_status'] = 'connected'
        except Exception as e:
            health_status['groq_status'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
    else:
        health_status['groq_status'] = 'not_configured'
        health_status['status'] = 'degraded'

    logger.info(f"Health status: {health_status['status']}")
    return jsonify(health_status)


@app.route("/test", methods=["GET", "POST"])
def test_endpoint():
    """Simple test endpoint for debugging"""
    logger.info(f"Test endpoint hit with method: {request.method}")

    if request.method == "POST":
        try:
            data = request.get_json()
            logger.debug(f"Test POST data: {data}")
            return jsonify({
                'success': True,
                'message': 'Test endpoint working',
                'received_data': data,
                'method': 'POST'
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e),
                'method': 'POST'
            })
    else:
        return jsonify({
            'success': True,
            'message': 'Test endpoint working',
            'method': 'GET',
            'server_status': 'running'
        })


# -------------------------------
# Error Handlers
# -------------------------------
@app.errorhandler(404)
def not_found_error(error):
    logger.warning(f"404 error for path: {request.path}")
    return jsonify({'error': 'Endpoint not found', 'path': request.path}), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


@app.errorhandler(405)
def method_not_allowed(error):
    logger.warning(f"405 error: Method {request.method} not allowed for {request.path}")
    return jsonify({'error': f'Method {request.method} not allowed'}), 405


# -------------------------------
# Run Server
# -------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("🚀 Starting Resume Builder (Groq-powered)")
    print("=" * 60)
    print(f"📡 Server running at: http://localhost:5000")
    print(f"🤖 Model: {GROQ_MODEL}")
    print(f"🔑 API Key: {'✅ Configured' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🔗 Groq Client: {'✅ Connected' if client else '❌ Failed'}")
    print("=" * 60)
    print("📍 Available endpoints:")
    print("   GET  /              - Frontend")
    print("   GET  /health        - Health check")
    print("   POST /enhance       - AI enhancement")
    print("   POST /generate_resume - Generate DOCX")
    print("   GET  /download      - Download resume")
    print("   GET/POST /test      - Test endpoint")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)