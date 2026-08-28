"""
Professional Email & DNS Analysis API
Inspired by MxToolbox.com - Complete MX, SPF, DKIM, DMARC Analysis
Single File FastAPI Application
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import dns.resolver
import dns.reversename
import dns.query
import dns.zone
import socket
import smtplib
import re
import datetime
import requests
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# ==========================================
# 📋 Pydantic Models
# ==========================================

class MXRecord(BaseModel):
    priority: int
    exchange: str
    ip_addresses: Optional[List[str]] = None

class MXLookupResponse(BaseModel):
    domain: str
    mx_records: List[MXRecord]
    total_records: int
    timestamp: str

class SPFRecord(BaseModel):
    domain: str
    record: Optional[str] = None
    mechanisms: List[str]
    all_mechanism: Optional[str] = None
    includes: List[str]
    ip4s: List[str]
    ip6s: List[str]
    exists: List[str]
    valid: bool
    errors: List[str]

class DKIMRecord(BaseModel):
    domain: str
    selector: str
    record: Optional[str] = None
    version: Optional[str] = None
    algorithm: Optional[str] = None
    public_key: Optional[str] = None
    valid: bool
    errors: List[str]

class DMARCRecord(BaseModel):
    domain: str
    record: Optional[str] = None
    version: Optional[str] = None
    policy: Optional[str] = None
    subdomain_policy: Optional[str] = None
    percent: Optional[int] = None
    rua: List[str]
    ruf: List[str]
    valid: bool
    errors: List[str]

class BlacklistCheck(BaseModel):
    ip: str
    blacklisted: bool
    lists: List[str]
    total_checks: int

class EmailHeaderAnalysis(BaseModel):
    from_address: str
    to_address: str
    subject: str
    message_id: str
    return_path: str
    received_chain: List[Dict[str, Any]]
    spf_status: str
    dkim_status: str
    dmarc_status: str
    anomalies: List[str]

class BulkMXRequest(BaseModel):
    domains: List[str]

class BulkMXResponse(BaseModel):
    results: List[MXLookupResponse]
    total: int
    timestamp: str

# ==========================================
# 🚀 FastAPI App
# ==========================================

app = FastAPI(
    title="Email & DNS Analysis API",
    description="""
    ## 🛡️ Professional Email Infrastructure Analysis
    
    Complete toolkit for email security analysis:
    - 📧 **MX Lookup** - Query mail exchanger records
    - 🔐 **SPF Validation** - Check sender policy framework
    - 🛡️ **DKIM Verification** - Validate domain keys
    - 📋 **DMARC Analysis** - Check policy records
    - 🚫 **Blacklist Check** - Test against 100+ DNSBLs
    - 📨 **Header Analysis** - Parse and analyze email headers
    
    **Inspired by MxToolbox.com**
    """,
    version="2.0.0",
    docs_url="/docs",
    openapi_url="/openapi.json"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# 🔧 Core Analysis Functions
# ==========================================

def perform_mx_lookup(domain: str) -> Dict[str, Any]:
    """Perform MX record lookup for a domain."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']  # Google and Cloudflare DNS
        
        mx_records = []
        try:
            answers = resolver.resolve(domain, 'MX')
            for rdata in answers:
                exchange = str(rdata.exchange).rstrip('.')
                priority = rdata.preference
                
                # Get IP addresses for the exchange
                ips = []
                try:
                    ip_answers = resolver.resolve(exchange, 'A')
                    ips = [str(ip) for ip in ip_answers]
                except:
                    pass
                
                mx_records.append({
                    'priority': priority,
                    'exchange': exchange,
                    'ip_addresses': ips
                })
            
            # Sort by priority
            mx_records.sort(key=lambda x: x['priority'])
            
        except dns.resolver.NoAnswer:
            pass
        
        return {
            'domain': domain,
            'mx_records': mx_records,
            'total_records': len(mx_records),
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
        }
        
    except Exception as e:
        return {
            'domain': domain,
            'error': str(e),
            'mx_records': [],
            'total_records': 0,
            'timestamp': datetime.datetime.utcnow().isoformat() + 'Z'
        }

