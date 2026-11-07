"""One bounded anonymous read; no scene mutation, credentials, retries or files."""
import json
import socket
import urllib.error
import urllib.parse
import urllib.request

MAX_BYTES = 131072


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main(query):
    if not isinstance(query, str) or not 3 <= len(query.strip()) <= 600:
        return {"success": False, "error": "invalid_query"}
    url = "https://veyrul.com/v1/context?" + urllib.parse.urlencode({
        "q": query.strip(), "detail": "compact", "limit": 3,
    })
    req = urllib.request.Request(url, headers={
        "Accept": "application/json", "User-Agent": "Veyrul-DCC-Media/0.1.0",
    })
    # Fixed origin, explicit redirect rejection and byte bounds are deliberate.
    # No inherited proxy credentials or environment-selected proxy is used.
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(req, timeout=10) as response:
            if response.headers.get_content_type() != "application/json":
                return {"success": False, "error": "unexpected_content_type"}
            raw = response.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            return {"success": False, "error": "response_too_large"}
        payload = json.loads(raw)
        if (not isinstance(payload, dict) or payload.get("schema") != "context/v1"
                or not isinstance(payload.get("records"), list)):
            return {"success": False, "error": "unexpected_response_shape"}
        return {"success": True, "context": payload,
                "source": "https://veyrul.com", "mode": "saved_public_knowledge"}
    except urllib.error.HTTPError as exc:
        return {"success": False, "error": "http_error", "status": exc.code}
    except (urllib.error.URLError, TimeoutError, socket.timeout):
        return {"success": False, "error": "service_unavailable"}
    except (ValueError, UnicodeError):
        return {"success": False, "error": "invalid_json"}


if __name__ == "__main__":
    from dcc_mcp_core.skill import run_main
    from dcc_mcp_core.skills_helper import skill_entry
    run_main(skill_entry(main))
