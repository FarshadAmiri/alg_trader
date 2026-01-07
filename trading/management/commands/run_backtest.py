"""
Management command to run backtest.
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime
from trading.models import Strategy, BacktestRun
from trading.services import execute_backtest_run
from core_engine.registry import StrategyRegistry


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
            '--fee-bps',
            type=int,
            default=10,
            help='Trading fee in basis points (10 = 0.10%%)'
        )
        parser.add_argument(
            '--slippage-bps',
            type=int,
            default=0,
            help='Slippage in basis points'
        )
        parser.add_argument(
            '--max-hold-override',
            type=float,
            default=None,
            help='Override strategy max hold hours (advanced)'
        )

    def handle(self, *args, **options):
        strategy_name = options['strategy']
        symbols = [s.strip() for s in options['symbols'].split(',')]
        fee_bps = options['fee_bps']
        slippage_bps = options['slippage_bps']
        max_hold_override = options.get('max_hold_override')
        
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
        
        # Load strategy from database
        try:
            strategy_model = Strategy.objects.get(name=strategy_name)
        except Strategy.DoesNotExist:
            raise CommandError(f'Strategy "{strategy_name}" not found in database')
        
        if not strategy_model.is_active:
            self.stdout.write(self.style.WARNING(f'Warning: Strategy "{strategy_name}" is not active'))
        
        # Instantiate strategy to get metadata
        StrategyClass = StrategyRegistry.load_from_path(strategy_model.module_path)
        strategy_instance = StrategyClass(parameters=strategy_model.parameters)
        
        # Display strategy info
        self.stdout.write(f"\n{'='*60}")
        self.stdout.write(f"Strategy: {strategy_name}")
        self.stdout.write(f"  Preferred timeframe: {strategy_instance.preferred_timeframe}")
        self.stdout.write(f"  Evaluation mode: {strategy_instance.evaluation_mode}")
        if strategy_instance.evaluation_mode == 'periodic':
            self.stdout.write(f"  Check interval: every {strategy_instance.evaluation_interval_hours}h")
        else:
            self.stdout.write(f"  Check interval: every candle")
        self.stdout.write(f"  Typical hold: {strategy_instance.typical_hold_range}")
        self.stdout.write(f"  Max hold: {max_hold_override or strategy_instance.max_hold_hours}h")
        self.stdout.write(f"{'='*60}\n")
        
        self.stdout.write(f"Period: {start_time} to {end_time}")
        self.stdout.write(f"Symbols: {', '.join(symbols)}")
        self.stdout.write(f"Fees: {fee_bps} bps, Slippage: {slippage_bps} bps\n")
        
        # Get required timeframe from strategy
        required_timeframe = strategy_instance.preferred_timeframe
        
        # Create backtest run record
        backtest_run = BacktestRun.objects.create(
            strategy=strategy_model,
            symbol_universe=symbols,
            start_time=start_time,
            end_time=end_time,
            base_timeframe=required_timeframe,
            window_hours=max_hold_override or strategy_instance.max_hold_hours,
            shift_hours=strategy_instance.evaluation_interval_hours if strategy_instance.evaluation_mode == 'periodic' else 0.1,
            fee_bps=fee_bps,
            slippage_bps=slippage_bps,
            status='running'
        )
        
        try:
            # Execute using shared service (same as web UI)
            self.stdout.write("Loading market data...")
            self.stdout.write("Computing features...")
            self.stdout.write("Initializing strategy...")
            self.stdout.write(f"  Strategy: {strategy_instance.name}")
            self.stdout.write("Running backtest...")
            
            result = execute_backtest_run(backtest_run)
            
            # Display results
            metrics = result.get('metrics', {})
            self.stdout.write(self.style.SUCCESS("\n=== Backtest Results ==="))
            self.stdout.write(f"Total Trades: {metrics.get('total_trades', 0)}")
            self.stdout.write(f"Win Rate: {metrics.get('win_rate', 0):.2f}%")
            self.stdout.write(f"Avg Return: {metrics.get('avg_return_pct', 0):.2f}%")
            self.stdout.write(f"Total Return: {metrics.get('total_return_pct', 0):.2f}%")
            self.stdout.write(f"Max Drawdown: {metrics.get('max_drawdown', 0):.2f}%")
            if metrics.get('profit_factor'):
                self.stdout.write(f"Profit Factor: {metrics.get('profit_factor'):.2f}")
            
            self.stdout.write(self.style.SUCCESS(f"\nBacktest #{backtest_run.id} completed successfully"))
            
        except Exception as e:
            backtest_run.status = 'failed'
            backtest_run.error_message = str(e)
            backtest_run.save()
            
            self.stdout.write(self.style.ERROR(f"Backtest failed: {str(e)}"))
            raise
