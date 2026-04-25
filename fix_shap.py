import os, sys, json
sys.path.insert(0, 'backend')
from dotenv import load_dotenv
load_dotenv('backend/.env', override=True)
from app.core.database import engine
from sqlalchemy import text
with engine.connect() as conn:
    shap_data = json.dumps([
        'உங்கள் மண்டலத்தில் மழை முன்னறிவிப்பு (+₹12)',
        'வெள்ள அபாய மண்டலம் (+₹8)',
        '5 வார சுத்தமான பதிவு (-₹5)'
    ])
    conn.execute(text('UPDATE policies SET shap_explanation_json = :shap WHERE worker_id = :wid'), {'shap': shap_data, 'wid': '8eeaef8d-4c1c-47ee-87a7-6f59a41e5cee'})
    conn.commit()
    print('Updated')
