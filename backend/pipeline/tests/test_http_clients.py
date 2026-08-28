import httpx

from app.services.clients import ForensicsHttpClient, MlHttpClient


def test_forensics_client_uses_documented_contract_paths():
    paths = []

    def responder(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        payloads = {
            "/forensics/headers/parse": {"from_address": "Finance <accounts@aicte-finance.co>", "return_path": "<reply@relay.co>", "reply_to": None, "message_id": "x", "received_chain": [{"hop": 0, "ip": "45.83.64.12", "from_host": "relay"}], "anomalies": []},
            "/forensics/auth/validate": {"spf": {"result": "fail"}, "dkim": {"result": "none"}, "dmarc": {"result": "fail"}, "alignment_ok": False},
            "/forensics/origin/trace": {"originating_ip": "45.83.64.12", "confidence": .88, "reasoning": "first public hop"},
            "/forensics/geo/lookup": {"country": "Netherlands", "region": "North Holland", "city": "Amsterdam", "isp": "M247", "hosting_provider": "M247", "lat": 52.3, "lon": 4.9},
            "/forensics/infra/flags": {"flags": ["cloud_hosted"]},
            "/forensics/domain/intel": {"registrar": "PrivacyGuardian", "created_date": "2026-08-24T00:00:00Z", "age_days": 4, "mx_records": ["mx.aicte-finance.co"]},
            "/forensics/domain/lookalike-check": {"lookalike_of": "aicte.org", "score": .93},
        }
        return httpx.Response(200, json=payloads[request.url.path])

    client = ForensicsHttpClient("https://forensics.test", httpx.Client(base_url="https://forensics.test", transport=httpx.MockTransport(responder)))
    fields, relays, _ = client.parse_headers("From: Finance <accounts@aicte-finance.co>")
    auth = client.validate_authentication("From: Finance <accounts@aicte-finance.co>")
    origin = client.build_origin(relays)
    intel = client.domain_intelligence("aicte-finance.co", ["aicte.org"])
    assert fields["from_address"].startswith("Finance")
    assert auth.dmarc == "fail"
    assert origin.originating_ip == "45.83.64.12"
    assert intel.lookalike_of == "aicte.org"
    assert paths == ["/forensics/headers/parse", "/forensics/auth/validate", "/forensics/origin/trace", "/forensics/geo/lookup", "/forensics/infra/flags", "/forensics/domain/intel", "/forensics/domain/lookalike-check"]


def test_ml_client_uses_documented_contract_paths():
    paths = []

    def responder(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        if request.url.path == "/ml/nlp/analyze-content":
            return httpx.Response(200, json={"urgency_score": .8, "impersonation_language_score": .6, "detected_patterns": []})
        return httpx.Response(200, json={"links": []})

    client = MlHttpClient("https://ml.test", httpx.Client(base_url="https://ml.test", transport=httpx.MockTransport(responder)))
    urgency, impersonation, _ = client.nlp("Urgent", "Act now")
    links = client.links("<p>no links</p>")
    assert (urgency, impersonation, links) == (.8, .6, [])
    assert paths == ["/ml/nlp/analyze-content", "/ml/links/extract-and-score"]
