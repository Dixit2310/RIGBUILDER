from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def currency_symbol(context):
    """Returns the currency symbol for the active currency"""
    selected_currency = context.get('selected_currency')
    if selected_currency:
        return selected_currency.symbol
        
    selected_country = context.get('selected_country')
    if selected_country and hasattr(selected_country, 'currency') and selected_country.currency:
        return selected_country.currency.symbol
    return "₹"

@register.simple_tag(takes_context=True)
def currency_code(context):
    """Returns the currency code for the active currency"""
    selected_currency = context.get('selected_currency')
    if selected_currency:
        return selected_currency.code
        
    selected_country = context.get('selected_country')
    if selected_country and hasattr(selected_country, 'currency') and selected_country.currency:
        return selected_country.currency.code
    return "INR"

@register.simple_tag(takes_context=True)
def convert_amount(context, value):
    """Converts a base amount to the active currency and formats it to 2 decimal places"""
    if value is None:
        return "0.00"
        
    selected_currency = context.get('selected_currency')
    if selected_currency:
        rate = float(selected_currency.exchange_rate_to_usd)
        try:
            converted = float(value) * rate
            return f"{converted:,.2f}"
        except (ValueError, TypeError):
            return "0.00"
            
    selected_country = context.get('selected_country')
    if selected_country and hasattr(selected_country, 'currency') and selected_country.currency:
        rate = float(selected_country.currency.exchange_rate_to_usd)
        try:
            converted = float(value) * rate
            return f"{converted:,.2f}"
        except (ValueError, TypeError):
            return "0.00"
            
    try:
        return f"{float(value):,.2f}"
    except (ValueError, TypeError):
        return "0.00"

@register.simple_tag(takes_context=True)
def convert_price(context, value):
    """Combines conversion and symbol display in one helper (e.g. ₹ 50,000.00 or $ 600.00)"""
    symbol = currency_symbol(context)
    amount = convert_amount(context, value)
    return f"{symbol}{amount}"
