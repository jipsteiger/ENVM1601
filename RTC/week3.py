import pyswmm as ps
import swmm_api as sa
import datetime as dt

file_loc = r"RTC/data/Dean Town_testing.inp"

def heuristic_sim(start_month, start_day, end_month, end_day, name):
    with ps.Simulation(file_loc) as sim:
        links = ps.Links(sim)
        nodes = ps.Nodes(sim)

        sim.step_advance = 300
        sim.report_start = dt.datetime(year=2020, month=start_month, day=start_day)
        sim.start_time = dt.datetime(year=2020, month=start_month, day=start_day)
        sim.end_time = dt.datetime(year=2020, month=end_month, day=end_day)
        for step in sim:
            if nodes["j_1"].depth >= 0.25:
                links["WWTP_inlet"].target_setting = 1
            if nodes["j_1"].depth <= 0.10:
                links["WWTP_inlet"].target_setting = 0
            if nodes["j_21"].depth >= 0.25:
                links["p_21_2"].target_setting = 1
            if nodes["j_21"].depth <= 0.10:
                links["p_21_2"].target_setting = 0
            if nodes["j_21"].depth >= 1.10:
                links["CSO_Pump_21"].target_setting = 1
            if nodes["j_21"].depth <= 0.9:
                links["CSO_Pump_21"].target_setting = 0
            if nodes["j_10"].depth >= 0.25:
                links["p10_1"].target_setting = 1
            if nodes["j_10"].depth <= 0.10:
                links["p10_1"].target_setting = 0
            if nodes["j_2"].depth >= 0.25:
                links["p_2_1"].target_setting = 1
            if nodes["j_2"].depth <= 0.10:
                links["p_2_1"].target_setting = 0
            if nodes["j_2"].depth >= 2.5:
                links["CSO_Pump_2"].target_setting = 1
            if nodes["j_2"].depth <= 2.0:
                links["CSO_Pump_2"].target_setting = 0

    read_file = sa.read_out_file(r"RTC\data\Dean Town_testing.out")
    output = read_file.to_frame()
    som = 0
    print(name)
    summer = [2, 2, 2, 2, 2, 1/500, 1/500]
    winter = [1, 1, 1, 1, 2, 1/500, 1/500]
    for i, cso in enumerate(["cso_1", "cso_20", "cso_2a", "cso_21a", "cso_10", "cso_21b", "cso_2b"]):
        if name == 'big rain event':
            som += output["node"][cso]["total_inflow"].sum() * summer[i] #For goss river recrreation
        else:
            som += output["node"][cso]["total_inflow"].sum() * winter[i] #No recreation
        print(f'{cso}: {output["node"][cso]["total_inflow"].sum():.3f}')
    som += output.system['']['flooding'].sum() * 100 #Flooding addition
    print(f"flooding is {output.system['']['flooding'].sum():.3f}")
    print(som)
    return som

rain1 = heuristic_sim(6, 11, 6, 16, 'big rain event') #Big rain event SUMMER MONTH
rain2 = heuristic_sim(12, 10, 12, 20, 'Little rain event') #Little rain event
rain3 = heuristic_sim(9, 22, 9, 30, 'Multiple rain alot of rain') #Multiple rain alot of rain
rain4 = heuristic_sim(2, 8, 2, 12, 'Much rain in 3 days') #Much rain in 3 days
rain5 = heuristic_sim(2, 20, 2, 22, 'Peak rain intensity') #Peak rain intensity
sum_rain = rain1 + rain2 + rain3 + rain4 + rain5
print(f'Reluting Objective function value is {sum_rain}')