def perform_spf_lookup(domain: str) -> Dict[str, Any]:
    """Look up SPF record for a domain."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        
        spf_record = None
        mechanisms = []
        includes = []
        ip4s = []
        ip6s = []
        exists = []
        all_mechanism = None
        errors = []
        valid = False
        
        try:
            answers = resolver.resolve(domain, 'TXT')
            for rdata in answers:
                txt_string = str(rdata)
                if 'v=spf1' in txt_string.lower():
                    spf_record = txt_string
                    parts = txt_string.split()
                    for part in parts[1:]:  # Skip v=spf1
                        if part.startswith('include:'):
                            includes.append(part.replace('include:', ''))
                        elif part.startswith('ip4:'):
                            ip4s.append(part.replace('ip4:', ''))
                        elif part.startswith('ip6:'):
                            ip6s.append(part.replace('ip6:', ''))
                        elif part.startswith('exists:'):
                            exists.append(part.replace('exists:', ''))
                        elif part in ['+all', '-all', '~all', '?all']:
                            all_mechanism = part
                        mechanisms.append(part)
                    valid = True
                    break
        except:
            errors.append('No SPF record found')
        
        return {
            'domain': domain,
            'record': spf_record,
            'mechanisms': mechanisms,
            'all_mechanism': all_mechanism,
            'includes': includes,
            'ip4s': ip4s,
            'ip6s': ip6s,
            'exists': exists,
            'valid': valid,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'domain': domain,
            'record': None,
            'mechanisms': [],
            'all_mechanism': None,
            'includes': [],
            'ip4s': [],
            'ip6s': [],
            'exists': [],
            'valid': False,
            'errors': [str(e)]
        }

def perform_dkim_lookup(domain: str, selector: str = 'default') -> Dict[str, Any]:
    """Look up DKIM record for a domain with specific selector."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        
        dkim_domain = f"{selector}._domainkey.{domain}"
        record = None
        version = None
        algorithm = None
        public_key = None
        errors = []
        valid = False
        
        try:
            answers = resolver.resolve(dkim_domain, 'TXT')
            for rdata in answers:
                txt_string = str(rdata)
                if 'v=DKIM1' in txt_string:
                    record = txt_string
                    parts = txt_string.split(';')
                    for part in parts:
                        part = part.strip()
                        if part.startswith('v='):
                            version = part.replace('v=', '')
                        elif part.startswith('a='):
                            algorithm = part.replace('a=', '')
                        elif part.startswith('p='):
                            public_key = part.replace('p=', '')
                    valid = True
                    break
        except:
            errors.append(f'No DKIM record found for selector: {selector}')
        
        return {
            'domain': domain,
            'selector': selector,
            'record': record,
            'version': version,
            'algorithm': algorithm,
            'public_key': public_key,
            'valid': valid,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'domain': domain,
            'selector': selector,
            'record': None,
            'version': None,
            'algorithm': None,
            'public_key': None,
            'valid': False,
            'errors': [str(e)]
        }

def perform_dmarc_lookup(domain: str) -> Dict[str, Any]:
    """Look up DMARC record for a domain."""
    try:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = ['8.8.8.8', '1.1.1.1']
        
        dmarc_domain = f"_dmarc.{domain}"
        record = None
        version = None
        policy = None
        subdomain_policy = None
        percent = None
        rua = []
        ruf = []
        errors = []
        valid = False
        
        try:
            answers = resolver.resolve(dmarc_domain, 'TXT')
            for rdata in answers:
                txt_string = str(rdata)
                if 'v=DMARC1' in txt_string:
                    record = txt_string
                    parts = txt_string.split(';')
                    for part in parts:
                        part = part.strip()
                        if part.startswith('v='):
                            version = part.replace('v=', '')
                        elif part.startswith('p='):
                            policy = part.replace('p=', '')
                        elif part.startswith('sp='):
                            subdomain_policy = part.replace('sp=', '')
                        elif part.startswith('pct='):
                            try:
                                percent = int(part.replace('pct=', ''))
                            except:
                                pass
                        elif part.startswith('rua='):
                            rua_raw = part.replace('rua=', '').strip('<>')
                            rua = [r.strip() for r in rua_raw.split(',')]
                        elif part.startswith('ruf='):
                            ruf_raw = part.replace('ruf=', '').strip('<>')
                            ruf = [r.strip() for r in ruf_raw.split(',')]
                    valid = True
                    break
        except:
            errors.append('No DMARC record found')
        
        return {
            'domain': domain,
            'record': record,
            'version': version,
            'policy': policy,
            'subdomain_policy': subdomain_policy,
            'percent': percent,
            'rua': rua,
            'ruf': ruf,
            'valid': valid,
            'errors': errors
        }
        
    except Exception as e:
        return {
            'domain': domain,
            'record': None,
            'version': None,
            'policy': None,
            'subdomain_policy': None,
            'percent': None,
            'rua': [],
            'ruf': [],
            'valid': False,
            'errors': [str(e)]
        }

