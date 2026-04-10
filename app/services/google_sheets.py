import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

def save_to_google_sheets(data: dict):
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            "beton-calculation-491913-6c6fb7df141f.json",
            scope
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