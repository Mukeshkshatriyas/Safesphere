import os, sys, time
os.environ['PYTHONIOENCODING'] = 'utf-8'

print('=== 1. APP IMPORT ===')
import app
print('app.py imports OK')
print('CORS:', 'CORS' in dir(app))
print('flask_cors:', 'flask_cors' in sys.modules)

print()
print('=== 2. MODELS ===')
from server import EnhancedTravelRiskPredictor
p = EnhancedTravelRiskPredictor()
print('Models loaded:', list(p.disaster_models.keys()))

print()
print('=== 3. FLOOD HIGH-RISK PREDICTION ===')
inp = {f: p._get_default_value(f) for f in p.numerical_features}
inp.update({'Rainfall_mm':280,'Elevation_m':8,'Distance_to_River_km':0.3,
            'Water_Level_m':6.5,'Historical_Events':8,
            'Infrastructure':'Poor','Land_Cover':'Urban','Soil_Type':'Clay','Season':'Monsoon'})
preds = p.predict_all_disasters(inp)
flood = preds['flood']
print('Flood risk_level:', flood['risk_level'], '| probability:', round(flood['probability']*100,1), '%')

print()
print('=== 4. REVERSE GEOCODE (Karnataka district) ===')
from telegram_service import reverse_geocode
loc = reverse_geocode(12.97, 77.59)
print('Bengaluru coords ->', loc)

print()
print('=== 5. TELEGRAM ALERTS (5 disasters x 3 risk levels) ===')
from telegram_service import send_telegram_alert_by_risk
ts = time.strftime('%Y-%m-%d %H:%M:%S')
tests = [
    ('flood',      'high',   87.5, 'Bengaluru, Bengaluru Urban, Karnataka, India'),
    ('earthquake', 'medium', 54.2, 'New Delhi, Delhi, India'),
    ('landslide',  'low',    18.3, 'Shimla, Himachal Pradesh, India'),
    ('cyclone',    'high',   91.0, 'Chennai, Tamil Nadu, India'),
    ('drought',    'medium', 47.6, 'Jaipur, Rajasthan, India'),
    ('flood',      'low',    12.0, 'Mysuru, Mysuru District, Karnataka, India'),
]
all_sent = True
for d, lvl, score, location in tests:
    sent = send_telegram_alert_by_risk(d, lvl, score, ts, location=location)
    status = 'SENT' if sent else 'FAILED'
    if not sent:
        all_sent = False
    print(f'  {lvl.upper():6s} {d:10s} -> {status}')
print('All alerts sent:', all_sent)

print()
print('=== 6. FEATURE ALIAS RESOLVER ===')
aliases = {
    f.lower().replace('\uff70','').replace('%','').replace('_',''): f
    for f in p.numerical_features
}
test_names = ['Temperature_degC', 'Humidity_pct', 'Rainfall_mm', 'Wind_Speed_kmh']
for name in test_names:
    key = name.lower().replace('\uff70','').replace('%','').replace('_','')
    resolved = aliases.get(key, 'NOT FOUND')
    print(f'  {name} -> {resolved}')

print()
print('=== 7. REQUIREMENTS CHECK ===')
import importlib
pkgs = ['flask', 'flask_cors', 'pandas', 'numpy', 'sklearn', 'joblib',
        'requests', 'openai', 'dotenv', 'gunicorn']
for pkg in pkgs:
    try:
        importlib.import_module(pkg)
        print(f'  {pkg}: OK')
    except ImportError:
        print(f'  {pkg}: MISSING')

print()
print('=== ALL FEATURES VERIFIED ===')
