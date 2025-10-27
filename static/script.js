// Backend API Configuration
// Use the same origin the page was served from to avoid localhost/IP mismatches
// and mixed-content issues. Fall back to localhost:5001 when window is not available.
const API_BASE_URL = (typeof window !== 'undefined' && window.location && window.location.origin)
    ? window.location.origin
    : 'http://localhost:5002';

let resumeData = {
    personal: { fullName: '', email: '', phone: '', location: '', linkedin: '', summary: '' },
    experiences: [],
    education: [],
    skills: '',
    projectsList: []
};

let experienceCounter = 0;
let educationCounter = 0;
let projectCounter = 0;
let isEnhancing = false;

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.className = `toast ${type}`;
    toast.classList.add('show');
    setTimeout(() => toast.classList.remove('show'), 3000);
}

function showLoading(show = true) {
    document.getElementById('loadingOverlay').style.display = show ? 'flex' : 'none';
}

async function generateAndDownload() {
    // 1. Validate that essential information exists.
    if (!resumeData.personal.fullName || !resumeData.personal.email) {
        showToast('Please fill in at least your Name and Email before generating.', 'error');
        return;
    }

    // 2. Show a loading indicator to the user.
    showLoading(true, 'Generating Resume...', 'AI is enhancing and formatting your document.');

    try {
        // 3. Call the backend's /generate_resume endpoint.
        const response = await fetch(`${API_BASE_URL}/generate_resume`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(resumeData) // Send all current resume data.
        });

        const result = await response.json();

        // 4. Check if the generation was successful.
        if (!response.ok || !result.success) {
            throw new Error(result.error || 'Failed to generate resume on the server.');
        }

        // 5. If successful, trigger the downloads.
        showToast('Resume generated! Downloads will start shortly.', 'success');

        // Trigger DOCX download by navigating to the download URL.
        window.location.href = `${API_BASE_URL}/download`;

        // Trigger PDF download after a short delay to ensure both start.
        setTimeout(() => {
            window.location.href = `${API_BASE_URL}/download_pdf`;
        }, 1000);

    } catch (error) {
        // 6. Show an error message if anything fails.
        console.error('Generation and download error:', error);
        showToast(error.message, 'error');
    } finally {
        // 7. Always hide the loading indicator.
        showLoading(false);
    }
}

function updateProgress() {
    const requiredFields = [
        resumeData.personal.fullName,
        resumeData.personal.email,
        resumeData.personal.summary,
        resumeData.experiences.length > 0,
        resumeData.education.length > 0,
        resumeData.skills
    ];
    const completed = requiredFields.filter(Boolean).length;
    const percentage = (completed / requiredFields.length) * 100;
    document.getElementById('progressBar').style.width = `${percentage}%`;
}

