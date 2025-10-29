"""
fabric-model-reader.py
================================
Minimal Power BI MCP Server for querying and discovery (FastMCP)

Auth: Service Principal (Tenant ID + Client ID + Client Secret) via MSAL
Example prompts:
'How many measures are in the semantic model Y?'
'What is the DAX for measure Z?'
'What is the total sales by product category?'
"""

# region Imports
import json
import os
import time
import requests
from fastmcp import FastMCP
from typing import Optional, List, Dict, Any
import msal

# endregion

# region Configuration
mcp = FastMCP("powerbi-server")

POWERBI_API = "https://api.powerbi.com/v1.0/myorg"
FABRIC_API = "https://api.fabric.microsoft.com/v1"
PBI_SCOPE = "https://analysis.windows.net/powerbi/api/.default"
# endregion


# region Auth (Service Principal)
class _State:
    tenant_id: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    app: Optional[msal.ConfidentialClientApplication] = None
    access_token: Optional[str] = None
    expires_at: float = 0.0


STATE = _State()


def _init_app_from_env_if_possible():
    """
    Nếu chưa init mà env có đủ, thì tạo app từ ENV:
      PBI_TENANT_ID, PBI_CLIENT_ID, PBI_CLIENT_SECRET
    """
    if STATE.app:
        return
    tid = os.environ.get("PBI_TENANT_ID")
    cid = os.environ.get("PBI_CLIENT_ID")
    sec = os.environ.get("PBI_CLIENT_SECRET")
    if tid and cid and sec:
        _configure_sp(tid, cid, sec)


def _configure_sp(tenant_id: str, client_id: str, client_secret: str):
    STATE.tenant_id = tenant_id.strip()
    STATE.client_id = client_id.strip()
    STATE.client_secret = client_secret.strip()
    STATE.app = msal.ConfidentialClientApplication(
        client_id=STATE.client_id,
        authority=f"https://login.microsoftonline.com/{STATE.tenant_id}",
        client_credential=STATE.client_secret,
    )
    # Clear token cache
    STATE.access_token = None
    STATE.expires_at = 0.0


def _ensure_token() -> str:
    """
    Lấy/cấp mới access_token bằng MSAL Client Credentials.
    Cache token đến khi gần hết hạn thì cấp mới.
    """
    if not STATE.app:
        _init_app_from_env_if_possible()
    if not STATE.app:
        raise RuntimeError(
            "Chưa cấu hình Service Principal. "
            "Gọi tool connect_service_principal(...) hoặc set ENV PBI_TENANT_ID/PBI_CLIENT_ID/PBI_CLIENT_SECRET."
        )

    # còn hạn > 60s thì dùng tiếp
    if STATE.access_token and (STATE.expires_at - time.time() > 60):
        return STATE.access_token

    # cấp token mới
    result = STATE.app.acquire_token_for_client(scopes=[PBI_SCOPE])
    if "access_token" not in result:
        raise RuntimeError(result.get("error_description") or str(result))

    STATE.access_token = result["access_token"]
    # MSAL có thể trả expires_in (giây) hoặc expires_on; ưu tiên expires_in
    expires_in = result.get("expires_in")
    if expires_in:
        STATE.expires_at = time.time() + int(expires_in)
    else:
        # fallback an toàn 50 phút
        STATE.expires_at = time.time() + 50 * 60
    return STATE.access_token


def _auth_headers() -> Dict[str, str]:
    token = _ensure_token()
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


session = requests.Session()
# endregion


