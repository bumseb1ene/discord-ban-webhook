# Discord Ban Webhook

This script utilizes a Discord webhook to post information about new bans in a Discord channel. It periodically checks for new bans through an API and sends this information to a specified Discord webhook.

## Requirements

- Python 3.8 or higher
- `aiohttp` library
- `requests` library
- A Discord webhook URL

## Installation

1. Clone the repository or download the files into a directory of your choice.

2. Install the required libraries:
    ```bash
    pip install aiohttp requests python-dotenv
    ```
3. Create a `.env` file in the same directory with the following content:
    ```bash
    DISCORD_WEBHOOK_URL=YourWebhookURL
    API_BASE_URL=YourAPIBaseURL
    API_TOKEN=YourAPIToken
    USERNAME=YourAPIUsername
    PASSWORD=YourAPIPassword
    CHECK_INTERVAL=300
    LANGUAGE=en / de
    ```
Replace the placeholders with your actual values.

4. Add the `webhook.py` and `api_client.py` scripts to the same directory.

5. Run the script with Python:
    ```bash
    python webhook.py
    ```
## Configuration

- `DISCORD_WEBHOOK_URL`: The webhook URL of your Discord channel.
- `API_BASE_URL`: The base URL of the API used for retrieving ban information.
- `API_TOKEN`: The token used for API authentication.
- `USERNAME` and `PASSWORD`: Username and password for the API.
- `CHECK_INTERVAL`: The interval in seconds at which the script checks for new bans.
- `LANGUAGE`: The language of the messages (e.g., 'de' for German or 'en' for English).

## Functionality

The script periodically calls the API to check for new bans. When a new ban is found, it retrieves additional player information and comments and sends this information to the specified Discord webhook.