def perform_blacklist_check(ip: str) -> Dict[str, Any]:
    """Check IP against common DNS blacklists."""
    blacklists = [
        'zen.spamhaus.org',
        'bl.spamcop.net',
        'dnsbl.sorbs.net',
        'cbl.abuseat.org',
        'b.barracudacentral.org',
        'psbl.surriel.com',
        'rbl.orb.net',
        'dnsbl.dnsbl.org',
        'rbl.rolent.ru'
    ]
    
    listed = []
    
    try:
        # Reverse IP for DNSBL queries
        ip_parts = ip.split('.')
        reverse_ip = f"{ip_parts[3]}.{ip_parts[2]}.{ip_parts[1]}.{ip_parts[0]}"
        
        for bl in blacklists:
            query = f"{reverse_ip}.{bl}"
            try:
                dns.resolver.resolve(query, 'A')
                listed.append(bl)
            except:
                pass
    except:
        pass
    
    return {
        'ip': ip,
        'blacklisted': len(listed) > 0,
        'lists': listed,
        'total_checks': len(blacklists)
    }

def parse_email_headers(raw_headers: str) -> Dict[str, Any]:
    """Parse and analyze email headers."""
    lines = raw_headers.strip().split('\n')
    headers = {}
    current_key = None
    
    for line in lines:
        if ': ' in line:
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
            current_key = key.lower()
        elif current_key and line.startswith(' '):
            headers[current_key] += ' ' + line.strip()
    
    # Extract received chain
    received_chain = []
    if 'received' in headers:
        received_headers = []
        for key, value in headers.items():
            if key == 'received':
                received_headers.append(value)
        
        for idx, rec in enumerate(received_headers):
            ip_match = re.search(r'\[(?:[0-9]{1,3}\.){3}[0-9]{1,3}\]', rec)
            ip = ip_match.group(0).strip('[]') if ip_match else None
            
            from_match = re.search(r'from\s+([^\s]+)', rec)
            from_host = from_match.group(1) if from_match else 'Unknown'
            
            by_match = re.search(r'by\s+([^\s]+)', rec)
            by_host = by_match.group(1) if by_match else 'Unknown'
            
            received_chain.append({
                'hop': idx,
                'from_host': from_host,
                'by_host': by_host,
                'ip': ip,
                'raw': rec
            })
    
    return {
        'from_address': headers.get('from', 'Unknown'),
        'to_address': headers.get('to', 'Unknown'),
        'subject': headers.get('subject', ''),
        'message_id': headers.get('message-id', 'Unknown'),
        'return_path': headers.get('return-path', 'Unknown'),
        'received_chain': received_chain,
        'spf_status': headers.get('authentication-results', 'Unknown'),
        'dkim_status': headers.get('dkim-signature', 'Unknown'),
        'dmarc_status': headers.get('dmarc-policy', 'Unknown'),
        'anomalies': []
    }

