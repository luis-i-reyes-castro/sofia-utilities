from __future__ import annotations

import os
import requests

from pathlib import Path

from .class_wrappers import SafeWarningDict


type Attachment = tuple[ str, bytes, str ]


def render_template(
    path   : Path,
    params : dict[ str, object],
) -> str :
    
    template    = path.read_text( encoding = "utf-8")
    safe_params = SafeWarningDict(params)
    
    return template.format_map(safe_params)


def send_via_mailgun(
    *,
    to_email       : str,
    subject        : str,
    html_body      : str,
    mailgun_domain : str,
    from_email     : str,
    sender_name    : str | None = None,
    text_body      : str | None = None,
    bcc_to         : str | None = None,
    attachments    : list[Attachment] | None = None,
) -> None :
    
    if not ( mailgun_api_key := os.getenv("MG_API_KEY") ) :
        raise RuntimeError("Environment variable 'MG_API_KEY' was not found")
    
    if not mailgun_domain :
        raise ValueError("'mailgun_domain' must not be empty")
    
    if not from_email :
        raise ValueError("'from_email' must not be empty")
    
    payload = {
        "from"    : (
            f"{sender_name} <{from_email}>"
            if sender_name else
            from_email
        ),
        "to"      : to_email,
        "subject" : subject,
        "html"    : html_body,
    }
    
    if text_body is not None :
        payload["text"] = text_body
    
    if bcc_to :
        payload["bcc"] = bcc_to
    
    files_payload = [
        ( "attachment", ( filename, content, mime_type ) )
        for filename, content, mime_type in ( attachments or [] )
    ]
    
    response = requests.post(
        f"https://api.mailgun.net/v3/{mailgun_domain}/messages",
        auth    = ( "api", mailgun_api_key ),
        data    = payload,
        files   = files_payload or None,
        timeout = 45,
    )
    
    try :
        response.raise_for_status()
    
    except requests.HTTPError as ex :
        e_msg = f"Mailgun error ({response.status_code}): {response.text}"
        raise RuntimeError(e_msg) from ex
    
    return
