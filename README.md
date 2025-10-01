# Professional AI Resume Builder

This project is a web-based resume builder that leverages the Groq AI API to help users craft professional, ATS-friendly resumes. It features a live preview, AI-powered content enhancement for each section, and generates downloadable DOCX and PDF files.

## Features

-   **Intuitive Web Interface**: A single-page application to easily input and manage resume content.
-   **AI-Powered Enhancement**: Utilizes the Groq API (`meta-llama/llama-4-scout-17b-16e-instruct`) to rewrite and improve the summary, work experience, skills, education, and projects sections.
-   **Live Resume Preview**: Instantly see your changes reflected in two different professional templates ('Modern' and 'Professional').
-   **Dynamic Form Sections**: Easily add or remove multiple entries for work experience, education, and projects.
-   **Dual Format Generation**: Generates and downloads the final resume in both `.docx` (via `python-docx`) and `.pdf` (via `reportlab`) formats.
-   **Simple Backend**: Built with Flask, providing a lightweight API for enhancement and file generation.

## Tech Stack

-   **Backend**: Python, Flask, Groq, python-docx, reportlab
-   **Frontend**: HTML, CSS, Vanilla JavaScript

## Project Structure

```
.
├── app.py              # Main Flask application, API endpoints, AI logic
├── templates/
│   └── index.html      # Frontend HTML, CSS, and JavaScript
├── generated/          # Directory for output DOCX and PDF files (auto-created)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

## Getting Started

### Prerequisites

-   Python 3.7+
-   A Groq API Key

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd resume
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Unix/macOS
    python3 -m venv venv
    source venv/bin/activate

    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure API Key:**
    The Groq API key is currently hardcoded in [`app.py`](app.py). For better security, it is recommended to use environment variables.

    ```python
    // filepath: app.py
    // ...existing code...
    # Groq API Configuration
    GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "your_default_key_here")
    // ...existing code...
    ```

### Running the Application

1.  **Start the Flask server:**
    ```bash
    flask run
    ```
    Or
    ```bash
    python app.py
    ```

2.  **Open your browser** and navigate to `http://127.0.0.1:5000`.

## Usage

1.  Fill in your personal information, summary, work experience, and other details in the left-hand panel.
2.  Use the **"Enhance"** buttons to let the AI rewrite and improve the content for a specific section.
3.  As you type, the resume preview on the right will update in real-time.
4.  Once you are satisfied, click the **"Generate & Download Resume"** button. The backend will process all sections, generate both DOCX and PDF files, and your browser will automatically download them.
