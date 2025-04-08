
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

@app.route("/", methods=["GET", "POST"])
def index():
    extracted_text = ""
    resume_sections = {}
    if request.method == "POST":
        file = request.files["resume"]
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

    return render_template("index.html", extracted_text=extracted_text, resume_sections=resume_sections)

if __name__ == "__main__":
    app.run(debug=True)
