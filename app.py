import os
import pytesseract
import pdfplumber
from PIL import Image
from flask import Flask, request, jsonify, render_template
import google.generativeai as genai

app = Flask(__name__)

# --- CONFIGURATION ---
# Windows Local Path
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# API Key
GENAI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GENAI_API_KEY:
    try:
        genai.configure(api_key=GENAI_API_KEY)
    except:
        pass

def extract_text(file, filename):
    text = ""
    try:
        # --- PDF LOGIC ---
        if filename.lower().endswith('.pdf'):
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            # Agar PDF padha lekin text khaali hai (Scanned PDF Check)
            if not text.strip():
                return None, "Ye ek Scanned PDF lag raha hai. Kripya iska screenshot lein aur IMAGE (JPG/PNG) upload karein."

        # --- IMAGE LOGIC (OCR) ---
        else:
            image = Image.open(file)
            # Image ko process karne se pahle thoda optimize karte hain
            text = pytesseract.image_to_string(image)
            
    except Exception as e:
        return None, f"Error: {str(e)}"
    
    return text, None

def analyze_content(text):
    if not GENAI_API_KEY:
        return "Error: API Key missing on Server."

    try:
        # Hum 'gemini-pro' use karenge kyunki ye sabse stable version hai purani aur nayi library dono ke liye
        model = genai.GenerativeModel('gemini-pro')
        
        prompt = f"""You are a Social Media Expert. Analyze this text and give 3 improvements.
        
        Text:
        {text}
        """
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
    if not text or not text.strip(): return jsonify({"error": "No text found. Try a clearer image."}), 400

    analysis = analyze_content(text)
    return jsonify({"extracted_text": text, "analysis": analysis})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=10000)