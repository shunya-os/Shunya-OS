from app import db
from app.observations.models import Observation


def record_observation(commitment_id: int, observed_value: dict, expected_value: dict = None):
    obs = Observation(
        commitment_id=commitment_id,
        observed_value=observed_value,
        expected_value=expected_value,
        status="recorded"
    )

    db.session.add(obs)
    db.session.commit()

    return obs


def evaluate_observation(obs: Observation):
    if not obs.expected_value:
        return obs

    if obs.observed_value == obs.expected_value:
        obs.status = "matched"
    else:
        obs.status = "deviated"

    db.session.commit()
    return obs