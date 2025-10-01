from flask import Flask, request, send_file, jsonify, send_from_directory
from flask_cors import CORS
from groq import Groq
from docx import Document
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib.colors import HexColor
import os
import traceback
import logging
import time
import uuid
import re
import json

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# CORS configuration
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

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
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        logger.info(f"Groq API connected successfully with model: {GROQ_MODEL}")
    except Exception as e:
        logger.error(f"Groq API connection failed: {e}")
        client = None
else:
    logger.error("No GROQ_API_KEY found")

# Resume Enhancement Prompts
GLOBAL_RULES = [
    "Use a professional, employer-focused tone.",
    "Do not use first-person pronouns.",
    "Be concise, quantifiable, and clear.",
    "Fix grammar, avoid redundancy.",
    "Do not invent experiences or education.",
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
        "Objective: Enhance the Work Experience section to highlight achievements, measurable impact, and transferable skills.\n"
        "Instruction 1: Rewrite each role in 70–120 words.\n"
        "Instruction 2: Use 3–5 concise bullet points per role to describe responsibilities, contributions, and achievements.\n"
        "Instruction 3: Start each bullet with a strong action verb (e.g., Managed, Led, Optimized, Implemented, Streamlined).\n"
        "Instruction 4: Quantify achievements wherever possible (numbers, percentages, or measurable outcomes) to demonstrate impact.\n"
        "Instruction 5: Highlight transferable skills and relevant expertise aligned with the targeted job description and ATS keywords.\n"
        "Instruction 6: Use plain-text, ATS-friendly bullets (dash - or •); avoid +, *, or markdown formatting.\n"
        "Instruction 7: Keep language professional, concise, and factual; avoid personal pronouns, opinions, or unnecessary details.\n"
        "Instruction 8: Ensure clarity, proper grammar, and polished formatting.\n"
        "Instruction 9: Return only the single best, fully polished version for the resume.\n"
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
        "Objective: Improve the Education section to clearly showcase qualifications relevant to the targeted role.\n"
        "Instruction 1: Rewrite in 50–100 words.\n"
        "Instruction 2: Clearly present degrees, certifications, relevant coursework, honors, and any notable academic achievements.\n"
        "Instruction 3: Highlight how the education supports career goals and aligns with the targeted job.\n"
        "Instruction 4: Use concise, professional language; maintain clarity, proper grammar, and factual accuracy.\n"
        "Instruction 5: Ensure formatting is ATS-friendly and easily scannable.\n"
        "Instruction 6: Return only the single best, polished version for the resume.\n"
        "Notes: Follow all Global Resume Rules."
    ),
    "projects": (
        "Role: Expert Resume Consultant\n"
        "Objective: Enhance the Projects section for clarity, relevance, and measurable impact.\n"
        "Instruction 1: For EACH project provided, enhance the title and description separately.\n"
        "Instruction 2: Provide a concise description of the project's purpose, scope, and relevance to the targeted job.\n"
        "Instruction 3: List key skills, technologies, and tools used during the project.\n"
        "Instruction 4: Highlight specific tasks and responsibilities using strong action verbs.\n"
        "Instruction 5: Quantify results and achievements wherever possible to demonstrate measurable impact (e.g., increased efficiency by 15%).\n"
        "Instruction 6: Use concise phrasing for readability and professional presentation.\n"
        "Instruction 7: Tailor descriptions to align with the job description and ATS keywords.\n"
        "Instruction 8: Ensure proper grammar, spelling, and consistent formatting.\n"
        "Instruction 9: Format your response EXACTLY as:\n"
        "Title: [Enhanced Project Title]\n"
        "Description: [Enhanced description in 2-3 sentences]\n"
        "---\n"
        "Instruction 10: Return only the enhanced content, no explanations.\n"
        "Notes: Follow all Global Resume Rules."
    )
}