// AI Enhancement Function
async function enhanceSection(sectionName) {
    if (isEnhancing) {
        showToast('Please wait for current enhancement to complete', 'error');
        return;
    }

    let content = '';
    let fieldElement = null;

    switch (sectionName) {
        case 'summary':
            fieldElement = document.getElementById('summary');
            content = fieldElement.value.trim();
            break;
        case 'skills':
            fieldElement = document.getElementById('skills');
            content = fieldElement.value.trim();
            break;
        case 'projects':
            if (resumeData.projectsList.length === 0) {
                showToast('Please add at least one project first', 'error');
                return;
            }
            content = resumeData.projectsList.map(p =>
                `Title: ${p.title}\nDescription: ${p.description}`
            ).join('\n---\n');
            break;
    }

    if (!content) {
        showToast(`Please add ${sectionName} content first`, 'error');
        return;
    }

    try {
        isEnhancing = true;
        showLoading(true);

        const response = await fetch(`${API_BASE_URL}/enhance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                section: sectionName,
                content: content
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            if (sectionName === 'projects') {
                try {
                    // Try to parse as JSON first
                    let enhanced;
                    if (data.enhanced.trim().startsWith('[') || data.enhanced.trim().startsWith('{')) {
                        enhanced = JSON.parse(data.enhanced);
                    } else {
                        // Parse text format
                        const projects = data.enhanced.split('---').map(proj => {
                            const lines = proj.trim().split('\n');
                            let title = '';
                            let description = '';

                            lines.forEach(line => {
                                if (line.toLowerCase().startsWith('title:')) {
                                    title = line.substring(line.indexOf(':') + 1).trim();
                                } else if (line.toLowerCase().startsWith('description:')) {
                                    description = line.substring(line.indexOf(':') + 1).trim();
                                } else if (description) {
                                    description += ' ' + line.trim();
                                }
                            });

                            return { title, description };
                        }).filter(p => p.title || p.description);

                        enhanced = projects;
                    }

                    const projectItems = document.querySelectorAll('#projectsContainer .dynamic-item');
                    enhanced.forEach((proj, idx) => {
                        if (projectItems[idx]) {
                            if (proj.title) {
                                projectItems[idx].querySelector('.proj-title').value = proj.title;
                            }
                            if (proj.description) {
                                projectItems[idx].querySelector('.proj-description').value = proj.description;
                            }
                        }
                    });
                    updateProjectData();
                } catch (parseError) {
                    console.error('Parse error:', parseError);
                    showToast('Error parsing enhanced projects. Try again.', 'error');
                    return;
                }
            } else {
                fieldElement.value = data.enhanced;
                updateResumeData();
            }
            showToast(`${sectionName.charAt(0).toUpperCase() + sectionName.slice(1)} enhanced successfully!`);
        } else {
            showToast(data.error || 'Enhancement failed', 'error');
        }
    } catch (error) {
        console.error('Enhancement error:', error);
        showToast('Failed to connect to backend. Make sure Flask server is running on port 5002.', 'error');
    } finally {
        isEnhancing = false;
        showLoading(false);
    }
}

// Enhance individual experience description
async function enhanceExperienceDescription(button) {
    if (isEnhancing) {
        showToast('Please wait for current enhancement to complete', 'error');
        return;
    }

    const experienceItem = button.closest('.dynamic-item');
    const descriptionField = experienceItem.querySelector('.exp-description');
    const content = descriptionField.value.trim();

    if (!content) {
        showToast('Please add experience description first', 'error');
        return;
    }

    try {
        isEnhancing = true;
        button.disabled = true;
        button.textContent = 'Enhancing...';

        const response = await fetch(`${API_BASE_URL}/enhance`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                section: 'experience',
                content: content
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (data.success) {
            descriptionField.value = data.enhanced;
            updateExperienceData();
            showToast('Experience description enhanced!');
        } else {
            showToast(data.error || 'Enhancement failed', 'error');
        }
    } catch (error) {
        console.error('Enhancement error:', error);
        showToast('Failed to enhance. Check if backend is running.', 'error');
    } finally {
        isEnhancing = false;
        button.disabled = false;
        button.textContent = 'Enhance';
    }
}

function addExperience() {
    experienceCounter++;
    const container = document.getElementById('experienceContainer');
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const experienceDiv = document.createElement('div');
    experienceDiv.className = 'dynamic-item';
    experienceDiv.innerHTML = `
        <div class="item-header">
            <h4 class="item-title">Experience ${experienceCounter}</h4>
            <div style="display: flex; gap: 0.5rem;">
                <button type="button" class="btn btn-enhance" onclick="enhanceExperienceDescription(this)">
                    Enhance
                </button>
                <button type="button" class="btn btn-remove" onclick="removeExperience(this)">Remove</button>
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Job Title</label>
                <input type="text" class="exp-title" placeholder="Software Engineer" onchange="updateExperienceData()">
            </div>
            <div class="form-group">
                <label>Company</label>
                <input type="text" class="exp-company" placeholder="Tech Corp" onchange="updateExperienceData()">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Start Date</label>
                <input type="month" class="exp-start" onchange="updateExperienceData()">
            </div>
            <div class="form-group">
                <label>End Date</label>
                <input type="month" class="exp-end" onchange="updateExperienceData()">
                <label style="margin-top: 0.5rem;">
                    <input type="checkbox" class="exp-current" onchange="toggleCurrentJob(this)"> Currently employed
                </label>
            </div>
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea class="exp-description" placeholder="• Developed web applications&#10;• Led team projects" onchange="updateExperienceData()"></textarea>
        </div>
    `;
    container.appendChild(experienceDiv);
    resumeData.experiences.push({ id: experienceCounter, title: '', company: '', startDate: '', endDate: '', current: false, description: '' });
    updatePreview();
}

function removeExperience(button) {
    const experienceItem = button.closest('.dynamic-item');
    const index = Array.from(experienceItem.parentNode.children).indexOf(experienceItem);
    if (index >= 0 && index < resumeData.experiences.length) {
        resumeData.experiences.splice(index, 1);
    }
    experienceItem.remove();
    const container = document.getElementById('experienceContainer');
    if (container.children.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">💼</div><p>No work experience added yet</p></div>';
    }
    updatePreview();
}

function updateExperienceData() {
    const experienceItems = document.querySelectorAll('#experienceContainer .dynamic-item');
    resumeData.experiences = [];
    experienceItems.forEach((item, index) => {
        resumeData.experiences.push({
            id: index + 1,
            title: item.querySelector('.exp-title').value,
            company: item.querySelector('.exp-company').value,
            startDate: item.querySelector('.exp-start').value,
            endDate: item.querySelector('.exp-end').value,
            current: item.querySelector('.exp-current').checked,
            description: item.querySelector('.exp-description').value
        });
    });
    updatePreview();
    updateProgress();
}

function toggleCurrentJob(checkbox) {
    const endDateInput = checkbox.closest('.form-group').querySelector('.exp-end');
    endDateInput.disabled = checkbox.checked;
    if (checkbox.checked) endDateInput.value = '';
    updateExperienceData();
}

function addEducation() {
    educationCounter++;
    const container = document.getElementById('educationContainer');
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const educationDiv = document.createElement('div');
    educationDiv.className = 'dynamic-item';
    educationDiv.innerHTML = `
        <div class="item-header">
            <h4 class="item-title">Education ${educationCounter}</h4>
            <button type="button" class="btn btn-remove" onclick="removeEducation(this)">Remove</button>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Degree</label>
                <input type="text" class="edu-degree" placeholder="Bachelor of Science" onchange="updateEducationData()">
            </div>
            <div class="form-group">
                <label>Field of Study</label>
                <input type="text" class="edu-field" placeholder="Computer Science" onchange="updateEducationData()">
            </div>
        </div>
        <div class="form-row">
            <div class="form-group">
                <label>Institution</label>
                <input type="text" class="edu-institution" placeholder="University Name" onchange="updateEducationData()">
            </div>
            <div class="form-group">
                <label>Graduation Year</label>
                <input type="number" class="edu-year" placeholder="2024" min="1950" max="2030" onchange="updateEducationData()">
            </div>
        </div>
        <div class="form-group">
            <label>Additional Details</label>
            <input type="text" class="edu-details" placeholder="GPA: 3.8/4.0" onchange="updateEducationData()">
        </div>
    `;
    container.appendChild(educationDiv);
    resumeData.education.push({ id: educationCounter, degree: '', field: '', institution: '', year: '', details: '' });
    updatePreview();
}

function removeEducation(button) {
    const educationItem = button.closest('.dynamic-item');
    const index = Array.from(educationItem.parentNode.children).indexOf(educationItem);
    if (index >= 0 && index < resumeData.education.length) {
        resumeData.education.splice(index, 1);
    }
    educationItem.remove();
    const container = document.getElementById('educationContainer');
    if (container.children.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎓</div><p>No education added yet</p></div>';
    }
    updatePreview();
}

function updateEducationData() {
    const educationItems = document.querySelectorAll('#educationContainer .dynamic-item');
    resumeData.education = [];
    educationItems.forEach((item, index) => {
        resumeData.education.push({
            id: index + 1,
            degree: item.querySelector('.edu-degree').value,
            field: item.querySelector('.edu-field').value,
            institution: item.querySelector('.edu-institution').value,
            year: item.querySelector('.edu-year').value,
            details: item.querySelector('.edu-details').value
        });
    });
    updatePreview();
    updateProgress();
}

function addProject() {
    projectCounter++;
    const container = document.getElementById('projectsContainer');
    const emptyState = container.querySelector('.empty-state');
    if (emptyState) emptyState.remove();

    const projectDiv = document.createElement('div');
    projectDiv.className = 'dynamic-item';
    projectDiv.innerHTML = `
        <div class="item-header">
            <h4 class="item-title">Project ${projectCounter}</h4>
            <button type="button" class="btn btn-remove" onclick="removeProject(this)">Remove</button>
        </div>
        <div class="form-group">
            <label>Project Title</label>
            <input type="text" class="proj-title" placeholder="Project Name" onchange="updateProjectData()">
        </div>
        <div class="form-group">
            <label>Description</label>
            <textarea class="proj-description" placeholder="Describe your project..." onchange="updateProjectData()"></textarea>
        </div>
    `;
    container.appendChild(projectDiv);
    resumeData.projectsList.push({ id: projectCounter, title: '', description: '' });
    updatePreview();
}

function removeProject(button) {
    const projectItem = button.closest('.dynamic-item');
    const index = Array.from(projectItem.parentNode.children).indexOf(projectItem);
    if (index >= 0 && index < resumeData.projectsList.length) {
        resumeData.projectsList.splice(index, 1);
    }
    projectItem.remove();
    const container = document.getElementById('projectsContainer');
    if (container.children.length === 0) {
        container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📁</div><p>No projects added yet</p></div>';
    }
    updatePreview();
}

function updateProjectData() {
    const projectItems = document.querySelectorAll('#projectsContainer .dynamic-item');
    resumeData.projectsList = [];
    projectItems.forEach((item, index) => {
        resumeData.projectsList.push({
            id: index + 1,
            title: item.querySelector('.proj-title').value,
            description: item.querySelector('.proj-description').value
        });
    });
    updatePreview();
    updateProgress();
}

function switchTemplate() {
    const templateSelect = document.getElementById('templateSelect');
    const selectedTemplate = templateSelect.value;
    const designControls = document.getElementById('designControls');
    
    document.querySelectorAll('.resume-template').forEach(template => {
        template.classList.remove('active');
    });
    document.getElementById(`${selectedTemplate}Template`).classList.add('active');
    
    // Show/hide design controls for custom template
    if (selectedTemplate === 'custom') {
        designControls.style.display = 'block';
        loadCustomDesign();
    } else {
        designControls.style.display = 'none';
    }
}

// Custom Design Configuration
let customDesignConfig = {
    headerStyle: 'gradient',
    primaryColor: '#667eea',
    secondaryColor: '#764ba2',
    textColor: '#2d3748',
    fontFamily: 'Arial, sans-serif',
    fontSize: 14,
    sectionSpacing: 2,
    borderStyle: 'solid',
    sectionHeaderStyle: 'underline',
    skillsDisplay: 'pills',
    layoutDensity: 'normal'
};

function updateCustomDesign() {
    // Get values from controls
    const config = {
        headerStyle: document.getElementById('headerStyle').value,
        primaryColor: document.getElementById('primaryColor').value,
        secondaryColor: document.getElementById('secondaryColor').value,
        textColor: document.getElementById('textColor').value,
        fontFamily: document.getElementById('fontFamily').value,
        fontSize: parseInt(document.getElementById('fontSize').value),
        sectionSpacing: parseFloat(document.getElementById('sectionSpacing').value),
        borderStyle: document.getElementById('borderStyle').value,
        sectionHeaderStyle: document.getElementById('sectionHeaderStyle').value,
        skillsDisplay: document.getElementById('skillsDisplay').value,
        layoutDensity: document.getElementById('layoutDensity').value
    };

    customDesignConfig = config;

    // Update display values
    document.getElementById('fontSizeValue').textContent = config.fontSize + 'px';
    document.getElementById('spacingValue').textContent = config.sectionSpacing + 'rem';

    // Apply styles to custom template
    const customTemplate = document.getElementById('customTemplate');
    const customHeader = document.getElementById('customHeader');
    
    // Set CSS variables
    customTemplate.style.setProperty('--primary-color', config.primaryColor);
    customTemplate.style.setProperty('--secondary-color', config.secondaryColor);
    customTemplate.style.setProperty('--text-color', config.textColor);
    customTemplate.style.fontFamily = config.fontFamily;
    customTemplate.style.fontSize = config.fontSize + 'px';
    customTemplate.style.color = config.textColor;

    // Apply header style
    customHeader.className = 'custom-header ' + config.headerStyle;

    // Apply section spacing
    const sections = customTemplate.querySelectorAll('.resume-section');
    sections.forEach(section => {
        section.style.marginBottom = config.sectionSpacing + 'rem';
    });

    // Apply section header style
    const sectionHeaders = customTemplate.querySelectorAll('.resume-section h2');
    sectionHeaders.forEach(header => {
        header.className = config.sectionHeaderStyle;
        header.style.color = config.textColor;
    });

    // Apply border style
    const items = customTemplate.querySelectorAll('.experience-item, .education-item, .project-item');
    items.forEach(item => {
        if (config.borderStyle !== 'none') {
            item.style.borderBottom = `1px ${config.borderStyle} #e2e8f0`;
        } else {
            item.style.borderBottom = 'none';
        }
    });

    // Apply skills display style
    const skillsContainer = document.getElementById('customSkillsContent');
    skillsContainer.className = 'skills-container ' + config.skillsDisplay;

    // Apply skill tag colors
    const skillTags = customTemplate.querySelectorAll('.skill-tag');
    skillTags.forEach(tag => {
        tag.style.background = `linear-gradient(135deg, ${config.primaryColor}, ${config.secondaryColor})`;
    });

    // Apply layout density
    customTemplate.classList.remove('compact', 'normal', 'spacious');
    customTemplate.classList.add(config.layoutDensity);

    // Save to localStorage
    localStorage.setItem('customResumeDesign', JSON.stringify(config));
}

