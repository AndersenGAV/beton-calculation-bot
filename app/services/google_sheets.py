import json
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import gspread
from oauth2client.service_account import ServiceAccountCredentials


SPREADSHEET_NAME = "LOGI"
WORKSHEET_NAME = "LOGI"


def money_to_int(value):
    if value is None or value == "":
        return ""

    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return value


def normalize_money(value) -> str:
    if value is None:
        return ""

    text = str(value)
    text = text.replace(" ", "")
    text = text.replace(" ", "")
    text = text.replace(",", ".")

    if text == "":
        return ""

    try:
        return str(int(round(float(text))))
    except ValueError:
        return text


def get_worksheet():
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

    return client.open(SPREADSHEET_NAME).worksheet(WORKSHEET_NAME)


def save_to_google_sheets(data: dict):
    try:
        sheet = get_worksheet()

        now = datetime.now(ZoneInfo("Europe/Kyiv"))

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
            money_to_int(data.get("total_cost")),
            money_to_int(data.get("price_per_m3")),
            money_to_int(data.get("client_price")),
            money_to_int(data.get("client_total")),
            money_to_int(data.get("margin_total")),
        ]

        sheet.insert_row(row, 2)

    except Exception as e:
        print(f"Google Sheets log error: {e}")


def update_margin_in_google_sheets(data: dict):
    try:
        sheet = get_worksheet()

        target_user_id = str(data.get("user_id"))
        target_total_cost = normalize_money(data.get("total_cost"))
        target_price_per_m3 = normalize_money(data.get("price_per_m3"))

        client_price = money_to_int(data.get("client_price"))
        client_total = money_to_int(data.get("client_total"))
        margin_total = money_to_int(data.get("margin_total"))

        for attempt in range(5):
            rows = sheet.get_all_values()

            for row_index, row in enumerate(rows[1:51], start=2):
                row_user_id = row[2] if len(row) > 2 else ""
                row_total_cost = row[10] if len(row) > 10 else ""
                row_price_per_m3 = row[11] if len(row) > 11 else ""

                is_same_user = str(row_user_id) == target_user_id
                is_same_total = normalize_money(row_total_cost) == target_total_cost
                is_same_price = normalize_money(row_price_per_m3) == target_price_per_m3

                if is_same_user and is_same_total and is_same_price:
                    sheet.update(
                        f"M{row_index}:O{row_index}",
                        [[client_price, client_total, margin_total]],
                    )
                    return

            time.sleep(0.5)

        full_row_data = dict(data)
        save_to_google_sheets(full_row_data)

    except Exception as e:
        print(f"Google Sheets margin update error: {e}")