def minus_time(*, time, weekday, hour_shift=0, minute_shift=0):
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


def plus_time(*, time, weekday, hour_shift=0, minute_shift=0):
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

def time_is_overlayed(*, duration_hours=0, duration_minutes=0, down_shift_hours=0, down_shift_minutes=0):
    if down_shift_hours-duration_hours > 0:
        return True
    if duration_hours == down_shift_hours:
        return down_shift_minutes-duration_minutes >= 0
    return False

def sort_times(times):
    return sorted(times)

def get_time_difference(time1, time2):
    assert ":" in time1, "first time format should be hh:mm or h:mm"
    assert ":" in time2, "second time format should be hh:mm or h:mm"


    hour1, minute1 = [int(value) for value in time1.split(":")]
    hour2, minute2 = [int(value) for value in time2.split(":")]
    hour_dif = abs(hour1 - hour2)
    minute_dif = abs(minute1 - minute2)
    return "{}:{}".format(hour_dif, minute_dif)



