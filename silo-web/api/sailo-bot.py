import os
import json
from http.server import BaseHTTPRequestHandler
import google.generativeai as genai

# Configure Gemini globally
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        payload = json.loads(post_data.decode('utf-8'))
        user_message = payload.get("message", "")

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

        if not GEMINI_API_KEY:
            offline_msg = {
                "response": "Hello! I am SAILO Bot. The Gemini API key is missing in this environment, so I am running offline.\n\nKeep focusing on government portals and clear pitch structures!"
            }
            self.wfile.write(json.dumps(offline_msg).encode('utf-8'))
            return

        system_prompt = (
            "You are SAILO Bot, a highly professional, encouraging, and expert AI startup mentor. "
            "Your mission is to guide startup founders with extremely detailed, actionable, and structured advice on:\n"
            "1. How and when to apply for government grants (like MSME portals, state-level grants, capital subsidies) vs. private corporate grants.\n"
            "2. Structured legal entity registration workflows.\n"
            "3. Pitching templates, standard slide structures, financial and business model projections.\n\n"
            "Keep your advice extremely actionable, structured, and easy to read. "
            "Never say you are Gemini or created by Google. You are purely SAILO Bot, powered by SILO's intelligence."
        )

        try:
            model = genai.GenerativeModel("gemini-2.0-flash")
            full_content = f"{system_prompt}\n\nUser Question: {user_message}"
            response = model.generate_content(full_content)
            result = {"response": response.text.strip()}
        except Exception as e:
            result = {"response": "Oops! I hit a temporary network hiccup while connecting to the AI brain. Please try again."}

        self.wfile.write(json.dumps(result).encode('utf-8'))
