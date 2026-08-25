# Broadcast Notification System

Deployment-ready Streamlit app.

## Run locally

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Deploy free with Streamlit Community Cloud

1. Create a GitHub repository.
2. Upload:
   - `app.py`
   - `requirements.txt`
   - `.gitignore`
3. Go to https://share.streamlit.io
4. Click **Create app**.
5. Select your GitHub repository and branch.
6. Set the main file path to:
   `app.py`
7. Click **Deploy**.

## Important about the Broadcast Repository

The app currently stores saved broadcasts in:

`broadcast_repository.db`

This works locally, but Streamlit Community Cloud can restart/redeploy the app and local SQLite data may be lost.

For simple personal use, you can still use the app normally. For reliable cloud repository storage later, move the repository to a hosted database such as PostgreSQL, Supabase, Neon, or Azure SQL.

## Included Templates

- Local Maintenance Advisory
- ISP Maintenance Advisory
- Global Maintenance Advisory
- Emergency Maintenance Advisory
- Incident Advisory
- DD Approval Template
