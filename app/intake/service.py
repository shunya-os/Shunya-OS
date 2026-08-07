from app import db
from app.intake.models import IntakeSignal


class IntakeService:

    @staticmethod
    def receive_input(raw_input: str, input_type: str = "text"):
        signal = IntakeSignal(
            raw_input=raw_input,
            input_type=input_type,
            status="received"
        )

        db.session.add(signal)
        db.session.commit()

        return signal

    @staticmethod
    def process_signal(signal: IntakeSignal):
        # Minimal processing (no assumptions)
        signal.structured_data = {
            "length": len(signal.raw_input),
        }

        signal.status = "processed"

        db.session.commit()

        return signal