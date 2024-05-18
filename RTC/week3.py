import pyswmm as ps
import swmm_api as sa
import datetime as dt

file_loc = r"RTC/data/Dean Town_testing.inp"

with ps.Simulation(file_loc) as sim:
    links = ps.Links(sim)
    nodes = ps.Nodes(sim)

    sim.step_advance = 300
    sim.report_start = dt.datetime(year=2020, month=6, day=1)
    sim.start_time = dt.datetime(year=2020, month=6, day=1)
    sim.end_time = dt.datetime(year=2020, month=7, day=1)
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
        print(sim.current_time)

read_file = sa.read_out_file(r"RTC\data\Dean Town_testing.out")
output = read_file.to_frame()
som = 0
for name in ["cso_1", "cso_20", "cso_2a", "cso_21a", "cso_10", "cso_21b", "cso_2b"]:
    som += output["node"][name]["total_inflow"].sum()
    print(output["node"][name]["total_inflow"].sum())
print(som)
