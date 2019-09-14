import datetime


def convert_time(input):
    """method for converting .srt time strings to number of seconds"""
    if isinstance(input, float):
        time = str(datetime.timedelta(seconds=input))
        time.replace(".", ",")  # second to milisecond separator is a comma in .srt
        time = time[:-3]
        return(time)
    elif isinstance(input, str):
        time = input
        time_struct = datetime.datetime.strptime(input, "%H:%M:%S,%f")
        td = time_struct - datetime.datetime(1900, 1, 1)
        time_float = td.total_seconds()
        return(time_float)