function loadCustomDesign() {
    // Load from localStorage
    const saved = localStorage.getItem('customResumeDesign');
    if (saved) {
        customDesignConfig = JSON.parse(saved);
        
        // Set control values
        document.getElementById('headerStyle').value = customDesignConfig.headerStyle;
        document.getElementById('primaryColor').value = customDesignConfig.primaryColor;
        document.getElementById('secondaryColor').value = customDesignConfig.secondaryColor;
        document.getElementById('textColor').value = customDesignConfig.textColor;
        document.getElementById('fontFamily').value = customDesignConfig.fontFamily;
        document.getElementById('fontSize').value = customDesignConfig.fontSize;
        document.getElementById('sectionSpacing').value = customDesignConfig.sectionSpacing;
        document.getElementById('borderStyle').value = customDesignConfig.borderStyle;
        document.getElementById('sectionHeaderStyle').value = customDesignConfig.sectionHeaderStyle;
        document.getElementById('skillsDisplay').value = customDesignConfig.skillsDisplay;
        document.getElementById('layoutDensity').value = customDesignConfig.layoutDensity;
    }
    
    updateCustomDesign();
}

function saveCustomDesign() {
    localStorage.setItem('customResumeDesign', JSON.stringify(customDesignConfig));
    showToast('✅ Design saved successfully!', 'success');
}

