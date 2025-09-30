from flask import Flask, request, send_file, jsonify, make_response, send_from_directory,render_template
from flask_cors import CORS
from groq import Groq
from docx import Document
import os
import traceback
import logging
import time
import uuid
import re

from sympy.physics.units import temperature

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Simple CORS configuration
CORS(app, resources={r"/*": {"origins": "*"}})

# Groq API Configuration
GROQ_API_KEY = "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"
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# Initialize Groq client
client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        test_response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": "Hello"}],
            max_tokens=5,
            temperature=0.7
        )
        logger.info(f" Groq API connection successful with model: {GROQ_MODEL}")
        print(f" Groq API Key loaded and tested successfully")
    except Exception as e:
        logger.error(f"Groq API connection failed: {e}")
        print(f" Groq API connection failed: {e}")
        client = None
else:
    logger.error(" No GROQ_API_KEY found")
    print("No GROQ_API_KEY found")

# Resume Enhancement Prompts
GLOBAL_RULES = [
    "Use a professional, employer-focused tone.",
    "Do not use first-person pronouns.",
    "Be concise, quantifiable, and clear.",
    "Fix grammar, avoid redundancy.",
    "Do not invent experiences or education.",
    "Do not output anything else other than the output that goes inside a particular section; no commentaries of any sort."
]

GLOBAL_RULE = "Global Resume Rules:\n" + "\n".join(f"{i + 1}. {rule}" for i, rule in enumerate(GLOBAL_RULES)) + "\n"

resume_prompts = {

    "summary": (
        "Role: Expert Resume Consultant\n"
        "Objective: Craft a highly professional, targeted Resume Summary.\n"
        "Instruction 1: Rewrite the summary in 50–70 words (2–4 concise sentences).\n"
        "Instruction 2: Start with the professional title and years of relevant experience.\n"
        "Instruction 3: Highlight top skills, key strengths, career goals, and 1–2 measurable achievements if possible.\n"
        "Instruction 4: Use strong, varied, and descriptive professional adjectives (e.g., results-driven, dynamic, dedicated, strategic, proactive, detail-oriented) to convey expertise and impact, while maintaining a factual, concise, and highly professional tone.\n"
        "Instruction 5: Tailor language to align with the targeted job description and ATS keywords.\n"
        "Instruction 6: Avoid first-person pronouns, personal opinions, or unnecessary details.\n"
        "Instruction 7: Ensure clarity, grammatical accuracy, and conciseness.\n"
        "Instruction 8: Return only the single best, polished version for the resume.\n"
        "Notes: Follow all Global Resume Rules."
    ),
    "experience": (
        "Role: Expert Resume Consultant\n"
        "Objective: Enhance the Work Experience section.\n"
        "Instruction 1: Rewrite experience in 70–120 words.\n"
        "Instruction 2: Use 3–5 bullet points per role; start each bullet with a strong action verb (e.g., Managed, Led, Improved).\n"
        "Instruction 3: Quantify achievements wherever possible; emphasize measurable outcomes and transferable skills.\n"
        "Instruction 4: Ensure ATS-friendly plain-text bullets (dash or •), avoid +, *, or markdown symbols.\n"
        "Instruction 5: Return only the single best version for the resume.\n"
        "Notes: Follow all Global Resume Rules."
    ),
    "skills": (
        "Role: Expert Resume Consultant\n"
        "Objective: Refine the Skills section for ATS optimization and employer appeal.\n"
        "Instruction 1: Rewrite as a concise list, limited to 10–15 core skills, using comma-separated format or grouped categories (e.g., Technical Skills, Soft Skills, Certifications).\n"
        "Instruction 2: Prioritize hard skills, technical competencies, certifications, and industry-specific terminology mentioned in the job description.\n"
        "Instruction 3: Use exact keywords and phrases from the posting, including both spelled-out and acronym forms (e.g., Search Engine Optimization (SEO)).\n"
        "Instruction 4: Avoid vague or outdated terms; keep all skills current, specific, and relevant to the targeted job.\n"
        "Instruction 5: Eliminate redundancy and ensure logical grouping for easy readability.\n"
        "Instruction 6: Integrate the most critical skills naturally in both this section and throughout work experience, avoiding keyword stuffing.\n"
        "Instruction 7: Ensure formatting is consistent, professional, and ATS-friendly.\n"
        "Instruction 8: Return only the single best version for the resume.\n"
        "Notes: Follow all Global Resume Rules."

    ),
    "education": (
        "Role: Expert Resume Consultant\n"
        "Objective: Improve the Education section.\n"
        "Instruction 1: Rewrite in 50–100 words.\n"
        "Instruction 2: Clearly present degree, university/college, dates, certifications, and relevant coursework.\n"
        "Instruction 3: Focus on what supports career goals; concise and factual sentences.\n"
        "Instruction 4: Return only the single best version for the resume.\n"
        "Notes: Follow all Global Resume Rules."
    ),
    "projects": (
        "Role: Expert Resume Consultant\n"
        "Objective: Enhance the Projects section to maximize relevance, clarity, and measurable impact for ATS and hiring managers.\n"
        "Instruction 1: Include Project Name, Role, and Dates/Duration.\n"
        "Instruction 2: List only projects relevant to the targeted job, prioritizing by impact.\n"
        "Instruction 3: Clearly state technologies, tools, or skills used (optional but recommended).\n"
        "Instruction 4: Use 50–100 words per project; provide concise bullet points for contributions, responsibilities, and achievements.\n"
        "Instruction 5: Start bullets with strong action verbs; apply PAR formula (Problem, Action, Result) wherever possible.\n"
        "Instruction 6: Quantify results and achievements with numbers, percentages, or measurable outcomes.\n"
        "Instruction 7: Include hyperlinks to online projects or portfolios with clean, descriptive text.\n"
        "Instruction 8: Use plain-text bullets (dash - or •); avoid +, *, or markdown formatting.\n"
        "Instruction 9: Keep language clear, professional, and tailored to the job description.\n"
        "Instruction 10: Limit bullets to 3–5 per project; ensure ATS-friendly formatting.\n"
        "Instruction 11: Return only the single best version for the resume.\n"
        "Notes: Follow all Global Resume Rules."
    )
}



