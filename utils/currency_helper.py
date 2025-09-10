"""
통화 변환 및 포맷 도우미
"""

import logging

class CurrencyHelper:
    def __init__(self):
        self.exchange_rate_manager = None
        try:
            from sqlite_exchange_rate_manager import SQLiteExchangeRateManager
            self.exchange_rate_manager = SQLiteExchangeRateManager()
        except:
            pass
        
    def format_currency(self, amount, currency='USD'):
        """통화 포맷팅"""
        if currency == 'VND':
            return f"{amount:,.0f} ₫"
        elif currency == 'USD':
            return f"${amount:,.2f}"
        elif currency == 'KRW':
            return f"₩{amount:,.0f}"
        else:
            return f"{amount:,.2f} {currency}"
    
    def convert_currency(self, amount, from_currency, to_currency):
        """환율 변환"""
        try:
            if self.exchange_rate_manager:
                rate = self.exchange_rate_manager.get_exchange_rate(from_currency, to_currency)
                if rate:
                    return amount * rate
            return amount
        except:
            return amount
    
    def get_currency_symbol(self, currency):
        """통화 기호 반환"""
        symbols = {
            'USD': '$',
            'VND': '₫', 
            'KRW': '₩',
            'EUR': '€',
            'JPY': '¥'
        }
        return symbols.get(currency, currency)