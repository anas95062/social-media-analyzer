import os
import pytesseract
import pdfplumber
from PIL import Image
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# TESSERACT CONFIGURATION
# Check if running on Windows (Local) or Linux (Render)
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# GEMINI AI CONFIGURATION
GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GENAI_API_KEY:
    genai.configure(api_key=GENAI_API_KEY)

def extract_text(file, filename):
    text = ""
    try:
        if filename.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted: text += extracted + "\n"
        else:
            image = Image.open(file)
            text = pytesseract.image_to_string(image)
    except Exception as e:
        return None, str(e)
    return text, None

def analyze_content(text):
    if not GENAI_API_KEY:
        return "AI Key Missing. Deployment step me ham ise add karenge."
    try:
        model = genai.GenerativeModel('gemini-pro')
        prompt = f"Analyze this social media post and suggest 3 engagement improvements:\n\n{text}"
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"AI Error: {str(e)}"

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    if 'file' not in request.files: return jsonify({"error": "No file uploaded"}), 400
    file = request.files['file']
    if file.filename == '': return jsonify({"error": "No file selected"}), 400

    text, error = extract_text(file, file.filename)
    if error: return jsonify({"error": error}), 500
    if not text.strip(): return jsonify({"error": "No text found."}), 400

    analysis = analyze_content(text)
    return jsonify({"extracted_text": text, "analysis": analysis})

if __name__ == '__main__':
    app.run(debug=True)