def _safe_response_content(response):
    """Extract text from Groq response."""
    try:
        return response.choices[0].message.content.strip()
    except Exception:
        return ""


def _sanitize_input(text, max_chars=3000):
    """Trim and sanitize input."""
    if not text:
        return ""
    s = re.sub(r'\s+', ' ', text).strip()
    if len(s) > max_chars:
        s = s[:max_chars].rsplit(' ', 1)[0]
    return s


def enhance_section(section_name, user_input, max_retries=2):
    """Enhance a resume section using Groq AI."""
    section_name = (section_name or "").strip()
    cleaned_input = _sanitize_input(user_input)

    if not cleaned_input:
        logger.warning("Empty input for section: %s", section_name)
        return f"[{section_name.title()} section not provided.]"

    if not client:
        logger.error("Groq client not available")
        return cleaned_input

    prompt_body = resume_prompts.get(section_name.lower(), "")
    prompt = (
        f"{GLOBAL_RULE}\n\n"
        f"{prompt_body}\n\n"
        "IMPORTANT: Return only plain text, no JSON, markdown, or code fences.\n\n"
        f"User Input:\n{cleaned_input}\n\nEnhanced Content:"
    )

    for attempt in range(max_retries + 1):
        try:
            logger.debug("Groq request attempt %d for section: %s", attempt + 1, section_name)
            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system",
                     "content": "You are an expert resume consultant. Improve the given content professionally."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=800
            )

            enhanced_content = _safe_response_content(response)
            if not enhanced_content:
                raise ValueError("Empty response from model")

            # Clean response
            enhanced_content = re.sub(r"^```(?:\w+)?\s*|```$", "", enhanced_content).strip()
            enhanced_content = re.sub(r"^\"|\"$", "", enhanced_content).strip()

            logger.info("Successfully enhanced section: %s", section_name)
            return enhanced_content

        except Exception as e:
            logger.error("Groq API failed (attempt %d): %s", attempt + 1, str(e))
            if attempt >= max_retries:
                return cleaned_input
            time.sleep(1 * (2 ** attempt))


def _format_paragraphs_for_doc(text):
    """Format text into paragraphs for DOCX."""
    text = text.strip()
    if ',' in text and '\n' not in text and len(text.split(',')) > 1 and len(text) < 200:
        yield text
        return

    for block in re.split(r'\n\s*\n', text):
        block = block.strip()
        if not block:
            continue
        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]
        if all(re.match(r'^(\-|\*|\d+\.)\s+', ln) for ln in lines) and len(lines) > 1:
            yield '\n'.join(lines)
        else:
            yield ' '.join(lines)


