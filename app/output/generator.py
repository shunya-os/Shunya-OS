def generate_output(entity):
    state = entity.state or {}

    if entity.type == "lead":
        return {
            "summary": f"Lead at stage: {state.get('stage')}",
            "next_action": state.get("next_step")
        }

    return {
        "summary": "Generic entity",
        "state": state
    }