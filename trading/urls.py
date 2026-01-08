"""
URL configuration for trading app.
"""
from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    path('', views.index, name='index'),
    path('strategies/', views.strategy_list, name='strategy_list'),
    path('data/ingest/', views.ingest_market_data, name='ingest_data'),
    path('data/ingest-ajax/', views.ingest_data_ajax, name='ingest_data_ajax'),
    path('data/manage/', views.manage_data, name='manage_data'),
    path('data/delete/', views.delete_data, name='delete_data'),
    path('backtests/', views.backtests, name='backtests'),
    path('backtest/run/', views.backtest_run, name='backtest_run'),  # Legacy redirect
    path('backtest/<int:backtest_id>/results/', views.backtest_results, name='backtest_results'),
    # Phase 1: Portfolio management
    path('portfolio/', views.portfolio_manager, name='portfolio_manager'),
    path('portfolio/backtest/', views.portfolio_backtest, name='portfolio_backtest'),
    path('portfolio/backtest/results/', views.portfolio_backtest_results, name='portfolio_backtest_results'),
]
