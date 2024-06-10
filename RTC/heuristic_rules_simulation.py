import pyswmm as ps
import swmm_api as sa
import datetime as dt
import pandas as pd
import RTC.heuristic_rules as rule
from typing import List
import datetime as dt
 

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

    parameters = [
        [6, 11, 6, 16, "Major event june"],
        [12, 10, 12, 20, "Minor event december"],
        [9, 22, 9, 30, "Multiple average events september"],
        [2, 8, 2, 12, "3 major events february"],
        [2, 20, 2, 22, "Peak intensity event february"],
    ]
    # parameters = [[6, 1, 7, 1, 'SWMM JUNE TEST']] #Test params
    # parameters = [[1, 1, 12, 31, 'Full year sim']]
    som, cso_sum, simulation = 0, 0, 1
    for params in parameters:
        simulate(*params, simulation)
        som, csos, cso_sum = process_output(params[-1], csos, som, cso_sum, simulation)
        simulation += 1
        print("-----------------------------")

    print(f"Objective function end result: {som}")
    print(f"Objecttive function contribition per CSO:")

    now = dt.datetime.now()
    cso_result = pd.DataFrame(csos, index=[now.strftime("%d/%m %H:%M")])
    sum_result = pd.DataFrame(
        {"obj_fun_sum": som, "spill_sum": cso_sum}, index=[now.strftime("%d/%m %H:%M")]
    )
    sim_result = pd.concat([cso_result, sum_result], axis=1)

    display(sim_result)  # type: ignore
    if parameters[-1][-1] == "Full year sim":
        results = pd.read_csv("RTC/results/full_sim_result.csv", index_col=0)
        updated_results = pd.concat([results, sim_result])
        updated_results.to_csv("RTC/results/full_sim_result.csv")
    else:
        results = pd.read_csv("RTC/results/sim_result.csv", index_col=0)
        updated_results = pd.concat([results, sim_result])
        updated_results.to_csv("RTC/results/sim_result.csv")


def simulate(
    start_month: int,
    start_day: int,
    end_month: int,
    end_day: int,
    name: str = "",
    simulation: int = 1,
):
    """Runs the pyswmm simulation, between start month and day until end month and day.
    For each simulation step pump target is re-set to desired value.

    Args:
        start_month (int)
        start_day (int)
        end_month (int)
        end_day (int)
        name (str, optional): Not used Defaults to ''.
        simulation (int, optional): keeps track of different simulated events
    """
    with ps.Simulation(
        rf"RTC\event_optimisation_input_data\Dean Town_pyswmm_{simulation}.inp",
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
            links = assign_target(*rule.p_20_2(nodes), links)


def assign_target(id: str, target: float, links):
    """Updates the specific pump target value, based on the pumps name (id),
    and the target value it has to be. If target is None this means no new rule
    has to be implemented, otherwise links is updated.

    Args:
        id (str): corresponding pump name
        target (float): pump target setting
        links (_type_): py swmm object

    Returns:
        _type_:
    """
    if target is not None:
        links[id].target_setting = target
    return links


def process_output(
    name: str, csos: dict, som: float, cso_sum: float, simulation: int = 1
):
    """Reads the report file from the ran simulation. Calculates the objective function,
    updates total cso spillage, and prints relevant information.

    Args:
        name (str): Name of the event
        csos (dict): Spillage information per cso
        som (float): Sum of the objective function value
        cso_sum (float): Sum of spillage
        simulation (int, optional): keeps track of different simulated events

    Returns:
        List[float, dict]: Updated sum of objective function and update spillage per cso.
    """

    rpt = sa.read_rpt_file(
        rf"RTC\event_optimisation_input_data\Dean Town_pyswmm_{simulation}.rpt"
    )
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
        cso_sum += output.loc[cso, "Total_Volume_10^6 ltr"]
    som += flooding["Flooding Loss"]["Volume_10^6 ltr"] * 10000  # Flooding addition
    print(f"Flooding loss is: {flooding['Flooding Loss']['Volume_10^6 ltr']:.3f}")
    print(f"Event objective function contribution: {som - initial_sum} ")

    return som, csos, cso_sum


if __name__ == "__main__":
    main()
