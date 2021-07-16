import logging
import os
import shutil

from smac.facade.smac_facade import SMAC

from smac.runhistory.runhistory import RunHistory
from smac.scenario.scenario import Scenario
from smac.stats.stats import Stats
from smac.utils.io.traj_logging import TrajLogger

"""
This file runs SMAC and then restores the run with an extended computation
budget. This will also work for SMAC runs that have crashed and are continued.
"""


def main():
    # Initialize scenario, using runcount_limit as budget.
    orig_scen_dict = {
        'algo': 'python3 cmdline_wrapper.py',
        'paramfile': 'param_config_space.pcs',
        'run_obj': 'quality',
        'runcount_limit': 25,
        'deterministic': True,
        'output_dir': 'restore_me'}
    original_scenario = Scenario(orig_scen_dict)
    smac = SMAC(scenario=original_scenario,
                run_id=1)
    smac.optimize()

    print("\n########## BUDGET EXHAUSTED! Restoring optimization: ##########\n")

    # Now the output is in the folder 'restore_me/run_1' (or whatever run_id has
    # been passed to the SMAC-object above)
    old_output_dir = os.path.join(original_scenario.output_dir, 'run_1')
    #
    # We could simply modify the scenario-object, stored in
    # 'smac.solver.scenario' and start optimization again:

    # smac.solver.scenario.ta_run_limit = 50
    # smac.optimize()

    # Or, to show the whole process of recovering a SMAC-run from the output
    # directory, create a new scenario with an extended budget:
    new_scenario = Scenario(orig_scen_dict,
                            cmd_options={'runcount_limit': 50,  # overwrite these args
                                         'output_dir': 'restored'})

    # We load the runhistory, ...
    rh_path = os.path.join(old_output_dir, "runhistory.json")
    runhistory = RunHistory(aggregate_func=None)
    runhistory.load_json(rh_path, new_scenario.cs)
    # ... stats, ...
    stats_path = os.path.join(old_output_dir, "stats.json")
    stats = Stats(new_scenario)
    stats.load(stats_path)
    # ... and trajectory.
    traj_path = os.path.join(old_output_dir, "traj_aclib2.json")
    trajectory = TrajLogger.read_traj_aclib_format(
        fn=traj_path, cs=new_scenario.cs)
    incumbent = trajectory[-1]["incumbent"]

    # Now we can initialize SMAC with the recovered objects and restore the
    # state where we left off. By providing stats and a restore_incumbent, SMAC
    # automatically detects the intention of restoring a state.
    smac = SMAC(scenario=new_scenario,
                runhistory=runhistory,
                stats=stats,
                restore_incumbent=incumbent,
                run_id=1)
    # Because we changed the output_dir, we might want to copy the old
    # trajectory-file (runhistory and stats will be complete, but trajectory is
    # written sequentially)
    new_traj_path = os.path.join(new_scenario.output_dir, "run_1", "traj_aclib2.json")
    shutil.copy(traj_path, new_traj_path)

    smac.optimize()


if "__main__" == __name__:
    logging.basicConfig(level="INFO")
    main()
