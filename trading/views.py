"""
Views for trading app.
NO computation logic here - only display and orchestration.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count
from .models import Strategy, BacktestRun, TradeResult, StrategyPerformance
from .forms import BacktestRunForm


def index(request):
    """Home page."""
    context = {
        'total_strategies': Strategy.objects.filter(is_active=True).count(),
        'total_backtests': BacktestRun.objects.count(),
        'recent_backtests': BacktestRun.objects.select_related('strategy').order_by('-created_at')[:5],
    }
    return render(request, 'trading/index.html', context)


def strategy_list(request):
    """List all strategies."""
    strategies = Strategy.objects.annotate(
        backtest_count=Count('backtestrun')
    ).order_by('name')
    
    context = {
        'strategies': strategies,
    }
    return render(request, 'trading/strategy_list.html', context)


def backtest_run(request):
    """Run a new backtest."""
    if request.method == 'POST':
        form = BacktestRunForm(request.POST)
        if form.is_valid():
            # Create backtest run (status will be pending)
            backtest = form.save(commit=False)
            backtest.status = 'pending'
            backtest.save()
            
            messages.success(
                request,
                f'Backtest #{backtest.id} created. Run it using: python manage.py run_backtest --help'
            )
            return redirect('trading:backtest_results', backtest_id=backtest.id)
    else:
        form = BacktestRunForm()
    
    context = {
        'form': form,
    }
    return render(request, 'trading/backtest_run.html', context)


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
    
    context = {
        'backtest': backtest,
        'trades': trades[:100],  # Limit display
        'total_trades': trades.count(),
        'performance': performance,
        'symbol_stats': symbol_stats,
    }
    return render(request, 'trading/backtest_results.html', context)
