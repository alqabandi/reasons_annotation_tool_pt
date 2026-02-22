#!/usr/bin/env python3
"""
Simple annotation server that:
1. Serves static files (HTML, CSS, JS)
2. Loads the template CSV (annotations_empty.csv)
3. Creates and saves user-specific annotation files (annotations_[USERNAME].csv)

Usage:
    python server.py
    
Then open http://localhost:8000 in your browser.
"""

import http.server
import socketserver
import json
import os
import csv
from urllib.parse import urlparse, parse_qs
from pathlib import Path

PORT = 8000
BASE_DIR = Path(__file__).parent.resolve()
TEMPLATE_CSV = BASE_DIR / "annotations_empty.csv"

class AnnotationHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)
    
    def do_GET(self):
        parsed = urlparse(self.path)
        
        # API endpoint to get the template CSV data
        if parsed.path == '/api/template':
            self.send_json_response(self.load_template_csv())
            return
        
        # API endpoint to get user's existing annotations (if any)
        if parsed.path == '/api/annotations':
            params = parse_qs(parsed.query)
            username = params.get('username', [''])[0]
            if username:
                data = self.load_user_annotations(username)
                self.send_json_response(data)
                return
            self.send_error(400, "Username required")
            return
        
        # API endpoint to check if user file exists
        if parsed.path == '/api/check-user':
            params = parse_qs(parsed.query)
            username = params.get('username', [''])[0]
            if username:
                user_file = BASE_DIR / f"annotations_{username}.csv"
                self.send_json_response({"exists": user_file.exists()})
                return
            self.send_error(400, "Username required")
            return
        
        # API endpoint to list all existing annotator files
        if parsed.path == '/api/list-users':
            self.send_json_response(self.list_existing_users())
            return
        
        # Serve index.html for root
        if parsed.path == '/':
            self.path = '/annotation_tool.html'
        
        return super().do_GET()
    
    def do_POST(self):
        parsed = urlparse(self.path)
        
        # API endpoint to save annotations
        if parsed.path == '/api/save':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                username = data.get('username', '')
                annotations = data.get('annotations', {})
                template_data = data.get('data', [])
                
                if not username:
                    self.send_error(400, "Username required")
                    return
                
                # Save to user-specific CSV
                self.save_user_annotations(username, template_data, annotations)
                self.send_json_response({"success": True, "message": f"Saved to annotations_{username}.csv"})
                
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        # API endpoint to initialize user file (copy template)
        if parsed.path == '/api/init-user':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                username = data.get('username', '')
                
                if not username:
                    self.send_error(400, "Username required")
                    return
                
                user_file = BASE_DIR / f"annotations_{username}.csv"
                
                # If file doesn't exist, create it from template
                if not user_file.exists():
                    self.create_user_file(username)
                    self.send_json_response({"success": True, "created": True, "message": f"Created annotations_{username}.csv"})
                else:
                    self.send_json_response({"success": True, "created": False, "message": f"File annotations_{username}.csv already exists"})
                    
            except Exception as e:
                self.send_error(500, str(e))
            return
        
        self.send_error(404, "Endpoint not found")
    
    def load_template_csv(self):
        """Load the template CSV file"""
        data = []
        if TEMPLATE_CSV.exists():
            with open(TEMPLATE_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
        return {"data": data, "count": len(data)}
    
    def list_existing_users(self):
        """Scan for existing annotations_*.csv files and return usernames + progress"""
        users = []
        for filepath in sorted(BASE_DIR.glob("annotations_*.csv")):
            filename = filepath.name
            # Skip the template file
            if filename == "annotations_empty.csv":
                continue
            # Extract username from annotations_USERNAME.csv
            username = filename[len("annotations_"):-len(".csv")]
            if not username:
                continue
            # Count how many rows have at least one annotation field filled in
            completed = 0
            total = 0
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        total += 1
                        # Check if any annotation field is filled
                        if row.get('emotion_anxiety_likert', ''):
                            completed += 1
            except Exception:
                pass
            users.append({
                "username": username,
                "completed": completed,
                "total": total
            })
        return {"users": users}
    
    def load_user_annotations(self, username):
        """Load existing user annotations if they exist"""
        user_file = BASE_DIR / f"annotations_{username}.csv"
        data = []
        annotations = {}
        
        if user_file.exists():
            with open(user_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    data.append(row)
                    # Extract annotations from the row
                    rowid_value = row.get('rowid', '')
                    if rowid_value:
                        ann = {}
                        annotation_fields = [
                            'skip_reason',
                            'emotion_anxiety_likert', 'emotion_anger_likert',
                            'emotion_sadness_likert', 'emotion_joy_likert',
                            'emotion_optimism_likert', 'emotion_frustration_likert',
                            'emotion_fear_likert', 'emotion_hope_likert',
                            'sentiment_categorical', 'sentiment_likert',
                            'mf_best', 'mf_orientation',
                            'political_guess'
                        ]
                        for field in annotation_fields:
                            if field in row and row[field]:
                                ann[field] = row[field]
                        if ann:
                            annotations[rowid_value] = ann
        
        return {"data": data, "annotations": annotations, "exists": user_file.exists()}
    
    def create_user_file(self, username):
        """Create a new user file from the template with annotation columns"""
        user_file = BASE_DIR / f"annotations_{username}.csv"
        
        # Define annotation columns
        annotation_columns = [
            'annotator_id',
            'skip_reason',
            'emotion_anxiety_likert',
            'emotion_anger_likert',
            'emotion_sadness_likert',
            'emotion_joy_likert',
            'emotion_optimism_likert',
            'emotion_frustration_likert',
            'emotion_fear_likert',
            'emotion_hope_likert',
            'sentiment_categorical',
            'sentiment_likert',
            'mf_best',
            'mf_orientation',
            'political_guess'
        ]
        
        # Read template and write to user file with additional columns
        if TEMPLATE_CSV.exists():
            with open(TEMPLATE_CSV, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                template_fields = reader.fieldnames or []
                
                # Create new fieldnames with annotation columns
                new_fields = template_fields + annotation_columns
                
                with open(user_file, 'w', newline='', encoding='utf-8') as out:
                    writer = csv.DictWriter(out, fieldnames=new_fields)
                    writer.writeheader()
                    
                    for row in reader:
                        # Add empty annotation columns
                        for col in annotation_columns:
                            row[col] = ''
                        writer.writerow(row)
        
        print(f"Criado: {user_file}")
    
    def save_user_annotations(self, username, template_data, annotations):
        """Save annotations to user-specific CSV"""
        user_file = BASE_DIR / f"annotations_{username}.csv"
        
        # Define all columns
        base_columns = ['rowid', 'ResponseId', 'statement', 'agree', 'X_describe']
        annotation_columns = [
            'annotator_id',
            'skip_reason',
            'emotion_anxiety_likert',
            'emotion_anger_likert',
            'emotion_sadness_likert',
            'emotion_joy_likert',
            'emotion_optimism_likert',
            'emotion_frustration_likert',
            'emotion_fear_likert',
            'emotion_hope_likert',
            'sentiment_categorical',
            'sentiment_likert',
            'mf_best',
            'mf_orientation',
            'political_guess'
        ]
        all_columns = base_columns + annotation_columns
        
        with open(user_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_columns)
            writer.writeheader()
            
            for item in template_data:
                row = {
                    'rowid': item.get('rowid', ''),
                    'ResponseId': item.get('ResponseId', ''),
                    'statement': item.get('statement', ''),
                    'agree': item.get('agree', ''),
                    'X_describe': item.get('X_describe', ''),
                    'annotator_id': username
                }
                
                # Add annotations if they exist for this row
                rowid_value = item.get('rowid', '')
                if rowid_value in annotations:
                    ann = annotations[rowid_value]
                    for col in annotation_columns[1:]:  # Skip annotator_id
                        row[col] = ann.get(col, '')
                else:
                    for col in annotation_columns[1:]:
                        row[col] = ''
                
                writer.writerow(row)
        
        print(f"Anotações de {username} salvas em {user_file}")
    
    def send_json_response(self, data):
        """Send a JSON response"""
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def main():
    with socketserver.TCPServer(("", PORT), AnnotationHandler) as httpd:
        print(f"""
╔════════════════════════════════════════════════════════════╗
║       Servidor da Ferramenta de Anotação Rodando!           ║
╠════════════════════════════════════════════════════════════╣
║                                                             ║
║  Abra seu navegador em:  http://localhost:{PORT}             ║
║                                                             ║
║  Arquivos salvos como: annotations_[USUARIO].csv            ║
║                                                             ║
║  Pressione Ctrl+C para parar o servidor                     ║
║                                                             ║
╚════════════════════════════════════════════════════════════╝
""")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServidor parado.")

if __name__ == "__main__":
    main()
