import math
import statistics as st
import matplotlib.pyplot as plt
from scipy.signal import butter, filtfilt

# ─────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────

gravity_acceleration = 9.806
cutoff = 2.0  # Hz — adjust if needed


# ─────────────────────────────────────────────
# MATH / VECTOR HELPERS
# ─────────────────────────────────────────────

def vect_length(vector):
    """
    Euclidean length of a 2D or 3D vector.
    Input: vector as a list
    """
    return math.sqrt(sum([math.pow(c, 2) for c in vector]))


def orientation(vector):
    """
    Unit vector of a 2D or 3D euclidean vector.
    Input: vector as a list
    """
    vl = vect_length(vector)
    return [c / vl for c in vector]


def Euler(dt, dx):
    """
    Euler's method: First Order Differential Equation Resolution.
    Starts with null vector as initial condition.
    Input:
        dt - non-fixed time steps list
        dx - x derivative in order of t
    """
    xx = [[0.0, 0.0, 0.0]]
    for ii in range(1, len(dt)):
        xx = xx + [[xx[-1][0] + dt[ii] * dx[ii - 1][0],
                    xx[-1][1] + dt[ii] * dx[ii - 1][1],
                    xx[-1][2] + dt[ii] * dx[ii - 1][2]]]
    return xx


def Esc_Prod(list01, list02):
    """
    Scalar product between two 2D or 3D euclidean vectors.
    Input:
        list01 - list of a list
        list02 - list of a list
    """
    return [sum([comp01 * comp02 for comp01, comp02 in zip(vect01, vect02)])
            for vect01, vect02 in zip(list01, list02)]


def RoundFloat(lst):
    """
    Rounds float values in a list to 4 decimal places.
    Input: list of floats or nested lists
    """
    for ii in range(len(lst)):
        if isinstance(lst[ii], float):
            lst[ii] = float(f'{(lst[ii] + 0.0005):.4f}')
        elif isinstance(lst[ii], list):
            lst[ii] = [float(f'{(e + 0.0005):.4f}') for e in lst[ii] if isinstance(e, float)]
    return lst


# ─────────────────────────────────────────────
# SIGNAL PROCESSING
# ─────────────────────────────────────────────

def butter_lowpass_filter(data, cutoff_freq, fs, order=4):
    """
    Applies a Butterworth low-pass filter to a signal.
    Input:
        data        - input signal (list or array)
        cutoff_freq - cutoff frequency in Hz
        fs          - sampling frequency in Hz
        order       - filter order (default: 4)
    """
    nyquist = 0.5 * fs
    normal_cutoff = cutoff_freq / nyquist
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return filtfilt(b, a, data)


# ─────────────────────────────────────────────
# ACCELEROMETER
# ─────────────────────────────────────────────

def prepare_accelerometer_data(exp_data):
    """
    Converts raw accelerometer data: unit conversion, gravity removal, low-pass filter.
    Input:
        exp_data - dict with key 'accelerometer' → list of [timestamp_ms, [ax, ay, az]]
    Returns:
        dict with keys:
            'meter_time'      - raw timestamps in ms
            'experiment_time' - relative timestamps in seconds
            'time_interv'     - time steps in seconds
            'accel_magnitude' - filtered acceleration magnitude per sample (list of floats)
    """
    raw             = exp_data['accelerometer']
    Meter_Time      = [d[0] for d in raw]
    Exp_Acceleration = [d[1] for d in raw]

    Experiment_Time = [(Meter_Time[ii] - Meter_Time[0]) * 1e-3 for ii in range(len(Meter_Time))]
    Time_Interv     = [0.0] + [(Meter_Time[ii] - Meter_Time[ii-1]) * 1e-3 for ii in range(1, len(Meter_Time))]

    Converted_Accel = [[e * gravity_acceleration * 0.001 for e in line] for line in Exp_Acceleration]
    Orient          = [orientation(line) for line in Converted_Accel]
    Corrected_Accel = [
        [l1 - gravity_acceleration * l2 for l1, l2 in zip(comp, grav)]
        for comp, grav in zip(Converted_Accel, Orient)
    ]

    # Find first non-zero interval to avoid ZeroDivisionError
    first_nonzero = next((t for t in Time_Interv if t > 0), None)
    if first_nonzero is None:
        raise ValueError("All time intervals are zero — check the accelerometer data for this sample.")
    fs  = 1 / first_nonzero
    flt = [butter_lowpass_filter([a[i] for a in Corrected_Accel], cutoff, fs) for i in range(3)]
    Corrected_Accel = [[flt[0][i], flt[1][i], flt[2][i]] for i in range(len(flt[0]))]

    accel_magnitude = [vect_length(line) for line in Corrected_Accel]

    return {
        'meter_time':      Meter_Time,
        'experiment_time': Experiment_Time,
        'time_interv':     Time_Interv,
        'accel_magnitude': accel_magnitude,
    }