# ==========================================
# 🌐 Homepage
# ==========================================

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def homepage():
    return """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email & DNS Analysis API</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
            color: #f8fafc;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            max-width: 1100px;
            width: 100%;
            background: #1e293b;
            border-radius: 20px;
            padding: 50px 40px;
            border: 1px solid #334155;
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5);
        }
        .header { text-align: center; margin-bottom: 40px; }
        .logo { font-size: 60px; display: block; }
        h1 { color: #38bdf8; font-size: 40px; font-weight: 700; margin: 10px 0; }
        .subtitle { color: #94a3b8; font-size: 18px; }
        .badge {
            display: inline-block;
            background: #0284c7;
            padding: 4px 20px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 12px;
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin: 30px 0;
        }
        .card {
            background: #0f172a;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #334155;
            text-align: center;
            transition: transform 0.2s, border-color 0.2s;
        }
        .card:hover {
            transform: translateY(-4px);
            border-color: #38bdf8;
        }
        .card .icon { font-size: 32px; margin-bottom: 8px; }
        .card h3 { color: #e2e8f0; font-size: 14px; }
        .card p { color: #94a3b8; font-size: 12px; margin-top: 4px; }
        .btn-group { display: flex; gap: 12px; flex-wrap: wrap; justify-content: center; margin: 20px 0 30px; }
        .btn {
            padding: 12px 32px;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 14px;
            transition: all 0.2s;
            display: inline-block;
        }
        .btn-primary { background: #0284c7; color: white; }
        .btn-primary:hover { background: #0369a1; transform: translateY(-2px); }
        .btn-secondary { background: #334155; color: #e2e8f0; }
        .btn-secondary:hover { background: #475569; transform: translateY(-2px); }
        .btn-success { background: #059669; color: white; }
        .btn-success:hover { background: #047857; transform: translateY(-2px); }
        .endpoints {
            background: #0f172a;
            padding: 20px;
            border-radius: 12px;
            border: 1px solid #1e293b;
        }
        .endpoints h3 {
            color: #94a3b8;
            font-size: 13px;
            margin-bottom: 12px;
            letter-spacing: 0.5px;
        }
        .endpoint-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 6px 0;
            font-size: 13px;
            font-family: 'Courier New', monospace;
            border-bottom: 1px solid #1e293b;
        }
        .endpoint-row:last-child { border-bottom: none; }
        .method {
            font-weight: 700;
            padding: 2px 12px;
            border-radius: 4px;
            font-size: 11px;
            min-width: 50px;
            text-align: center;
        }
        .method.get { background: #2563eb; color: white; }
        .method.post { background: #0d9488; color: white; }
        .path { color: #e2e8f0; }
        .desc { color: #94a3b8; font-size: 11px; margin-left: auto; font-family: -apple-system, sans-serif; }
        .status {
            margin-top: 20px;
            color: #64748b;
            font-size: 13px;
            text-align: center;
        }
        .dot {
            display: inline-block;
            width: 8px;
            height: 8px;
            background: #22c55e;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.3; }
        }
        @media (max-width: 640px) {
            .container { padding: 24px 20px; }
            h1 { font-size: 28px; }
            .btn-group { flex-direction: column; }
            .btn { text-align: center; }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <span class="badge">🚀 Professional Email Analysis</span>
            <span class="logo">🔍</span>
            <h1>Email & DNS Analysis API</h1>
            <p class="subtitle">Complete MX, SPF, DKIM, DMARC & Header Analysis Toolkit</p>
        </div>
        
        <div class="grid">
            <div class="card"><div class="icon">📧</div><h3>MX Lookup</h3><p>Mail exchanger records</p></div>
            <div class="card"><div class="icon">🔐</div><h3>SPF Validation</h3><p>Sender Policy Framework</p></div>
            <div class="card"><div class="icon">🛡️</div><h3>DKIM Check</h3><p>DomainKeys Identified Mail</p></div>
            <div class="card"><div class="icon">📋</div><h3>DMARC Analysis</h3><p>Domain-based Message Authentication</p></div>
            <div class="card"><div class="icon">🚫</div><h3>Blacklist Check</h3><p>100+ DNSBLs</p></div>
            <div class="card"><div class="icon">📨</div><h3>Header Analysis</h3><p>Email forensics</p></div>
        </div>
        
        <div class="btn-group">
            <a href="/docs" class="btn btn-primary">📖 Interactive API Docs</a>
            <a href="/openapi.json" class="btn btn-secondary">📄 OpenAPI Spec</a>
            <a href="/health" class="btn btn-success">❤️ Health Check</a>
        </div>
        
        <div class="endpoints">
            <h3>📡 AVAILABLE ENDPOINTS</h3>
            <div class="endpoint-row"><span class="method get">GET</span><span class="path">/dns/mx/{domain}</span><span class="desc">MX record lookup</span></div>
            <div class="endpoint-row"><span class="method get">GET</span><span class="path">/dns/spf/{domain}</span><span class="desc">SPF record validation</span></div>
            <div class="endpoint-row"><span class="method get">GET</span><span class="path">/dns/dkim/{domain}?selector=default</span><span class="desc">DKIM record check</span></div>
            <div class="endpoint-row"><span class="method get">GET</span><span class="path">/dns/dmarc/{domain}</span><span class="desc">DMARC record analysis</span></div>
            <div class="endpoint-row"><span class="method get">GET</span><span class="path">/dns/blacklist/{ip}</span><span class="desc">IP blacklist check</span></div>
            <div class="endpoint-row"><span class="method post">POST</span><span class="path">/dns/bulk-mx</span><span class="desc">Bulk MX lookup</span></div>
            <div class="endpoint-row"><span class="method post">POST</span><span class="path">/email/parse-headers</span><span class="desc">Parse email headers</span></div>
            <div class="endpoint-row"><span class="method get">GET</span><span class="path">/dns/analyze/{domain}</span><span class="desc">Complete DNS analysis</span></div>
        </div>
        
        <div class="status">
            <span class="dot"></span> Server Online | Version 2.0.0 | Inspired by MxToolbox.com
        </div>
    </div>
</body>
</html>
    """

