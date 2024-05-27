import pyswmm as ps
import swmm_api as sa
import datetime as dt
import pandas as pd
import os

file_loc = r"RTC/data/Dean Town_pyswmm.inp"


def heuristic_sim(start_month, start_day, end_month, end_day, name):
    with ps.Simulation(
        file_loc,
    ) as sim:
        links = ps.Links(sim)
        nodes = ps.Nodes(sim)

        sim.step_advance = 300
        sim.report_start = dt.datetime(year=2020, month=start_month, day=start_day)
        sim.start_time = dt.datetime(year=2020, month=start_month, day=start_day)
        sim.end_time = dt.datetime(year=2020, month=end_month, day=end_day)
        # p_20_2  p_21_2   p10_1   p_2_1
        for step in sim:
            # if (nodes["j_10"].depth <= 0.20) & (nodes["j_1"].depth >= 0.20):
            #     links["p10_1"].target_setting = 1
            if nodes["j_10"].depth >= 0.25:
                links["p10_1"].target_setting = 1
            if nodes["j_10"].depth <= 0.10:
                links["p10_1"].target_setting = 0

            # if (nodes["j_2"].depth >= 0.20) & (nodes["j_21"].depth <= 0.15):
            #     links["p_21_2"].target_setting = 0
            if nodes["j_21"].depth >= 0.25:
                links["p_21_2"].target_setting = 1
            if nodes["j_21"].depth <= 0.10:
                links["p_21_2"].target_setting = 0

            if nodes["j_1"].depth >= 0.25:
                links["WWTP_inlet"].target_setting = 1
            if nodes["j_1"].depth <= 0.10:
                links["WWTP_inlet"].target_setting = 0

            if nodes["j_21"].depth >= 1.10:
                links["CSO_Pump_21"].target_setting = 1
            if nodes["j_21"].depth <= 0.9:
                links["CSO_Pump_21"].target_setting = 0

            if nodes["j_2"].depth >= 0.25:
                links["p_2_1"].target_setting = 1
            if nodes["j_2"].depth <= 0.10:
                links["p_2_1"].target_setting = 0

            if nodes["j_2"].depth >= 2.5:
                links["CSO_Pump_2"].target_setting = 1
            if nodes["j_2"].depth <= 2.0:
                links["CSO_Pump_2"].target_setting = 0

    rpt = sa.read_rpt_file(r"RTC\data\Dean Town_pyswmm.rpt")
    output = rpt.outfall_loading_summary
    output = output.drop(["Wastewater_Treatment_Plant"], axis=0)
    flooding = rpt.flow_routing_continuity

    som = 0
    print(name)
    print(f"CSO OVER FLOW: {output['Total_Volume_10^6 ltr'].sum()}")
    summer = [2, 2, 2, 2, 2, 1 / 500, 1 / 500]
    winter = [1, 1, 1, 1, 2, 1 / 500, 1 / 500]
    for i, cso in enumerate(
        ["cso_1", "cso_20", "cso_2a", "cso_21a", "cso_10", "cso_21b", "cso_2b"]
    ):
        if name == "big rain event":
            som += (
                output.loc[cso, "Total_Volume_10^6 ltr"] * summer[i]
            )  # For goss river recrreation
            csos[cso] += output.loc[cso, "Total_Volume_10^6 ltr"] * summer[i]
        else:
            som += output.loc[cso, "Total_Volume_10^6 ltr"] * winter[i]  # No recreation
            csos[cso] += output.loc[cso, "Total_Volume_10^6 ltr"] * winter[i]
        print(f'{cso}: {output.loc[cso, "Total_Volume_10^6 ltr"]:.3f}')
    som += flooding["Flooding Loss"]["Volume_10^6 ltr"] * 10000  # Flooding addition
    print(f"flooding is {flooding['Flooding Loss']['Volume_10^6 ltr']:.3f}")
    print(f"Objective function contribution: {som} ")
    return som


csos = {
    "cso_1": 0,
    "cso_20": 0,
    "cso_2a": 0,
    "cso_21a": 0,
    "cso_10": 0,
    "cso_21b": 0,
    "cso_2b": 0,
}

rain1 = heuristic_sim(1, 1, 12, 31, "big rain event")  # Big rain event SUMMER MONTH
# rain2 = heuristic_sim(12, 10, 12, 20, "Little rain event")  # Little rain event
# rain3 = heuristic_sim(
#     9, 22, 9, 30, "Multiple rain alot of rain"
# )  # Multiple rain alot of rain
# rain4 = heuristic_sim(2, 8, 2, 12, "Much rain in 3 days")  # Much rain in 3 days
# rain5 = heuristic_sim(2, 20, 2, 22, "Peak rain intensity")  # Peak rain intensity
sum_rain = rain1
print(f"Resuting Objective function value is {sum_rain}")
print(f"Contribution per CSO:")
pd.DataFrame(csos, index=["CSO spill"])
