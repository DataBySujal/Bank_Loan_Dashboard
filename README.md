# Loan Dashboard

This is a Dash-based loan analytics dashboard that reads data from `financial_loan.csv` and presents KPIs, charts, a map, and a details table.

Quick start (Windows PowerShell):

1. Create and activate a virtual environment (only once):

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
pip install -r requirements.txt
```

3. Run the dashboard:

```powershell
python .\loan_dashboard.py
```

4. Open your browser at `http://127.0.0.1:8050/`.

Notes:
- The app expects `financial_loan.csv` in the same folder as `loan_dashboard.py`.
- The app will prefer images placed in an `assets/` folder. If no images are present, it uses embedded SVG placeholders.
- If the choropleth map is empty, ensure `address_state` in your CSV contains 2-letter US state abbreviations (e.g., 'CA', 'NY').

If you want me to tweak the visuals further (exact layout, colors, or additional charts), tell me what to adjust and I'll update the project.
