import email
from email import policy
from email.parser import BytesParser
import hashlib
import os
import re
from typing import Dict, Any, List
from backend.app.schemas.schemas import AttachmentItem

class EmailParser:
    """
    RFC 5322 MIME Email Parser.
    Safely unpacks headers, plain text, HTML bodies, and attachment metadata
    without executing untrusted files. Resilient to international charsets and malformed parts.
    """

    @staticmethod
    def parse_raw_eml(eml_bytes: bytes, submission_id: str, storage_dir: str = "./data/storage") -> Dict[str, Any]:
        os.makedirs(storage_dir, exist_ok=True)
        try:
            msg = BytesParser(policy=policy.default).parsebytes(eml_bytes)
        except Exception:
            try:
                msg = email.message_from_bytes(eml_bytes)
            except Exception:
                msg = email.message_from_string(eml_bytes.decode('utf-8', errors='ignore'))

        # 1. Raw headers
        raw_headers = ""
        try:
            for k, v in msg.raw_items():
                raw_headers += f"{k}: {v}\n"
        except Exception:
            try:
                for k, v in msg.items():
                    raw_headers += f"{k}: {v}\n"
            except Exception:
                raw_headers = "From: unknown\nSubject: unknown\n"

        # 2. Extract bodies
        text_plain = ""
        text_html = ""

        try:
            body_part = msg.get_body(preferencelist=('plain', 'html'))
            if body_part:
                content = body_part.get_content()
                if body_part.get_content_type() == 'text/plain':
                    text_plain = str(content)
                elif body_part.get_content_type() == 'text/html':
                    text_html = str(content)
        except Exception:
            pass

        # Also search walk for HTML part if plain was preferred or if get_body failed
        try:
            for part in msg.walk():
                try:
                    ctype = part.get_content_type()
                    if ctype == 'text/html' and not text_html:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text_html = payload.decode('utf-8', errors='ignore')
                    elif ctype == 'text/plain' and not text_plain:
                        payload = part.get_payload(decode=True)
                        if payload:
                            text_plain = payload.decode('utf-8', errors='ignore')
                except Exception:
                    pass
        except Exception:
            pass

        # 3. Extract attachments metadata
        attachments: List[AttachmentItem] = []
        try:
            for part in msg.iter_attachments():
                try:
                    fname = part.get_filename() or "unnamed_attachment.bin"
                    ctype = part.get_content_type() or "application/octet-stream"
                    payload = part.get_payload(decode=True) or b""
                    sha256 = hashlib.sha256(payload).hexdigest()
                    size = len(payload)

                    safe_att_name = re.sub(r'[^a-zA-Z0-9_\.-]', '_', fname)[:60]
                    safe_fname = f"att_{submission_id[:8]}_{sha256[:8]}_{safe_att_name}"
                    att_path = os.path.join(storage_dir, safe_fname)
                    with open(att_path, "wb") as f:
                        f.write(payload)

                    attachments.append(
                        AttachmentItem(
                            filename=fname,
                            content_type=ctype,
                            sha256=sha256,
                            size_bytes=size,
                            storage_ref=att_path
                        )
                    )
                except Exception:
                    pass
        except Exception:
            pass

        # 4. Extract standard metadata
        sender = str(msg.get('from', '') or '')
        recipient = str(msg.get('to', '') or '')
        subject = str(msg.get('subject', '') or '')
        date_header = str(msg.get('date', '') or '')

        return {
            "raw_headers": raw_headers,
            "sender": sender,
            "recipient": recipient,
            "subject": subject,
            "date_header": date_header,
            "text_plain": text_plain,
            "text_html": text_html,
            "attachments": attachments
        }

email_parser = EmailParser()
