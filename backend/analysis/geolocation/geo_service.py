import ipaddress
import json
import os
import urllib.request
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from backend.app.schemas.schemas import GeoLocation

class GeoLocationProvider:
    """
    Strict Zero-Hallucination IP Geolocation & Network Intelligence Provider.
    Queries live IP intelligence providers (ip-api / ipinfo) with in-memory caching.
    Never uses hardcoded locations or fake data.
    """

    def __init__(self):
        self._cache: Dict[str, GeoLocation] = {}
        self._token: Optional[str] = os.environ.get("IPINFO_TOKEN")

    def is_private_or_invalid(self, ip: str) -> bool:
        try:
            ip_obj = ipaddress.ip_address(ip)
            return ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local
        except ValueError:
            return True

    def lookup(self, ip: Optional[str]) -> GeoLocation:
        queried_at = datetime.now(timezone.utc).isoformat()
        if not ip or not isinstance(ip, str) or not ip.strip():
            return GeoLocation(
                country="Unknown",
                region="Unknown",
                city="Unknown",
                isp="Unknown",
                hosting_provider=None,
                lat=None,
                lon=None,
                asn=None,
                status="empty_ip",
                provenance={"provider": "input_validator", "queried_at": queried_at, "status": "empty"}
            )

        ip = ip.strip()

        # Check Cache
        if ip in self._cache:
            return self._cache[ip]

        # RFC 1918 / Private network check
        if self.is_private_or_invalid(ip):
            res = GeoLocation(
                country="Private / Internal Network",
                region="Internal Subnet",
                city="Non-Routable IP (RFC 1918)",
                isp="Private Infrastructure",
                hosting_provider="Local / Enterprise LAN",
                lat=None,
                lon=None,
                asn="Private-AS",
                status="private_ip",
                provenance={
                    "provider": "rfc1918_filter",
                    "queried_at": queried_at,
                    "status": "non_routable",
                    "detail": "IP address belongs to an internal, non-routable private address range."
                }
            )
            self._cache[ip] = res
            return res

        # Try ip-api.com live endpoint
        try:
            url = f"http://ip-api.com/json/{ip}?fields=status,message,country,countryCode,regionName,city,lat,lon,isp,org,as,hosting,proxy,query"
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "TraceX-Forensic-Intelligence-Platform/1.0", "Accept": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode('utf-8'))
                    if data.get("status") == "success":
                        hosting_flag = "Hosting / Data Center" if data.get("hosting") else "Residential / Business Broadband"
                        if data.get("proxy"):
                            hosting_flag += " (Proxy/VPN Detected)"
                            
                        res = GeoLocation(
                            country=data.get("country") or "Unknown",
                            region=data.get("regionName") or "Unknown",
                            city=data.get("city") or "Unknown",
                            isp=data.get("isp") or data.get("org") or "Unknown ISP",
                            hosting_provider=hosting_flag,
                            lat=float(data.get("lat")) if data.get("lat") is not None else None,
                            lon=float(data.get("lon")) if data.get("lon") is not None else None,
                            asn=data.get("as") or "Unknown ASN",
                            status="verified",
                            provenance={
                                "provider": "ip-api.com",
                                "queried_at": queried_at,
                                "response_status": "verified",
                                "country_code": data.get("countryCode"),
                                "is_hosting": bool(data.get("hosting")),
                                "is_proxy": bool(data.get("proxy"))
                            }
                        )
                        self._cache[ip] = res
                        return res
        except Exception:
            pass

        # Fallback to ipinfo.io if token is provided
        if self._token:
            try:
                url = f"https://ipinfo.io/{ip}/json?token={self._token}"
                req = urllib.request.Request(url, headers={"Accept": "application/json"})
                with urllib.request.urlopen(req, timeout=3.0) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode('utf-8'))
                        loc = data.get("loc", "").split(",")
                        lat = float(loc[0]) if len(loc) == 2 else None
                        lon = float(loc[1]) if len(loc) == 2 else None
                        res = GeoLocation(
                            country=data.get("country") or "Unknown",
                            region=data.get("region") or "Unknown",
                            city=data.get("city") or "Unknown",
                            isp=data.get("org") or "Unknown Org",
                            hosting_provider=None,
                            lat=lat,
                            lon=lon,
                            asn=data.get("org", "").split()[0] if data.get("org") else None,
                            status="verified",
                            provenance={"provider": "ipinfo.io", "queried_at": queried_at}
                        )
                        self._cache[ip] = res
                        return res
            except Exception:
                pass

        # If live API is unreachable or rate limited, return UNKNOWN (NEVER FAKE!)
        res = GeoLocation(
            country="Unavailable",
            region="Unavailable",
            city="Unavailable",
            isp="Unavailable",
            hosting_provider=None,
            lat=None,
            lon=None,
            asn="Unavailable",
            status="unavailable",
            provenance={
                "provider": "geoip_resolver",
                "queried_at": queried_at,
                "response_status": "unavailable",
                "detail": "Live GeoIP provider timed out or was unreachable."
            }
        )
        self._cache[ip] = res
        return res

geo_service = GeoLocationProvider()