def sanitize_input(text, max_chars=3000):
    """Clean and limit input text."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    if len(text) > max_chars:
        text = text[:max_chars].rsplit(' ', 1)[0]
    return text


def clean_ai_response(text):
    """Remove common AI response artifacts."""
    if not text:
        return ""

    # Remove code fences
    text = re.sub(r'^```(?:\w+)?\s*|```$', '', text, flags=re.MULTILINE).strip()

    # Remove common preambles
    patterns = [
        r'^(?:Here\'s|Here is|Enhanced version:|Enhanced:|Sure,?.*?:)\s*',
        r'^(?:Certainly|Of course|Absolutely).*?:\s*',
        r'^\*\*.*?\*\*\s*',  # Remove markdown bold headers
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)

    # Remove quotes
    text = re.sub(r'^["\']|["\']$', '', text.strip())

    return text.strip()


def enhance_section(section_name, content, max_retries=2):
    """Enhance a resume section using Groq AI with your specific prompts."""
    if not client:
        logger.error("Groq client not available")
        return content

    section_name = section_name.lower().strip()

    # Handle projects - parse JSON if provided
    if section_name == "projects":
        try:
            projects = json.loads(content)
            if isinstance(projects, list) and projects:
                formatted = "\n\n".join([
                    f"Project {i + 1}:\nTitle: {p.get('title', 'Untitled')}\n"
                    f"Description: {p.get('description', 'No description')}"
                    for i, p in enumerate(projects)
                ])
                content = formatted
        except (json.JSONDecodeError, TypeError):
            pass

    # Sanitize input
    content = sanitize_input(content)
    if not content:
        logger.warning(f"Empty content for section: {section_name}")
        return ""

    # Get the detailed prompt
    prompt_template = resume_prompts.get(section_name, resume_prompts["summary"])

    # Construct full prompt with global rules
    full_prompt = (
        f"{GLOBAL_RULE}\n\n"
        f"{prompt_template}\n\n"
        f"User Input:\n{content}\n\n"
        f"Enhanced Content:"
    )

    # Retry logic with exponential backoff
    for attempt in range(max_retries + 1):
        try:
            logger.info(f"Enhancing {section_name} (attempt {attempt + 1}/{max_retries + 1})")

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert resume consultant. Follow the instructions precisely and return ONLY the enhanced content without any preambles, explanations, or meta-commentary."
                    },
                    {
                        "role": "user",
                        "content": full_prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1024,
                top_p=0.95
            )

            enhanced = response.choices[0].message.content.strip()
            enhanced = clean_ai_response(enhanced)

            if not enhanced:
                raise ValueError("Empty response from AI")

            logger.info(f"Successfully enhanced {section_name} ({len(enhanced)} chars)")
            return enhanced

        except Exception as e:
            logger.error(f"Enhancement failed (attempt {attempt + 1}): {str(e)}")
            if attempt >= max_retries:
                logger.warning(f"Max retries reached, returning original content for {section_name}")
                return content
            time.sleep(1 * (2 ** attempt))

    return content


def format_for_docx(text):
    """Format text into paragraphs for DOCX."""
    if not text:
        return

    text = text.strip()

    # Handle comma-separated lists (skills)
    if ',' in text and '\n' not in text and len(text.split(',')) > 2:
        yield text
        return

    # Split by double newlines or "---"
    for block in re.split(r'\n\s*\n|---', text):
        block = block.strip()
        if not block:
            continue

        lines = [ln.strip() for ln in block.splitlines() if ln.strip()]

        # Check if it's a bullet list
        is_list = all(re.match(r'^[•\-]\s+', ln) for ln in lines if ln)

        if is_list and len(lines) > 1:
            yield '\n'.join(lines)
        else:
            yield ' '.join(lines)


def create_enhanced_docx(resume_data, filename=None):
    """Create a professionally formatted DOCX resume."""
    if not filename:
        filename = f"Resume_{uuid.uuid4().hex[:8]}.docx"

    os.makedirs("generated", exist_ok=True)
    filepath = os.path.join("generated", filename)

    doc = Document()

    # Set default font
    style = doc.styles['Normal']
    font = style.font
    font.name = 'Calibri'
    font.size = Pt(11)

    # Add name as title
    name = resume_data.get('Name', '').strip()
    if name:
        title = doc.add_heading(name, level=0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

    # Section order
    section_order = [
        'Contact Information',
        'Professional Summary',
        'Work Experience',
        'Education',
        'Skills',
        'Projects'
    ]

    # Add sections
    for section_name in section_order:
        content = resume_data.get(section_name, '').strip()
        if not content or content.startswith('['):
            continue

        # Add section heading
        heading = doc.add_heading(section_name, level=1)
        heading_format = heading.runs[0].font
        heading_format.color.rgb = RGBColor(31, 78, 121)

        # Add content
        for paragraph_text in format_for_docx(content):
            para = doc.add_paragraph(paragraph_text)
            para.paragraph_format.space_after = Pt(6)

    doc.save(filepath)
    logger.info(f"DOCX saved: {filepath}")
    return filepath


def create_enhanced_pdf(resume_data, filename=None):
    """Create a professionally formatted PDF resume."""
    if not filename:
        filename = f"Resume_{uuid.uuid4().hex[:8]}.pdf"

    os.makedirs("generated", exist_ok=True)
    filepath = os.path.join("generated", filename)

    doc = SimpleDocTemplate(filepath, pagesize=letter,
                            topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                            leftMargin=0.75 * inch, rightMargin=0.75 * inch)

    # Custom styles
    styles = getSampleStyleSheet()

    # Name style
    name_style = ParagraphStyle(
        'CustomName',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=HexColor('#1F4E79'),
        alignment=TA_CENTER,
        spaceAfter=6
    )

    # Contact style
    contact_style = ParagraphStyle(
        'ContactInfo',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_CENTER,
        spaceAfter=12
    )

    # Section heading style
    section_style = ParagraphStyle(
        'SectionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=HexColor('#1F4E79'),
        spaceBefore=12,
        spaceAfter=6,
        borderWidth=0,
        borderColor=HexColor('#1F4E79'),
        borderPadding=0
    )

    # Body text style
    body_style = ParagraphStyle(
        'BodyText',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=6
    )

    # Build document
    story = []

    # Add name
    name = resume_data.get('Name', '').strip()
    if name:
        story.append(Paragraph(name, name_style))

    # Add contact information
    contact = resume_data.get('Contact Information', '').strip()
    if contact:
        story.append(Paragraph(contact, contact_style))

    story.append(Spacer(1, 0.1 * inch))

    # Section order
    section_order = [
        'Professional Summary',
        'Work Experience',
        'Education',
        'Skills',
        'Projects'
    ]

    # Add sections
    for section_name in section_order:
        content = resume_data.get(section_name, '').strip()
        if not content or content.startswith('['):
            continue

        # Add section heading
        story.append(Paragraph(section_name, section_style))

        # Add content
        # Handle bullet points
        content_lines = content.split('\n')
        for line in content_lines:
            line = line.strip()
            if not line:
                continue

            # Convert bullet points
            if line.startswith('•') or line.startswith('-'):
                line = '&bull; ' + line[1:].strip()

            story.append(Paragraph(line, body_style))

        story.append(Spacer(1, 0.1 * inch))

    # Build PDF
    doc.build(story)
    logger.info(f"PDF saved: {filepath}")
    return filepath


# Routes
@app.route("/")
def index():
    """Serve main page."""
    try:
        return send_from_directory('templates', 'index.html')
    except:
        return jsonify({
            "message": "Resume Builder API",
            "status": "healthy",
            "endpoints": ["/health", "/enhance", "/generate_resume", "/download", "/download_pdf"]
        })


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    status = {
        'status': 'healthy',
        'groq_configured': bool(client),
        'model': GROQ_MODEL,
        'api_key_present': bool(GROQ_API_KEY)
    }

    if client:
        try:
            client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[{"role": "user", "content": "ping"}],
                max_tokens=1
            )
            status['groq_status'] = 'connected'
        except Exception as e:
            status['groq_status'] = f'error: {str(e)}'
            status['status'] = 'degraded'
    else:
        status['groq_status'] = 'not_configured'
        status['status'] = 'degraded'

    return jsonify(status)


@app.route("/enhance", methods=["POST", "OPTIONS"])
def enhance_endpoint():
    """Enhance a single resume section."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        section = data.get('section', '').strip()
        content = data.get('content', '').strip()

        if not section:
            return jsonify({'success': False, 'error': 'Section name required'}), 400

        if not content:
            return jsonify({'success': False, 'error': 'Content required'}), 400

        if not client:
            return jsonify({'success': False, 'error': 'AI service unavailable'}), 503

        logger.info(f"Enhancement request for: {section} ({len(content)} chars)")
        enhanced = enhance_section(section, content)

        return jsonify({
            'success': True,
            'enhanced_content': enhanced,
            'section': section
        })

    except Exception as e:
        logger.error(f"Enhancement error: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/generate_resume", methods=["POST", "OPTIONS"])
