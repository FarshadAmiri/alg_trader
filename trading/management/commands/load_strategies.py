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
                'description': 'Baseline strategy using MACD histogram and RSI with volatility and volume filters. Ranks symbols by combined momentum score.',
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
                'description': 'Ranks symbols by multi-timeframe momentum score with volume confirmation and volatility control.',
                'parameters': {
                    'min_momentum_score': 0.2,
                    'atr_pct_max': 6.0,
                    'volume_min_zscore': -0.5,
                    'max_positions': 3
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