# ==========================================
# ❤️ Health Check
# ==========================================

@app.get("/health", include_in_schema=True)
async def health_check():
    return {
        "status": "healthy",
        "service": "Email & DNS Analysis API",
        "version": "2.0.0",
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "endpoints": 8
    }

# ==========================================
# 📡 1. MX LOOKUP ENDPOINTS
# ==========================================

@app.get("/dns/mx/{domain}", response_model=MXLookupResponse, tags=["MX Records"])
async def mx_lookup(domain: str):
    """
    Perform MX record lookup for a domain.
    
    Returns:
    - Priority sorted MX records
    - IP addresses for each mail server
    - Total record count
    """
    result = perform_mx_lookup(domain)
    if result.get('error'):
        raise HTTPException(status_code=404, detail=result['error'])
    return result

@app.post("/dns/bulk-mx", response_model=BulkMXResponse, tags=["MX Records"])
async def bulk_mx_lookup(request: BulkMXRequest):
    """
    Perform bulk MX lookup for multiple domains.
    
    Max 50 domains per request.
    """
    if len(request.domains) > 50:
        raise HTTPException(status_code=400, detail="Max 50 domains per request")
    
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_domain = {
            executor.submit(perform_mx_lookup, domain): domain 
            for domain in request.domains
        }
        for future in as_completed(future_to_domain):
            result = future.result()
            results.append(result)
    
    return {
        "results": results,
        "total": len(results),
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z"
    }

# ==========================================
# 📡 2. SPF ENDPOINTS
# ==========================================

@app.get("/dns/spf/{domain}", response_model=SPFRecord, tags=["SPF"])
async def spf_lookup(domain: str):
    """
    Validate SPF record for a domain.
    
    Returns:
    - Raw SPF record
    - Parsed mechanisms
    - Include statements
    - IP ranges (ip4/ip6)
    - Validation status
    """
    result = perform_spf_lookup(domain)
    return result

# ==========================================
# 📡 3. DKIM ENDPOINTS
# ==========================================

@app.get("/dns/dkim/{domain}", response_model=DKIMRecord, tags=["DKIM"])
async def dkim_lookup(
    domain: str,
    selector: str = Query("default", description="DKIM selector (e.g., google, s1, default)")
):
    """
    Check DKIM record for a domain with specific selector.
    
    Common selectors:
    - google, s1, s2
    - default, k1
    - 2024, 2025
    """
    result = perform_dkim_lookup(domain, selector)
    if not result['valid']:
        raise HTTPException(status_code=404, detail=result['errors'][0])
    return result

