import os
import json
import hmac
import hashlib
import base64
import logging
import datetime
import threading
from typing import Optional

import requests


class LogAnalyticsHandler(logging.Handler):
    """
    Logging handler that ships JSON logs to Azure Log Analytics (Data Collector API).

    Environment variables required:
      - LOG_ANALYTICS_WORKSPACE_ID
      - LOG_ANALYTICS_SHARED_KEY
      - LOG_ANALYTICS_LOG_TYPE (e.g., SaramsaAppLogs)

    Optional:
      - LOG_ANALYTICS_ENDPOINT (default: https://{workspace}.ods.opinsights.azure.com)
    """

    def __init__(self, log_type_env: str = 'LOG_ANALYTICS_LOG_TYPE'):
        super().__init__()
        self.workspace_id = os.getenv('LOG_ANALYTICS_WORKSPACE_ID')
        self.shared_key = os.getenv('LOG_ANALYTICS_SHARED_KEY')
        self.log_type = os.getenv(log_type_env)
        # Allow overriding endpoint for sovereign clouds
        self.endpoint = os.getenv('LOG_ANALYTICS_ENDPOINT') or (
            f"https://{self.workspace_id}.ods.opinsights.azure.com" if self.workspace_id else None
        )

        self.api_path = '/api/logs'
        self.api_version = '2016-04-01'
        self.session = requests.Session()

        # If not configured, mark disabled
        self.enabled = bool(self.workspace_id and self.shared_key and self.log_type and self.endpoint)

    def emit(self, record: logging.LogRecord) -> None:
        if not self.enabled:
            return
        try:
            body = self.format(record)
            # Ensure body is a JSON object string; wrap single object into array for ingestion friendliness
            try:
                parsed = json.loads(body)
                payload = json.dumps([parsed])
            except Exception:
                payload = json.dumps([{'message': str(body)}])

            # Send asynchronously to avoid blocking request thread
            threading.Thread(target=self._post, args=(payload,), daemon=True).start()
        except Exception:
            # Never raise from logging handler
            pass

    def _build_signature(self, date: str, content_length: int) -> str:
        string_to_hash = f"POST\n{content_length}\napplication/json\nx-ms-date:{date}\n{self.api_path}"
        bytes_to_hash = bytes(string_to_hash, encoding='utf-8')
        decoded_key = base64.b64decode(self.shared_key)
        hashed = hmac.new(decoded_key, bytes_to_hash, digestmod=hashlib.sha256).digest()
        encoded_hash = base64.b64encode(hashed).decode()
        return f"SharedKey {self.workspace_id}:{encoded_hash}"

    def _post(self, payload: str) -> None:
        try:
            rfc1123date = datetime.datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
            signature = self._build_signature(rfc1123date, len(payload))
            url = f"{self.endpoint}{self.api_path}?api-version={self.api_version}"
            headers = {
                'Content-Type': 'application/json',
                'Log-Type': self.log_type,
                'x-ms-date': rfc1123date,
                'Authorization': signature,
            }
            # Fire-and-forget; small timeout
            self.session.post(url, data=payload, headers=headers, timeout=3)
        except Exception:
            # Swallow errors; avoid crashing app due to shipper
            pass