def save_resume_docx(enhanced_resume, filename=None):
    """Save enhanced resume to DOCX file."""
    try:
        if not filename:
            filename = f"Enhanced_Resume_{uuid.uuid4().hex[:8]}.docx"
        os.makedirs("generated", exist_ok=True)
        filepath = os.path.join("generated", filename)

        doc = Document()

        name = enhanced_resume.get('Name') or enhanced_resume.get('name')
        if name and isinstance(name, str) and name.strip():
            doc.add_heading(name.strip(), level=0)

        order = [
            'Contact Information', 'Professional Summary', 'Work Experience',
            'Education', 'Skills', 'Projects'
        ]
        remaining = [k for k in enhanced_resume.keys() if k not in order and k != 'Name']
        ordered_keys = [k for k in order if k in enhanced_resume] + remaining

        for section in ordered_keys:
            text = enhanced_resume.get(section)
            if not text:
                continue
            text = text.strip()
            if text.startswith('[') and text.endswith('section not provided.]'):
                continue

            doc.add_heading(section.replace('_', ' ').title(), level=1)

            for paragraph in _format_paragraphs_for_doc(text):
                if '\n' in paragraph and any(re.match(r'^(\-|\*|\d+\.)\s+', ln) for ln in paragraph.splitlines()):
                    for ln in paragraph.splitlines():
                        doc.add_paragraph(ln)
                else:
                    doc.add_paragraph(paragraph)

        doc.save(filepath)
        logger.info("DOCX file saved: %s", filepath)
        return filepath
    except Exception as e:
        logger.error("Failed to create DOCX: %s", str(e))
        traceback.print_exc()
        raise


# Routes
@app.route("/")
def index():
    """Serve the main page."""
    return render_template("index.html")


@app.route("/enhance", methods=["POST", "OPTIONS"])
def enhance_ajax():
    """Enhance a resume section."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        section_name = data.get('section')
        content = data.get('content')

        if not section_name:
            return jsonify({'success': False, 'error': 'Missing section name'}), 400

        if not client:
            return jsonify({'success': False, 'error': 'AI service not available'}), 500

        enhanced_content = enhance_section(section_name, content or "")

        return jsonify({
            'success': True,
            'enhanced_content': enhanced_content,
            'section': section_name
        })

    except Exception as e:
        logger.error(f"Enhancement error: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/generate_resume", methods=["POST", "OPTIONS"])
def generate_resume():
    """Generate complete resume DOCX."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        enhanced_resume = {}

        # Personal info
        personal_info = data.get('personal', {})
        if personal_info:
            contact_info = [personal_info.get(field) for field in ['email', 'phone', 'location', 'linkedin'] if
                            personal_info.get(field)]
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
                        end = exp.get('endDate', 'Present') if not exp.get('current') else 'Present'
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

        # Skills and Projects
        if data.get('skills'):
            enhanced_resume['Skills'] = enhance_section("skills", data['skills'])
        if data.get('projects'):
            enhanced_resume['Projects'] = enhance_section("projects", data['projects'])

        if not enhanced_resume:
            return jsonify({'success': False, 'error': 'No content to generate'}), 400

        filename = save_resume_docx(enhanced_resume)

        return jsonify({
            'success': True,
            'message': 'Resume generated successfully',
            'filename': os.path.basename(filename)
        })

    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/download")
def download():
    """Download generated resume."""
    try:
        files = [f for f in os.listdir('generated') if f.endswith('.docx')]
        if not files:
            return jsonify({"error": "No resume found. Generate one first."}), 404

        latest_file = max([os.path.join('generated', f) for f in files], key=os.path.getctime)
        return send_file(latest_file, as_attachment=True, download_name='Enhanced_Resume.docx')
    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/health")
def health():
    """Health check endpoint."""
    health_status = {
        'status': 'healthy',
        'groq_configured': bool(client),
        'model': GROQ_MODEL,
        'endpoints': ['/enhance', '/generate_resume', '/download', '/health']
    }

    if client:
        try:
            client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                temperature=0.7
            )
            health_status['groq_status'] = 'connected'
        except Exception as e:
            health_status['groq_status'] = f'error: {str(e)}'
            health_status['status'] = 'degraded'
    else:
        health_status['groq_status'] = 'not_configured'
        health_status['status'] = 'degraded'

    return jsonify(health_status)


if __name__ == "__main__":
    print("=" * 60)
    print("Resume Builder Server Starting")
    print("=" * 60)
    print(f"🤖 Model: {GROQ_MODEL}")
    print(f"🔑 API Key: {' Configured' if GROQ_API_KEY else '❌ Missing'}")
    print(f"🔗 Groq Client: {'Connected' if client else '❌ Failed'}")
    print(f"🌐 Server: http://localhost:5000")
    print("=" * 60)

    app.run(debug=True, host='0.0.0.0', port=5000)