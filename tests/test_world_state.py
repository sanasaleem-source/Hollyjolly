import pytest
from src.core.world_state.world_state import WorldStateManager
from src.core.world_state.character_db import CharacterModel
from src.core.world_state.object_db import ObjectModel
from src.core.world_state.world_db import WorldEventModel
from src.core.world_state.shot_db import ShotModel

@pytest.fixture
def world_state_manager(tmp_path):
    config = {"storage_path": str(tmp_path)}
    return WorldStateManager(config)

def test_character_upsert_and_get(world_state_manager):
    # Test Create
    char = CharacterModel(
        name="John Doe",
        appearance={"hair": "black", "eyes": "blue"},
        clothing={"shirt": "red"},
        injuries={"bruises": "none"},
        relationships={"partner": "Jane Doe"},
        history="A test character",
        last_seen_shot_id="shot_001"
    )
    saved = world_state_manager.save_character(char)
    assert saved.id is not None
    assert saved.name == "John Doe"

    # Test Retrieve
    retrieved = world_state_manager.get_character("John Doe")
    assert retrieved is not None
    assert retrieved.name == "John Doe"
    assert retrieved.appearance["hair"] == "black"
    assert retrieved.clothing["shirt"] == "red"
    assert retrieved.last_seen_shot_id == "shot_001"

    # Test Update (Upsert)
    retrieved.clothing["shirt"] = "blue"
    retrieved.last_seen_shot_id = "shot_002"
    _ = world_state_manager.save_character(retrieved)
    
    retrieved_updated = world_state_manager.get_character("John Doe")
    assert retrieved_updated is not None
    assert retrieved_updated.clothing["shirt"] == "blue"
    assert retrieved_updated.last_seen_shot_id == "shot_002"

    # Test Get All
    all_chars = world_state_manager.get_all_characters()
    assert len(all_chars) == 1
    assert all_chars[0].name == "John Doe"


def test_object_upsert_and_get(world_state_manager):
    # Test Create
    obj = ObjectModel(
        name="Excalibur",
        owner="King Arthur",
        condition="Intact",
        location="Stone",
        version=1
    )
    saved = world_state_manager.save_object(obj)
    assert saved.id is not None
    assert saved.name == "Excalibur"

    # Test Retrieve
    retrieved = world_state_manager.get_object("Excalibur")
    assert retrieved is not None
    assert retrieved.name == "Excalibur"
    assert retrieved.owner == "King Arthur"
    assert retrieved.condition == "Intact"

    # Test Update (Upsert)
    retrieved.condition = "Chipped"
    retrieved.location = "Lake"
    _ = world_state_manager.save_object(retrieved)

    retrieved_updated = world_state_manager.get_object("Excalibur")
    assert retrieved_updated is not None
    assert retrieved_updated.condition == "Chipped"
    assert retrieved_updated.location == "Lake"

    # Test Get All
    all_objs = world_state_manager.get_all_objects()
    assert len(all_objs) == 1
    assert all_objs[0].name == "Excalibur"


def test_world_event_upsert_and_get(world_state_manager):
    # Test Create
    event = WorldEventModel(
        shot_id="shot_001",
        time_of_day="Day",
        weather="Sunny",
        lighting="Cinematic high-key",
        damage_state={"castle_wall": "cracked"},
        events={"description": "Dragon flew by"}
    )
    saved = world_state_manager.save_world_event(event)
    assert saved.shot_id == "shot_001"

    # Test Retrieve
    retrieved = world_state_manager.get_world_event("shot_001")
    assert retrieved is not None
    assert retrieved.shot_id == "shot_001"
    assert retrieved.time_of_day == "Day"
    assert retrieved.weather == "Sunny"
    assert retrieved.damage_state["castle_wall"] == "cracked"

    # Test Update (Upsert)
    retrieved.time_of_day = "Night"
    retrieved.weather = "Rainy"
    _ = world_state_manager.save_world_event(retrieved)

    retrieved_updated = world_state_manager.get_world_event("shot_001")
    assert retrieved_updated is not None
    assert retrieved_updated.time_of_day == "Night"
    assert retrieved_updated.weather == "Rainy"

    # Test Get All
    all_events = world_state_manager.get_world_events()
    assert len(all_events) == 1
    assert all_events[0].shot_id == "shot_001"


def test_shot_upsert_and_get(world_state_manager):
    # Test Create
    shot = ShotModel(
        shot_id="shot_001",
        scene_id="scene_01",
        status="pending",
        asset_versions={"John Doe": "v2", "Excalibur": "v1"},
        render_path="/renders/shot_001.mp4",
        validation_result={"passed": True, "failures": []},
        repair_attempts=0
    )
    saved = world_state_manager.save_shot(shot)
    assert saved.shot_id == "shot_001"

    # Test Retrieve
    retrieved = world_state_manager.get_shot("shot_001")
    assert retrieved is not None
    assert retrieved.shot_id == "shot_001"
    assert retrieved.scene_id == "scene_01"
    assert retrieved.status == "pending"
    assert retrieved.asset_versions["John Doe"] == "v2"

    # Test Update (Upsert)
    retrieved.status = "done"
    retrieved.repair_attempts = 1
    _ = world_state_manager.save_shot(retrieved)

    retrieved_updated = world_state_manager.get_shot("shot_001")
    assert retrieved_updated is not None
    assert retrieved_updated.status == "done"
    assert retrieved_updated.repair_attempts == 1

    # Test Get All
    all_shots = world_state_manager.get_all_shots()
    assert len(all_shots) == 1
    assert all_shots[0].shot_id == "shot_001"
