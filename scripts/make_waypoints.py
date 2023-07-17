"""
Creates runner-specific "waypoint" configurations. Waypoints are named circular regions which
will wake devices on entrance and exit. On iOS, there's a limit of 20 regions per app so we'll give the subset
relevant to each runner.
"""
import json
from copy import deepcopy
# Provide your own waypoints. We pulled these out of the Ragnar NWP course map data.
waypoints = json.load(open("../waypoints.json"))

# This the ragnar leg configuration. Adjust for what you need.
runners = list(range(1,13))
runner_legs = [[1, 13, 25], [2, 14, 26], [3, 15, 27], [4, 16, 28], [5, 17, 29], [6, 18, 30], [7, 19, 31], [8, 20, 32], [9, 21, 33], [10, 22, 34], [11, 23, 35], [12, 24, 36]]

for runner in runners:
    runner_waypoints = []
    runners_legs = runner_legs[runner - 1]
    for waypoint in waypoints:
        if waypoint["desc"].startswith("Exchange"):
            exchange_number = int(waypoint["desc"].split(" ")[1])
            if exchange_number in runners_legs:
                # It's an end exchange
                end_mon_waypoint = deepcopy(waypoint)
                # The iOS client lets you auto switch modes on region transitions.
                # This suffix takes the client from mode 1 (move) on entrance to 2 (significant) on exit
                end_mon_waypoint["desc"] += "|2|1"
                runner_waypoints.append(end_mon_waypoint)
                continue
            elif exchange_number in map(lambda x: x - 1, runners_legs):
                # It's a start exchange
                start_mon_waypoint = deepcopy(waypoint)
                # This suffix takes the client from mode 2 (significant) on entrance to 1 (move) on exit
                start_mon_waypoint["desc"] += "|1|2"
                runner_waypoints.append(start_mon_waypoint)
                continue
            else:
                # There's a limit on number of regions we can monitor so ignore
                # other runner's exchanges
                continue
        # Pass through
        runner_waypoints.append(waypoint)
    # Save waypoints
    json.dump(runner_waypoints, open(f"../client_configs/runner{runner}_waypoints.json", "w"))
