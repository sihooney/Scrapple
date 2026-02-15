"""
Arm/LeRobot Endpoints
======================
GET  /api/arm/next          — Returns the last valid pick target
POST /api/lerobot/start     — Start a LeRobot recording session
POST /api/lerobot/stop      — Stop the current LeRobot session
POST /api/lerobot/enter     — Send Enter key to LeRobot process
POST /api/lerobot/run       — Trigger LeRobot (pauses video, writes trigger)
POST /api/lerobot/kill      — Kill the LeRobot process and resume video
GET  /api/lerobot/status    — Get LeRobot session status
POST /api/video/pause       — Pause video feed (release camera)
POST /api/video/resume      — Resume video feed
"""

import subprocess
from flask import jsonify, request
from services.lerobot_bridge import (
    lerobot_bridge,
    start_lerobot_session,
    stop_lerobot_session,
    send_enter_to_lerobot,
    is_lerobot_running,
)
from services.cv_video_service import cv_video_service
from config import Config


def register_arm_routes(app, global_state):
    """Register arm/LeRobot interaction routes."""

    @app.route('/api/arm/next', methods=['GET'])
    def arm_next():
        """
        Return the next pick target for the arm/RL pipeline.
        When last_decision is valid, returns { "target": "<name>" }; otherwise { "target": null }.
        """
        decision = global_state.get("last_decision") or {}
        if decision.get("valid") and decision.get("target"):
            return jsonify({"target": decision["target"]})
        return jsonify({"target": None})

    @app.route('/api/lerobot/start', methods=['POST'])
    def lerobot_start():
        """
        Start a LeRobot recording session.
        
        Request body (all optional, defaults from config):
        {
            "task": "Grab the Nut",
            "episode_time_s": 3600,
            "repo_id": "jakkii/eval_scrapple",
            "policy_path": "outputs/train/scrapple_model_4"
        }
        
        Response:
        {
            "success": true,
            "message": "LeRobot session started",
            "running": true
        }
        """
        data = request.json or {}
        
        task = data.get('task', Config.LEROBOT_DEFAULT_TASK)
        episode_time_s = data.get('episode_time_s', Config.LEROBOT_EPISODE_TIME_S)
        repo_id = data.get('repo_id', Config.LEROBOT_REPO_ID)
        policy_path = data.get('policy_path', Config.LEROBOT_POLICY_PATH)
        
        success = start_lerobot_session(
            task_description=task,
            episode_time_s=episode_time_s,
            repo_id=repo_id,
            policy_path=policy_path,
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "LeRobot session started",
                "running": True,
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to start LeRobot session",
                "running": is_lerobot_running(),
            }), 500

    @app.route('/api/lerobot/stop', methods=['POST'])
    def lerobot_stop():
        """
        Stop the current LeRobot recording session.
        
        Response:
        {
            "success": true,
            "message": "LeRobot session stopped",
            "running": false
        }
        """
        success = stop_lerobot_session()
        
        return jsonify({
            "success": success,
            "message": "LeRobot session stopped" if success else "No session to stop",
            "running": False,
        })

    @app.route('/api/lerobot/enter', methods=['POST'])
    def lerobot_enter():
        """
        Send Enter key to the LeRobot process.
        
        This is used to:
        - Start recording an episode
        - Confirm prompts in the LeRobot terminal
        
        Response:
        {
            "success": true,
            "message": "Enter key sent"
        }
        """
        success = send_enter_to_lerobot()
        
        if success:
            return jsonify({
                "success": True,
                "message": "Enter key sent to LeRobot",
            })
        else:
            return jsonify({
                "success": False,
                "message": "No active LeRobot session or failed to send Enter",
                "running": is_lerobot_running(),
            }), 400

    @app.route('/api/lerobot/status', methods=['GET'])
    def lerobot_status():
        """
        Get the current LeRobot session status.
        
        Response:
        {
            "running": true,
            "last_target": "skull"
        }
        """
        return jsonify({
            "running": is_lerobot_running(),
            "last_target": lerobot_bridge.get_last_target(),
        })

    @app.route('/api/lerobot/run', methods=['POST'])
    def lerobot_run():
        """
        Trigger LeRobot by pausing video and writing a trigger file.
        
        1. Pauses the CV video service (releases camera)
        2. Writes trigger file for run_scrapple.py
        """
        import os
        import time
        
        # Always use "nut" as the target (hardcoded for demo)
        target = "nut"
        
        # PAUSE VIDEO FIRST - release camera for LeRobot
        cv_video_service.pause()
        time.sleep(0.5)  # Give camera time to release
        
        # Build the lerobot command
        lerobot_cmd = (
            f'python -m lerobot.record '
            f'--robot.type={Config.LEROBOT_ROBOT_TYPE} '
            f'--robot.port={Config.LEROBOT_ROBOT_PORT} '
            f'--robot.id={Config.LEROBOT_ROBOT_ID} '
            f'--robot.cameras="{Config.LEROBOT_CAMERAS_CONFIG}" '
            f'--display_data=true '
            f'--dataset.repo_id={Config.LEROBOT_REPO_ID} '
            f'--dataset.episode_time_s={Config.LEROBOT_EPISODE_TIME_S} '
            f'--dataset.single_task="Grab the {target.title()}" '
            f'--policy.path={Config.LEROBOT_POLICY_PATH}'
        )
        
        # Write trigger file for run_scrapple.py to pick up
        trigger_file = os.path.join(os.path.dirname(__file__), '..', 'lerobot_trigger.txt')
        
        try:
            with open(trigger_file, 'w') as f:
                f.write(f"TARGET={target}\n")
                f.write(f"TIMESTAMP={time.time()}\n")
                f.write(f"COMMAND={lerobot_cmd}\n")
            
            print(f"\n{'='*60}")
            print(f"[LEROBOT] 🤖 TRIGGER WRITTEN!")
            print(f"[LEROBOT] Target: {target}")
            print(f"[LEROBOT] Video: PAUSED (camera released)")
            print(f"{'='*60}")
            print(f"[LEROBOT] Command: {lerobot_cmd}")
            print(f"{'='*60}\n")
            
            # Mark as running
            lerobot_bridge._running = True
            lerobot_bridge._last_target = target
            
            return jsonify({
                "success": True,
                "target": target,
                "video_paused": True,
                "message": f"LeRobot triggered for: {target}",
            })
            
        except Exception as e:
            print(f"[LEROBOT] Failed to write trigger: {e}")
            # Resume video on error
            cv_video_service.resume()
            return jsonify({
                "success": False,
                "error": str(e),
                "message": f"Failed to trigger LeRobot: {e}",
            }), 500

    @app.route('/api/lerobot/kill', methods=['POST'])
    def lerobot_kill():
        """
        Kill LeRobot processes, reset state, and RESUME video.
        """
        killed_count = 0
        
        try:
            # First, kill the stored process if it exists
            if hasattr(lerobot_bridge, '_process') and lerobot_bridge._process:
                try:
                    lerobot_bridge._process.terminate()
                    lerobot_bridge._process.kill()
                    killed_count += 1
                    print(f"[LEROBOT] Killed stored process")
                except:
                    pass
                lerobot_bridge._process = None
            
            # Reset bridge state
            lerobot_bridge._running = False
            lerobot_bridge._last_target = None
            
            # Try to kill any lerobot processes
            try:
                subprocess.run(
                    ['taskkill', '/F', '/IM', 'python.exe', '/FI', 'WINDOWTITLE eq *lerobot*'],
                    capture_output=True,
                    timeout=5
                )
            except:
                pass
            
            # RESUME VIDEO - restart camera
            cv_video_service.resume()
            
            print(f"[LEROBOT] ■ Terminated, state reset, video RESUMED")
            
            return jsonify({
                "success": True,
                "message": "LeRobot terminated, video resumed",
                "video_resumed": True,
            })
            
        except Exception as e:
            print(f"[LEROBOT] Kill error: {e}")
            # Still reset state and resume video
            lerobot_bridge._running = False
            lerobot_bridge._process = None
            cv_video_service.resume()
            return jsonify({
                "success": True,
                "message": f"State reset, video resumed (kill had error: {e})",
            })

    # Video control endpoints
    @app.route('/api/video/pause', methods=['POST'])
    def video_pause():
        """Pause video feed and release camera."""
        cv_video_service.pause()
        return jsonify({"success": True, "paused": True})

    @app.route('/api/video/resume', methods=['POST'])
    def video_resume():
        """Resume video feed."""
        cv_video_service.resume()
        return jsonify({"success": True, "paused": False})
