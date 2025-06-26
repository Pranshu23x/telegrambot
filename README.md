# Telegram AI Chatbot--NExT_23x

A smart, conversational Telegram bot built with Python, powered by Gemini, that can intelligently respond to user queries and perform powerful PDF operations like converting, splitting, merging, and compressing.

 🚀 Features:::

 AI-powered chatbot using Gemini (or OpenAI) API
 Works inside Telegram chat---- N
 Github repository uses .env for API tokens security. 
 Deployed via Render (free hosting)
 Pings every 5 mins via [UptimeRobot](https://uptimerobot.com) to stay awake
 Could convert/merge/split and compress pdf files, with prompt-"convert/merge/split/compress this pdf"
 
---

📦 Tech Stack

- Python 3.12
- python-telegram-bot==20.3
- Google Generative AI
- python-dotenv
- logging

---

 📁 Project Structure
.
├── pythontonybot.py       # Main bot logic
├── requirements.txt       # Python dependencies
├── Procfile               # For Render deployment
├── .env                   # (Ignored) Contains API keys
└── README.md              # This file
