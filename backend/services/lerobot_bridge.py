"""
LeRobot integration bridge.
After a valid voice decision, the backend calls run_lerobot_commands(target).
Demo: logs and prints instructions; manual entry may be required to drive the arm.
Replace or extend with actual LeRobot API/CLI calls when the RL team integrates.
"""


def run_lerobot_commands(target: str) -> None:
    """
    Execute command-prompt / control commands to drive LeRobot for the given target.
    Demo: log and print so operator can run commands manually if needed.
    """
    if not target:
        return
    msg = f"LeRobot: pick target = {target!r}"
    print(f"\n[LEROBOT] {msg}")
    # TODO: RL team can add actual LeRobot API or subprocess calls here.
    # Manual entry: operator may type or confirm commands in terminal / LeRobot UI.
