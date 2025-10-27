# 📄 Professional Resume Builder

An AI-powered resume builder that helps you create stunning, ATS-friendly resumes with intelligent content enhancement using Groq AI.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![Flask](https://img.shields.io/badge/flask-3.0.0-green.svg)

## ✨ Features

- 🤖 **AI-Powered Enhancement**: Leverages Groq AI (LLaMA 4 Scout) to enhance resume content
- 📝 **Multiple Sections**: Personal info, work experience, education, skills, and projects
- 🎨 **6 Professional Templates**: Modern, Professional, Executive, Creative, Minimalist, and Custom Designer
- 🎨 **Custom Design Tool**: Real-time visual customization with 11+ design controls
- 📱 **Real-time Preview**: See your resume as you build it with live updates
- 📊 **Progress Tracking**: Visual progress bar to track completion
- 💾 **Export Options**: Download as DOCX and PDF formats
- ✅ **ATS-Optimized**: Content formatted to pass Applicant Tracking Systems
- 🎯 **Dynamic API Configuration**: Automatically adapts to different server origins
- 💡 **Enhanced Prompts**: Industry-standard STAR/CAR methodology for achievements

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- pip (Python package installer)
- Groq API key ([Get one here](https://console.groq.com))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/archanashakyaa/resume-bsi.git
   cd resume-bsi
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   
   Or install packages individually:
   ```bash
   pip install flask flask-cors groq python-docx reportlab
   ```

3. **Configure API Key**
   
   Open `app.py` and update the Groq API key (line 41):
   ```python
   GROQ_API_KEY = "your_groq_api_key_here"
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open in browser**
   
   Navigate to: `http://localhost:5002`
   
   > **Note**: The default port is now 5002 (changed from 5000 to avoid common port conflicts)

## 📁 Project Structure

```
resume-bsi/
├── app.py                  # Flask backend server
├── requirements.txt        # Python dependencies
├── static/                 # Static assets
│   ├── styles.css         # All CSS styling (700+ lines, 6 templates)
│   └── script.js          # Frontend JavaScript (860+ lines)
├── templates/              # HTML templates
│   ├── index.html         # Main application page (440+ lines)
│   └── index_old.html     # Backup of original file
├── generated/              # Generated resume files (auto-created)
│   ├── *.docx            # Word documents
│   └── *.pdf             # PDF documents
├── server.log             # Server logs (when running with nohup)
└── README.md              # This file
```

## 🎯 Usage

### Building Your Resume

1. **Personal Information**
   - Enter your full name, email, phone, location, and LinkedIn profile
   - Add a professional summary
   - Click "Enhance Summary" to improve your summary with AI

2. **Work Experience**
   - Click "Add Experience" to add work history
   - Fill in job title, company, dates, and description
   - Click "Enhance" button on individual experiences for AI improvement

3. **Education**
   - Add your degrees, institutions, and graduation years
   - Include additional details like GPA or honors

4. **Skills**
   - Add comma-separated skills
   - Use "Enhance Skills" for ATS-optimized keyword suggestions

5. **Projects**
   - Add project titles and descriptions
   - Click "Enhance Projects" to improve all project descriptions

6. **Choose Your Template**
   - Switch between 6 professional templates using the dropdown:
     - **Modern**: Clean gradient header with contemporary styling
     - **Professional**: Traditional business format with blue accents
     - **Executive**: Sophisticated design for senior positions
     - **Creative**: Bold, colorful style for creative fields
     - **Minimalist**: Simple black-and-white aesthetic
     - **Custom Designer**: Visual design tool with 11+ customization options

7. **Custom Designer Features** (when Custom template is selected)
   - **Header Style**: 4 options (gradient, solid, minimal, bordered)
   - **Colors**: Primary, secondary, and text color pickers
   - **Typography**: Font family and size controls
   - **Layout**: Spacing and density adjustments
   - **Section Headers**: 4 styles (underline, background, left-border, box)
   - **Borders**: 5 types (none, light, medium, bold, dashed)
   - **Skills Display**: 4 modes (pills, badges, list, grid)
   - **Save/Reset/Export**: Persistent design configurations in localStorage

8. **Generate & Download**
   - Review your resume in the live preview panel
   - Click "Generate & Download Resume" to create DOCX and PDF files

### AI Enhancement Features

The AI enhancement uses carefully crafted prompts to:

- **Summary**: Create concise, impactful 50-70 word professional summaries
- **Experience**: Transform bullet points into achievement-focused narratives with CAR/STAR methodology
- **Skills**: Optimize for ATS with industry-specific keywords
- **Education**: Highlight relevant qualifications and achievements
- **Projects**: Emphasize technical skills, impact, and measurable results

## 🔧 Configuration

### Groq AI Model

The application uses `meta-llama/llama-4-scout-17b-16e-instruct` by default. You can change the model in `app.py`:

```python
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
```

### Server Configuration

- **Host**: `0.0.0.0` (accessible from all network interfaces)
- **Port**: `5002` (changed from 5000 to avoid conflicts)
- **Debug Mode**: Enabled (disable for production)

Change these settings at the bottom of `app.py`:

```python
if __name__ == "__main__":
    PORT = 5002  # Changed from 5000 to avoid conflicts
    app.run(debug=True, host='0.0.0.0', port=PORT)
```

### Frontend API Configuration

The frontend automatically adapts to the server's origin:

```javascript
// In static/script.js
const API_BASE_URL = (typeof window !== 'undefined' && window.location && window.location.origin)
    ? window.location.origin
    : 'http://localhost:5002';
```

This prevents connection errors when accessing from different IPs or hostnames.

## 🌐 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serve the main application page |
| `/health` | GET | Health check endpoint |
| `/enhance` | POST | Enhance resume section with AI |
| `/generate_resume` | POST | Generate DOCX and PDF resumes |
| `/download` | GET | Download latest DOCX file |
| `/download_pdf` | GET | Download latest PDF file |

### Example API Request

```javascript
// Enhance a resume section
fetch('http://localhost:5002/enhance', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        section: 'summary',
        content: 'Your original summary text here'
    })
});
```

## 🎨 Template Customization

### Modifying Styles

Edit `static/styles.css` to customize:
- Colors and gradients
- Font sizes and families
- Layout and spacing
- Animations and transitions

### Adding New Templates

1. Add template HTML in `templates/index.html` preview section
2. Add corresponding styles in `static/styles.css`
3. Update template switcher in `static/script.js` `switchTemplate()` function
4. Add preview update functions for the new template

### Custom Designer

The Custom Designer template allows users to:
- Modify header styles (gradient, solid, minimal, bordered)
- Choose custom colors with color pickers
- Adjust typography (font family, size)
- Control layout density (compact, normal, spacious)
- Customize section header styles
- Change border styles and widths
- Select skills display formats
- Save and export design configurations

## 🛠️ Technologies Used

- **Backend**: Flask (Python web framework)
- **AI**: Groq AI with LLaMA 4 Scout model
- **Document Generation**: 
  - python-docx (Word documents)
  - ReportLab (PDF documents)
- **Frontend**: 
  - Vanilla JavaScript (ES6+)
  - CSS3 with animations
  - Responsive design
- **CORS**: Flask-CORS for cross-origin requests

## 📊 Resume Enhancement Methodology

### STAR/CAR Framework

The AI enhancement follows proven resume writing methodologies:

- **S**ituation: Context of the challenge
- **T**ask: Responsibility or assignment
- **A**ction: Steps taken to address the task
- **R**esult: Measurable outcomes and impact

### ATS Optimization

- Keywords from job descriptions
- Clean, parseable formatting
- Standard section headings
- Quantifiable achievements
- Industry-specific terminology

## 🔍 Troubleshooting

### Server Won't Start - Port Already in Use

If you see "Address already in use" error:

```bash
# Option 1: Kill process on port 5002
lsof -ti:5002 | xargs kill -9

# Option 2: Change port in app.py
# Edit the PORT variable at the bottom of app.py
PORT = 5003  # or any available port
```

### Template Not Responding to Input

If the preview doesn't update when you type:

1. Open browser DevTools (F12) and check Console for JavaScript errors
2. Verify `updatePreview()` function exists in `static/script.js`
3. Clear browser cache and reload (Ctrl+Shift+R)
4. Check that event listeners are attached in `initializeEventListeners()`

### Backend Connection Failed

If frontend shows "Failed to connect to backend":

1. Verify Flask server is running (`ps aux | grep "python.*app.py"`)
2. Check health endpoint: `curl http://localhost:5002/health`
3. Ensure frontend is using correct port (check browser DevTools Network tab)
4. Verify `API_BASE_URL` in `static/script.js` is set correctly

### CSS Not Loading

If styles aren't appearing:
```bash
# Verify static files exist
ls -la static/

# Check Flask is using render_template (not send_from_directory)
grep "render_template" app.py
```

### API Key Issues

If you see "Invalid API Key" errors:
1. Verify your Groq API key is correct
2. Check the API key hasn't expired
3. Ensure you have API credits remaining
4. Test the API key: `curl https://api.groq.com/openai/v1/models -H "Authorization: Bearer YOUR_API_KEY"`

### Enhancement Not Working

If AI enhancement fails:
1. Check Groq API connection in server logs (`tail -f server.log`)
2. Verify you have content in the section before enhancing
3. Check network connectivity
4. Review browser console for JavaScript errors
5. Ensure you're not being rate-limited by Groq API

## 📝 Best Practices

1. **Content First**: Write your basic content before using AI enhancement
2. **Review AI Output**: Always review and customize AI-generated content
3. **Be Specific**: Provide detailed descriptions for better AI results
4. **Quantify**: Include numbers and metrics in your original content
5. **Iterate**: Enhance multiple times and pick the best version
6. **Proofread**: Always proofread before downloading final documents

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- [Groq](https://groq.com/) for providing fast AI inference
- [Flask](https://flask.palletsprojects.com/) for the web framework
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [python-docx](https://python-docx.readthedocs.io/) for DOCX creation

## 📧 Contact

**Archana Shakya**
- GitHub: [@archanashakyaa](https://github.com/archanashakyaa)
- Repository: [resume-bsi](https://github.com/archanashakyaa/resume-bsi)

## 🔮 Future Enhancements

- [x] Multiple resume templates (6 templates implemented)
- [x] Custom design tool with visual controls
- [x] Dynamic API configuration for different origins
- [x] Enhanced AI prompts with STAR/CAR methodology
- [ ] Multiple AI model support
- [ ] Cover letter generation
- [ ] LinkedIn profile import
- [ ] Resume analysis and scoring
- [ ] Multi-language support
- [ ] Cloud storage integration
- [ ] User authentication and saving
- [ ] Resume versioning
- [ ] Job description matching
- [ ] Dark mode support
- [ ] Export to additional formats (LaTeX, HTML)

---

**Made with ❤️ by Archana Shakya**
