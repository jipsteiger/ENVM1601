import RTC.ENVM1601_CentralBasinApproach as CBA
import swmm_api


storages = [
    ["j_1", 1.83],  # Crest height from .inp file
    ["j_21", 2.16],
    ["j_10", 2.21],
    ["j_2", 2.48],
    ["j_20", 1.90],
]
c = CBA.Central_Basin_Approach("RTC/CBA_folder/")
model = c.create_CBA_model(storages)

read_file = swmm_api.read_out_file("RTC/data/Dean Town.out")
output = read_file.to_frame()
runoff = output["system"][""]["runoff"]
dwf = output["system"][""]["dry_weather_inflow"]

inflow = runoff + dwf
timestep = (runoff.index[2] - runoff.index[1]).seconds

wwtp_capacity = 1.167  # m3/s

total_cso_volume, storage_filled, cso_tracked = c.run_CBA_model(
    wwtp_capacity, inflow, timestep
)
