"""
Pipeline Orchestrator Module
Acts as the central engine regulating tasks, failures, repairs, and state updates.
Signals UI views on progressive completion.
"""

import logging
from typing import List, Dict, Any, Optional
from src.core.world_state.world_state import WorldStateManager, ShotModel
from src.core.orchestrator.process_manager import ProcessManager
from src.core.orchestrator.task_runner import TaskRunner

class PipelineOrchestrator:
    """Manages sequential execution queue, handles validator failures, and triggers the repair loop."""
    
    def __init__(self, config: dict, world_state: WorldStateManager, asset_manager, scene_composer, validator_manager, repair_engine) -> None:
        self.config = config
        self.world_state = world_state
        self.repair_engine = repair_engine
        self.logger = logging.getLogger("Orchestrator")
        
        # Spawn dependencies
        self.process_manager = ProcessManager(config)
        self.task_runner = TaskRunner(asset_manager, scene_composer, self.process_manager, validator_manager)
        
        self.max_repairs = config.get("max_repair_attempts", 3)
        self.task_queue: List[Dict[str, Any]] = []

    def load_task_schedule(self, tasks: List[Dict[str, Any]]) -> None:
        """Injects sequential tasks to be executed by the pipeline."""
        self.task_queue = tasks
        self.logger.info(f"Loaded {len(tasks)} tasks into pipeline queue.")

    def run_pipeline(self) -> None:
        """Sequential processing of the queue with integrated validation and repair loops."""
        self.logger.info("Starting pipeline execution run...")
        
        # Group tasks by shot so we finish shot-by-shot
        shots_tasks: Dict[str, List[Dict[str, Any]]] = {}
        for t in self.task_queue:
            shot_id = t["shot_id"]
            if shot_id not in shots_tasks:
                shots_tasks[shot_id] = []
            shots_tasks[shot_id].append(t)
            
        for shot_id, tasks in shots_tasks.items():
            self.logger.info(f"Processing Shot Block: {shot_id}")
            
            # 1. Fetch or create Shot record in World State
            shot_model = self.world_state.get_shot(shot_id)
            if not shot_model:
                shot_model = ShotModel(shot_id=shot_id, scene_id="scene_001", status="generating")
                self.world_state.save_shot(shot_model)
            else:
                shot_model.status = "generating"
                self.world_state.save_shot(shot_model)
                
            shot_failed = False
            
            # 2. Execute tasks for this shot
            for task in tasks:
                try:
                    result = self.task_runner.execute_task(task, shot_model)
                    self.world_state.save_shot(shot_model)
                    
                    if task["type"] == "shot_validation" and result["status"] == "failed":
                        # Validation failed! Trigger repair loop
                        passed = self._run_repair_loop(shot_model, result["report"])
                        if not passed:
                            shot_failed = True
                            break # abort task queue for this shot
                except Exception as e:
                    self.logger.error(f"Task {task['task_id']} failed with error: {e}", exc_info=True)
                    shot_failed = True
                    break
                    
            # 3. Update final shot state
            if shot_failed:
                shot_model.status = "failed"
                self.logger.warning(f"Shot {shot_id} failed validation after checking repairs.")
            else:
                shot_model.status = "done"
                self.logger.info(f"Shot {shot_id} compiled successfully.")
                
            self.world_state.save_shot(shot_model)
            
        self.logger.info("Pipeline run complete.")

    def _run_repair_loop(self, shot_model: ShotModel, failure_report: Dict[str, Any]) -> bool:
        """
        Runs the iterative Repair Engine loop until validation passes
        or max_repair_attempts is exceeded.
        """
        shot_id = shot_model.shot_id
        self.logger.info(f"Initiating repair loop for shot {shot_id}")
        
        while shot_model.repair_attempts < self.max_repairs:
            shot_model.repair_attempts += 1
            self.logger.info(f"Repair attempt {shot_model.repair_attempts}/{self.max_repairs} for shot {shot_id}")
            
            # 1. Run repair modification
            self.repair_engine.repair_shot(shot_model, failure_report)
            
            # 2. Re-run render and validation
            # (Godot render mock in Phase 1)
            re_validation = self.task_runner.validator_manager.run_all_validators(shot_model)
            shot_model.validation_result = re_validation
            self.world_state.save_shot(shot_model)
            
            if re_validation["passed"]:
                self.logger.info(f"Repair succeeded on attempt {shot_model.repair_attempts} for shot {shot_id}")
                return True
                
            # Update failure report for next round
            failure_report = re_validation
            
        self.logger.error(f"Repair loop exhausted. Shot {shot_id} remains failed.")
        return False
logging = logging
List = List
Dict = Dict
Any = Any
Optional = Optional
WorldStateManager = WorldStateManager
ShotModel = ShotModel
ProcessManager = ProcessManager
TaskRunner = TaskRunner
PipelineOrchestrator = PipelineOrchestrator
