"""
URL configuration for trading app.
"""
from django.urls import path
from . import views

app_name = 'trading'

urlpatterns = [
    path('', views.index, name='index'),
    path('strategies/', views.strategy_list, name='strategy_list'),
    path('backtest/run/', views.backtest_run, name='backtest_run'),
    path('backtest/<int:backtest_id>/results/', views.backtest_results, name='backtest_results'),
]
