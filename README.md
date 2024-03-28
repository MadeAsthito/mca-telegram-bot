# MCA Telegram Bot

## Description

Welcome to the Testing Platform Bot! This bot serves as a platform for testing and experimentation. Users can interact with the bot by sending messages, which will be saved to a database for analysis or further processing. Whether you're testing new features, experimenting with chat functionalities, or exploring bot development, this bot provides a sandbox environment for your testing needs.

## Features

- Receive messages from users and save them to a database.
- Support for both group and personal chat interactions.
- Error handling for robust performance.

## Installation

To install and run the Testing Platform Bot locally, follow these steps:

1. Clone the repository:

```
git clone https://github.com/MadeAsthito/mca-telegram-bot.git
```

2. Install dependencies:

```
pip install -r requirements.txt

```
3. Set up environment variables:
- Obtain a Telegram Bot API token from BotFather and set it as an environment variable.
- Configure database connection parameters (host, username, password, database name) in a `.env` file.
```
TOKEN=
BOT_USERNAME=
DB_HOST=
DB_USER=
DB_PASSWORD=
DB_NAME=
```
4. Run the bot: 
```
python main.py

```
