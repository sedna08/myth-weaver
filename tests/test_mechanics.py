import rollforge

def test_sys_04_rollforge_mechanics(seeded_rollforge):
    # Arrange
    state = seeded_rollforge.SessionState()
    player = state.player
    player.stats.strength = 16  # Modifies to +3
    
    goblin = seeded_rollforge.Entity()
    goblin.armor_class = 12
    goblin.current_hp = 10
    goblin.max_hp = 10

    # Act
    # Seed 42 guarantees a specific d20 roll. 
    # If the logic is correct: (d20_roll + 3) >= 12 will determine the hit.
    hit = seeded_rollforge.ActionResolver.resolve_attack(player, goblin, seeded_rollforge.StatType.Strength)

    # Assert
    assert isinstance(hit, bool), "resolve_attack must return a boolean."
    
    # Check if damage application works
    if hit:
        seeded_rollforge.ActionResolver.apply_damage(goblin, 5)
        assert goblin.current_hp == 5, "apply_damage did not reduce target HP correctly."

def test_sys_08_serialization():
    # Arrange
    state = rollforge.SessionState()
    state.current_location = "Dungeon Entrance"
    
    # Rollforge uses dictionaries/maps for world flags
    state.world_flags = {"door_unlocked": True}

    # Act
    save_data = state.serialize_to_json()
    loaded_state = rollforge.SessionState.deserialize_from_json(save_data)

    # Assert
    assert loaded_state.current_location == "Dungeon Entrance", "Location failed to deserialize."
    assert loaded_state.world_flags.get("door_unlocked") is True, "World flags failed to deserialize."