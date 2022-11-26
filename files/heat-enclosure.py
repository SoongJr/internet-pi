#!/usr/bin/env python3

from simple_pid import PID
from datetime import datetime
import requests
import time
import os
from math import ceil
import faulthandler
import signal

faulthandler.enable() # dump a trace when receiving SIGSEGV, SIGFPE, SIGABRT, SIGBUS or SIGILL
faulthandler.register(signal.SIGUSR1.value) # dump a trace on demand, by someone sending `kill -s SIGUSR1 $(pidof python3)`

# inputs
if (temp_get := os.environ.get('TEMPERATURE_GET')) is None:
    raise TypeError("Variable is mandatory: TEMPERATURE_GET")
temp_reboot = os.environ.get('TEMPERATURE_REBOOT')
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
pid.Kp = 2  # full blast if we are half a degree from our target
pid.Ki = 0.0005 # 0.001 was good when sensor directly next to heater, 0.0005 is better when sensor is buried under some insulation
# big Kd as it only has effect for a single heating cycle. So if temp changes by .1°C we steer in the other direction for a bit, even if it's the wrong direction.
# It might make sense to use something different here if we had higher precision temp sensors and/or raised the sample_time significantly, but the latter also reduces reaction time.
pid.Kd = 150  # 600 equals 100% PWM
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

    # on every loop, reset the timer for faulthandler to trace and exit the process. This is a watchdog to ensure the script does not freeze.
    faulthandler.dump_traceback_later(180, repeat=True, exit=True) # note: I haven't noticed parameter exit actually doing anything...

    # measure actual temperature
    last_measurement = now
    while True:
        try:
            response = requests.get(temp_get)
        except requests.exceptions.ConnectionError as errc:
            print("Error reading temperature: ", errc)
            if not temp_reboot is None:
                print("Will reboot temp sensor and try again.")
                # posting to this URL should reboot the device. This can easily be done with a shellyplug.
                requests.post(temp_reboot)
                # give device some time to reboot before attempting another connection
                time.sleep(30)
            else:
                raise
        else:
            break
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
        print("temp: {:.1f}/{:.1f}°C".format(temp_actual, pid.setpoint))
        continue

    # we've exceeded pid.sample_time!
    last_update = now

    # determine current target temperature we wish to achieve (this can change over time):
    pid.setpoint = get_setpoint()

    # run actual temp through PID to get the new target setting for heater cable (in percentage of the total sample time, so as PWM)
    heater_pwm = pid(temp_actual)
    p, i, d = pid.components  # individual components that lead to the heater value
    if heater_pwm > 0:
        print("temp: {:.1f}/{:.1f}°C\theater: {:.0f}%\t(p: {:.2f}, i: {:.2f}, d: {:.2f})".format(
            temp_actual, pid.setpoint, heater_pwm*100, p, i, d))

        # activate heater cable for the calculated duration (must be less than sample_time! But we ensured that in pid.output_limits)
        heater_ontime = ceil(heater_pwm * pid.sample_time)
        requests.post(heater_post.format(timer=heater_ontime))
    else:
        print("temp: {:.1f}/{:.1f}°C\theater: off\t(p: {:.2f}, i: {:.2f}, d: {:.2f})".format(
            temp_actual, pid.setpoint, p, i, d))
        # TODO: We could wire up the cooler and actively cool down the enclosure if it's too hot, is that a good idea?