function resetCustomDesign() {
    if (confirm('Reset design to default settings?')) {
        localStorage.removeItem('customResumeDesign');
        customDesignConfig = {
            headerStyle: 'gradient',
            primaryColor: '#667eea',
            secondaryColor: '#764ba2',
            textColor: '#2d3748',
            fontFamily: 'Arial, sans-serif',
            fontSize: 14,
            sectionSpacing: 2,
            borderStyle: 'solid',
            sectionHeaderStyle: 'underline',
            skillsDisplay: 'pills',
            layoutDensity: 'normal'
        };
        loadCustomDesign();
        showToast('🔄 Design reset to defaults', 'success');
    }
}

function exportDesignConfig() {
    const config = JSON.stringify(customDesignConfig, null, 2);
    const blob = new Blob([config], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'resume-design-config.json';
    a.click();
    URL.revokeObjectURL(url);
    showToast('📥 Design configuration exported!', 'success');
}

function updatePreview() {
    updatePersonalInfo();
    updateSummary();
    updateExperiences();
    updateEducationPreview();
    updateSkillsPreview();
    updateProjectsPreview();
}

function updatePersonalInfo() {
    const name = resumeData.personal.fullName || 'Your Name';
    const contactParts = [];
    if (resumeData.personal.email) contactParts.push(resumeData.personal.email);
    if (resumeData.personal.phone) contactParts.push(resumeData.personal.phone);
    if (resumeData.personal.location) contactParts.push(resumeData.personal.location);
    if (resumeData.personal.linkedin) contactParts.push(resumeData.personal.linkedin);
    const contactInfo = contactParts.join(' • ');

    ['modern', 'professional', 'executive', 'creative', 'minimalist', 'custom'].forEach(template => {
        document.getElementById(`${template}Name`).textContent = name;
        document.getElementById(`${template}Contact`).textContent = contactInfo;
    });
}

function updateSummary() {
    const summary = resumeData.personal.summary;
    ['modern', 'professional', 'executive', 'creative', 'minimalist', 'custom'].forEach(template => {
        const section = document.getElementById(`${template}Summary`);
        const text = document.getElementById(`${template}SummaryText`);
        if (summary) {
            section.style.display = 'block';
            text.textContent = summary;
        } else {
            section.style.display = 'none';
        }
    });
}

function updateExperiences() {
    ['modern', 'professional', 'executive', 'creative', 'minimalist', 'custom'].forEach(template => {
        const section = document.getElementById(`${template}Experience`);
        const content = document.getElementById(`${template}ExperienceContent`);
        if (resumeData.experiences.length > 0) {
            section.style.display = 'block';
            content.innerHTML = resumeData.experiences.map(exp => {
                const dateRange = getDateRange(exp);
                return `
                    <div class="experience-item">
                        <div class="item-header-preview">
                            <div>
                                <div class="item-title-preview">${exp.title || 'Job Title'}</div>
                                <div class="item-company">${exp.company || 'Company Name'}</div>
                            </div>
                            <div class="item-date">${dateRange}</div>
                        </div>
                        ${exp.description ? `<div class="item-description">${formatDescription(exp.description)}</div>` : ''}
                    </div>
                `;
            }).join('');
        } else {
            section.style.display = 'none';
        }
    });
}

function updateEducationPreview() {
    ['modern', 'professional', 'executive', 'creative', 'minimalist', 'custom'].forEach(template => {
        const section = document.getElementById(`${template}Education`);
        const content = document.getElementById(`${template}EducationContent`);
        if (resumeData.education.length > 0) {
            section.style.display = 'block';
            content.innerHTML = resumeData.education.map(edu => {
                const degreeField = [edu.degree, edu.field].filter(Boolean).join(' in ');
                return `
                    <div class="education-item">
                        <div class="item-header-preview">
                            <div>
                                <div class="item-title-preview">${degreeField || 'Degree'}</div>
                                <div class="item-company">${edu.institution || 'Institution'}</div>
                                ${edu.details ? `<div class="education-details">${edu.details}</div>` : ''}
                            </div>
                            <div class="item-date">${edu.year || ''}</div>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            section.style.display = 'none';
        }
    });
}

function updateSkillsPreview() {
    const skills = resumeData.skills ? resumeData.skills.split(',').map(s => s.trim()).filter(Boolean) : [];
    ['modern', 'professional', 'executive', 'creative', 'minimalist', 'custom'].forEach(template => {
        const section = document.getElementById(`${template}Skills`);
        const content = document.getElementById(`${template}SkillsContent`);
        if (skills.length > 0) {
            section.style.display = 'block';
            content.innerHTML = skills.map(skill => `<span class="skill-tag">${skill}</span>`).join('');
        } else {
            section.style.display = 'none';
        }
    });
    
    // Reapply custom design for skills after update
    if (document.getElementById('templateSelect').value === 'custom') {
        updateCustomDesign();
    }
}

function updateProjectsPreview() {
    ['modern', 'professional', 'executive', 'creative', 'minimalist', 'custom'].forEach(template => {
        const section = document.getElementById(`${template}Projects`);
        const content = document.getElementById(`${template}ProjectsContent`);
        if (resumeData.projectsList.length > 0) {
            section.style.display = 'block';
            content.innerHTML = resumeData.projectsList.map(project => `
                <div class="project-item">
                    <div class="item-title-preview">${project.title || 'Project Title'}</div>
                    <div class="item-description">${project.description || ''}</div>
                </div>
            `).join('');
        } else {
            section.style.display = 'none';
        }
    });
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString + '-01');
    return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short' });
}

function getDateRange(exp) {
    if (!exp.startDate) return '';
    const start = formatDate(exp.startDate);
    const end = exp.current ? 'Present' : (exp.endDate ? formatDate(exp.endDate) : '');
    return end ? `${start} - ${end}` : start;
}

function formatDescription(description) {
    return description.split('\n').map(line => {
        const trimmed = line.trim();
        if (!trimmed) return '';
        if (trimmed.startsWith('•') || trimmed.startsWith('-')) return trimmed;
        return `• ${trimmed}`;
    }).filter(Boolean).join('<br>');
}

function updateResumeData() {
    resumeData.personal.fullName = document.getElementById('fullName').value;
    resumeData.personal.email = document.getElementById('email').value;
    resumeData.personal.phone = document.getElementById('phone').value;
    resumeData.personal.location = document.getElementById('location').value;
    resumeData.personal.linkedin = document.getElementById('linkedin').value;
    resumeData.personal.summary = document.getElementById('summary').value;
    resumeData.skills = document.getElementById('skills').value;
    updatePreview();
    updateProgress();
}

function clearAll() {
    if (confirm('Are you sure you want to clear all data?')) {
        document.querySelectorAll('input, textarea').forEach(field => field.value = '');
        document.getElementById('experienceContainer').innerHTML = '<div class="empty-state"><div class="empty-state-icon">💼</div><p>No work experience added yet</p></div>';
        document.getElementById('educationContainer').innerHTML = '<div class="empty-state"><div class="empty-state-icon">🎓</div><p>No education added yet</p></div>';
        document.getElementById('projectsContainer').innerHTML = '<div class="empty-state"><div class="empty-state-icon">📁</div><p>No projects added yet</p></div>';
        resumeData = {
            personal: { fullName: '', email: '', phone: '', location: '', linkedin: '', summary: '' },
            experiences: [],
            education: [],
            skills: '',
            projectsList: []
        };
        experienceCounter = 0;
        educationCounter = 0;
        projectCounter = 0;
        updatePreview();
        updateProgress();
        showToast('All data cleared');
    }
}

function initializeEventListeners() {
    ['fullName', 'email', 'phone', 'location', 'linkedin', 'summary', 'skills'].forEach(id => {
        const element = document.getElementById(id);
        if (element) {
            element.addEventListener('input', updateResumeData);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initializeEventListeners();
    updatePreview();
    updateProgress();
    showToast('Ready! Make sure Flask backend is running on port 5002');
});
