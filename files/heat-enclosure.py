#!/usr/bin/env python3

from simple_pid import PID
from datetime import datetime
import requests
import time
import os
from math import ceil


# inputs
if (temp_get := os.environ.get('TEMPERATURE_GET')) is None:
    raise TypeError("Variable is mandatory: TEMPERATURE_GET")
if (heater_post := os.environ.get('HEATER_POST')) is None:
    raise TypeError("Variable is mandatory: HEATER_POST")
if (start_temp := os.environ.get('START_TEMP')) is None:
    raise TypeError("Variable is mandatory: START_TEMP")
if (target_temp := os.environ.get('TARGET_TEMP')) is None:
    raise TypeError("Variable is mandatory: TARGET_TEMP")
if (start_date := os.environ.get('START_DATE')) is None:
    raise TypeError("Variable is mandatory: START_DATE")
if (target_date := os.environ.get('TARGET_DATE')) is None:
    raise TypeError("Variable is mandatory: TARGET_DATE")

# convert into expected types
start_temp = float(start_temp)
target_temp = float(target_temp)
start_date = datetime.fromisoformat(start_date).astimezone()
target_date = datetime.fromisoformat(target_date).astimezone()

# sanity checks
if start_date > target_date:
    raise ValueError("Start Date must be before Target Date.")


def get_setpoint():
    now = datetime.now().astimezone()
    # determine value for setpoint: Transition from start temp at start time to target temp at target time.
    # Before start date we set start temp as the setpoint and after target date we keep target temp as setpoint.
    if now < start_date:
        return start_temp
    elif now > target_date:
        return target_temp
    # transition between the two dates: linear slope (simple rule of three)
    temp_range = (target_temp-start_temp)
    date_range = (target_date-start_date)
    # result must be rounded to the same precision we can actually measure (or the PID can never reach the target)
    return round(start_temp + temp_range * (now-start_date) / date_range, 1)


# create PID object
pid = PID()
pid.sample_time = 60  # seconds
pid.Kp = 1  # full blast if we're one degree from our target
pid.Ki = 0.001
# big Kd as it only has effect for a single heating cycle. So if temp changes by .1°C we steer in the other direction for a bit, even if it's the wrong direction.
# It might make sense to use something different here if we had higher precision temp sensors and/or raised the sample_time significantly, but the latter also reduces reaction time.
pid.Kd = 300  # 300 -> 50% PWM
# ensure we don't get any nonsensical values
pid.output_limits = (-0.9, 0.9)

# PID loop
# observing the system in a quick cycle to give PID good data about the system,
# but the PWM width of heater cable (pid.sample_time) is much longer so it can only be changed at that frequency.
last_update = 0
last_measurement = 0
while True:
    time.sleep(0.1)
    now = time.time()
    if not now - last_measurement >= 5:
        continue

    # measure actual temperature
    last_measurement = now
    response = requests.get(temp_get)
    if response.status_code != 200:
        raise RuntimeError("call to {} responded with status {}".format(
            temp_get, response.status_code))
    try:
        temp_actual = response.json()['temperature']
    except KeyError:
        raise RuntimeError("call to {} did not respond with JSON dict containing 'temperature'. Response was:\n{}".format(
            temp_get, response.json()))

    if now - last_update < pid.sample_time:
        # feed actual temperature into PID
        # (return value is ignored as sample_time has not been exceeded yet,
        # but this lets PID get a better picture of the system)
        pid(temp_actual)
        print("temp: {}/{}°C".format(temp_actual, pid.setpoint))
        continue

    # we've exceeded pid.sample_time!
    last_update = now

    # determine current target temperature we wish to achieve (this can change over time):
    pid.setpoint = get_setpoint()

    # run actual temp through PID to get the new target setting for heater cable (in percentage of the total sample time, so as PWM)
    heater_pwm = pid(temp_actual)
    p, i, d = pid.components  # individual components that lead to the heater value
    if heater_pwm > 0:
        print("temp: {}/{}°C\theater: {:.0f}%\t(p: {:.2f}, i: {:.2f}, d: {:.2f})".format(
            temp_actual, pid.setpoint, heater_pwm*100, p, i, d))

        # activate heater cable for the calculated duration (must be less than sample_time! But we ensured that in pid.output_limits)
        heater_ontime = ceil(heater_pwm * pid.sample_time)
        requests.post(heater_post.format(timer=heater_ontime))
    else:
        print("temp: {}/{}°C\theater: off\t(p: {:.2f}, i: {:.2f}, d: {:.2f})".format(
            temp_actual, pid.setpoint, p, i, d))
        # TODO: We could wire up the cooler and actively cool down the enclosure if it's too hot, is that a good idea?
