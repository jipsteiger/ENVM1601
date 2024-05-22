import pyswmm as ps
import swmm_api as sa
import datetime as dt
import pandas as pd
import RTC.heuristic_rules as rule

def main():
    csos = {
        "cso_1": 0,
        "cso_20": 0,
        "cso_2a": 0,
        "cso_21a": 0,
        "cso_10": 0,
        "cso_21b": 0,
        "cso_2b": 0,
    }
    
    parameters = [[6, 11, 6, 16, "Major event june"],
                  [12, 10, 12, 20, "Minor event december"],
                  [9, 22, 9, 30, "Multiple average events september"],
                  [2, 8, 2, 12, "3 major events february"],
                  [2, 20, 2, 22, "Peak intensity event february"]]
    # parameters = [[6, 1, 7, 1, 'SWMM JUNE TEST']] #Test params
    som = 0
    for params in parameters:
        simulate(*params)
        som, csos = process_output(params[-1], csos, som)
        print('-----------------------------')
    
    print(f"Objective function end result: {som}")
    print(f"Objecttive function contribition per CSO:")
    display(pd.DataFrame(csos, index=["CSO spill"])) # type: ignore


def simulate(start_month, start_day, end_month, end_day, name):
    with ps.Simulation(
        r"RTC/data/Dean Town_pyswmm.inp",
    ) as sim:
        links = ps.Links(sim)
        nodes = ps.Nodes(sim)

        sim.step_advance = 300
        sim.report_start = dt.datetime(year=2020, month=start_month, day=start_day)
        sim.start_time = dt.datetime(year=2020, month=start_month, day=start_day)
        sim.end_time = dt.datetime(year=2020, month=end_month, day=end_day)
        
        for step in sim:
            links = assign_target(*rule.p10_1(nodes), links)
            links = assign_target(*rule.p_21_2(nodes), links)
            links = assign_target(*rule.WWTP_inlet(nodes), links)
            links = assign_target(*rule.CSO_Pump_21(nodes), links)
            links = assign_target(*rule.p_2_1(nodes), links)
            links = assign_target(*rule.CSO_Pump_2(nodes), links)

def assign_target(id, target, links):
    if target is not None:
        links[id].target_setting = target
    return links  
            
def process_output(name, csos, som):
    rpt = sa.read_rpt_file(r"RTC\data\Dean Town_pyswmm.rpt")
    output = rpt.outfall_loading_summary
    output = output.drop(["Wastewater_Treatment_Plant"], axis=0)
    flooding = rpt.flow_routing_continuity  
    initial_sum = som

    print(name)
    print(f"Total CSO overflow in this event: {output['Total_Volume_10^6 ltr'].sum()}")
    summer = [2, 2, 2, 2, 2, 1 / 500, 1 / 500]
    winter = [1, 1, 1, 1, 2, 1 / 500, 1 / 500]
    
    for i, cso in enumerate(
        ["cso_1", "cso_20", "cso_2a", "cso_21a", "cso_10", "cso_21b", "cso_2b"]
    ):
        if name == "Major event june":
            som += (
                output.loc[cso, "Total_Volume_10^6 ltr"] * summer[i]
            )  # For goss river recrreation
            csos[cso] += output.loc[cso, "Total_Volume_10^6 ltr"] * summer[i]
        else:
            som += output.loc[cso, "Total_Volume_10^6 ltr"] * winter[i]  # No recreation
            csos[cso] += output.loc[cso, "Total_Volume_10^6 ltr"] * winter[i]
        print(f'{cso} spilled: {output.loc[cso, "Total_Volume_10^6 ltr"]:.3f}')
    som += flooding["Flooding Loss"]["Volume_10^6 ltr"] * 10000  # Flooding addition
    print(f"Flooding loss is: {flooding['Flooding Loss']['Volume_10^6 ltr']:.3f}")
    print(f"Event objective function contribution: {som - initial_sum} ")  
    
    return som, csos 

if __name__ == '__main__':
    main()