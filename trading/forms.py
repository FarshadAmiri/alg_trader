"""
Forms for trading app.
"""
from django import forms
from django.utils import timezone
from datetime import datetime, timedelta
from .models import BacktestRun, Strategy, Candle
import importlib


class BacktestRunForm(forms.ModelForm):
    """Form for creating a backtest run."""
    
    # Override strategy field to show timeframe in label
    strategy = forms.ChoiceField(
        label='Strategy',
        required=True
    )
    
    available_symbols = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label='Select Symbols (from ingested data)',
        required=False,
        help_text='Check symbols you want to backtest'
    )
    
    custom_symbols = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Or enter custom symbols'}),
        label='Custom Symbols (optional)',
        required=False,
        help_text='Only if you want symbols not listed above'
    )
    
    max_hold_override = forms.FloatField(
        required=False,
        label='Max Hold Override (hours)',
        help_text='Optional: Override strategy default max hold time',
        widget=forms.NumberInput(attrs={'step': '0.5', 'placeholder': 'Auto from strategy'})
    )
    
    class Meta:
        model = BacktestRun
        fields = [
            'start_time',
            'end_time',
            'fee_bps',
            'slippage_bps'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
        labels = {
            'fee_bps': 'Trading Fee (bps)',
            'slippage_bps': 'Slippage (bps)',
        }
        help_texts = {
            'fee_bps': '10 bps = 0.10% per trade side',
            'slippage_bps': 'Additional slippage cost (usually 0-5 bps)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Populate strategy choices with timeframe
        strategies = Strategy.objects.filter(is_active=True)
        strategy_choices = []
        for strategy in strategies:
            try:
                module_path, class_name = strategy.module_path.split(':')
                module = importlib.import_module(module_path)
                strategy_class = getattr(module, class_name)
                strategy_instance = strategy_class(parameters=strategy.parameters)
                timeframe = strategy_instance.preferred_timeframe
                label = f"{strategy.name} ({timeframe})"
                print(f"[FORM DEBUG] Strategy: {label}")  # Debug
            except Exception as e:
                print(f"[FORM DEBUG] Error loading {strategy.name}: {e}")  # Debug
                label = strategy.name
            strategy_choices.append((strategy.id, label))
        
        self.fields['strategy'].choices = [('', '---------')] + strategy_choices
        self.fields['strategy'].widget.choices = self.fields['strategy'].choices  # Explicitly set widget choices
        print(f"[FORM DEBUG] Final choices: {self.fields['strategy'].choices}")  # Debug
        
        # Get available symbols from ingested data
        symbols_data = Candle.objects.values('symbol', 'timeframe').distinct().order_by('symbol', 'timeframe')
        symbol_choices = []
        symbol_info = {}
        
        for item in symbols_data:
            symbol = item['symbol']
            timeframe = item['timeframe']
            
            # Get date range for this symbol/timeframe
            candles = Candle.objects.filter(symbol=symbol, timeframe=timeframe)
            if candles.exists():
                min_date = candles.earliest('timestamp').timestamp
                max_date = candles.latest('timestamp').timestamp
                count = candles.count()
                
                # Use symbol as value (strategy will use its preferred timeframe)
                label = f"{symbol} ({timeframe}) - {count} candles - {min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
                symbol_choices.append((symbol, label))
                
                # Store info for later use
                if symbol not in symbol_info:
                    symbol_info[symbol] = {
                        'min_date': min_date,
                        'max_date': max_date,
                        'timeframes': [timeframe]
                    }
                else:
                    if min_date < symbol_info[symbol]['min_date']:
                        symbol_info[symbol]['min_date'] = min_date
                    if max_date > symbol_info[symbol]['max_date']:
                        symbol_info[symbol]['max_date'] = max_date
                    symbol_info[symbol]['timeframes'].append(timeframe)
        
        # Keep all symbol-timeframe combinations (don't remove duplicates)
        self.fields['available_symbols'].choices = symbol_choices
        self.symbol_info = symbol_info
        
        # Set initial date range from available data if not already set
        if not self.is_bound and symbol_info:
            # Find the common date range across all symbols
            all_min_dates = [info['min_date'] for info in symbol_info.values()]
            all_max_dates = [info['max_date'] for info in symbol_info.values()]
            if all_min_dates and all_max_dates:
                # Use the most restrictive range (latest start, earliest end)
                self.fields['start_time'].initial = max(all_min_dates)
                self.fields['end_time'].initial = min(all_max_dates)
    
    def clean(self):
        """Validate and combine symbol selections."""
        cleaned_data = super().clean()
        selected = cleaned_data.get('available_symbols', [])
        custom = cleaned_data.get('custom_symbols', '')
        strategy_id = cleaned_data.get('strategy')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        # Convert strategy ID to Strategy object
        if strategy_id:
            try:
                strategy = Strategy.objects.get(id=int(strategy_id))
                cleaned_data['strategy_obj'] = strategy
            except (Strategy.DoesNotExist, ValueError):
                raise forms.ValidationError('Invalid strategy selected')
        else:
            strategy = None
        
        # Combine selected and custom symbols
        symbols = list(selected)
        
        # Parse custom symbols
        if custom:
            for line in custom.split('\n'):
                for symbol in line.split(','):
                    symbol = symbol.strip().upper()
                    if symbol and symbol not in symbols:
                        symbols.append(symbol)
        
        if not symbols:
            raise forms.ValidationError('Please select at least one symbol')
        
        # Load strategy to get required timeframe
        if strategy and start_time and end_time:
            try:
                module_path, class_name = strategy.module_path.split(':')
                import importlib
                module = importlib.import_module(module_path)
                strategy_class = getattr(module, class_name)
                strategy_instance = strategy_class(parameters=strategy.parameters)
                required_timeframe = strategy_instance.preferred_timeframe
                
                # Validate data exists for selected symbols at strategy's timeframe
                for symbol in symbols:
                    candles = Candle.objects.filter(
                        symbol=symbol,
                        timeframe=required_timeframe,
                        timestamp__gte=start_time,
                        timestamp__lte=end_time
                    )
                    if not candles.exists():
                        raise forms.ValidationError(
                            f'No data found for {symbol} at {required_timeframe} timeframe '
                            f'(required by strategy "{strategy.name}") '
                            f'between {start_time.strftime("%Y-%m-%d")} and {end_time.strftime("%Y-%m-%d")}. '
                            f'Please ingest data for {required_timeframe} timeframe first.'
                        )
            except Exception as e:
                # If we can't load strategy, that's a different error
                if 'No data found' in str(e):
                    raise
                # Otherwise, let it pass and fail during execution with better error
                pass
        
        cleaned_data['symbols'] = symbols
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set strategy from cleaned data (convert ID back to object)
        instance.strategy = self.cleaned_data.get('strategy_obj')
        
        # Store as JSON list, not comma-separated string
        instance.symbol_universe = self.cleaned_data['symbols']
        
        # Set max_hold_override if provided
        max_hold = self.cleaned_data.get('max_hold_override')
        if max_hold is not None:
            instance.max_hold_override = max_hold
        
        if commit:
            instance.save()
        
        return instance


class MarketDataIngestForm(forms.Form):
    """Form for ingesting market data from exchange."""
    
    PROVIDER_CHOICES = [
        ('binance', 'Binance (Direct API)'),
        ('ccxt', 'CCXT (Other Exchanges)'),
        ('mock', 'Mock Data (for testing)'),
    ]
    
    POPULAR_SYMBOLS = [
        ('BTCUSDT', 'Bitcoin (BTC/USDT)'),
        ('ETHUSDT', 'Ethereum (ETH/USDT)'),
        ('BNBUSDT', 'Binance Coin (BNB/USDT)'),
        ('SOLUSDT', 'Solana (SOL/USDT)'),
        ('XRPUSDT', 'Ripple (XRP/USDT)'),
        ('ADAUSDT', 'Cardano (ADA/USDT)'),
        ('DOGEUSDT', 'Dogecoin (DOGE/USDT)'),
        ('MATICUSDT', 'Polygon (MATIC/USDT)'),
        ('DOTUSDT', 'Polkadot (DOT/USDT)'),
        ('AVAXUSDT', 'Avalanche (AVAX/USDT)'),
        ('LTCUSDT', 'Litecoin (LTC/USDT)'),
        ('LINKUSDT', 'Chainlink (LINK/USDT)'),
        ('ATOMUSDT', 'Cosmos (ATOM/USDT)'),
        ('UNIUSDT', 'Uniswap (UNI/USDT)'),
        ('NEARUSDT', 'NEAR Protocol (NEAR/USDT)'),
    ]
    
    symbol_selection = forms.MultipleChoiceField(
        choices=POPULAR_SYMBOLS,
        widget=forms.CheckboxSelectMultiple,
        label='Select Symbols',
        required=False,
        help_text='Select one or more trading pairs'
    )
    
    custom_symbols = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Or enter custom symbols: BTCUSDT, ETHUSDT'}),
        label='Custom Symbols (optional)',
        required=False,
        help_text='Enter additional symbols separated by commas'
    )
    
    timeframe = forms.ChoiceField(
        choices=[
            ('1m', '1 minute'),
            ('5m', '5 minutes'),
            ('15m', '15 minutes'),
            ('1h', '1 hour'),
            ('4h', '4 hours'),
            ('1d', '1 day'),
        ],
        initial='5m',
        label='Timeframe'
    )
    
    days_back = forms.IntegerField(
        initial=30,
        min_value=1,
        max_value=365,
        label='Days Back',
        help_text='How many days of historical data to fetch'
    )
    
    provider = forms.ChoiceField(
        choices=PROVIDER_CHOICES,
        initial='binance',
        label='Data Provider'
    )
    
    exchange = forms.CharField(
        initial='binance',
        label='Exchange Name',
        help_text='For CCXT provider (e.g., binance, kraken, coinbase)'
    )
    
    def clean(self):
        """Validate and combine symbol selections."""
        cleaned_data = super().clean()
        selected = cleaned_data.get('symbol_selection', [])
        custom = cleaned_data.get('custom_symbols', '')
        
        # Combine selected and custom symbols
        symbols = list(selected)
        
        # Parse custom symbols
        if custom:
            for line in custom.split('\n'):
                for symbol in line.split(','):
                    symbol = symbol.strip().upper()
                    if symbol and symbol not in symbols:
                        symbols.append(symbol)
        
        if not symbols:
            raise forms.ValidationError('Please select at least one symbol or enter custom symbols')
        
        cleaned_data['symbols'] = symbols
        return cleaned_data
