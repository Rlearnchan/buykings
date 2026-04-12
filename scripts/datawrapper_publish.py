#!/usr/bin/env python3
"""Create, populate, and publish a Datawrapper chart from a JSON spec."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import urllib.error
import urllib.request


API_BASE = "https://api.datawrapper.de/v3"
APP_BASE = "https://app.datawrapper.de/chart"


def load_json(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def read_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(f"Missing required environment variable: {name}")
    return value


class DatawrapperClient:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | None = None,
        raw_body: bytes | None = None,
        content_type: str | None = None,
    ) -> dict | list | bytes | None:
        url = f"{API_BASE}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/json",
        }

        body = raw_body
        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        elif content_type:
            headers["Content-Type"] = content_type

        request = urllib.request.Request(url, data=body, method=method, headers=headers)
        try:
            with urllib.request.urlopen(request) as response:
                payload = response.read()
                if not payload:
                    return None
                response_type = response.headers.get("Content-Type", "")
                if "application/json" in response_type:
                    return json.loads(payload.decode("utf-8"))
                return payload
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")
            raise SystemExit(
                f"Datawrapper API error ({exc.code}) on {method} {path}:\n{details}"
            ) from exc

    def me(self) -> dict:
        response = self.request("GET", "/me")
        assert isinstance(response, dict)
        return response

    def create_chart(self, payload: dict) -> dict:
        response = self.request("POST", "/charts", json_body=payload)
        assert isinstance(response, dict)
        return response

    def get_chart(self, chart_id: str) -> dict:
        response = self.request("GET", f"/charts/{chart_id}")
        assert isinstance(response, dict)
        return response

    def upload_csv(self, chart_id: str, csv_bytes: bytes) -> None:
        self.request(
            "PUT",
            f"/charts/{chart_id}/data",
            raw_body=csv_bytes,
            content_type="text/csv; charset=utf-8",
        )

    def patch_metadata(self, chart_id: str, metadata: dict) -> dict:
        response = self.request("PATCH", f"/charts/{chart_id}", json_body=metadata)
        assert isinstance(response, dict)
        return response

    def publish_chart(self, chart_id: str) -> dict:
        response = self.request("POST", f"/charts/{chart_id}/publish", json_body={})
        assert isinstance(response, dict)
        return response


def build_create_payload(spec: dict) -> dict:
    payload = {
        "title": spec["title"],
        "type": spec["chart_type"],
    }
    if spec.get("theme"):
        payload["theme"] = spec["theme"]
    if spec.get("folder_id"):
        payload["folderId"] = spec["folder_id"]
    return payload


def build_patch_payload(spec: dict) -> dict:
    metadata = {}
    describe = {}
    if spec.get("title"):
        metadata["title"] = spec["title"]
    if spec.get("subtitle"):
        describe["intro"] = spec["subtitle"]
    if spec.get("source_name"):
        describe["source-name"] = spec["source_name"]
    if spec.get("source_url"):
        describe["source-url"] = spec["source_url"]
    if spec.get("byline"):
        describe["byline"] = spec["byline"]
    if describe:
        metadata["metadata"] = {"describe": describe}

    extra_metadata = spec.get("metadata")
    if extra_metadata:
        metadata.setdefault("metadata", {})
        merge_dict(metadata["metadata"], extra_metadata)

    apply_default_chart_tweaks(spec, metadata)
    return metadata


def merge_dict(target: dict, source: dict) -> None:
    for key, value in source.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            merge_dict(target[key], value)
        else:
            target[key] = value


def apply_default_chart_tweaks(spec: dict, payload: dict) -> None:
    chart_type = spec.get("chart_type")
    metadata = payload.setdefault("metadata", {})
    publish = metadata.setdefault("publish", {})
    blocks = publish.setdefault("blocks", {})
    blocks.setdefault("logo", {"enabled": False})
    blocks.setdefault("embed", False)
    blocks.setdefault("download-pdf", False)
    blocks.setdefault("download-svg", False)
    blocks.setdefault("download-image", False)
    blocks.setdefault("get-the-data", False)

    if chart_type not in {"column-chart", "grouped-column-chart"}:
        return

    visualize = metadata.setdefault("visualize", {})
    visualize.setdefault("show-values", "always")

    value_labels = visualize.setdefault("valueLabels", {})
    value_labels.setdefault("enabled", True)
    value_labels.setdefault("show", "always")
    value_labels.setdefault("placement", "outside")


def chart_urls(chart_id: str, publish_response: dict | None) -> dict:
    urls = {
        "chart_id": chart_id,
        "edit_url": f"{APP_BASE}/{chart_id}/edit",
        "public_url": None,
    }
    if publish_response:
        public_version = publish_response.get("publicVersion")
        if public_version:
            urls["public_url"] = f"https://datawrapper.dwcdn.net/{chart_id}/{public_version}/"
        elif publish_response.get("url"):
            urls["public_url"] = publish_response["url"]
    return urls


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("spec", help="Path to chart JSON spec")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate config and auth, but do not create a chart",
    )
    args = parser.parse_args()

    spec_path = pathlib.Path(args.spec).resolve()
    spec = load_json(spec_path)
    csv_path = pathlib.Path(spec["prepared_csv"]).resolve()
    if not csv_path.exists():
        raise SystemExit(f"Prepared CSV not found: {csv_path}")

    token = read_env("DATAWRAPPER_ACCESS_TOKEN")
    client = DatawrapperClient(token)
    me = client.me()

    if args.dry_run:
        print(
            json.dumps(
                {
                    "ok": True,
                    "mode": "dry-run",
                    "account": me.get("email") or me.get("id"),
                    "spec": str(spec_path),
                    "prepared_csv": str(csv_path),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    chart_id = spec.get("chart_id")
    created = None
    if chart_id:
        client.get_chart(chart_id)
    else:
        created = client.create_chart(build_create_payload(spec))
        chart_id = created["id"]

    assert chart_id is not None
    csv_bytes = csv_path.read_bytes()
    client.upload_csv(chart_id, csv_bytes)

    patch_payload = build_patch_payload(spec)
    if patch_payload:
        client.patch_metadata(chart_id, patch_payload)

    publish_response = client.publish_chart(chart_id)
    result = {
        "ok": True,
        "account": me.get("email") or me.get("id"),
        "project": spec.get("project"),
        "slug": spec.get("slug"),
        "title": spec.get("title"),
        "chart_type": spec.get("chart_type"),
        "mode": "update" if spec.get("chart_id") else "create",
        "prepared_csv": str(csv_path),
    }
    result.update(chart_urls(chart_id, publish_response))

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
