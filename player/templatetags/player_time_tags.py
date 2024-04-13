import time

from django import template

register = template.Library()


@register.filter(name='btime')
def beautiful_time(playtime):
    pattern = '%H:%M:%S'
    result = ''
    convert_to_time = time.strptime(playtime, pattern)
    hour = convert_to_time.tm_hour
    minute = convert_to_time.tm_min
    seconds = convert_to_time.tm_sec
    if hour:
        result += str(hour) + ':'
    result += str(minute).zfill(1) + ':'
    result += str(seconds).zfill(2)
    return result