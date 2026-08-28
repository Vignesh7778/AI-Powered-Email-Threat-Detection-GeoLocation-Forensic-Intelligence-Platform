from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_extract_and_score_links():
    html_content = """
    <html>
        <body>
            <p>Please update your billing info here: <a href="http://192.168.1.100/login">https://paypal.com/update</a></p>
            <p>Short link: <a href="https://bit.ly/3xY90abc">Click Here</a></p>
            <p>Safe link: <a href="https://google.com">Google</a></p>
        </body>
    </html>
    """
    response = client.post("/ml/links/extract-and-score", json={"body_html": html_content})
    assert response.status_code == 200
    data = response.json()
    assert "links" in data
    assert len(data["links"]) >= 3

    # Check the IP literal / mismatched link
    ip_link = next((l for l in data["links"] if "192.168.1.100" in l["actual_url"]), None)
    assert ip_link is not None
    assert ip_link["obfuscated"] is True
    assert ip_link["risk_score"] > 0.5
    assert "ip_literal_host" in ip_link["reasons"] or "mismatched_display_text" in ip_link["reasons"]

    # Check the shortener link
    short_link = next((l for l in data["links"] if "bit.ly" in l["actual_url"]), None)
    assert short_link is not None
    assert "url_shortener" in short_link["reasons"]