# region HTTP helpers
def make_request(url: str, method: str = "GET", data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    HTTP helper có kèm refresh token tự động.
    """
    try:
        headers = _auth_headers()
    except Exception as e:
        return {"error": f"Auth error: {e}"}

    try:
        resp = session.request(method, url, json=data, headers=headers)
        if resp.ok:
            return resp.json() if resp.content else {}
        # Nếu 401/403 thì thử refresh thêm lần nữa
        if resp.status_code in (401, 403):
            try:
                # ép lấy token mới ngay
                STATE.access_token = None
                _ensure_token()
                headers = _auth_headers()
                resp2 = session.request(method, url, json=data, headers=headers)
                if resp2.ok:
                    return resp2.json() if resp2.content else {}
                return {"error": f"HTTP {resp2.status_code}: {resp2.text[:200]}"}
            except Exception as e:
                return {"error": f"Auth refresh failed: {e}"}
        return {"error": f"HTTP {resp.status_code}: {resp.text[:200]}"}
    except Exception as e:
        return {"error": str(e)}


def wait_for_operation(location_url: str, retry_seconds: int = 30) -> Dict[str, Any]:
    """
    Poll LRO đến khi Succeeded/Failed, luôn gửi kèm Authorization header hợp lệ.
    """
    while True:
        time.sleep(retry_seconds)
        try:
            headers = _auth_headers()
        except Exception as e:
            return {"error": f"Auth error: {e}"}

        r = session.get(location_url, headers=headers)
        if not r.ok:
            return {"error": f"Failed to check status: {r.status_code}"}

        data = r.json()
        status = (data.get("status") or data.get("operationState") or "").capitalize()

        if status == "Succeeded":
            res = session.get(f"{location_url.rstrip('/')}/result", headers=headers)
            return res.json() if res.ok else {"error": f"Failed to get result: {res.status_code}"}
        if status in ("Failed", "Error"):
            return {"error": data.get("error") or data}


# endregion


# region MCP Tool: connect SP
@mcp.tool()
def connect_service_principal(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Cấu hình Service Principal và lấy access token (client credentials).
    Gọi tool này 1 lần trước khi gọi các tool khác, hoặc set ENV:
      PBI_TENANT_ID / PBI_CLIENT_ID / PBI_CLIENT_SECRET
    """
    try:
        _configure_sp(tenant_id, client_id, client_secret)
        tok = _ensure_token()
        return "Connected: acquired Power BI access token via service principal."
    except Exception as e:
        # clear on failure
        STATE.access_token = None
        STATE.expires_at = 0.0
        STATE.app = None
        return f"Error acquiring token: {e}"


# endregion


# region MCP Tools (unchanged behavior, now using SP auth)
@mcp.tool()
def get_model_definition(
    workspace_id: str,
    dataset_id: str,
    file_filter: Optional[str] = None,
    page: Optional[int] = None,
    page_size: int = 10,
    metadata_only: bool = False,
    file_range: Optional[str] = None,
) -> str:
    """
    Get the TMDL definition of a semantic model with pagination and filtering support.
    """
    url = f"{FABRIC_API}/workspaces/{workspace_id}/semanticModels/{dataset_id}/getDefinition"

    # Start LRO
    headers = None
    try:
        headers = _auth_headers()
    except Exception as e:
        return f"Error: {e}"

    response = session.post(url, headers=headers)
    if response.status_code == 202:
        location_header = response.headers.get("Location")
        retry_after = int(response.headers.get("Retry-After", 30))
        if location_header:
            result = wait_for_operation(location_header, retry_after)
        else:
            return "Error: No Location header in 202 response"
    elif response.ok:
        result = response.json()
    else:
        return f"Error: HTTP {response.status_code}: {response.text[:200]}"

    if isinstance(result, dict) and "error" in result:
        return f"Error: {result['error']}"

    # Extract & decode TMDL parts
    all_parts = result.get("definition", {}).get("parts", [])
    if not all_parts:
        return "No model definition found"

    tmdl_parts = [p for p in all_parts if p.get("path", "").endswith(".tmdl")]

    if file_filter:
        tmdl_parts = [p for p in tmdl_parts if file_filter.lower() in p.get("path", "").lower()]

    total_parts = len(tmdl_parts)

    # Pagination math
    start_idx = 0
    end_idx = total_parts
    total_pages = 1

    if file_range and page:
        return "Error: Please use either 'page' or 'file_range', not both"

    if file_range:
        try:
            start_file, end_file = map(int, file_range.split("-"))
            start_idx = start_file - 1
            end_idx = min(end_file, total_parts)
        except ValueError:
            return "Error: Invalid file_range format. Use '1-10' or '11-20'"
    else:
        if page is None:
            page = 1
        total_pages = ((total_parts + page_size - 1) // page_size) if page_size > 0 else 1
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, total_parts)

    page_parts = tmdl_parts[start_idx:end_idx]

    output = [
        f"Dataset Model Definition (TMDL Format)\n",
        f"{'='*40}\n",
    ]

    if file_range:
        output.append(f"File range: {file_range} | Total files: {total_parts}\n")
    else:
        current_page = page if page is not None else 1
        output.append(f"Page {current_page} of {total_pages} | Total files: {total_parts}\n")
        output.append(f"Page size: {page_size}\n")

    output.append(f"Filter: {file_filter or 'None'}\n")
    output.append(f"{'='*40}\n")

    if metadata_only:
        output.append("\nAvailable files:\n")
        for i, part in enumerate(tmdl_parts):
            marker = "→" if start_idx <= i < end_idx else " "
            output.append(f"{marker} {i+1}. {part['path']}\n")
    else:
        import base64

        for part in page_parts:
            try:
                content = base64.b64decode(part.get("payload", "")).decode("utf-8")
                output.extend([f"\n{'─'*40}\n", f"File: {part['path']}\n", f"{'─'*40}\n", content, "\n"])
            except Exception as e:
                output.append(f"\nError decoding {part.get('path', 'unknown')}: {str(e)}\n")

    # Navigation hints
    output.append(f"\n{'─'*40}\n")
    output.append("Navigation:\n")

    if file_range:
        current_end = end_idx
        if current_end < total_parts:
            next_start = current_end + 1
            next_end = min(current_end + (end_idx - start_idx), total_parts)
            output.append(f"→ Next range: Use file_range='{next_start}-{next_end}'\n")

        if start_idx > 0:
            prev_size = end_idx - start_idx
            prev_start = max(1, start_idx - prev_size + 1)
            prev_end = start_idx
            output.append(f"← Previous range: Use file_range='{prev_start}-{prev_end}'\n")

        output.append(f"\nSuggested ranges for complete retrieval:\n")
        range_size = 10
        for i in range(0, total_parts, range_size):
            range_start = i + 1
            range_end = min(i + range_size, total_parts)
            output.append(f"  file_range='{range_start}-{range_end}'\n")
    else:
        if total_pages > 1 and page is not None:
            if page > 1:
                output.append(f"← Previous page: Use page={page-1}\n")
            if page < total_pages:
                output.append(f"→ Next page: Use page={page+1}\n")
            output.append(f"\nTo jump to a specific page, use page=N (1 to {total_pages})\n")

    output.append("\nTo see only file list, use metadata_only=True\n")
    output.append("To filter files, use file_filter='search_term'\n")

    return "".join(output)


@mcp.tool()
def execute_dax_query(workspace_id: str, dataset_id: str, query: str) -> str:
    """
    Execute a DAX query against a Power BI dataset.
    Returns query results as JSON data.
    """
    url = f"{POWERBI_API}/groups/{workspace_id}/datasets/{dataset_id}/executeQueries"
    result = make_request(url, method="POST", data={"queries": [{"query": query}]})

    if "error" in result:
        return f"Error: {result['error']}"

    results = result.get("results", [])
    return json.dumps(results[0]["tables"], indent=2) if results and "tables" in results[0] else "No data returned"


# endregion

# region Main
if __name__ == "__main__":
    # Nếu bạn muốn cấu hình SP bằng ENV, set:
    #   export PBI_TENANT_ID=...
    #   export PBI_CLIENT_ID=...
    #   export PBI_CLIENT_SECRET=...
    # rồi chạy server. Hoặc gọi tool connect_service_principal từ client MCP.
    mcp.run()
# endregion
