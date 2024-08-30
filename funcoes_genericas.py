# Custom function to format numbers with a comma as the decimal separator
def format_number(value, decimal_places=0):
    # Create a format string based on the number of decimal places
    format_string = f"{{:,.{decimal_places}f}}"
    
    # Format the number and replace the comma and dot for desired formatting
    return format_string.format(value).replace(",", "X").replace(".", ",").replace("X", ".")
