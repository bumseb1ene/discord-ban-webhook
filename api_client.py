import requests
import aiohttp
import logging

class APIClient:
    def __init__(self, base_url, api_token):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Connection": "keep-alive",
            "Content-Type": "application/json"
        })

    def login(self, username, password):
        url = f'{self.base_url}/api/login'
        data = {'username': username, 'password': password}
        response = self.session.post(url, json=data)
        if response.status_code != 200:
            return False
        return True

    async def get_bans(self):
        try:
            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                url = f"{self.base_url}/api/get_bans"
                async with session.get(url) as response:
                    if response.status != 200:
                        print(f"Fehler bei der API-Anfrage: Statuscode {response.status}")
                        return None
                    else:
                        data = await response.json()
                        return data
        except aiohttp.ClientError as ce:
            print(f"Fehler bei der Verbindung zur API: {ce}")
            return None
        except Exception as e:
            print(f"Unerwarteter Fehler beim Abrufen von Bans: {e}")
            return None


    async def get_player_by_steam_id(self, steam_id_64):
        url = f'{self.base_url}/api/player?steam_id_64={steam_id_64}'
        try:
            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data and 'result' in data:
                        player_data = data['result']
                        # Extrahieren der vorhandenen Daten
                        names = [name_entry['name'] for name_entry in player_data.get('names', []) if 'name' in name_entry]
                        blacklist_data = player_data.get("blacklist", {})
                        actions_data = player_data.get("received_actions", [])
                        sessions = player_data.get("sessions", [])
                        sessions_count = player_data.get("sessions_count", 0)
                        current_playtime_seconds = player_data.get("current_playtime_seconds", 0)
                        penalty_count = player_data.get("penalty_count", {})
                        flags = player_data.get("flags", [])
                        watchlist = player_data.get("watchlist")
                        steaminfo = player_data.get("steaminfo")
                        vips = player_data.get("vips", [])

                        return {
                            "names": names,
                            "steam_id_64": player_data.get("steam_id_64", None),
                            "total_playtime_seconds": player_data.get("total_playtime_seconds", 0),
                            "blacklist": blacklist_data,
                            "received_actions": actions_data,
                            "sessions": sessions,
                            "sessions_count": sessions_count,
                            "current_playtime_seconds": current_playtime_seconds,
                            "penalty_count": penalty_count,
                            "flags": flags,
                            "watchlist": watchlist,
                            "steaminfo": steaminfo,
                            "vips": vips
                        }
                    return None
        except Exception as e:
            logging.error(f"Error fetching player data for Steam ID {steam_id_64}: {e}")
            return None

    async def get_player_comments(self, steam_id_64):
        url = f'{self.base_url}/api/get_player_comment?steam_id_64={steam_id_64}'
        try:
            async with aiohttp.ClientSession(headers=self.session.headers) as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    data = await response.json()
                    if data and 'result' in data:
                        return data['result']
                    return None
        except Exception as e:
            logging.error(f"Fehler beim Abrufen von Spielerkommentaren für Steam ID {steam_id_64}: {e}")
            return None
