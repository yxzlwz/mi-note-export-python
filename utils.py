from time import time as _time

def time():
    return round(_time() * 1000)