def detect_peaks(accel_data):
    """
    Detects peaks (repetitions) from the filtered acceleration magnitude.
    Input:
        accel_data - dict returned by prepare_accelerometer_data()
    Returns:
        list of peak indices (Peeks_Loc)
    """
    mag = accel_data['accel_magnitude']
    threshold = st.fmean(mag) + st.stdev(mag) / 3

    return [
        t for t in range(1, len(mag) - 1)
        if ((mag[t] - mag[t-1]) > 0) and
           ((mag[t+1] - mag[t]) < 0) and
           (mag[t] > threshold)
    ]


def compute_step_metrics(accel_data, peaks):
    """
    Computes step/repetition metrics from detected peaks.
    Input:
        accel_data - dict returned by prepare_accelerometer_data()
        peaks      - list of peak indices returned by detect_peaks()
    Returns:
        dict with keys:
            'total_time'     - total experiment duration in seconds
            'num_steps'      - number of detected repetitions
            'mean_step_time' - mean time between repetitions in seconds
            'std_step_time'  - standard deviation of step times
            'study_interval' - [start_ms, end_ms] of the active study window
    """
    Meter_Time      = accel_data['meter_time']
    Experiment_Time = accel_data['experiment_time']
    Peeks_Loc       = list(peaks)

    total_time = (Meter_Time[-1] - Meter_Time[0]) * 1.0e-3
    num_steps  = len(Peeks_Loc)

    try:
        mean_step_time = st.fmean([
            (Meter_Time[Peeks_Loc[ii]] - Meter_Time[Peeks_Loc[ii-1]]) * 1.0e-3
            for ii in range(1, num_steps)
        ])
        std_step_time = st.stdev([
            (Meter_Time[Peeks_Loc[ii]] - Meter_Time[Peeks_Loc[ii-1]]) * 1.0e-3
            for ii in range(1, num_steps)
        ], mean_step_time)

        step = 1; lower_limit = Peeks_Loc[0]
        while ((lower_limit - step) >= 0) and \
              (Experiment_Time[lower_limit] - Experiment_Time[lower_limit - step] < mean_step_time / 2):
            Peeks_Loc = [Peeks_Loc[0] - 1] + Peeks_Loc
            step += 1

        step = 1; higher_limit = Peeks_Loc[-1]
        while ((higher_limit + step) < (len(Experiment_Time) - 1)) and \
              ((Experiment_Time[higher_limit + step] - Experiment_Time[higher_limit]) < mean_step_time / 2):
            Peeks_Loc = Peeks_Loc + [Peeks_Loc[-1] + 1]
            step += 1

        study_interval = [Meter_Time[Peeks_Loc[0]], Meter_Time[Peeks_Loc[-1]]]

    except (st.StatisticsError, IndexError):
        mean_step_time = 0
        std_step_time  = 0
        study_interval = [0, 0]

    return {
        'total_time':     round(total_time,     4),
        'num_steps':      num_steps,
        'mean_step_time': round(mean_step_time, 4),
        'std_step_time':  round(std_step_time,  4),
        'study_interval': study_interval,
    }


# ─────────────────────────────────────────────
# FORCE & POWER
# ─────────────────────────────────────────────

def compute_force_power(accel_data, weight_kg):
    """
    Computes Mean Force (N) and Mean Power (W).

    Mean Force = mass × mean acceleration magnitude  (F = m·a)
    Mean Speed = estimated via numerical integration of acceleration over time
    Mean Power = Mean Force × Mean Speed              (P = F·v)

    Input:
        accel_data - dict returned by prepare_accelerometer_data()
        weight_kg  - subject's mass in kg
    Returns:
        (mean_force, mean_power) — both rounded to 4 decimal places
    """
    mag         = accel_data['accel_magnitude']
    Time_Interv = accel_data['time_interv']

    mean_accel = st.fmean(mag)
    mean_force = weight_kg * mean_accel

    velocity   = 0.0
    velocities = [0.0]
    for ii in range(1, len(mag)):
        dt = Time_Interv[ii]
        velocity += 0.5 * (mag[ii - 1] + mag[ii]) * dt
        velocities.append(abs(velocity))

    mean_speed = st.fmean(velocities)
    mean_power = mean_force * mean_speed

    return round(mean_force, 4), round(mean_power, 4)
