from colorama import Fore


def amount_to_str(value, currency):
    if not value or value < 0:
        return Fore.RED + "%10s %s" % ("%.2f" % (value or 0), currency)
    else:
        return Fore.GREEN + "%10s %s" % ("%.2f" % (value or 0), currency)
