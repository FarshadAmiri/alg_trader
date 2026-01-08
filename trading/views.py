"""
Views for trading app.
NO computation logic here - only display and orchestration.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Strategy, BacktestRun, TradeResult, StrategyPerformance, Candle
from .forms import BacktestRunForm, MarketDataIngestForm
from .services import execute_backtest_run
from core_engine.data.providers import BinanceDirectProvider, CCXTProvider, MockProvider
from core_engine.data.fetchers import DataFetcher
import importlib


def index(request):
    """Home page."""
    total_candles = Candle.objects.count()
    symbols_count = Candle.objects.values('symbol').distinct().count()
    
    context = {
        'total_strategies': Strategy.objects.filter(is_active=True).count(),
        'total_backtests': BacktestRun.objects.count(),
        'total_candles': total_candles,
        'symbols_count': symbols_count,
        'recent_backtests': BacktestRun.objects.select_related('strategy').order_by('-created_at')[:5],
    }
    return render(request, 'trading/index.html', context)


def strategy_list(request):
    """List all strategies."""
    strategies = Strategy.objects.annotate(
        backtest_count=Count('backtestrun')
    ).order_by('name')
    
    # Load timeframe for each strategy
    for strategy in strategies:
        try:
            module_path, class_name = strategy.module_path.split(':')
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, class_name)
            strategy_instance = strategy_class(parameters=strategy.parameters)
            strategy.timeframe = strategy_instance.preferred_timeframe
        except Exception:
            strategy.timeframe = '?'
    
    context = {
        'strategies': strategies,
    }
    return render(request, 'trading/strategy_list.html', context)


def backtests(request):
    """List all backtests and create new ones."""
    if request.method == 'POST':
        form = BacktestRunForm(request.POST)
        if form.is_valid():
            # Create backtest run (status will be pending)
            backtest = form.save(commit=False)
            
            # Load strategy to get metadata
            strategy_obj = backtest.strategy
            module_path, class_name = strategy_obj.module_path.split(':')
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, class_name)
            strategy_instance = strategy_class(parameters=strategy_obj.parameters)
            
            # Auto-populate fields from strategy metadata
            backtest.base_timeframe = strategy_instance.preferred_timeframe
            # Use override if provided, otherwise use strategy default
            backtest.window_hours = backtest.max_hold_override if backtest.max_hold_override else strategy_instance.max_hold_hours
            # For every_bar mode, use small shift (0.1h) to trigger bar-by-bar evaluation
            backtest.shift_hours = strategy_instance.evaluation_interval_hours if strategy_instance.evaluation_mode == 'periodic' else 0.1
            
            backtest.status = 'pending'
            backtest.save()
            
            # Execute backtest immediately
            try:
                execute_backtest_run(backtest)
                messages.success(request, f'Backtest #{backtest.id} completed successfully!')
            except Exception as e:
                backtest.status = 'failed'
                backtest.error_message = str(e)
                backtest.save()
                messages.error(request, f'Backtest failed: {str(e)}')
            
            return redirect('trading:backtest_results', backtest_id=backtest.id)
    else:
        form = BacktestRunForm()
    
    # Get all backtests
    all_backtests = BacktestRun.objects.select_related('strategy').order_by('-created_at')
    
    # Extract timeframe mapping from form for JavaScript
    import json
    strategy_timeframes = getattr(form, 'strategy_timeframes', {})
    symbols_by_timeframe = getattr(form, 'symbols_by_timeframe', {})
    
    context = {
        'form': form,
        'backtests': all_backtests,
        'strategy_timeframes_json': json.dumps(strategy_timeframes),
        'symbols_by_timeframe_json': json.dumps(symbols_by_timeframe),
    }
    return render(request, 'trading/backtests.html', context)


def backtest_run(request):
    """Legacy redirect to backtests page."""
    return redirect('trading:backtests')


def backtest_results(request, backtest_id):
    """Display backtest results."""
    backtest = get_object_or_404(BacktestRun, id=backtest_id)
    
    # Get trades
    trades = TradeResult.objects.filter(backtest=backtest).order_by('-entry_time')
    
    # Get performance metrics
    try:
        performance = StrategyPerformance.objects.get(backtest=backtest)
    except StrategyPerformance.DoesNotExist:
        performance = None
    
    # Calculate per-symbol statistics
    symbol_stats = {}
    for symbol in set(trades.values_list('symbol', flat=True)):
        symbol_trades = trades.filter(symbol=symbol)
        if symbol_trades.exists():
            winning = symbol_trades.filter(return_pct__gt=0).count()
            total = symbol_trades.count()
            avg_return = sum(t.return_pct for t in symbol_trades) / total
            
            symbol_stats[symbol] = {
                'total_trades': total,
                'win_rate': (winning / total * 100) if total > 0 else 0,
                'avg_return': avg_return,
            }
    
    # Prepare chart data (price data + trades for each symbol)
    import json
    chart_data = {}
    for symbol in backtest.symbol_universe:
        # Get price data for this symbol
        candles = Candle.objects.filter(
            symbol=symbol,
            timeframe=backtest.base_timeframe,
            timestamp__gte=backtest.start_time,
            timestamp__lte=backtest.end_time
        ).order_by('timestamp').values('timestamp', 'open', 'high', 'low', 'close', 'volume')
        
        # Get trades for this symbol - extract prices from metadata
        symbol_trades_raw = trades.filter(symbol=symbol)
        symbol_trades = []
        for trade in symbol_trades_raw:
            symbol_trades.append({
                'entry_time': trade.entry_time,
                'exit_time': trade.exit_time,
                'entry_price': trade.metadata.get('entry_price', 0),
                'exit_price': trade.metadata.get('exit_price', 0),
                'return_pct': trade.return_pct,
                'direction': trade.direction
            })
        
        chart_data[symbol] = {
            'candles': list(candles),
            'trades': symbol_trades
        }
    
    # Convert to JSON for JavaScript
    chart_data_json = json.dumps(chart_data, default=str)
    
    context = {
        'backtest': backtest,
        'trades': trades[:100],  # Limit display
        'total_trades': trades.count(),
        'performance': performance,
        'symbol_stats': symbol_stats,
        'chart_data_json': chart_data_json,
    }
    return render(request, 'trading/backtest_results.html', context)


def ingest_market_data(request):
    """Ingest market data from exchange via web interface."""
    if request.method == 'POST':
        form = MarketDataIngestForm(request.POST)
        if form.is_valid():
            symbols = form.cleaned_data['symbols']
            timeframe = form.cleaned_data['timeframe']
            date_mode = form.cleaned_data['date_mode']
            provider_name = form.cleaned_data['provider']
            exchange_name = form.cleaned_data['exchange']
            
            # Calculate time range based on mode
            if date_mode == 'days_back':
                days_back = form.cleaned_data['days_back']
                end_time = timezone.now()
                start_time = end_time - timedelta(days=days_back)
            else:  # date_range
                start_time = form.cleaned_data['start_date']
                end_time = form.cleaned_data['end_date']
                # Ensure timezone-aware
                if start_time.tzinfo is None:
                    start_time = timezone.make_aware(start_time)
                if end_time.tzinfo is None:
                    end_time = timezone.make_aware(end_time)
            
            # Initialize provider
            try:
                if provider_name == 'binance':
                    provider = BinanceDirectProvider()
                elif provider_name == 'mock':
                    provider = MockProvider()
                    messages.info(request, '🧪 Using mock data provider for testing')
                else:
                    provider = CCXTProvider(exchange_name=exchange_name)
            except Exception as e:
                messages.error(request, f'Failed to initialize provider: {str(e)}')
                context = {'form': form}
                return render(request, 'trading/ingest_data.html', context)
            
            fetcher = DataFetcher(provider)
            
            # Track results
            results = []
            total_created = 0
            total_updated = 0
            errors = []
            
            # Fetch and store data for each symbol
            for symbol in symbols:
                try:
                    # Use provider directly to avoid DataFetcher timezone issues
                    df = provider.fetch_ohlcv(symbol, timeframe, start_time, end_time)
                    
                    if df.empty:
                        error_msg = 'No data retrieved'
                        if provider_name == 'ccxt':
                            error_msg += f' - Check if {symbol} exists on {exchange_name} exchange'
                        errors.append(f"{symbol}: {error_msg}")
                        results.append({
                            'symbol': symbol,
                            'error': error_msg,
                            'success': False
                        })
                        continue
                    
                    # Ensure timezone-aware timestamps
                    if df['timestamp'].dt.tz is None:
                        df['timestamp'] = df['timestamp'].dt.tz_localize('UTC')
                    else:
                        df['timestamp'] = df['timestamp'].dt.tz_convert('UTC')
                    
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
                    
                    total_created += candles_created
                    total_updated += candles_updated
                    results.append({
                        'symbol': symbol,
                        'created': candles_created,
                        'updated': candles_updated,
                        'success': True
                    })
                    
                except Exception as e:
                    error_detail = str(e)
                    
                    # Make network errors more user-friendly
                    if 'Connection' in error_detail or 'Network' in error_detail:
                        error_detail = 'Network error - Check internet connection, proxy settings, or firewall'
                    elif 'refused' in error_detail.lower():
                        error_detail = 'Connection refused - API may be blocked by firewall/proxy'
                    
                    errors.append(f"{symbol}: {error_detail}")
                    results.append({
                        'symbol': symbol,
                        'error': error_detail,
                        'success': False
                    })
            
            # Show results
            if results:
                success_count = sum(1 for r in results if r.get('success'))
                messages.success(
                    request,
                    f'Data ingestion complete! {success_count}/{len(symbols)} symbols successful. '
                    f'{total_created} candles created, {total_updated} updated.'
                )
            
            if errors:
                for error in errors:
                    messages.warning(request, error)
            
            context = {
                'form': form,
                'results': results,
                'total_created': total_created,
                'total_updated': total_updated,
            }
            return render(request, 'trading/ingest_data.html', context)
    else:
        form = MarketDataIngestForm()
    
    # Get database stats
    total_candles = Candle.objects.count()
    symbols_count = Candle.objects.values('symbol').distinct().count()
    
    context = {
        'form': form,
        'total_candles': total_candles,
        'symbols_count': symbols_count,
    }
    return render(request, 'trading/ingest_data.html', context)


def manage_data(request):
    """View and manage ingested market data."""
    from django.db.models import Count, Min, Max
    from .forms import MarketDataIngestForm
    
    # Get data grouped by symbol and timeframe
    data_summary = Candle.objects.values('symbol', 'timeframe').annotate(
        count=Count('id'),
        min_date=Min('timestamp'),
        max_date=Max('timestamp')
    ).order_by('symbol', 'timeframe')
    
    form = MarketDataIngestForm()
    
    context = {
        'data_summary': data_summary,
        'total_candles': Candle.objects.count(),
        'form': form,
    }
    return render(request, 'trading/manage_data.html', context)


def delete_data(request):
    """Delete specific symbol-timeframe data."""
    if request.method == 'POST':
        symbol = request.POST.get('symbol')
        timeframe = request.POST.get('timeframe')
        
        if symbol and timeframe:
            deleted_count = Candle.objects.filter(symbol=symbol, timeframe=timeframe).delete()[0]
            messages.success(request, f'Deleted {deleted_count} candles for {symbol} ({timeframe})')
    
    return redirect('trading:manage_data')


def ingest_data_ajax(request):
    """AJAX endpoint for data ingestion with progress updates."""
    from django.http import StreamingHttpResponse
    from .forms import MarketDataIngestForm
    from core_engine.data.providers import BinanceDirectProvider, CCXTProvider, MockProvider
    import json
    from datetime import timedelta
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    def generate_progress():
        """Generator that yields Server-Sent Events with progress updates."""
        form = MarketDataIngestForm(request.POST)
        
        if not form.is_valid():
            yield f"data: {json.dumps({'error': 'Invalid form data', 'complete': True})}\n\n"
            return
        
        symbols = form.cleaned_data['symbols']  # Already a list
        timeframe = form.cleaned_data['timeframe']
        days_back = form.cleaned_data['days_back']
        provider_name = form.cleaned_data['provider']
        exchange_name = form.cleaned_data['exchange']
        
        # Calculate time range
        end_time = timezone.now()
        start_time = end_time - timedelta(days=days_back)
        
        # Initialize provider
        try:
            if provider_name == 'binance':
                provider = BinanceDirectProvider()
            elif provider_name == 'mock':
                provider = MockProvider()
            else:
                provider = CCXTProvider(exchange_name=exchange_name)
        except Exception as e:
            yield f"data: {json.dumps({'error': f'Failed to initialize provider: {str(e)}', 'complete': True})}\n\n"
            return
        
        total_symbols = len(symbols)
        results = []
        errors = []
        total_created = 0
        total_updated = 0
        total_candles_processed = 0
        total_expected_candles = 0
        
        # First, fetch all data to know total candles
        all_data = []
        for idx, symbol in enumerate(symbols):
            yield f"data: {json.dumps({'progress': 0, 'message': f'Fetching {symbol}... ({idx+1}/{total_symbols})'})}\n\n"
            
            try:
                df = provider.fetch_ohlcv(symbol, timeframe, start_time, end_time)
                
                if df.empty:
                    errors.append(f"{symbol}: No data returned")
                    results.append({'symbol': symbol, 'error': 'No data', 'success': False, 'created': 0, 'updated': 0})
                else:
                    all_data.append({'symbol': symbol, 'df': df})
                    total_expected_candles += len(df)
                    
            except Exception as e:
                error_detail = str(e)
                
                # Make network errors more user-friendly
                if 'Connection' in error_detail or 'Network' in error_detail:
                    error_detail = 'Network error - Check internet connection'
                elif 'refused' in error_detail.lower():
                    error_detail = 'Connection refused - API may be blocked'
                
                errors.append(f"{symbol}: {error_detail}")
                results.append({
                    'symbol': symbol,
                    'error': error_detail,
                    'success': False,
                    'created': 0,
                    'updated': 0
                })
        
        # Now process and save candles with detailed progress
        if total_expected_candles > 0:
            for data in all_data:
                symbol = data['symbol']
                df = data['df']
                
                candles_created = 0
                candles_updated = 0
                
                for idx, (_, row) in enumerate(df.iterrows()):
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
                    
                    total_candles_processed += 1
                    
                    # Update progress every 10 candles or at the end
                    if total_candles_processed % 10 == 0 or total_candles_processed == total_expected_candles:
                        progress = (total_candles_processed / total_expected_candles) * 100
                        yield f"data: {json.dumps({'progress': progress, 'message': f'Saving {symbol}... ({total_candles_processed}/{total_expected_candles} candles)'})}\n\n"
                
                total_created += candles_created
                total_updated += candles_updated
                results.append({
                    'symbol': symbol,
                    'created': candles_created,
                    'updated': candles_updated,
                    'success': True
                })
        
        # Final progress update
        success_count = sum(1 for r in results if r.get('success'))
        summary = f'{success_count}/{total_symbols} symbols successful. {total_created} candles created, {total_updated} updated.'
        
        yield f"data: {json.dumps({'progress': 100, 'message': 'Complete!', 'complete': True, 'summary': summary, 'results': results, 'errors': errors})}\n\n"
    
    response = StreamingHttpResponse(generate_progress(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


# ============================================================================
# Phase 1: Portfolio Management Views
# ============================================================================

def portfolio_manager(request):
    """Portfolio manager interface for combining multiple strategies."""
    from core_engine.portfolio.manager import PortfolioManager
    from core_engine.portfolio.combiners import SignalCombiner
    from core_engine.portfolio.allocators import CapitalAllocator
    from django.db import models
    
    # Get all active strategies
    strategies_qs = Strategy.objects.filter(is_active=True)
    
    # Default settings
    selected_strategy_ids = request.GET.getlist('strategies', [])
    combination_method = request.GET.get('combination_method', 'weighted')
    allocation_method = request.GET.get('allocation_method', 'proportional')
    total_capital = float(request.GET.get('total_capital', 100000))
    
    # Available methods
    combiner = SignalCombiner()
    allocator = CapitalAllocator()
    combination_methods = combiner.get_available_methods()
    allocation_methods = allocator.get_available_methods()
    
    # Method display names
    combination_method_names = {
        'weighted': 'Weighted Average',
        'confidence_weighted': 'Confidence Weighted',
        'rank_average': 'Rank Average',
        'best_strategy': 'Best Strategy'
    }
    allocation_method_names = {
        'proportional': 'Proportional',
        'equal_weight': 'Equal Weight',
        'top_n': 'Top N',
        'threshold': 'Threshold'
    }
    
    # Get available data from database
    available_data = []
    candle_data = Candle.objects.values('symbol', 'timeframe').annotate(
        min_date=models.Min('timestamp'),
        max_date=models.Max('timestamp'),
        count=models.Count('id')
    ).order_by('timeframe', 'symbol')
    
    for data in candle_data:
        available_data.append({
            'symbol': data['symbol'],
            'timeframe': data['timeframe'],
            'min_date': data['min_date'],
            'max_date': data['max_date'],
            'count': data['count']
        })
    
    context = {
        'strategies': strategies_qs,
        'selected_strategy_ids': [int(s) for s in selected_strategy_ids if s],
        'combination_method': combination_method,
        'allocation_method': allocation_method,
        'total_capital': total_capital,
        'combination_methods': combination_methods,
        'allocation_methods': allocation_methods,
        'combination_method_names': combination_method_names,
        'allocation_method_names': allocation_method_names,
        'available_data': available_data,
    }
    
    return render(request, 'trading/portfolio_manager.html', context)


def portfolio_backtest(request):
    """Run backtest for a portfolio of strategies."""
    if request.method != 'POST':
        return redirect('trading:portfolio_manager')
    
    from core_engine.backtest.engine import BacktestEngine
    import json
    
    # Get parameters
    strategy_ids = request.POST.getlist('strategies')
    combination_method = request.POST.get('combination_method', 'weighted')
    allocation_method = request.POST.get('allocation_method', 'proportional')
    total_capital = float(request.POST.get('total_capital', 100000))
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    symbol_universe = request.POST.get('symbol_universe', '').split(',')
    symbol_universe = [s.strip() for s in symbol_universe if s.strip()]
    
    if not strategy_ids or not symbol_universe:
        messages.error(request, 'Please select strategies and symbols')
        return redirect('trading:portfolio_manager')
    
    # Load strategies
    strategies_qs = Strategy.objects.filter(id__in=strategy_ids, is_active=True)
    
    if not strategies_qs.exists():
        messages.error(request, 'No valid strategies selected')
        return redirect('trading:portfolio_manager')
    
    # Instantiate strategy objects
    strategy_instances = []
    for strategy_obj in strategies_qs:
        try:
            module_path, class_name = strategy_obj.module_path.split(':')
            module = importlib.import_module(module_path)
            strategy_class = getattr(module, class_name)
            strategy_instance = strategy_class(parameters=strategy_obj.parameters)
            strategy_instances.append(strategy_instance)
        except Exception as e:
            messages.error(request, f'Error loading strategy {strategy_obj.name}: {e}')
            return redirect('trading:portfolio_manager')
    
    # Load data and run backtest
    try:
        from trading.services import load_features_for_backtest
        from datetime import datetime
        from django.utils import timezone as tz
        import time
        
        # Parse dates and make timezone-aware
        start_time = datetime.fromisoformat(start_date)
        end_time = datetime.fromisoformat(end_date)
        
        if start_time.tzinfo is None:
            start_time = tz.make_aware(start_time)
        if end_time.tzinfo is None:
            end_time = tz.make_aware(end_time)
        
        print(f"[PORTFOLIO] Starting portfolio backtest...")
        print(f"[PORTFOLIO] Strategies: {[s.name for s in strategy_instances]}")
        print(f"[PORTFOLIO] Symbols: {symbol_universe}")
        print(f"[PORTFOLIO] Period: {start_time} to {end_time}")
        
        start_load = time.time()
        
        # Load features
        features_by_symbol = load_features_for_backtest(
            symbol_universe,
            start_time,
            end_time
        )
        
        load_time = time.time() - start_load
        print(f"[PORTFOLIO] Data loaded in {load_time:.2f} seconds")
        print(f"[PORTFOLIO] Running backtest engine...")
        
        start_backtest = time.time()
        
        # Run portfolio backtest
        engine = BacktestEngine()
        results = engine.run_portfolio_backtest(
            strategies=strategy_instances,
            features_by_symbol=features_by_symbol,
            start_time=start_time,
            end_time=end_time,
            combination_method=combination_method,
            allocation_method=allocation_method,
            total_capital=total_capital
        )
        
        backtest_time = time.time() - start_backtest
        total_time = time.time() - start_load
        print(f"[PORTFOLIO] Backtest completed in {backtest_time:.2f} seconds")
        print(f"[PORTFOLIO] Total time: {total_time:.2f} seconds")
        
        # Store results in session for display
        request.session['portfolio_backtest_results'] = {
            'portfolio_metrics': results['portfolio_metrics'].to_dict(),
            'combination_method': combination_method,
            'allocation_method': allocation_method,
            'num_strategies': len(strategy_instances),
            'strategy_names': [s.name for s in strategy_instances],
            'start_date': start_date,
            'end_date': end_date,
            'load_time': f"{load_time:.2f}s",
            'backtest_time': f"{backtest_time:.2f}s",
            'total_time': f"{total_time:.2f}s",
        }
        
        messages.success(request, f'Portfolio backtest completed in {total_time:.1f} seconds!')
        return redirect('trading:portfolio_backtest_results')
    
    except Exception as e:
        messages.error(request, f'Backtest failed: {str(e)}')
        return redirect('trading:portfolio_manager')


def portfolio_backtest_results(request):
    """Display portfolio backtest results."""
    results = request.session.get('portfolio_backtest_results')
    
    if not results:
        messages.warning(request, 'No backtest results found')
        return redirect('trading:portfolio_manager')
    
    context = {
        'results': results,
    }
    
    return render(request, 'trading/portfolio_backtest_results.html', context)
