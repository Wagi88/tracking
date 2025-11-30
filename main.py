from flask import Flask, request, render_template, jsonify
import sqlite3
import datetime
import threading
import time
import os
import socket
import requests

app = Flask(__name__)

# Global variable for port
SERVER_PORT = 5000

# Color codes for terminal
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

def is_port_available(port):
    """Check if a port is available"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0', port))
            return True
        except socket.error:
            return False

def get_available_port(start_port):
    """Find an available port starting from start_port"""
    port = start_port
    while not is_port_available(port):
        print(f"{Colors.YELLOW}Port {port} is busy, trying {port + 1}{Colors.RESET}")
        port += 1
        if port > 65535:
            raise Exception("No available ports found!")
    return port

def init_db():
    conn = sqlite3.connect('ip_logs.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS ip_logs
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         ip TEXT,
         user_agent TEXT,
         referrer TEXT,
         timestamp TEXT,
         country TEXT,
         country_code TEXT,
         region TEXT,
         region_code TEXT,
         city TEXT,
         zip_code TEXT,
         timezone TEXT,
         isp TEXT,
         org TEXT,
         asn TEXT,
         latitude TEXT,
         longitude TEXT)
    ''')
    conn.commit()
    conn.close()

init_db()

def get_detailed_ip_info(ip):
    """Get comprehensive IP information"""
    try:
        # For localhost/docker networks
        if ip in ['127.0.0.1', '::1', 'localhost']:
            return {
                'ip': ip,
                'country': 'Local Network',
                'country_code': 'LOCAL',
                'region': 'Internal Network',
                'region_code': 'INT',
                'city': 'Local Machine',
                'zip_code': '00000',
                'timezone': 'Local System Time',
                'isp': 'Local Network Interface',
                'org': 'Your Local Machine',
                'asn': 'N/A - Local Network',
                'latitude': '0.0000',
                'longitude': '0.0000'
            }
        
        if ip.startswith('172.') or ip.startswith('192.168') or ip.startswith('10.'):
            return {
                'ip': ip,
                'country': 'Private Network',
                'country_code': 'PVT',
                'region': 'Internal Network',
                'region_code': 'INT',
                'city': 'Local Network',
                'zip_code': '00000',
                'timezone': 'Local System Time',
                'isp': 'Local Network',
                'org': 'Private Range',
                'asn': 'N/A - Private IP',
                'latitude': '0.0000',
                'longitude': '0.0000'
            }
        
        response = requests.get(f'http://ip-api.com/json/{ip}', timeout=10)
        data = response.json()
        
        if data.get('status') == 'success':
            return {
                'ip': ip,
                'country': data.get('country', 'Unknown'),
                'country_code': data.get('countryCode', 'Unknown'),
                'region': data.get('regionName', 'Unknown'),
                'region_code': data.get('region', 'Unknown'),
                'city': data.get('city', 'Unknown'),
                'zip_code': data.get('zip', 'Unknown'),
                'timezone': data.get('timezone', 'Unknown'),
                'isp': data.get('isp', 'Unknown'),
                'org': data.get('org', 'Unknown'),
                'asn': data.get('as', 'Unknown'),
                'latitude': str(data.get('lat', '0.0000')),
                'longitude': str(data.get('lon', '0.0000'))
            }
        else:
            return {
                'ip': ip,
                'country': 'Unknown',
                'country_code': 'Unknown',
                'region': 'Unknown',
                'region_code': 'Unknown',
                'city': 'Unknown',
                'zip_code': 'Unknown',
                'timezone': 'Unknown',
                'isp': 'Unknown',
                'org': 'Unknown',
                'asn': 'Unknown',
                'latitude': '0.0000',
                'longitude': '0.0000'
            }
            
    except Exception as e:
        return {
            'ip': ip,
            'country': 'Error',
            'country_code': 'ERR',
            'region': 'Error',
            'region_code': 'ERR',
            'city': 'Error',
            'zip_code': 'Error',
            'timezone': 'Error',
            'isp': 'Error: ' + str(e),
            'org': 'Error',
            'asn': 'Error',
            'latitude': '0.0000',
            'longitude': '0.0000'
        }

def log_visit(ip, user_agent, referrer):
    """Log visitor information to database"""
    try:
        ip_info = get_detailed_ip_info(ip)
        current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = sqlite3.connect('ip_logs.db')
        c = conn.cursor()
        c.execute('''
            INSERT INTO ip_logs (ip, user_agent, referrer, timestamp, country, country_code, 
                                region, region_code, city, zip_code, timezone, isp, org, asn, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (ip, user_agent, referrer, current_time,
              ip_info['country'], ip_info['country_code'],
              ip_info['region'], ip_info['region_code'],
              ip_info['city'], ip_info['zip_code'],
              ip_info['timezone'], ip_info['isp'],
              ip_info['org'], ip_info['asn'],
              ip_info['latitude'], ip_info['longitude']))
        conn.commit()
        conn.close()
        
        # Print to terminal with beautiful colors
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}IP-TOOL - TARGET INFORMATION CAPTURED{Colors.RESET}")
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        print(f"{Colors.YELLOW}IP Address    {Colors.RESET}> {Colors.GREEN}{ip_info['ip']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Country code  {Colors.RESET}> {Colors.CYAN}{ip_info['country_code']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Country       {Colors.RESET}> {Colors.WHITE}{ip_info['country']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Date & Time   {Colors.RESET}> {Colors.PURPLE}{current_time}{Colors.RESET}")
        print(f"{Colors.YELLOW}Region code   {Colors.RESET}> {Colors.CYAN}{ip_info['region_code']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Region        {Colors.RESET}> {Colors.WHITE}{ip_info['region']}{Colors.RESET}")
        print(f"{Colors.YELLOW}City          {Colors.RESET}> {Colors.WHITE}{ip_info['city']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Zip code      {Colors.RESET}> {Colors.CYAN}{ip_info['zip_code']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Time zone     {Colors.RESET}> {Colors.PURPLE}{ip_info['timezone']}{Colors.RESET}")
        print(f"{Colors.YELLOW}ISP           {Colors.RESET}> {Colors.GREEN}{ip_info['isp']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Organization  {Colors.RESET}> {Colors.WHITE}{ip_info['org']}{Colors.RESET}")
        print(f"{Colors.YELLOW}ASN           {Colors.RESET}> {Colors.CYAN}{ip_info['asn']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Latitude      {Colors.RESET}> {Colors.PURPLE}{ip_info['latitude']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Longitude     {Colors.RESET}> {Colors.PURPLE}{ip_info['longitude']}{Colors.RESET}")
        print(f"{Colors.YELLOW}Location      {Colors.RESET}> {Colors.BLUE}{ip_info['latitude']}, {ip_info['longitude']}{Colors.RESET}")
        
        if user_agent and user_agent != 'Unknown':
            print(f"{Colors.YELLOW}User Agent    {Colors.RESET}> {Colors.GRAY}{user_agent[:60]}...{Colors.RESET}")
        if referrer and referrer != 'Unknown':
            print(f"{Colors.YELLOW}Referrer      {Colors.RESET}> {Colors.GRAY}{referrer}{Colors.RESET}")
        
        print(f"{Colors.CYAN}{'='*70}{Colors.RESET}")
        
    except Exception as e:
        print(f"{Colors.RED}ERROR: Error logging visit: {e}{Colors.RESET}")

@app.route('/')
def index():
    # Get client information
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0]
    else:
        ip = request.remote_addr
    
    user_agent = request.headers.get('User-Agent', 'Unknown')
    referrer = request.headers.get('Referer', 'Unknown')
    
    # Log the visit in background
    threading.Thread(target=log_visit, args=(ip, user_agent, referrer)).start()
    
    # Serve a simple page
    return render_template('index.html')

@app.route('/stats')
def stats():
    """API endpoint to get statistics"""
    conn = sqlite3.connect('ip_logs.db')
    c = conn.cursor()
    
    # Get total visits
    c.execute('SELECT COUNT(*) FROM ip_logs')
    total_visits = c.fetchone()[0]
    
    # Get unique IPs
    c.execute('SELECT COUNT(DISTINCT ip) FROM ip_logs')
    unique_ips = c.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_visits': total_visits,
        'unique_ips': unique_ips
    })

def display_stats(port):
    """Display statistics in terminal"""
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        
        # Print logo and header with colors
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.CYAN}{Colors.BOLD}")
        print("  _____ _____    _______          _ ")
        print(" |_   _|  __ \  |__   __|        | |")
        print("   | | | |__) |    | | ___   ___ | |")
        print("   | | |  ___/     | |/ _ \ / _ \| |")
        print("  _| |_| |         | | (_) | (_) | |")
        print(" |_____|_|         |_|\___/ \___/|_|")
        print(f"{Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
        print(f"{Colors.YELLOW}Server running on port: {Colors.GREEN}{port}{Colors.RESET}")
        print(f"{Colors.YELLOW}Local URL: {Colors.CYAN}http://localhost:{port}{Colors.RESET}")
        print(f"{Colors.YELLOW}Network URL: {Colors.CYAN}http://{get_local_ip()}:{port}{Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
        print()
        
        conn = sqlite3.connect('ip_logs.db')
        c = conn.cursor()
        
        # Total stats
        c.execute('SELECT COUNT(*) FROM ip_logs')
        total = c.fetchone()[0]
        
        c.execute('SELECT COUNT(DISTINCT ip) FROM ip_logs')
        unique = c.fetchone()[0]
        
        print(f"{Colors.YELLOW}Total Visits: {Colors.GREEN}{total}{Colors.RESET} {Colors.YELLOW}| Unique IPs: {Colors.GREEN}{unique}{Colors.RESET}")
        print()
        
        # Recent visits
        c.execute('''
            SELECT ip, timestamp, country, city, isp 
            FROM ip_logs 
            ORDER BY id DESC LIMIT 10
        ''')
        visits = c.fetchall()
        
        if visits:
            print(f"{Colors.CYAN}{Colors.BOLD}Recent Visitors:{Colors.RESET}")
            print(f"{Colors.BLUE}{'-'*85}{Colors.RESET}")
            print(f"{Colors.YELLOW}{'Time':<19} | {'IP Address':<15} | {'Country':<12} | {'City':<15} | {'ISP'}{Colors.RESET}")
            print(f"{Colors.BLUE}{'-'*85}{Colors.RESET}")
            for visit in visits:
                ip, timestamp, country, city, isp = visit
                print(f"{Colors.PURPLE}{timestamp}{Colors.RESET} | {Colors.GREEN}{ip:<15}{Colors.RESET} | {Colors.CYAN}{country:<12}{Colors.RESET} | {Colors.WHITE}{city:<15}{Colors.RESET} | {Colors.GRAY}{isp}{Colors.RESET}")
            print(f"{Colors.BLUE}{'-'*85}{Colors.RESET}")
        else:
            print(f"{Colors.YELLOW}No visitors yet. Waiting for connections...{Colors.RESET}")
            print(f"{Colors.CYAN}Share your URL with someone to see their IP information here!{Colors.RESET}")
        
        conn.close()
        
        print(f"\n{Colors.GRAY}Last update: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")
        print(f"{Colors.YELLOW}Press Ctrl+C to exit{Colors.RESET}")
        print(f"{Colors.BLUE}{Colors.BOLD}{'='*70}{Colors.RESET}")
        
        time.sleep(5)  # Update every 5 seconds

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def get_user_port():
    """Get port number from user input"""
    while True:
        try:
            print(f"{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.RESET}")
            print(f"{Colors.CYAN}{Colors.BOLD}           IP-TOOL SERVER SETUP{Colors.RESET}")
            print(f"{Colors.BLUE}{Colors.BOLD}{'='*50}{Colors.RESET}")
            print(f"\n{Colors.YELLOW}Available ports: 8080, 3000, 5000, 8000, 9000{Colors.RESET}")
            
            port_input = input(f"\n{Colors.GREEN}Enter port number (default: 5000): {Colors.RESET}").strip()
            
            if not port_input:
                port = 5000
            else:
                port = int(port_input)
            
            if port < 1 or port > 65535:
                print(f"{Colors.RED}Port must be between 1 and 65535{Colors.RESET}")
                continue
                
            # Check if port is available
            if is_port_available(port):
                return port
            else:
                print(f"{Colors.RED}Port {port} is busy!{Colors.RESET}")
                choice = input(f"{Colors.YELLOW}Try another port? (y/n): {Colors.RESET}").lower().strip()
                if choice != 'y':
                    # Find next available port
                    new_port = get_available_port(port + 1)
                    print(f"{Colors.GREEN}Using available port: {new_port}{Colors.RESET}")
                    return new_port
                    
        except ValueError:
            print(f"{Colors.RED}Please enter a valid number{Colors.RESET}")
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Setup cancelled{Colors.RESET}")
            exit(0)

if __name__ == '__main__':
    # Get port from user
    SERVER_PORT = get_user_port()
    
    # Start terminal display in separate thread
    display_thread = threading.Thread(target=display_stats, args=(SERVER_PORT,), daemon=True)
    display_thread.start()
    
    print(f"\n{Colors.GREEN}Starting IP-TOOL Server on port {SERVER_PORT}...{Colors.RESET}")
    print(f"{Colors.CYAN}Local access: http://localhost:{SERVER_PORT}{Colors.RESET}")
    print(f"{Colors.CYAN}Network access: http://{get_local_ip()}:{SERVER_PORT}{Colors.RESET}")
    print(f"{Colors.YELLOW}Share the network URL with your target!{Colors.RESET}")
    print(f"{Colors.PURPLE}Terminal will display comprehensive IP information automatically{Colors.RESET}")
    print(f"{Colors.RED}Press Ctrl+C to stop the server{Colors.RESET}")
    
    try:
        app.run(debug=False, host='0.0.0.0', port=SERVER_PORT, use_reloader=False)
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"{Colors.RED}Error: Port {SERVER_PORT} is already in use!{Colors.RESET}")
            print(f"{Colors.YELLOW}Try running the script again with a different port{Colors.RESET}")
        else:
            print(f"{Colors.RED}Error: {e}{Colors.RESET}")
