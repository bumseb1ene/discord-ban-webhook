import os
import asyncio
from dotenv import load_dotenv
from api_client import APIClient
from datetime import datetime
import requests
import json

# Spracheinstellungen laden
with open('languages.json', 'r') as file:
    languages = json.load(file)

LAST_CHECKED_FILE = 'last_checked.txt'

# Lade .env-Datei
load_dotenv()

# Konfiguration
WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK_URL')  # Webhook-URL hinzugefügt
API_BASE_URL = os.getenv('API_BASE_URL')
API_TOKEN = os.getenv('API_TOKEN')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', 60))  # Standardwert ist 60 Sekunden
selected_language = os.getenv('LANGUAGE', 'de')

class BanChecker:
    def __init__(self, api_base_url, api_token):
        self.api_client = APIClient(api_base_url, api_token)
        self.last_checked = self.read_last_checked_date()

    async def on_ready(self):
        if self.api_client.login(USERNAME, PASSWORD):
            print(f"API Login erfolgreich für URL: {self.api_client.base_url}")
            await self.check_bans()  # Startet die Überprüfung von Bans
        else:
            print(f"API Login fehlgeschlagen für URL: {self.api_client.base_url}. Überprüfen Sie die Anmeldedaten.")


    def read_last_checked_date(self):
        try:
            with open("last_checked.txt", "r") as file:
                last_checked_str = file.read().strip()
                return datetime.strptime(last_checked_str, "%Y.%m.%d-%H.%M.%S")
        except FileNotFoundError:
            print("Datei 'last_checked.txt' nicht gefunden.")
            return datetime.min
        except ValueError as e:
            print(f"Fehler beim Lesen des Datums: {e}")
            return datetime.min
        except Exception as e:
            print(f"Allgemeiner Fehler beim Lesen des Datums: {e}")
            return datetime.min

    def get_last_checked_date(self):
        if os.path.exists(LAST_CHECKED_FILE):
            with open(LAST_CHECKED_FILE, 'r') as file:
                date_str = file.read().strip()
                return datetime.strptime(date_str, "%Y.%m.%d-%H.%M.%S")
        return datetime.min


    def set_last_checked_date(self, date):
        try:
            with open(LAST_CHECKED_FILE, "w") as file:
                file.write(date.strftime("%Y.%m.%d-%H.%M.%S"))
            print(f"Letztes geprüftes Datum gespeichert: {date}")
        except Exception as e:
            print(f"Fehler beim Speichern des letzten geprüften Datums in '{LAST_CHECKED_FILE}': {e}")

    def is_new_ban(self, ban):
        if all(key in ban and ban[key] is not None for key in ['type', 'steam_id_64', 'ban_time']):
            try:
                ban_time = datetime.strptime(ban["ban_time"], "%Y.%m.%d-%H.%M.%S")
                return ban_time > self.last_checked
            except ValueError:
                print(f"Ungültiges Datumformat für Ban: {ban['ban_time']}. Vollständiges Ban-Objekt: {ban}")
                return False
        else:
            return False  # Unvollständige Objekte ignorieren


    async def get_player_info(self, steam_id):
        player_info = await self.api_client.get_player_by_steam_id(steam_id)
        print("Abgerufene Spieler-Info:", player_info)
        return player_info




    def update_last_checked(self):
        self.last_checked = datetime.now()

    async def check_bans(self):
        while True:
            try:
                print("Abrufen der aktuellen Bans...")
                current_bans = await self.api_client.get_bans()

                if not current_bans or 'result' not in current_bans:
                    print(f"Fehler: Ungültige Antwort von get_bans: {current_bans}")
                    await asyncio.sleep(CHECK_INTERVAL)
                    continue

                new_bans = [ban for ban in current_bans['result'] if self.is_new_ban(ban)]
                print(f"Verarbeitung von {len(new_bans)} neuen Bans.")

                if new_bans:
                    # Aktualisiere das last_checked Datum mit dem Datum des neuesten Banns
                    latest_ban_time = max(datetime.strptime(ban["ban_time"], "%Y.%m.%d-%H.%M.%S") for ban in new_bans)
                    self.set_last_checked_date(latest_ban_time)
                    self.last_checked = latest_ban_time

                for ban in new_bans:
                    try:
                        print(f"Verarbeitung von Ban für Steam ID {ban['steam_id_64']}.")
                        player_details = await self.get_player_info(ban["steam_id_64"])

                        if player_details:
                            await self.post_ban_info(ban, player_details)

                    except Exception as e:
                        print(f'Fehler bei der Verarbeitung des Bans: {e}')

                await asyncio.sleep(CHECK_INTERVAL)

            except Exception as e:
                print(f'Fehler bei der Überprüfung auf Bans: {e}')
                await asyncio.sleep(CHECK_INTERVAL)

    async def post_ban_info(self, ban_info, player_info):
        # Laden der Spracheinstellungen
        language = languages[os.getenv('LANGUAGE', 'de')]  # Lädt die Spracheinstellung aus .env

        # Berechnung der Spielzeit in Stunden und Minuten
        total_playtime_seconds = player_info.get('total_playtime_seconds', 0)
        hours = total_playtime_seconds // 3600
        minutes = (total_playtime_seconds % 3600) // 60

        # Aktionen und Blacklist-Status extrahieren
        actions = player_info.get("received_actions", [])
        blacklist = player_info.get("blacklist", {})
        is_blacklisted = blacklist.get("is_blacklisted", False)

        # Banngrund
        ban_reason = blacklist.get('reason', language['unknown']) if is_blacklisted else actions[0].get('reason', language['unknown']) if actions else language['unknown']

        # Bannzeit
        formatted_ban_time = language['unknown']
        if actions:
            latest_action = actions[0]
            action_time = latest_action.get('time', '')
            if action_time:
                try:
                    ban_time = datetime.strptime(action_time, "%Y-%m-%dT%H:%M:%S.%f")
                    formatted_ban_time = ban_time.strftime("%d.%m.%Y %H:%M:%S")
                except ValueError:
                    print(f"Fehler beim Parsen des Zeitstempels: {action_time}")

        # Kommentare des Spielers abrufen
        player_comments = await self.api_client.get_player_comments(player_info['steam_id_64'])

        # Nachricht zusammenstellen
        message = f"**{language['new_ban']}**\n\n"
        message += f"**{language['name']}** {player_info.get('names', [language['unknown']])[0]}\n"
        message += f"**{language['steam_id']}** {player_info.get('steam_id_64', language['unknown'])}\n"
        message += f"**{language['ban_time']}** {formatted_ban_time}\n"
        message += f"**{language['on_blacklist']}** {language['yes'] if is_blacklisted else language['no']}\n"
        message += f"**{language['steam_url']}** https://steamcommunity.com/profiles/{player_info.get('steam_id_64', language['unknown'])}\n"
        message += f"**{language['total_playtime']}** {hours} {language['hours']} und {minutes} {language['minutes']}\n"
        message += f"**{language['reason']}** {ban_reason}\n"
        message += f"**{language['ban_enforced_by']}** {blacklist.get('by', language['unknown']) if is_blacklisted else latest_action.get('by', language['unknown'])}\n"
        message += f"**{language['ban_type']}** {latest_action.get('action_type', language['unknown']) if actions else language['unknown']}\n"

        # Nur den neuesten Kommentar hinzufügen
        if player_comments:
            latest_comment = max(player_comments, key=lambda x: x['creation_time'])
            comment_time = datetime.strptime(latest_comment["creation_time"], "%Y-%m-%dT%H:%M:%S.%f").strftime("%d.%m.%Y %H:%M:%S")
            message += f"**{language['player_comments']}**\n"
            message += f"- {comment_time}: {latest_comment['content']} (von {latest_comment['by']})\n"

        # Senden der Nachricht an den Webhook
        response = requests.post(WEBHOOK_URL, json={"content": message})
        if response.status_code != 204:
            print(f"Fehler beim Senden der Nachricht an den Webhook: {response.status_code}")





if __name__ == "__main__":
    load_dotenv()

    api_base_urls = os.getenv('API_BASE_URLS')
    if api_base_urls:
        api_base_urls = api_base_urls.split(',')
    else:
        api_base_urls = [os.getenv('API_BASE_URL')]  # Einzelne URL verwenden, wenn keine Liste vorhanden ist

    for api_base_url in api_base_urls:
        bot = BanChecker(api_base_url, os.getenv('API_TOKEN'))
        asyncio.run(bot.on_ready())