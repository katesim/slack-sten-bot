def minus_time(*, time, weekday, hour_shift, minute_shift):
    # calculate time minus hour_shift hours and minute_shift minutes
    assert ":" in time, "time format should be hh:mm or h:mm or hh:m or h:m"
    assert hour_shift < 24, "too much hour shift"
    assert minute_shift < 60, "too much minute shift"
    assert 0 <= weekday < 7, "invalid weekday"

    hour, minute = [int(value) for value in time.split(":")]
    new_hour = (hour - hour_shift) % 24
    new_minute = (minute - minute_shift) % 60
    if new_hour > hour:
        weekday = (weekday - 1) % 7
    if new_minute > minute:
        tmp_hour = new_hour
        new_hour = (new_hour - 1) % 24
        if new_hour > tmp_hour:
            weekday = (weekday - 1) % 7
    new_time = "{}:{}".format(new_hour, new_minute)
    return new_time, weekday


def plus_time(*, time, weekday, hour_shift, minute_shift):
    # calculate time plus hour_shift hours and minute_shift minutes
    assert ":" in time, "time format should be hh:mm or h:mm"
    assert hour_shift < 24, "too much time shift"
    assert minute_shift < 60, "too much minute shift"
    assert 0 <= weekday < 7, "invalid weekday"

    hour, minute = [int(value) for value in time.split(":")]
    new_hour = (hour + hour_shift) % 24
    new_minute = (minute + minute_shift) % 60
    if new_hour < hour:
        weekday = (weekday + 1) % 7
    if new_minute < minute:
        tmp_hour = new_hour
        new_hour = (new_hour + 1) % 24
        if new_hour < tmp_hour:
            weekday = (weekday + 1) % 7
    new_time = "{}:{}".format(new_hour, new_minute)
    return new_time, weekday

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

def time_is_overlayed(*, duration_hours, duration_minutes, down_shift_hours, down_shift_minutes):
    if down_shift_hours-duration_hours > 0:
        return True
    if duration_hours == down_shift_hours:
        return down_shift_minutes-duration_minutes >= 0
    return False

def sort_times(times):
    return sorted(times)
