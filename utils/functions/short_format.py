def short_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num = round(num / 1000.0, 2)
    return "{:.{}f}{}".format(num, 2, ["", "K", "M", "B", "T", "Q"][magnitude])
