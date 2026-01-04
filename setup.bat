@echo off
REM Quick setup script for Windows

echo ========================================
echo Algo Trader - Quick Setup
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo Installing dependencies...
pip install -r requirements.txt
echo.

echo Running Django migrations...
python manage.py migrate
echo.

echo Loading initial strategies...
python manage.py load_strategies
echo.

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Next steps:
echo 1. Create admin user: python manage.py createsuperuser
echo 2. Ingest data: python manage.py ingest_market_data --symbols "BTC/USDT,ETH/USDT" --start-date 30 --provider ccxt --exchange binance
echo 3. Start server: python manage.py runserver
echo.
echo For detailed usage, see README.md
echo ========================================
pause
