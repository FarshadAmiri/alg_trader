"""
Initial data fixture for strategies.
"""
from django.core.management.base import BaseCommand
from trading.models import Strategy


class Command(BaseCommand):
    help = 'Load initial strategy data'

    def handle(self, *args, **options):
        strategies = [
            {
                'name': 'MACD RSI Confluence',
                'module_path': 'core_engine.strategies.macd_rsi_confluence:MACDRSIStrategy',
                'description': 'Baseline strategy using MACD histogram and RSI with volatility and volume filters. Works on 1h candles, checks every 2h, typical 4-8h holds.',
                'parameters': {
                    'rsi_min': 40,
                    'rsi_max': 65,
                    'macd_hist_min': 0.0,
                    'atr_pct_max': 5.0,
                    'volume_min_ratio': 0.8,
                    'max_positions': 3
                },
                'is_active': True
            },
            {
                'name': 'Momentum Rank',
                'module_path': 'core_engine.strategies.momentum_rank:MomentumRankStrategy',
                'description': 'Multi-timeframe momentum ranking strategy. Works on 15m candles, checks every hour, typical 2-6h holds.',
                'parameters': {
                    'min_momentum_score': 0.2,
                    'atr_pct_max': 6.0,
                    'volume_min_zscore': -0.5,
                    'max_positions': 3
                },
                'is_active': True
            },
            {
                'name': 'Bollinger Mean Reversion',
                'module_path': 'core_engine.strategies.bollinger_mean_reversion:BollingerMeanReversionStrategy',
                'description': 'Short-term mean reversion using Bollinger Bands. Requires 5m candles, checks every bar, typical 1-3h holds. High-frequency entries on oversold bounces.',
                'parameters': {
                    'bb_period': 20,
                    'bb_std': 2.0,
                    'rsi_oversold': 30,
                    'volume_spike_min': 1.2,
                    'atr_pct_max': 4.0,
                    'rsi_overbought': 70,
                    'stop_loss_pct': 1.5,
                    'max_hold_hours': 4,
                    'max_positions': 2
                },
                'is_active': True
            }
        ]
        
        for strategy_data in strategies:
            strategy, created = Strategy.objects.update_or_create(
                name=strategy_data['name'],
                defaults=strategy_data
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created strategy: {strategy.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'• Updated strategy: {strategy.name}')
                )
        
        self.stdout.write(self.style.SUCCESS('\nInitial strategies loaded'))
