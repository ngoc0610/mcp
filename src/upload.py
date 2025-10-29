# region Imports
from __future__ import annotations

import os
import sys
import time
import json
import traceback
import requests
import msal
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

# Thử import Context cho type hints. Nếu không có SDK phù hợp, dùng Any để tránh NameError.
if TYPE_CHECKING:
    try:
        from mcp import Context as _Context
    except Exception:
        from typing import Any as _Context
else:
    _Context = Any  # runtime không cần class thật
# endregion


# region Small debug helper (log mọi uncaught exception ra stderr)
def _install_excepthook():
    def _hook(exctype, value, tb):
        print("UNCAUGHT EXCEPTION:", file=sys.stderr, flush=True)
        traceback.print_exception(exctype, value, tb, file=sys.stderr)
        sys.stderr.flush()
    sys.excepthook = _hook
_install_excepthook()
# endregion


# region Server & Constants
mcp = FastMCP("powerbi-server")

POWERBI_API = "https://api.powerbi.com/v1.0/myorg"
FABRIC_API  = "https://api.fabric.microsoft.com/v1"
PBI_SCOPE   = "https://analysis.windows.net/powerbi/api/.default"
# endregion

# region State
STATE = SimpleNamespace(
    tenant_id=None,
    client_id=None,
    client_secret=None,
    access_token=None,   # Bearer token hiện tại
    app=None,            # msal.ConfidentialClientApplication
    scopes=[PBI_SCOPE],
)
# endregion

# region Auth helpers
def _build_app(tenant_id: str, client_id: str, client_secret: str) -> msal.ConfidentialClientApplication:
    return msal.ConfidentialClientApplication(
        client_id=client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        client_credential=client_secret,
    )

def _acquire_token() -> str:
    if not STATE.app:
        raise RuntimeError("Not connected. Call connect_powerbi(...) first.")
    res = STATE.app.acquire_token_for_client(scopes=STATE.scopes)
    if "access_token" not in res:
        raise RuntimeError(res.get("error_description") or str(res))
    return res["access_token"]

def _ensure_token() -> str:
    if not STATE.access_token:
        STATE.access_token = _acquire_token()
    return STATE.access_token
# endregion

# region HTTP helpers (sync) – dùng cho các helper khác
def make_request(url: str, method: str = "GET", data: dict | None = None):
    """Simple HTTP helper using current access token."""
    try:
        token = _ensure_token()
    except Exception as e:
        return {"error": f"Auth error: {e}"}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers)
        else:
            resp = requests.post(url, headers=headers, json=data)

        if resp.ok:
            return resp.json() if resp.content else {}
        return {"error": f"HTTP {resp.status_code}: {resp.text[:500]}"}
    except Exception as e:
        return {"error": str(e)}

def wait_for_operation(location_url: str, retry_seconds: int = 30):
    """Poll long-running operation until Succeeded/Failed."""
    try:
        token = _ensure_token()
    except Exception as e:
        return {"error": f"Auth error: {e}"}

    headers = {"Authorization": f"Bearer {token}"}

    while True:
        time.sleep(retry_seconds)
        r = requests.get(location_url, headers=headers)
        if not r.ok:
            return {"error": f"Failed to check status: {r.status_code} {r.text[:300]}"}

        data = r.json()
        status = (data.get("status") or data.get("operationState") or "").capitalize()

        if status == "Succeeded":
            res = requests.get(f"{location_url.rstrip('/')}/result", headers=headers)
            return res.json() if res.ok else {"error": f"Failed to get result: {res.status_code} {res.text[:300]}"}
        if status in ("Failed", "Error"):
            return {"error": data.get("error") or data}
        # else keep waiting
# endregion


# region Safe ctx helpers (không làm crash nếu thiếu Context)
async def _ctx_info(ctx: _Context | None, msg: str):
    try:
        if ctx:
            await ctx.info(msg)
        else:
            print(f"[info] {msg}", file=sys.stderr, flush=True)
    except Exception:
        print(f"[info] {msg}", file=sys.stderr, flush=True)

async def _ctx_progress(ctx: _Context | None, current: int, total: int):
    try:
        if ctx:
            await ctx.report_progress(current, total)
        else:
            print(f"[progress] {current}/{total}", file=sys.stderr, flush=True)
    except Exception:
        print(f"[progress] {current}/{total}", file=sys.stderr, flush=True)
# endregion


# region Tools
@mcp.tool()
def connect_powerbi(tenant_id: str, client_id: str, client_secret: str) -> str:
    """
    Authenticate with Azure AD (service principal) and cache an access token.
    Call this once before other tools.
    """
    try:
        STATE.tenant_id = tenant_id.strip()
        STATE.client_id = client_id.strip()
        STATE.client_secret = client_secret.strip()
        STATE.scopes = [PBI_SCOPE]

        STATE.app = _build_app(STATE.tenant_id, STATE.client_id, STATE.client_secret)
        STATE.access_token = _acquire_token()
        return "Connected: acquired Power BI access token."
    except Exception as e:
        # Clear state on failure
        STATE.access_token = None
        STATE.app = None
        print(f"[connect_powerbi] Error acquiring token: {e}", file=sys.stderr, flush=True)
        return f"Error acquiring token: {e}"


