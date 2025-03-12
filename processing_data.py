import math
import statistics as st
import matplotlib.pyplot as plt
import matplotlib as mpl

mpl.rcParams.update(mpl.rcParamsDefault)

plt.rcParams['text.usetex'] = True

gravity_acceleration = 9.806


def vect_length(vector):
    """
        Length of an euclidean vector of 2 and 3 dimensions
        Input:
            vector is an list
    """

    return math.sqrt(sum([math.pow(component, 2) for component in vector]))


def orientation(vector):
    """
        Unit vector of an euclidean vector of 2 and 3 dimensions
        Input:
            vector is an list
    """

    vector_len = vect_length(vector)

    return [component / vector_len for component in vector]


def Euler(dt, dx):
    """
        Euler's method:
            Fisrt Order Differentional Equation Resolution
            Stating nul vector as initial condition
        Input:
            dt - non-fix time steps list
            dx - x derivative in order of t
    """

    xx = [[0.0, 0.0, 0.0]]

    for ii in range(1, len(dt)):
        xx = xx + [[xx[-1][0] + dt[ii] * dx[ii - 1][0], \
                    xx[-1][1] + dt[ii] * dx[ii - 1][1], \
                    xx[-1][2] + dt[ii] * dx[ii - 1][2]]]

    return xx


def Esc_Prod(list01, list02):
    """
        Escalar Product between two euclidean vectors of 2 and 3 dimensions
        Input:
            list01 is an list of a list
            list02 is an list of a list
    """

    return [sum([comp01 * comp02 for comp01, comp02 in zip(vect01, vect02)]) for vect01, vect02 in zip(list01, list02)]


def RoundFloat(List):
    for ii in range(len(List)):
        if isinstance(List[ii], float):
            List[ii] = float(f'{(List[ii] + 0.0005):.4f}')
        elif isinstance(List[ii], list):
            list01 = [float(f'{(element + 0.0005):.4f}') for element in List[ii] if isinstance(List[ii], float)]
            if len(list01) > 0:
                List[ii] = list01

    return List


