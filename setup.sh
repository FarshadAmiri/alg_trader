#!/bin/bash
# Quick setup script for Linux/Mac

echo "========================================"
echo "Algo Trader - Quick Setup"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo ""
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
echo ""

echo "Running Django migrations..."
python manage.py migrate
echo ""

echo "Loading initial strategies..."
python manage.py load_strategies
echo ""

echo "========================================"
echo "Setup complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "1. Create admin user: python manage.py createsuperuser"
echo "2. Ingest data: python manage.py ingest_market_data --symbols 'BTC/USDT,ETH/USDT' --start-date 30 --provider ccxt --exchange binance"
echo "3. Start server: python manage.py runserver"
echo ""
echo "For detailed usage, see README.md"
echo "========================================"
