"""
Management command to run backtest.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime
from trading.models import Strategy, BacktestRun, TradeResult, StrategyPerformance, Candle
from core_engine.registry import StrategyRegistry
from core_engine.features.momentum import MomentumFeatures, TrendFeatures
from core_engine.features.volatility import VolatilityFeatures
from core_engine.features.liquidity import LiquidityFeatures, CompositeFeatures
from core_engine.backtest.engine import BacktestEngine
import pandas as pd


class Command(BaseCommand):
    help = 'Run backtest for a strategy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--strategy',
            type=str,
            required=True,
            help='Strategy name (from database)'
        )
        parser.add_argument(
            '--symbols',
            type=str,
            required=True,
            help='Comma-separated list of symbols'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            required=True,
            help='Start date (YYYY-MM-DD HH:MM)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            required=True,
            help='End date (YYYY-MM-DD HH:MM)'
        )
        parser.add_argument(
            '--window-hours',
            type=int,
            default=4,
            help='Holding window in hours'
        )
        parser.add_argument(
            '--shift-hours',
            type=int,
            default=2,
            help='Window shift in hours'
        )
        parser.add_argument(
            '--fee-bps',
            type=int,
            default=10,
            help='Fee in basis points (10 = 0.10%)'
        )
        parser.add_argument(
            '--timeframe',
            type=str,
            default='5m',
            help='Base timeframe'
        )

    def handle(self, *args, **options):
        strategy_name = options['strategy']
        symbols = [s.strip() for s in options['symbols'].split(',')]
        window_hours = options['window_hours']
        shift_hours = options['shift_hours']
        fee_bps = options['fee_bps']
        timeframe = options['timeframe']
        
        # Parse dates
        try:
            start_time = datetime.strptime(options['start_date'], '%Y-%m-%d %H:%M')
            end_time = datetime.strptime(options['end_date'], '%Y-%m-%d %H:%M')
        except ValueError:
            try:
                start_time = datetime.strptime(options['start_date'], '%Y-%m-%d')
                end_time = datetime.strptime(options['end_date'], '%Y-%m-%d')
            except ValueError:
                raise CommandError('Invalid date format. Use YYYY-MM-DD or YYYY-MM-DD HH:MM')
        
        # Make timezone-aware
        start_time = timezone.make_aware(start_time) if timezone.is_naive(start_time) else start_time
        end_time = timezone.make_aware(end_time) if timezone.is_naive(end_time) else end_time
        
        self.stdout.write(f"Running backtest: {strategy_name}")
        self.stdout.write(f"Period: {start_time} to {end_time}")
        self.stdout.write(f"Symbols: {', '.join(symbols)}")
        
        # Load strategy from database
        try:
            strategy_model = Strategy.objects.get(name=strategy_name)
        except Strategy.DoesNotExist:
            raise CommandError(f'Strategy "{strategy_name}" not found in database')
        
        if not strategy_model.is_active:
            self.stdout.write(self.style.WARNING(f'Warning: Strategy "{strategy_name}" is not active'))
        
        # Create backtest run record
        backtest_run = BacktestRun.objects.create(
            strategy=strategy_model,
            symbol_universe=symbols,
            start_time=start_time,
            end_time=end_time,
            base_timeframe=timeframe,
            window_hours=window_hours,
            shift_hours=shift_hours,
            fee_bps=fee_bps,
            status='running'
        )
        
        try:
            # Load candles from database
            self.stdout.write("Loading market data...")
            candles_by_symbol = {}
            
            for symbol in symbols:
                candles = Candle.objects.filter(
                    symbol=symbol,
                    timeframe=timeframe,
                    timestamp__gte=start_time,
                    timestamp__lte=end_time
                ).order_by('timestamp')
                
                if not candles.exists():
                    self.stdout.write(
                        self.style.WARNING(f"No data found for {symbol}")
                    )
                    continue
                
                # Convert to DataFrame
                data = list(candles.values('timestamp', 'open', 'high', 'low', 'close', 'volume'))
                df = pd.DataFrame(data)
                candles_by_symbol[symbol] = df
                
                self.stdout.write(f"  {symbol}: {len(df)} candles")
            
            if not candles_by_symbol:
                raise CommandError("No data available for any symbol")
            
            # Compute features
            self.stdout.write("Computing features...")
            features_by_symbol = {}
            
            momentum = MomentumFeatures()
            volatility = VolatilityFeatures()
            liquidity = LiquidityFeatures()
            composite = CompositeFeatures()
            
            for symbol, df in candles_by_symbol.items():
                try:
                    # Compute all features
                    df = momentum.compute(df)
                    df = volatility.compute(df)
                    df = liquidity.compute(df)
                    df = composite.compute(df)
                    
                    features_by_symbol[symbol] = df
                    self.stdout.write(f"  {symbol}: {len(df.columns)} features")
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f"  Error computing features for {symbol}: {e}")
                    )
            
            # Load strategy class
            self.stdout.write("Initializing strategy...")
            try:
                StrategyClass = StrategyRegistry.load_from_path(strategy_model.module_path)
                strategy_instance = StrategyClass(parameters=strategy_model.parameters)
                self.stdout.write(f"  Strategy: {strategy_instance.name}")
            except Exception as e:
                raise CommandError(f"Failed to load strategy: {e}")
            
            # Run backtest
            self.stdout.write("Running backtest...")
            engine = BacktestEngine(
                window_hours=window_hours,
                shift_hours=shift_hours,
                fee_bps=fee_bps
            )
            
            result = engine.run(
                strategy_instance,
                features_by_symbol,
                start_time,
                end_time
            )
            
            # Save results
            self.stdout.write("Saving results...")
            
            for trade in result['trades']:
                TradeResult.objects.create(
                    backtest=backtest_run,
                    symbol=trade.symbol,
                    entry_time=trade.entry_time,
                    exit_time=trade.exit_time,
                    direction=trade.direction,
                    return_pct=trade.return_pct,
                    max_drawdown=trade.max_drawdown,
                    metadata=trade.metadata
                )
            
            # Save performance metrics
            metrics = result['metrics']
            StrategyPerformance.objects.create(
                backtest=backtest_run,
                total_trades=metrics['total_trades'],
                winning_trades=metrics['winning_trades'],
                losing_trades=metrics['losing_trades'],
                win_rate=metrics['win_rate'],
                avg_return_pct=metrics['avg_return_pct'],
                median_return_pct=metrics['median_return_pct'],
                profit_factor=metrics['profit_factor'],
                max_drawdown=metrics['max_drawdown'],
                total_return_pct=metrics['total_return_pct']
            )
            
            # Update backtest status
            backtest_run.status = 'completed'
            backtest_run.save()
            
            # Display results
            self.stdout.write(self.style.SUCCESS("\n=== Backtest Results ==="))
            self.stdout.write(f"Total Trades: {metrics['total_trades']}")
            self.stdout.write(f"Win Rate: {metrics['win_rate']:.2f}%")
            self.stdout.write(f"Avg Return: {metrics['avg_return_pct']:.2f}%")
            self.stdout.write(f"Total Return: {metrics['total_return_pct']:.2f}%")
            self.stdout.write(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
            if metrics['profit_factor']:
                self.stdout.write(f"Profit Factor: {metrics['profit_factor']:.2f}")
            
            self.stdout.write(self.style.SUCCESS(f"\nBacktest #{backtest_run.id} completed successfully"))
            
        except Exception as e:
            backtest_run.status = 'failed'
            backtest_run.error_message = str(e)
            backtest_run.save()
            
            self.stdout.write(self.style.ERROR(f"Backtest failed: {str(e)}"))
            raise
