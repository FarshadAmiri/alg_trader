"""
Management command to ingest market data from exchange.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from trading.models import Candle
from core_engine.data.providers import NobitexProvider, CCXTProvider
from core_engine.data.fetchers import DataFetcher
import pandas as pd


class Command(BaseCommand):
    help = 'Ingest OHLCV market data from exchange'

    def add_arguments(self, parser):
        parser.add_argument(
            '--symbols',
            type=str,
            required=True,
            help='Comma-separated list of symbols (e.g., BTCUSDT,ETHUSDT)'
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            default='5m',
            help='Timeframe (e.g., 5m, 1h, 4h)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD) or days ago (e.g., 30 for 30 days ago)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD), defaults to now'
        )
        parser.add_argument(
            '--provider',
            type=str,
            default='nobitex',
            choices=['nobitex', 'ccxt'],
            help='Data provider'
        )
        parser.add_argument(
            '--exchange',
            type=str,
            default='binance',
            help='Exchange name (for CCXT provider)'
        )

    def handle(self, *args, **options):
        symbols = [s.strip() for s in options['symbols'].split(',')]
        timeframe = options['timeframe']
        provider_name = options['provider']
        
        # Parse dates
        if options['start_date']:
            try:
                # Try parsing as date
                start_time = datetime.strptime(options['start_date'], '%Y-%m-%d')
            except ValueError:
                # Try parsing as days ago
                try:
                    days_ago = int(options['start_date'])
                    start_time = datetime.now() - timedelta(days=days_ago)
                except ValueError:
                    raise CommandError('Invalid start-date format. Use YYYY-MM-DD or number of days ago.')
        else:
            # Default to 30 days ago
            start_time = datetime.now() - timedelta(days=30)
        
        if options['end_date']:
            end_time = datetime.strptime(options['end_date'], '%Y-%m-%d')
        else:
            end_time = datetime.now()
        
        # Make timezone-aware
        start_time = timezone.make_aware(start_time) if timezone.is_naive(start_time) else start_time
        end_time = timezone.make_aware(end_time) if timezone.is_naive(end_time) else end_time
        
        self.stdout.write(f"Ingesting data for {len(symbols)} symbols from {start_time} to {end_time}")
        
        # Initialize provider
        if provider_name == 'nobitex':
            provider = NobitexProvider()
        else:
            provider = CCXTProvider(exchange_name=options['exchange'])
        
        fetcher = DataFetcher(provider)
        
        # Fetch and store data for each symbol
        for symbol in symbols:
            self.stdout.write(f"Fetching {symbol}...")
            
            try:
                df = fetcher.fetch_ohlcv(symbol, timeframe, start_time, end_time)
                
                if df.empty:
                    self.stdout.write(self.style.WARNING(f"No data retrieved for {symbol}"))
                    continue
                
                # Store in database
                candles_created = 0
                candles_updated = 0
                
                for _, row in df.iterrows():
                    candle, created = Candle.objects.update_or_create(
                        symbol=symbol,
                        timeframe=timeframe,
                        timestamp=row['timestamp'],
                        defaults={
                            'open': row['open'],
                            'high': row['high'],
                            'low': row['low'],
                            'close': row['close'],
                            'volume': row['volume'],
                        }
                    )
                    
                    if created:
                        candles_created += 1
                    else:
                        candles_updated += 1
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ {symbol}: {candles_created} created, {candles_updated} updated"
                    )
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"✗ Error fetching {symbol}: {str(e)}")
                )
        
        self.stdout.write(self.style.SUCCESS("Data ingestion complete"))
