import datetime


def minutes(time_str):
    time = datetime.strptime(time_str, "%H:%M")
    return time.hour * 60 + time.minute


def desired(booking):
    if not booking['out_of_capacity']:
        return closest(booking) <= 30
    return False


def closest(booking, target_time):
    target_minutes = target_time.hour * 60 + target_time.minute
    return abs(minutes(booking['start_time']) - target_minutes)