@mcp.tool()
async def publish_pbix_to_powerbi(
    file_path: str,
    group_id: str | None,
    ctx: _Context | None = None,                 # ctx giờ là optional
    dataset_display_name: str | None = None,
    name_conflict: str = "CreateOrOverwrite",    # "Abort", "Overwrite", "CreateOrOverwrite"
    access_token: str | None = None,             # Nếu đã có token sẵn, ưu tiên dùng
    poll: bool = True,                           # Chờ import xong rồi trả kết quả
    poll_interval_sec: float = 2.0,
    timeout_sec: int = 1800
) -> str:
    """
    Upload 1 file PBIX từ local lên Power BI Service (Import PBIX vào workspace).
    Ưu tiên dùng token từ connect_powerbi(); fallback sang token truyền vào nếu có.
    """
    import asyncio
    import anyio
    import httpx

    BASE_URL = POWERBI_API

    def _normalize_group(group_id_val: str | None):
        # Nếu muốn import vào My Workspace: None / "me" / "myworkspace"
        if not group_id_val or str(group_id_val).lower() in ("me", "myworkspace"):
            return None
        return group_id_val

    async def _get_token() -> str:
        # 1) access_token truyền vào
        if access_token:
            return access_token

        # 2) STATE.access_token có sẵn
        tok = getattr(STATE, "access_token", None)
        if tok:
            return tok

        # 3) Refresh qua STATE.app
        app = getattr(STATE, "app", None)
        scopes = getattr(STATE, "scopes", [PBI_SCOPE])
        if app:
            result = app.acquire_token_silent(scopes, account=None)
            if not result:
                result = app.acquire_token_for_client(scopes=scopes)
            if "access_token" in result:
                STATE.access_token = result["access_token"]
                return STATE.access_token

        raise RuntimeError("Chưa có access token. Hãy gọi connect_powerbi() trước, hoặc truyền access_token trực tiếp.")

    async def _authorized_post(client: httpx.AsyncClient, url: str, params: dict, files: dict) -> httpx.Response:
        """
        POST có tự động refresh token nếu 401/403, retry 1 lần.
        """
        token = await _get_token()
        headers = {"Authorization": f"Bearer {token}"}

        resp = await client.post(url, params=params, headers=headers, files=files)
        if resp.status_code in (401, 403):
            app = getattr(STATE, "app", None)
            scopes = getattr(STATE, "scopes", [PBI_SCOPE])
            if app and not access_token:
                result = app.acquire_token_for_client(scopes=scopes)
                if "access_token" in result:
                    STATE.access_token = result["access_token"]
                    headers["Authorization"] = f"Bearer {STATE.access_token}"
                    return await client.post(url, params=params, headers=headers, files=files)
        return resp

    async def _authorized_get(client: httpx.AsyncClient, url: str) -> httpx.Response:
        token = await _get_token()
        headers = {"Authorization": f"Bearer {token}"}
        resp = await client.get(url, headers=headers)
        if resp.status_code in (401, 403):
            app = getattr(STATE, "app", None)
            scopes = getattr(STATE, "scopes", [PBI_SCOPE])
            if app and not access_token:
                result = app.acquire_token_for_client(scopes=scopes)
                if "access_token" in result:
                    STATE.access_token = result["access_token"]
                    headers["Authorization"] = f"Bearer {STATE.access_token}"
                    return await client.get(url, headers=headers)
        return resp

    try:
        file_path = os.path.expanduser(file_path)
        if not os.path.exists(file_path):
            return f"Error: File '{file_path}' không tồn tại."
        if not file_path.lower().endswith(".pbix"):
            return f"Error: File '{file_path}' không phải .pbix."

        group_id_norm = _normalize_group(group_id)
        import_url = f"{BASE_URL}/groups/{group_id_norm}/imports" if group_id_norm else f"{BASE_URL}/imports"

        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        await _ctx_info(ctx, f"Uploading PBIX: {file_path} ({file_size_mb:.2f} MB) -> "
                             f"{'workspace ' + group_id_norm if group_id_norm else 'My Workspace'}")
        await _ctx_progress(ctx, 0, 100)

        dataset_display_name = dataset_display_name or os.path.splitext(os.path.basename(file_path))[0]
        if name_conflict not in ("Abort", "Overwrite", "CreateOrOverwrite"):
            name_conflict = "CreateOrOverwrite"

        params = {"datasetDisplayName": dataset_display_name, "nameConflict": name_conflict}

        cancel_progress = anyio.Event()

        # Progress UI mềm
        async def progress_reporter():
            progress = 5
            try:
                while not cancel_progress.is_set() and progress < 95:
                    await _ctx_progress(ctx, progress, 100)
                    progress += 5 if progress < 50 else 2
                    await anyio.sleep(1)
            except Exception as e:
                await _ctx_info(ctx, f"Progress reporter error: {e}")

        progress_task = asyncio.create_task(progress_reporter())

        # Upload (multipart/form-data)
        async with httpx.AsyncClient(timeout=None) as client:
            with open(file_path, "rb") as f:
                files = {"file": (os.path.basename(file_path), f, "application/octet-stream")}
                resp = await _authorized_post(client, import_url, params=params, files=files)

        cancel_progress.set()
        await progress_task

        if resp.status_code not in (200, 201, 202):
            try:
                err_json = resp.json()
                msg = (err_json.get("error", {}).get("message") or err_json.get("message") or err_json)
            except Exception:
                msg = resp.text
            return f"Error: Upload thất bại ({resp.status_code}). Chi tiết: {msg}"

        data = resp.json()
        import_id = data.get("id") or data.get("importId") or data.get("Id")
        state = (data.get("importState") or data.get("status") or "").lower()
        await _ctx_info(ctx, f"Import started. id={import_id}, state={state or 'unknown'}")

        if not poll or not import_id:
            await _ctx_progress(ctx, 100, 100)
            return f"Đã gửi file '{os.path.basename(file_path)}' lên Power BI (import_id={import_id or 'N/A'})."

        # Poll trạng thái
        start = time.time()
        status_url = (f"{BASE_URL}/groups/{group_id_norm}/imports/{import_id}"
                      if group_id_norm else f"{BASE_URL}/imports/{import_id}")

        last_progress = 95
        async with httpx.AsyncClient(timeout=None) as client:
            while True:
                if time.time() - start > timeout_sec:
                    return f"Error: Quá thời gian chờ {timeout_sec}s, trạng thái import chưa hoàn tất (import_id={import_id})."

                s = await _authorized_get(client, status_url)
                if s.status_code != 200:
                    await anyio.sleep(poll_interval_sec)
                    continue

                info = s.json()
                import_state = (info.get("importState") or "").lower()

                if import_state in ("publishing", "inprogress", "queued", "importing"):
                    last_progress = min(99, last_progress + 1)
                    await _ctx_progress(ctx, last_progress, 100)
                    await anyio.sleep(poll_interval_sec)
                    continue

                if import_state == "succeeded":
                    await _ctx_progress(ctx, 100, 100)
                    datasets = info.get("datasets") or []
                    reports = info.get("reports") or []
                    ds_summary = ", ".join([f"{d.get('name')} ({d.get('id')})" for d in datasets]) or "—"
                    rp_summary = ", ".join([f"{r.get('name')} ({r.get('id')})" for r in reports]) or "—"
                    return (
                        f"✅ Import thành công.\n"
                        f"- Import ID: {import_id}\n"
                        f"- Dataset: {ds_summary}\n"
                        f"- Report: {rp_summary}"
                    )

                if import_state == "failed":
                    await _ctx_progress(ctx, 100, 100)
                    failure_detail = (info.get("error") or info.get("failureReason") or info)
                    try:
                        failure_text = json.dumps(failure_detail, ensure_ascii=False)
                    except Exception:
                        failure_text = str(failure_detail)
                    return f"❌ Import thất bại (import_id={import_id}). Chi tiết: {failure_text}"

                # Trường hợp không rõ, chờ thêm
                await anyio.sleep(poll_interval_sec)

    except Exception as e:
        # luôn log stderr để MCP client thấy nguyên nhân
        print(f"[publish_pbix_to_powerbi] Upload error: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        return f"Error: {e}"
# endregion


if __name__ == "__main__":
    try:
        mcp.run()
    except Exception as e:
        print(f"[mcp.run] crashed: {e}", file=sys.stderr, flush=True)
        traceback.print_exc(file=sys.stderr)
        raise


# # @mcp.tool()
# # def list_datasets(workspace_id: str) -> str:
# #     """
# #     List all datasets (semantic models) in a specific workspace.
# #     """
# #     result = make_request(f"{POWERBI_API}/groups/{workspace_id}/datasets")

# #     if isinstance(result, dict) and "error" in result:
# #         return f"Error: {result['error']}"

# #     datasets = result.get("value", []) if isinstance(result, dict) else []
# #     if not datasets:
# #         return "No datasets found in this workspace"

# #     out = [f"Found {len(datasets)} datasets:\n"]
# #     for ds in datasets:
# #         out.append(f"• {ds.get('name','<no name>')} (ID: {ds.get('id','')})")
# #     return "\n".join(out)
# # endregion

# # region Main

# # endregion








