"""
Pipeline Orchestrator — central engine managing tasks, failures, repairs, and state updates.
"""
import logging
from typing import List, Dict, Any
from src.core.world_state.world_state import WorldStateManager
from src.core.world_state.shot_db import ShotModel          # ← correct location
from src.core.orchestrator.process_manager import ProcessManager
from src.core.orchestrator.task_runner import TaskRunner


class PipelineOrchestrator:
    """Sequential task queue with integrated validation and repair loop."""

    def __init__(self, config: dict, world_state: WorldStateManager,
                 asset_manager, scene_composer, validator_manager, repair_engine) -> None:
        self.config          = config
        self.world_state     = world_state
        self.repair_engine   = repair_engine
        self.logger          = logging.getLogger("Orchestrator")
        self.process_manager = ProcessManager(config)
        self.task_runner     = TaskRunner(
            asset_manager, scene_composer,
            self.process_manager, validator_manager, self.world_state, config
        )
        self.max_repairs  = config.get("max_repair_attempts", 3)
        self.task_queue: List[Dict[str, Any]] = []

    def load_task_schedule(self, tasks: List[Dict[str, Any]]) -> None:
        """Inject ordered tasks into the pipeline queue."""
        self.task_queue = tasks
        self.logger.info(f"Loaded {len(tasks)} tasks into queue.")

    def run_pipeline(self) -> None:
        """Process every shot in sequence with validation and repair."""
        self.logger.info("Pipeline execution starting.")

        # Group tasks by shot_id, preserving order
        shots_tasks: Dict[str, List[Dict[str, Any]]] = {}
        for t in self.task_queue:
            sid = t["shot_id"]
            shots_tasks.setdefault(sid, []).append(t)

        for shot_id, tasks in shots_tasks.items():
            self.logger.info(f"Processing shot: {shot_id}")

            shot_model = self.world_state.get_shot(shot_id)
            if not shot_model:
                shot_model = ShotModel(shot_id=shot_id, scene_id=tasks[0].get("scene_id", "scene_001"), status="generating")
            else:
                shot_model.status = "generating"
            self.world_state.save_shot(shot_model)

            shot_failed = False
            for task in tasks:
                try:
                    result = self.task_runner.execute_task(task, shot_model)
                    self.world_state.save_shot(shot_model)
                    if task["type"] == "shot_validation" and result["status"] == "failed":
                        passed = self._run_repair_loop(shot_model, result["report"])
                        if not passed:
                            shot_failed = True
                            break
                except Exception as e:
                    self.logger.error(f"Task {task.get('task_id')} error: {e}", exc_info=True)
                    shot_failed = True
                    break

            shot_model.status = "failed" if shot_failed else "done"
            self.world_state.save_shot(shot_model)
            self.logger.info(f"Shot {shot_id}: {shot_model.status}")

        self.logger.info("Pipeline run complete.")

    def _run_repair_loop(self, shot_model: ShotModel, failure_report: Dict[str, Any]) -> bool:
        """Retry repair up to max_repair_attempts times."""
        while shot_model.repair_attempts < self.max_repairs:
            shot_model.repair_attempts += 1
            self.logger.info(f"Repair attempt {shot_model.repair_attempts}/{self.max_repairs} for {shot_model.shot_id}")
            self.repair_engine.repair_shot(shot_model, failure_report)
            re_val = self.task_runner.validator_manager.run_all_validators(shot_model, self.world_state)
            shot_model.validation_result = re_val
            self.world_state.save_shot(shot_model)
            if re_val["passed"]:
                self.logger.info(f"Repair succeeded on attempt {shot_model.repair_attempts}")
                return True
            failure_report = re_val
        self.logger.error(f"Repair exhausted for {shot_model.shot_id}")
        return False
