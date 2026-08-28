from typing import Dict, Any, Optional
from app.schemas.attachment import AttachmentScanRequest, AttachmentScanResponse

class AttachmentScanner:
    """
    Analyzes attachments by sha256 hash, storage ref, extension, and content_type
    for macro droppers, malicious executables, obfuscated scripts, and suspicious PDFs.
    """

    KNOWN_MALWARE_HASHES = {
        "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855": {
            "score": 0.99,
            "type": "known_malware_sample"
        },
        "44d88612fea8a8f36de82e1278abb02f": {
            "score": 0.95,
            "type": "trojan_dropper"
        }
    }

    HIGH_RISK_MIME_TYPES = {
        "application/x-msdownload": "executable_binary",
        "application/x-dosexec": "pe_executable",
        "application/vnd.ms-excel.sheet.macroEnabled.12": "macro_dropper",
        "application/vnd.ms-word.document.macroEnabled.12": "macro_dropper",
        "application/x-vbs": "vbs_script",
        "application/javascript": "obfuscated_js",
        "application/x-bat": "batch_script",
        "application/x-powershell": "powershell_payload",
        "application/x-iso9660-image": "iso_container",
        "application/x-7z-compressed": "compressed_archive",
        "application/zip": "zip_archive"
    }

    HIGH_RISK_EXTENSIONS = [
        ".exe", ".vbs", ".bat", ".cmd", ".ps1", ".xlsm", ".docm", ".iso", ".lnk", ".hta", ".scr", ".js"
    ]

    def scan(self, req: AttachmentScanRequest) -> AttachmentScanResponse:
        sha = req.sha256.lower().strip()
        ref = req.storage_ref.lower()
        mime = req.content_type.lower().strip()

        # 1. Known malware hash lookup
        if sha in self.KNOWN_MALWARE_HASHES:
            info = self.KNOWN_MALWARE_HASHES[sha]
            return AttachmentScanResponse(
                status="complete",
                malware_score=info["score"],
                detected_type=info["type"],
                sandbox_report_ref=f"reports/sandbox_{sha[:12]}.json"
            )

        # 2. Macro enabled documents or executables
        if mime in self.HIGH_RISK_MIME_TYPES:
            detected = self.HIGH_RISK_MIME_TYPES[mime]
            score = 0.85 if "macro" in detected or "executable" in detected or "payload" in detected else 0.45
            return AttachmentScanResponse(
                status="complete",
                malware_score=score,
                detected_type=detected,
                sandbox_report_ref=f"reports/sandbox_{sha[:12]}.json" if score > 0.5 else None
            )

        # 3. High risk extension in storage reference
        for ext in self.HIGH_RISK_EXTENSIONS:
            if ref.endswith(ext) or f"{ext}." in ref:
                detected_type = "macro_dropper" if "m" in ext else "executable"
                return AttachmentScanResponse(
                    status="complete",
                    malware_score=0.82,
                    detected_type=detected_type,
                    sandbox_report_ref=f"reports/sandbox_{sha[:12]}.json"
                )

        # 4. PDFs with potential active content / form scripts
        if "pdf" in mime or ref.endswith(".pdf"):
            # Check for suspicious naming like invoice_update.pdf
            if "invoice" in ref or "remit" in ref or "wire" in ref:
                return AttachmentScanResponse(
                    status="complete",
                    malware_score=0.35,
                    detected_type="financial_doc",
                    sandbox_report_ref=None
                )
            return AttachmentScanResponse(
                status="complete",
                malware_score=0.08,
                detected_type="none",
                sandbox_report_ref=None
            )

        # 5. Generic safe attachment
        return AttachmentScanResponse(
            status="complete",
            malware_score=0.02,
            detected_type="none",
            sandbox_report_ref=None
        )

attachment_scanner = AttachmentScanner()

