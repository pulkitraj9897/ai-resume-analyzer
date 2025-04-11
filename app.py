
from flask import Flask, render_template, request
import os
import docx2txt
import PyPDF2
import spacy

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(file_path):
    with open(file_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join([page.extract_text() for page in reader.pages if page.extract_text()])

def extract_text_from_docx(file_path):
    return docx2txt.process(file_path)

def extract_sections(text):
    sections = {
        "Education": [],
        "Experience": [],
        "Projects": [],
        "Skills": []
    }
    lines = text.splitlines()
    current_section = None

    for line in lines:
        line = line.strip()
        lower = line.lower()
        if any(key.lower() in lower for key in sections.keys()):
            for key in sections:
                if key.lower() in lower:
                    current_section = key
                    break
            continue
        if current_section and line:
            sections[current_section].append(line)

    return sections

def get_keywords(text):
    doc = nlp(text.lower())
    return set([token.lemma_ for token in doc if token.is_alpha and not token.is_stop])

def generate_feedback(resume_text, job_desc):
    resume_keywords = get_keywords(resume_text)
    jd_keywords = get_keywords(job_desc)

    matched = resume_keywords & jd_keywords
    missing = jd_keywords - resume_keywords

    feedback = {
        "matched_keywords": list(matched),
        "missing_keywords": list(missing),
        "score": int((len(matched) / len(jd_keywords)) * 100) if jd_keywords else 0,
        "message": "",
        "class": "bad"
    }

    if feedback["score"] > 75:
        feedback["message"] = "Great match! Your resume aligns well with the job description."
        feedback["class"] = "good"
    elif feedback["score"] > 50:
        feedback["message"] = "Good, but you can include more specific skills or tools mentioned in the job."
        feedback["class"] = "okay"
    else:
        feedback["message"] = "Consider tailoring your resume to better match the job description keywords."
        feedback["class"] = "bad"

    return feedback

@app.route("/", methods=["GET", "POST"])
def index():
    extracted_text = ""
    resume_sections = {}
    feedback = {}
    job_desc = ""

    if request.method == "POST":
        file = request.files["resume"]
        job_desc = request.form.get("job_desc", "")

        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            if filename.endswith(".pdf"):
                extracted_text = extract_text_from_pdf(filepath)
            elif filename.endswith(".docx"):
                extracted_text = extract_text_from_docx(filepath)
            else:
                extracted_text = "Unsupported file type."

            resume_sections = extract_sections(extracted_text)

            if job_desc:
                feedback = generate_feedback(extracted_text, job_desc)

    return render_template("index.html", extracted_text=extracted_text, resume_sections=resume_sections, feedback=feedback, job_desc=job_desc)

if __name__ == "__main__":
    app.run(debug=True)
