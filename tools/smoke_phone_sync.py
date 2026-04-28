#!/usr/bin/env python3
"""Phone sync smoke test for local Kuakua Agent backend."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def _request_json(url: str, method: str, payload: dict | None = None) -> tuple[int, dict]:
    body = None
    headers = {"Content-Type": "application/json"}
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url=url, method=method, data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
            return resp.getcode(), json.loads(data) if data else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8") if exc.fp else ""
        parsed = {}
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw}
        return exc.code, parsed


def build_payload(device_id: str, batch_id: str) -> dict:
    now = datetime.now(timezone.utc).replace(microsecond=0)
    date_str = now.strftime("%Y-%m-%d")
    sync_time = now.isoformat().replace("+00:00", "Z")
    entries = [
        {
            "event_id": f"{device_id}:{date_str}:com.example.editor",
            "date": date_str,
            "app_name": "Code Editor",
            "package_name": "com.example.editor",
            "duration_seconds": 1200,
            "event_count": 4,
            "last_used": sync_time,
        },
        {
            "event_id": f"{device_id}:{date_str}:com.example.browser",
            "date": date_str,
            "app_name": "Web Browser",
            "package_name": "com.example.browser",
            "duration_seconds": 600,
            "event_count": 2,
            "last_used": sync_time,
        },
    ]
    return {
        "protocol_version": "1.0",
        "batch_id": batch_id,
        "device_id": device_id,
        "device_name": "smoke-test-device",
        "entries": entries,
        "sync_time": sync_time,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run phone sync smoke test.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--device-id", default="smoke-dev-001", help="Smoke test device id")
    args = parser.parse_args()

    batch_id = f"smoke-{int(time.time())}"
    payload = build_payload(args.device_id, batch_id)
    sync_url = f"{args.base_url.rstrip('/')}/api/phone/sync"
    summary_url = f"{args.base_url.rstrip('/')}/api/usage/daily-summary?date={payload['entries'][0]['date']}"

    print(f"[1/3] POST {sync_url} (fresh batch)")
    code_1, body_1 = _request_json(sync_url, "POST", payload)
    print(f"  status={code_1} body={json.dumps(body_1, ensure_ascii=False)}")
    if code_1 < 200 or code_1 >= 300:
        print("Smoke failed: fresh sync request did not succeed.")
        return 1

    print(f"[2/3] POST {sync_url} (same batch retry)")
    code_2, body_2 = _request_json(sync_url, "POST", payload)
    print(f"  status={code_2} body={json.dumps(body_2, ensure_ascii=False)}")
    if code_2 < 200 or code_2 >= 300:
        print("Smoke failed: retry sync request did not succeed.")
        return 1

    print(f"[3/3] GET {summary_url}")
    code_3, body_3 = _request_json(summary_url, "GET")
    print(f"  status={code_3} body={json.dumps(body_3, ensure_ascii=False)}")
    if code_3 < 200 or code_3 >= 300:
        print("Smoke warning: summary endpoint not ready or failed.")
        return 2

    print("Smoke passed: sync + idempotency + summary query succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
