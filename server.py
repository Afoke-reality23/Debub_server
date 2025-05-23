import socket
import threading
from urllib.parse import urlparse

def auth_header(status="200 OK"):
    headers = (
        f"HTTP/1.1 {status}\r\n"
        "Content-Type: application/json\r\n"
        #"Cache-Control: no-cache\r\n"
        "Access-Control-Allow-Origin: https://inquisitive-snickerdoodle-eb4bf2.netlify.app\r\n"
        "Access-Control-Allow-Methods: GET, POST, OPTIONS\r\n"
        "Access-Control-Allow-Headers: Content-Type\r\n"
        "Access-Control-Allow-Credentials: true\r\n"
    )
    return headers

def response(sock, method, data='', session_id='', max_age=None):
    print('inside response')
    header = ""
    if session_id:
        print('session id header sent, max_age:', max_age)
        cookie_attrs = "HttpOnly; Path=/; SameSite=None; Secure"
        if max_age is not None and max_age != '':
            cookie_attrs += f"; Max-Age={max_age}"
        set_cookie = f"Set-Cookie: session_id={session_id}; {cookie_attrs}\r\n"
        header = auth_header() + set_cookie + '\r\n'
    else:
        if method == 'OPTIONS':
            header = auth_header("204 No Content") + '\r\n'
        else:
            header = auth_header() + '\r\n'
    
    rsp = header + (data if data else '')
    print("Response:", rsp)
    sock.send(rsp.encode('utf-8'))
    sock.shutdown(socket.SHUT_RDWR)

def handle_client(client_sock):
    try:
        request = client_sock.recv(1024).decode('utf-8')
        print("Request:", request)
        
        # Parse method and path
        method = request.split()[0]
        path = request.split()[1] if len(request.split()) > 1 else '/'
        
        # Parse headers
        headers = {}
        for line in request.split('\r\n')[1:]:
            if ': ' in line:
                key, value = line.split(': ', 1)
                headers[key] = value
        
        if method == 'OPTIONS':
            response(client_sock, method)
        elif path == '/set-cookie':
            response(client_sock, method, '{"message":"Cookie set","cookie_id":"test123"}', session_id='test123', max_age='3600')
        elif path == '/check-cookie':
            cookie = headers.get('Cookie', 'No cookie received')
            response(client_sock, method, f'{{"cookie_received":"{cookie}"}}')
        else:
            response(client_sock, method, '{"error":"Not found"}')
            
    except Exception as e:
        print("Error:", e)
        response(client_sock, method, f'{{"error":"{str(e)}"}}')
    finally:
        client_sock.close()

def main():
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind(('0.0.0.0', 8080))  # Render uses PORT env, default 8080
    server_sock.listen(5)
    print("Server running on port 8080")
    
    while True:
        client_sock, addr = server_sock.accept()
        print(f"Connection from {addr}")
        threading.Thread(target=handle_client, args=(client_sock,)).start()

if __name__ == "__main__":
    main()
