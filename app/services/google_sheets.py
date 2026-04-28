import json
import os
from datetime import datetime

import gspread
from oauth2client.service_account import ServiceAccountCredentials


def save_to_google_sheets(data: dict):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ]

        credentials_json = os.getenv("GOOGLE_CREDENTIALS")

        if not credentials_json:
            raise ValueError("GOOGLE_CREDENTIALS variable is empty or missing")

        credentials_dict = json.loads(credentials_json)

        creds = ServiceAccountCredentials.from_json_keyfile_dict(
            credentials_dict,
            scope,
        )

        client = gspread.authorize(creds)

        sheet = client.open("LOGI").worksheet("LOGI")

        now = datetime.now()

        row = [
            now.strftime("%Y-%m-%d"),
            now.strftime("%H:%M:%S"),
            data.get("user_id"),
            data.get("username"),
            data.get("phone"),
            data.get("concrete_mark"),
            data.get("amount"),
            data.get("concrete_discount"),
            data.get("distance"),
            data.get("distance_discount"),
            data.get("total_cost"),
            data.get("price_per_m3"),
        ]

        sheet.insert_row(row, 2)

    except Exception as e:
        print(f"Google Sheets log error: {e}")