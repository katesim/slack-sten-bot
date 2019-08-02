def minus_hours(time, weekday, hour_shift=1):
    # calculate time for reminder message (1 hour earlier)
    assert ":" in time, "time format should be hh:mm or h:mm"
    assert hour_shift < 24, "too much time shift"

    hour, minute = [int(value) for value in time.split(":")]
    new_hour = (hour - hour_shift) % 24
    if new_hour > hour:
        weekday = (weekday - 1) % 7
    new_time = "{}:{}".format(new_hour, minute)
    return new_time, weekday


def plus_hours(time, weekday, hour_shift=3):
    # calculate time for report message (n hour later)
    assert ":" in time, "time format should be hh:mm or h:mm"
    assert hour_shift < 24, "too much time shift"

    hour, minute = [int(value) for value in time.split(":")]
    new_hour = (hour + hour_shift) % 24
    if new_hour < hour:
        weekday = (weekday + 1) % 7
    new_time = "{}:{}".format(new_hour, minute)
    return new_time, weekday


def plus_minutes(time, minute_shift):
    # TODO delete or modify this function
    assert ":" in time, "time format should be hh:mm or h:mm"

    hour, minute = [int(value) for value in time.split(":")]
    minute += minute_shift
    return "{}:{}".format(hour, minute)


def formatted_time(time):
    # formatting time for schedule
    assert ":" in time, "time format should be hh:mm or h:mm"

    hour, minute = time.split(":")
    len_hour = len(hour)
    len_minute = len(minute)
    assert 3 > len_hour > 0, "invalid hour format"
    assert 3 > len_minute > 0, "invalid minute format"
    if len_hour < 2:
        hour = "0{}".format(hour)
    if len_minute < 2:
        minute = "0{}".format(minute)
    return "{}:{}".format(hour, minute)
