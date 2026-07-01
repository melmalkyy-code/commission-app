@echo off
title Surveying Experts - Commission Web App

echo Installing/checking packages...
C:\Users\Mahmoud Elmalky\AppData\Local\Programs\Python\Python314\python.exe -m pip install streamlit pandas plotly openpyxl reportlab psycopg2-binary --quiet

echo.
echo Starting web app... (will open in browser automatically)
echo Press Ctrl+C to stop.
echo.

C:\Users\Mahmoud Elmalky\AppData\Local\Programs\Python\Python314\python.exe -m streamlit run Home.py --server.port 8501

pause
