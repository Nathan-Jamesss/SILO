from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            data = json.loads(post_data.decode('utf-8'))
            email = data.get('email')
            opp_id = data.get('opportunity_id')
            
            # Since we're serverless & static, we log the scheduled reminder to console
            # and succeed. You can hook this up to SendGrid / Mailgun later if needed!
            print(f"[REMINDER] Registered alert for {email} on opportunity ID {opp_id}")
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            
            response = {"status": "success", "message": "Reminder scheduled successfully!"}
            self.wfile.write(json.dumps(response).encode('utf-8'))
            
        except Exception as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            response = {"status": "error", "message": str(e)}
            self.wfile.write(json.dumps(response).encode('utf-8'))