def generate_resume():
    """Generate complete enhanced resume in both DOCX and PDF formats."""
    if request.method == "OPTIONS":
        return "", 200

    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data received'}), 400

        resume_data = {}

        # Personal information
        personal = data.get('personal', {})
        if personal.get('fullName'):
            resume_data['Name'] = personal['fullName']

        contact_parts = []
        for field in ['email', 'phone', 'location', 'linkedin']:
            if personal.get(field):
                contact_parts.append(personal[field])
        if contact_parts:
            resume_data['Contact Information'] = ' | '.join(contact_parts)

        if personal.get('summary'):
            logger.info("Enhancing professional summary...")
            resume_data['Professional Summary'] = enhance_section('summary', personal['summary'])

        # Work experience
        experiences = data.get('experiences', [])
        if experiences:
            exp_texts = []
            for exp in experiences:
                if exp.get('title') or exp.get('company'):
                    exp_text = f"{exp.get('title', 'Position')} - {exp.get('company', 'Company')}"
                    if exp.get('startDate'):
                        end = 'Present' if exp.get('current') else exp.get('endDate', '')
                        exp_text += f" ({exp['startDate']} - {end})"
                    if exp.get('description'):
                        exp_text += f"\n{exp['description']}"
                    exp_texts.append(exp_text)
            if exp_texts:
                logger.info("Enhancing work experience...")
                resume_data['Work Experience'] = enhance_section('experience', '\n\n'.join(exp_texts))

        # Education
        education = data.get('education', [])
        if education:
            edu_texts = []
            for edu in education:
                parts = []
                if edu.get('degree'):
                    parts.append(edu['degree'])
                if edu.get('field'):
                    parts.append(f"in {edu['field']}")
                if edu.get('institution'):
                    parts.append(f"- {edu['institution']}")
                if edu.get('year'):
                    parts.append(f"({edu['year']})")
                edu_text = ' '.join(parts)
                if edu.get('details'):
                    edu_text += f"\n{edu['details']}"
                if edu_text:
                    edu_texts.append(edu_text)
            if edu_texts:
                logger.info("Enhancing education...")
                resume_data['Education'] = enhance_section('education', '\n\n'.join(edu_texts))

        # Skills
        if data.get('skills'):
            logger.info("Enhancing skills...")
            resume_data['Skills'] = enhance_section('skills', data['skills'])

        # Projects
        projects_list = data.get('projectsList', [])
        if projects_list:
            logger.info(f"Enhancing {len(projects_list)} projects...")
            resume_data['Projects'] = enhance_section('projects', json.dumps(projects_list))

        if not resume_data:
            return jsonify({'success': False, 'error': 'No content to generate'}), 400

        # Generate both formats
        logger.info("Creating DOCX file...")
        docx_filepath = create_enhanced_docx(resume_data)

        logger.info("Creating PDF file...")
        pdf_filepath = create_enhanced_pdf(resume_data)

        return jsonify({
            'success': True,
            'message': 'Resume generated successfully',
            'filename': os.path.basename(docx_filepath),
            'pdf_filename': os.path.basename(pdf_filepath)
        })

    except Exception as e:
        logger.error(f"Generation error: {str(e)}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route("/download", methods=["GET"])
def download():
    """Download the most recent resume in DOCX format."""
    try:
        if not os.path.exists('generated'):
            return jsonify({"error": "No resumes generated yet"}), 404

        files = [f for f in os.listdir('generated') if f.endswith('.docx')]
        if not files:
            return jsonify({"error": "No resume found"}), 404

        latest = max([os.path.join('generated', f) for f in files], key=os.path.getctime)
        return send_file(latest, as_attachment=True, download_name='Enhanced_Resume.docx')

    except Exception as e:
        logger.error(f"Download error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    """Download the most recent resume in PDF format."""
    try:
        if not os.path.exists('generated'):
            return jsonify({"error": "No resumes generated yet"}), 404

        files = [f for f in os.listdir('generated') if f.endswith('.pdf')]
        if not files:
            return jsonify({"error": "No PDF resume found"}), 404

        latest = max([os.path.join('generated', f) for f in files], key=os.path.getctime)
        return send_file(latest, as_attachment=True, download_name='Enhanced_Resume.pdf')

    except Exception as e:
        logger.error(f"Download PDF error: {str(e)}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 70)
    print("  Resume Builder Backend Server")
    print("=" * 70)
    print(f"  Model: {GROQ_MODEL}")
    print(f"  API Key: {'Configured' if GROQ_API_KEY else 'Missing'}")
    print(f"  Groq Client: {'Connected' if client else 'Failed'}")
    print(f"  Server: http://localhost:5000")
    print(f"  Health Check: http://localhost:5000/health")
    print("=" * 70)

    app.run(debug=True, host='0.0.0.0', port=5000)