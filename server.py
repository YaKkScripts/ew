import http.server
import socketserver
import webbrowser
import os
import json
from urllib.parse import urlparse, parse_qs
import uuid
import shutil

PORT = 8000
PRODUCTS_FILE = "products.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self, content_type='text/html'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()

    def do_GET(self):
        try:
            url = urlparse(self.path)
            
            if url.path == '/':
                self.serve_file('index.html')
            elif url.path == '/create':
                self.serve_file('create.html')
            elif url.path == '/get_products':
                self.serve_products()
            elif url.path.startswith('/download/'):
                self.serve_download(url.path[10:])
            elif url.path.startswith('/uploads/'):
                self.serve_uploaded_file(url.path)
            else:
                super().do_GET()
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def do_POST(self):
        try:
            url = urlparse(self.path)
            
            if url.path == '/create_product':
                self.handle_create_product()
            elif url.path == '/upload_image':
                self.handle_upload('image')
            elif url.path == '/upload_file':
                self.handle_upload('file')
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def serve_file(self, filename):
        if os.path.exists(filename):
            self._set_headers()
            with open(filename, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        else:
            self.send_error(404, "File not found")

    def serve_products(self):
        products = self._load_products()
        self._set_headers('application/json')
        self.wfile.write(json.dumps(products).encode())

    def serve_download(self, file_id):
        products = self._load_products()
        product = next((p for p in products if p['file_id'] == file_id), None)
        
        if product and os.path.exists(product['file_path']):
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', 
                           f'attachment; filename="{product["original_file_name"]}"')
            self.send_header('Content-Length', os.path.getsize(product['file_path']))
            self.end_headers()
            
            with open(product['file_path'], 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        else:
            self.send_error(404, "File not found")

    def serve_uploaded_file(self, path):
        filepath = path[1:]  # Remove leading slash
        if os.path.exists(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            content_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.rbxl': 'application/octet-stream'
            }.get(ext, 'application/octet-stream')
            
            self._set_headers(content_type)
            with open(filepath, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        else:
            self.send_error(404, "File not found")

    def handle_create_product(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        product_data = json.loads(post_data)
        
        products = self._load_products()
        product_id = str(uuid.uuid4())
        
        new_product = {
            "id": product_id,
            "name": product_data['name'],
            "image": product_data['image'],
            "file_id": str(uuid.uuid4()),
            "file_path": product_data['file_path'],
            "original_file_name": product_data['original_file_name'],
            "file_type": product_data.get('file_type', 'application/octet-stream')
        }
        
        products.append(new_product)
        self._save_products(products)
        
        self._set_headers('application/json')
        self.wfile.write(json.dumps({
            "status": "success",
            "redirect": "/?created=true"
        }).encode())

    def handle_upload(self, file_type):
        content_type = self.headers['Content-Type']
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400, "Bad Request: Invalid content type")
            return
            
        content_length = int(self.headers['Content-Length'])
        boundary = content_type.split("=")[1].encode()
        data = self.rfile.read(content_length)
        
        for part in data.split(boundary):
            if b'filename="' in part:
                header, file_data = part.split(b'\r\n\r\n', 1)
                filename = header.split(b'filename="')[1].split(b'"')[0].decode()
                file_data = file_data.rstrip(b'\r\n--')
                
                # Validate Roblox Place file
                if file_type == 'file' and not filename.lower().endswith('.rbxl'):
                    self.send_error(400, "Bad Request: Only .rbxl files are allowed")
                    return
                
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                
                self._set_headers('application/json')
                self.wfile.write(json.dumps({
                    "status": "success",
                    "filename": unique_filename,
                    "filepath": filepath,
                    "original_filename": filename,
                    "file_type": 'application/octet-stream'
                }).encode())
                return
        
        self.send_error(400, "Bad Request: No file uploaded")

    def _load_products(self):
        try:
            if os.path.exists(PRODUCTS_FILE):
                with open(PRODUCTS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def _save_products(self, products):
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products, f, indent=2)

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Roblox Store Server running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    webbrowser.open_new_tab(f"http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped successfully")
import http.server
import socketserver
import webbrowser
import os
import json
from urllib.parse import urlparse, parse_qs
import uuid
import shutil
from datetime import datetime

PORT = 8000
PRODUCTS_FILE = "products.json"
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

class MyHandler(http.server.SimpleHTTPRequestHandler):
    def _set_headers(self, content_type='text/html', status=200):
        self.send_response(status)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        self.end_headers()

    def do_GET(self):
        try:
            url = urlparse(self.path)
            
            if url.path == '/':
                self.serve_file('index.html')
            elif url.path == '/create':
                self.serve_file('create.html')
            elif url.path == '/get_products':
                self.serve_products()
            elif url.path.startswith('/download/'):
                self.serve_download(url.path[10:])
            elif url.path.startswith('/uploads/'):
                self.serve_uploaded_file(url.path)
            elif url.path == '/api/stats':
                self.serve_stats()
            else:
                super().do_GET()
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def do_POST(self):
        try:
            url = urlparse(self.path)
            
            if url.path == '/create_product':
                self.handle_create_product()
            elif url.path == '/upload_image':
                self.handle_upload('image')
            elif url.path == '/upload_file':
                self.handle_upload('file')
            else:
                self.send_error(404, "Not Found")
        except Exception as e:
            self.send_error(500, f"Server Error: {str(e)}")

    def serve_file(self, filename):
        if os.path.exists(filename):
            self._set_headers()
            with open(filename, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        else:
            self.send_error(404, "File not found")

    def serve_products(self):
        products = self._load_products()
        self._set_headers('application/json')
        self.wfile.write(json.dumps(products).encode())

    def serve_stats(self):
        products = self._load_products()
        stats = {
            'total_products': len(products),
            'last_updated': datetime.now().isoformat(),
            'server_version': '1.2.0'
        }
        self._set_headers('application/json')
        self.wfile.write(json.dumps(stats).encode())

    def serve_download(self, file_id):
        products = self._load_products()
        product = next((p for p in products if p['file_id'] == file_id), None)
        
        if product and os.path.exists(product['file_path']):
            # Record download count
            if 'downloads' not in product:
                product['downloads'] = 0
            product['downloads'] += 1
            self._save_products(products)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', 
                           f'attachment; filename="{product["original_file_name"]}"')
            self.send_header('Content-Length', os.path.getsize(product['file_path']))
            self.end_headers()
            
            with open(product['file_path'], 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        else:
            self.send_error(404, "File not found")

    def serve_uploaded_file(self, path):
        filepath = path[1:]  # Remove leading slash
        if os.path.exists(filepath):
            ext = os.path.splitext(filepath)[1].lower()
            content_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.rbxl': 'application/octet-stream'
            }.get(ext, 'application/octet-stream')
            
            self._set_headers(content_type)
            with open(filepath, 'rb') as f:
                shutil.copyfileobj(f, self.wfile)
        else:
            self.send_error(404, "File not found")

    def handle_create_product(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        product_data = json.loads(post_data)
        
        products = self._load_products()
        product_id = str(uuid.uuid4())
        
        new_product = {
            "id": product_id,
            "name": product_data['name'],
            "description": product_data.get('description', ''),
            "image": product_data['image'],
            "file_id": str(uuid.uuid4()),
            "file_path": product_data['file_path'],
            "original_file_name": product_data['original_file_name'],
            "file_type": product_data.get('file_type', 'application/octet-stream'),
            "created_at": datetime.now().isoformat(),
            "downloads": 0,
            "author": product_data.get('author', 'Anonymous'),
            "version": product_data.get('version', '1.0.0')
        }
        
        products.append(new_product)
        self._save_products(products)
        
        self._set_headers('application/json')
        self.wfile.write(json.dumps({
            "status": "success",
            "redirect": "/?created=true"
        }).encode())

    def handle_upload(self, file_type):
        content_type = self.headers['Content-Type']
        if not content_type.startswith('multipart/form-data'):
            self.send_error(400, "Bad Request: Invalid content type")
            return
            
        content_length = int(self.headers['Content-Length'])
        boundary = content_type.split("=")[1].encode()
        data = self.rfile.read(content_length)
        
        for part in data.split(boundary):
            if b'filename="' in part:
                header, file_data = part.split(b'\r\n\r\n', 1)
                filename = header.split(b'filename="')[1].split(b'"')[0].decode()
                file_data = file_data.rstrip(b'\r\n--')
                
                # Validate Roblox Place file
                if file_type == 'file' and not filename.lower().endswith('.rbxl'):
                    self.send_error(400, "Bad Request: Only .rbxl files are allowed")
                    return
                
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
                
                with open(filepath, 'wb') as f:
                    f.write(file_data)
                
                self._set_headers('application/json')
                self.wfile.write(json.dumps({
                    "status": "success",
                    "filename": unique_filename,
                    "filepath": filepath,
                    "original_filename": filename,
                    "file_type": 'application/octet-stream'
                }).encode())
                return
        
        self.send_error(400, "Bad Request: No file uploaded")

    def _load_products(self):
        try:
            if os.path.exists(PRODUCTS_FILE):
                with open(PRODUCTS_FILE, 'r') as f:
                    return json.load(f)
        except:
            pass
        return []

    def _save_products(self, products):
        with open(PRODUCTS_FILE, 'w') as f:
            json.dump(products, f, indent=2)

with socketserver.TCPServer(("", PORT), MyHandler) as httpd:
    print(f"Roblox Store Server running at http://localhost:{PORT}")
    print("Press Ctrl+C to stop the server")
    webbrowser.open_new_tab(f"http://localhost:{PORT}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped successfully")