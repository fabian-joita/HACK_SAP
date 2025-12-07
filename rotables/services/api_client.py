# rotables/services/api_client.py

import os
import requests
from rotables.dto.dto import HourRequest, HourResponse

BASE_URL = "https://hackaton2025-lsac-eval.cfapps.eu12.hana.ondemand.com/api/v1"
SESSION_FILE = "session.id"


class ApiClient:
    def __init__(self):
        self.api_key = "c3abbeb9-cf27-4c4a-9b60-288e56505756"
        self.session_id = None

    # ----------------------------------------------------------
    # LOAD LOCAL SESSION
    # ----------------------------------------------------------
    def load_session_local(self):
        if os.path.exists(SESSION_FILE):
            with open(SESSION_FILE, "r") as f:
                self.session_id = f.read().strip()
            print("[INFO] Loaded existing local session:", self.session_id)
            return True
        return False

    # ----------------------------------------------------------
    # SAVE LOCAL SESSION
    # ----------------------------------------------------------
    def save_session_local(self):
        if self.session_id:
            with open(SESSION_FILE, "w") as f:
                f.write(self.session_id)

    # ----------------------------------------------------------
    # START OR RECOVER SESSION
    # ----------------------------------------------------------
    def start_session(self):
        url = f"{BASE_URL}/session/start"
        headers = {"API-KEY": self.api_key}

        res = requests.post(url, headers=headers)

        # ------------------------------------------------------
        # EXISTING SESSION (409)
        # ------------------------------------------------------
        if res.status_code == 409:
            print("[INFO] Backend reports active session. Using local session.id...")

            if self.load_session_local():
                return  # good: can continue with stored session

            raise RuntimeError(
                "Backend has an active session for your API key, "
                "but session.id file does not exist locally. "
                "Restart backend or create session.id manually."
            )

        # ------------------------------------------------------
        # NEW SESSION (200)
        # ------------------------------------------------------
        if res.status_code == 200:
            sid = res.text.strip().strip('"')
            print("[INFO] Started new session:", sid)

            self.session_id = sid
            self.save_session_local()
            return

        # ------------------------------------------------------
        # ANY OTHER RESPONSE = ERROR
        # ------------------------------------------------------
        raise RuntimeError(f"Unexpected response {res.status_code}: {res.text}")

    # ----------------------------------------------------------
    # PLAY ROUND
    # ----------------------------------------------------------
    def play_round(self, req: HourRequest):
        if not self.session_id:
            raise RuntimeError("Session not started. Call start_session() first.")

        url = f"{BASE_URL}/play/round"
        headers = {
            "API-KEY": self.api_key,
            "SESSION-ID": self.session_id,
            "Content-Type": "application/json",
        }

        res = requests.post(url, json=req.to_json(), headers=headers)

        if res.status_code != 200:
            print("[ERROR] Backend error:", res.status_code, res.text)
            raise RuntimeError(f"Backend error {res.status_code}: {res.text}")

        return HourResponse.from_json(res.json())

    # ----------------------------------------------------------
    # END SESSION
    # ----------------------------------------------------------
    def end_session(self):
        if not self.session_id:
            print("[WARN] No active session_id to end.")
            return None

        url = f"{BASE_URL}/session/end"
        headers = {"API-KEY": self.api_key, "SESSION-ID": self.session_id}

        res = requests.post(url, headers=headers)

        if res.status_code != 200:
            print("[WARN] Failed to end session:", res.text)
            return None

        return HourResponse.from_json(res.json())