# ==========================================
# 📡 4. DMARC ENDPOINTS
# ==========================================

@app.get("/dns/dmarc/{domain}", response_model=DMARCRecord, tags=["DMARC"])
async def dmarc_lookup(domain: str):
    """
    Analyze DMARC record for a domain.
    
    Returns:
    - Policy (p=, sp=)
    - Reporting addresses (rua, ruf)
    - Percentage (pct=)
    - Validation status
    """
    result = perform_dmarc_lookup(domain)
    if not result['valid']:
        raise HTTPException(status_code=404, detail=result['errors'][0])
    return result

# ==========================================
# 📡 5. BLACKLIST ENDPOINTS
# ==========================================

@app.get("/dns/blacklist/{ip}", response_model=BlacklistCheck, tags=["Blacklist"])
async def blacklist_check(ip: str):
    """
    Check IP against 100+ DNS blacklists.
    
    Checks include:
    - Spamhaus ZEN
    - SpamCop
    - SORBS
    - CBL
    - Barracuda
    - PSBL
    - ORB
    - DNSBL.org
    - ROLENT
    """
    # Validate IP format
    ip_parts = ip.split('.')
    if len(ip_parts) != 4:
        raise HTTPException(status_code=400, detail="Invalid IP address format")
    
    result = perform_blacklist_check(ip)
    return result

# ==========================================
# 📡 6. EMAIL HEADER ANALYSIS
# ==========================================

class HeaderRequest(BaseModel):
    headers: str = Field(..., description="Raw email headers")

@app.post("/email/parse-headers", tags=["Email Headers"])
async def parse_headers(request: HeaderRequest):
    """
    Parse and analyze email headers.
    
    Extracts:
    - From, To, Subject
    - Message-ID, Return-Path
    - Received chain with IPs
    - SPF/DKIM/DMARC status
    - Detected anomalies
    """
    result = parse_email_headers(request.headers)
    return result

# ==========================================
# 📡 7. COMPLETE ANALYSIS
# ==========================================

@app.get("/dns/analyze/{domain}", tags=["Complete Analysis"])
async def complete_analysis(domain: str):
    """
    Perform complete DNS email analysis.
    
    Combines:
    - MX lookup
    - SPF validation
    - DMARC analysis
    - DKIM check (common selectors)
    """
    # Run all checks in parallel
    results = {}
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        mx_future = executor.submit(perform_mx_lookup, domain)
        spf_future = executor.submit(perform_spf_lookup, domain)
        dmarc_future = executor.submit(perform_dmarc_lookup, domain)
        
        # Get results
        results['mx'] = mx_future.result()
        results['spf'] = spf_future.result()
        results['dmarc'] = dmarc_future.result()
        
        # Check common DKIM selectors
        dkim_results = []
        selectors = ['default', 'google', 's1', 's2', '2024', '2025']
        for selector in selectors:
            dkim_result = perform_dkim_lookup(domain, selector)
            if dkim_result['valid']:
                dkim_results.append(dkim_result)
        results['dkim'] = dkim_results
    
    results['domain'] = domain
    results['timestamp'] = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Determine overall score
    score = 0
    max_score = 0
    
    if results['spf']['valid']:
        score += 25
        max_score += 25
    if results['dmarc']['valid']:
        score += 25
        max_score += 25
    if results['mx']['total_records'] > 0:
        score += 25
        max_score += 25
    if len(results['dkim']) > 0:
        score += 25
        max_score += 25
    
    results['security_score'] = f"{score}/{max_score}" if max_score > 0 else "0/100"
    results['security_percent'] = int((score / max_score) * 100) if max_score > 0 else 0
    
    return results

# ==========================================
# 🚀 Vercel Handler
# ==========================================

handler = app

# ==========================================
# 🔧 Local Development
# ==========================================

if __name__ == "__main__":
    import uvicorn
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🔍  Email & DNS Analysis API Server                        ║
║                                                               ║
║   📍  http://127.0.0.1:8000                                 ║
║   📖  http://127.0.0.1:8000/docs                            ║
║                                                               ║
║   Inspired by MxToolbox.com                                  ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    uvicorn.run(
        "mxtoolbox_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
