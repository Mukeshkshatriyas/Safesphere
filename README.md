# AI-Powered Disaster Prediction & Emergency Management System

A full-stack disaster risk platform for predicting flood, earthquake, landslide, cyclone, and drought conditions, with a Python Flask API and a dashboard frontend.

## Overview

This project combines:

- ML-based risk prediction for multiple disaster types
- Geographic and weather-informed analysis
- Dashboard-driven monitoring and alert outputs
- API endpoints for location and disaster assessments
- Integration with a FloodGuard frontend for a visual monitoring experience

The repository currently runs through a root startup script that launches:

- the Flask backend at http://localhost:5000
- the FloodGuard dashboard at a dynamic local port such as http://localhost:3000/

The root app redirects users to the dashboard while the API remains available at the backend port.

## Features

- Multi-disaster prediction: flood, earthquake, landslide, cyclone, drought
- Location-based analysis using city or coordinate inputs
- API-based disaster predictions with validation
- Emergency route and shelter lookup support
- Dashboard UI under the FloodGuard folder
- Training and inference workflow for ML models

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/karansingh7773-rathore/Pre-Disaster-Predictor-Trained-on-ML-algorithms-Powered-by-AI
cd Pre-Disaster-Predictor-Trained-on-ML-algorithms-Powered-by-AI
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the application

From the project root, run:

```powershell
.\start-dashboard.ps1
```

This script:

- installs frontend dependencies in the FloodGuard folder if needed
- starts the Flask backend
- starts the dashboard frontend
- prints the local URLs to use

### 5. Open the app

- Backend API: http://localhost:5000
- Dashboard: http://localhost:3000/ (port may shift if 3000 is already occupied)

## Manual startup

If you want to run the backend and frontend separately:

### Backend

```bash
python app.py
```

### Frontend

```bash
cd FloodGuard
npm install
npm run dev -- --hostname 127.0.0.1 --port 3000
```

## Environment variables

Create a `.env` file in the project root if you want to configure external API support:

```bash
FLASK_SECRET_KEY=your-secret-key
MAPBOX_ACCESS_TOKEN=your-mapbox-token
WEATHER_API_KEY=your-weather-api-key
FLASK_DEBUG=True
FLASK_PORT=5000
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_ALERT_COOLDOWN_SECONDS=300
```

These values are optional for local dashboard startup but are required for some weather, mapping, and routing features.

### Telegram high-risk alerts

Copy `.env.example` to `.env` in the project root and set `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. Create a bot by messaging `@BotFather` with `/newbot`, then open that bot and send `/start`. To find your chat ID, message `@userinfobot` or call `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` after sending `/start` and read `message.chat.id` from the response. Keep `.env` private; it is ignored by Git.

The active `POST /api/predict-disaster` endpoint sends a Telegram alert only when the selected prediction's `risk_level` is `High`. The default cooldown is five minutes per disaster and can be changed with `TELEGRAM_ALERT_COOLDOWN_SECONDS`; set it to `0` to disable the cooldown. Notification failures do not fail the prediction response, and `telegram_alert_sent` reports whether the message was sent.

To verify Telegram without waiting for a high-risk prediction, configure `.env`, start the virtual environment, and run this from the project root:

```powershell
python -c "from telegram_service import send_telegram_test_alert; print('sent' if send_telegram_test_alert() else 'not sent')"
```

## Project structure

```text
.
├── app.py                     # Flask entry point and API routes
├── server.py                  # Predictor logic and data fetchers
├── anomaly_detector.py        # Anomaly monitoring logic
├── mapbox_integration.py      # Shelters and route utilities
├── requirements.txt           # Python dependencies
├── start-dashboard.ps1        # Main app launcher
├── FloodGuard/                # Dashboard frontend and supporting app code
├── static/                   # Static assets
├── README.md                 # Project documentation
├── .gitignore                # Ignored files
└── ...
```

## Key API endpoints

The app includes these main routes:

- `GET /` — redirects to the dashboard
- `GET /api/analyze?city=...` — analyze a city for disasters
- `GET /api/analyze-location?lat=...&lon=...` — analyze coordinates
- `GET /api/analyze-coords?lat=...&lon=...` — coordinate-based disaster data
- `GET /api/evacuation-route?lat=...&lon=...` — nearest shelter route
- `POST /api/predict-disaster` — custom disaster prediction with structured inputs
- `GET /api/isochrone?lat=...&lon=...` — isochrone polygon data

## Notes

- The provided startup script is the recommended way to run the full project.
- If the frontend port is already busy, the script automatically picks the next available local port.
- Some advanced features depend on external services such as Mapbox or weather APIs.
- Model files and generated artifacts may be created during training or runtime and should remain ignored when appropriate.

## License

This project is intended for educational and prototype use.