def accelerometer(exp_data):
    ### Acelerometer

    Acelerometer_data = exp_data['accelerometer']

    Meter_Time = [data[0] for data in Acelerometer_data]
    Exp_Acceleration = [data[1] for data in Acelerometer_data]

    # Time variables
    Experiment_Tt_Time = (Meter_Time[-1] - Meter_Time[0]) * 1.0e-3
    Experiment_Time = [(Meter_Time[ii] - Meter_Time[0]) * 1e-3 for ii in range(len(Meter_Time))]
    Time_Interv = [0.0] + [(Meter_Time[ii] - Meter_Time[ii - 1]) * 1e-3 for ii in range(1, len(Meter_Time))]

    # Correction of the acceleration: Remove the accelaration of gravity

    Orient_ot_acceleration = [orientation(line) for line in Exp_Acceleration]

    Corrected_Accel = []
    for component, grav_comp in zip(Exp_Acceleration, Orient_ot_acceleration):
        Corrected_Accel = Corrected_Accel + [
            [line1 - gravity_acceleration * line2 for line1, line2 in zip(component, grav_comp)]]

    # Velocity
    Velocity = Euler(Time_Interv, Corrected_Accel)

    # Position
    Position = Euler(Time_Interv, Velocity)

    # Filter the first ten seconds
    Experiment_Tt_Time = (Meter_Time[-1] - Meter_Time[0]) * 1.0e-3
    if Experiment_Tt_Time > 10.0:
        Meter_Time = [Instant for Instant in Meter_Time if ((Instant - Meter_Time[0]) * 1.0e-3) > 10.0]
        First_Ten_Sec = len(Exp_Acceleration) - len(Meter_Time)
        Experiment_Time[:First_Ten_Sec] = []
        Corrected_Accel[:First_Ten_Sec] = []
        Velocity[:First_Ten_Sec] = []
        Position[:First_Ten_Sec] = []

    Corrected_Accel_Int = [vect_length(line) for line in Corrected_Accel]

    Peeks_Loc = [Time_ind for Time_ind in range(1, len(Corrected_Accel_Int) - 1) \
                 if (((Corrected_Accel_Int[Time_ind] - Corrected_Accel_Int[Time_ind - 1]) > 0) & \
                     ((Corrected_Accel_Int[Time_ind + 1] - Corrected_Accel_Int[Time_ind]) < 0) & \
                     (Corrected_Accel_Int[Time_ind] > (st.fmean([component for component in Corrected_Accel_Int]) + \
                                                       st.stdev(
                                                           [component for component in Corrected_Accel_Int]) / 3)))]

    Num_Steps = len(Peeks_Loc)
    # Plot data
    fig, axs = plt.subplots(2, 1, figsize=(16, 16), gridspec_kw={'height_ratios': [1, 1]})
    axs[0].plot(Experiment_Time, Corrected_Accel_Int)
    axs[0].scatter([Experiment_Time[j] for j in Peeks_Loc], [Corrected_Accel_Int[j] for j in Peeks_Loc])

    # try:
    #     Mean_Step_Time = st.fmean([((Meter_Time[Peeks_Loc[ii]] - Meter_Time[Peeks_Loc[ii-1]])*1.0e-3) for ii in range(1, Num_Steps)])
    #     #STD_Step_Time = st.stdev([((Meter_Time[Peeks_Loc[ii]] - Meter_Time[Peeks_Loc[ii-1]])*1.0e-3) for ii in range(1, Num_Steps)], Mean_Step_Time)
    #     step = 1; lower_limit = Peeks_Loc[0]
    #     while ((lower_limit - step) >= 0) & (Experiment_Time[lower_limit] - Experiment_Time[lower_limit - step] < Mean_Step_Time/2):
    #         Peeks_Loc = [Peeks_Loc[0] - 1] + Peeks_Loc
    #         step = step +1
    #     step = 1; higher_limit = Peeks_Loc[-1]
    #     while ((higher_limit + step) < (len(Experiment_Time) - 1)) & ((Experiment_Time[higher_limit + step] - Experiment_Time[higher_limit]) < Mean_Step_Time/2):
    #         Peeks_Loc = Peeks_Loc + [Peeks_Loc[-1] + 1]
    #         step = step +1
    #     #Study_Interval = [Meter_Time[Peeks_Loc[0]], Meter_Time[Peeks_Loc[-1]]]
    # except st.StatisticsError:
    #     return [Experiment_Tt_Time, Num_Steps, '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', '#N/A', ['#N/A', '#N/A']]

    axs[0].scatter([Experiment_Time[j] for j in [Peeks_Loc[0], Peeks_Loc[-1]]],
                   [Corrected_Accel_Int[j] for j in [Peeks_Loc[0], Peeks_Loc[-1]]], color='red')

    # Acceleration = [vect_length(line) for line in Corrected_Accel]
    Speed = [vect_length(line) for line in Velocity[Peeks_Loc[0]:Peeks_Loc[-1] + 1]]

    axs[1].plot(Experiment_Time[Peeks_Loc[0]:Peeks_Loc[-1] + 1], Speed)

    plt.show()

    # fig, axs = plt.subplots(3,1,figsize=(16,24), gridspec_kw={'height_ratios': [1, 1, 1]})

    # axs[0].plot(Experiment_Time, [value[0] for value in Corrected_Accel], color="b")
    # axs[0].scatter([Experiment_Time[j] for j in Peeks_Loc], [Corrected_Accel[j][0] for j in Peeks_Loc], color="b")
    # axs[0].set_xlabel('t / s', fontsize="18")
    # axs[0].set_ylabel('$a_{x} / \\textrm{ms}^{-1}$', fontsize="18")
    # axs[0].set_title('Acceleration in xx direction', size='24', color='k')
    # axs[1].plot(Experiment_Time, [value[1] for value in Corrected_Accel], color="r")
    # axs[1].scatter([Experiment_Time[j] for j in Peeks_Loc], [Corrected_Accel[j][1] for j in Peeks_Loc], color="r")
    # axs[1].set_title('Acceleration in yy direction', size='24', color='k')
    # axs[1].set_xlabel('t / s', size="18")
    # axs[1].set_ylabel('$a_{y} / \\textrm{ms}^{-1}$', fontsize="18")
    # axs[2].plot(Experiment_Time, [value[2] for value in Corrected_Accel], color="g")
    # axs[2].scatter([Experiment_Time[j] for j in Peeks_Loc], [Corrected_Accel[j][2] for j in Peeks_Loc], color="g")
    # axs[2].set_title('Acceleration in zz direction', size='24', color='k')
    # axs[2].set_xlabel('t / s', size="18")
    # axs[2].set_ylabel('$a_{z} / \\textrm{ms}^{-1}$', fontsize="18")

    # plt.savefig('AccelComp.png')

    # plt.show()

    return 0
