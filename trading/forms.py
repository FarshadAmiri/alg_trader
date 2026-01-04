"""
Forms for trading app.
"""
from django import forms
from .models import BacktestRun, Strategy


class BacktestRunForm(forms.ModelForm):
    """Form for creating a backtest run."""
    
    symbol_universe_text = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'placeholder': 'Enter symbols, one per line or comma-separated'}),
        label='Symbols',
        help_text='Enter trading symbols (e.g., BTCUSDT, ETHUSDT)'
    )
    
    class Meta:
        model = BacktestRun
        fields = [
            'strategy',
            'start_time',
            'end_time',
            'base_timeframe',
            'window_hours',
            'shift_hours',
            'fee_bps',
            'slippage_bps'
        ]
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['strategy'].queryset = Strategy.objects.filter(is_active=True)
    
    def clean_symbol_universe_text(self):
        """Parse symbol input."""
        text = self.cleaned_data['symbol_universe_text']
        
        # Split by newlines or commas
        symbols = []
        for line in text.split('\n'):
            for symbol in line.split(','):
                symbol = symbol.strip().upper()
                if symbol:
                    symbols.append(symbol)
        
        if not symbols:
            raise forms.ValidationError('At least one symbol is required')
        
        return symbols
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.symbol_universe = self.cleaned_data['symbol_universe_text']
        
        if commit:
            instance.save()
        
        return instance
