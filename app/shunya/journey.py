"""Shunya OS — Continuous Customer Journey Engine.

Maps every entity type to its position in the infinite customer journey loop.
Each stage naturally flows to the next. Bird AI uses this to guide users.

The Infinite Loop (Travel vertical):
  Inquiry → Quote → Booking → Payment → Trip → Feedback → Repeat
"""
from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum

class JourneyStage(Enum):
    LEAD = "lead"           # Inquiry/Lead capture
    QUOTE = "quote"         # Proposal/Itinerary
    BOOKING = "booking"     # Confirmed booking
    PAYMENT = "payment"     # Payment/Invoice
    TRIP = "trip"           # Live trip / In-progress
    FEEDBACK = "feedback"   # Post-trip follow-up
    RETENTION = "retention" # Repeat: offers, referrals → back to LEAD

JOURNEY_ORDER = [
    JourneyStage.LEAD,
    JourneyStage.QUOTE, 
    JourneyStage.BOOKING,
    JourneyStage.PAYMENT,
    JourneyStage.TRIP,
    JourneyStage.FEEDBACK,
    JourneyStage.RETENTION,
]

@dataclass
class JourneyItem:
    stage: JourneyStage
    count: int = 0
    entities: List[Dict] = field(default_factory=list)
    next_action: Optional[str] = None
    next_entity_type: Optional[str] = None

@dataclass
class JourneyReport:
    stages: List[JourneyItem] = field(default_factory=list)
    total_active: int = 0
    loop_completed: int = 0  # How many times customers have completed the full loop
    current_focus: Optional[str] = None  # Which stage needs most attention
    
    def stage_by_type(self, entity_type: str) -> Optional[JourneyStage]:
        mapping = {
            'lead': JourneyStage.LEAD,
            'enquiry': JourneyStage.LEAD,
            'inquiry': JourneyStage.LEAD,
            'quote': JourneyStage.QUOTE,
            'proposal': JourneyStage.QUOTE,
            'itinerary': JourneyStage.QUOTE,
            'booking': JourneyStage.BOOKING,
            'reservation': JourneyStage.BOOKING,
            'invoice': JourneyStage.PAYMENT,
            'payment': JourneyStage.PAYMENT,
            'receipt': JourneyStage.PAYMENT,
            'trip': JourneyStage.TRIP,
            'experience': JourneyStage.TRIP,
            'feedback': JourneyStage.FEEDBACK,
            'review': JourneyStage.FEEDBACK,
            'retention': JourneyStage.RETENTION,
            'campaign': JourneyStage.RETENTION,
            'referral': JourneyStage.RETENTION,
        }
        return mapping.get(entity_type.lower())
    
    def next_stage(self, current: JourneyStage) -> Optional[JourneyStage]:
        """Get the next stage in the infinite loop."""
        idx = JOURNEY_ORDER.index(current)
        return JOURNEY_ORDER[(idx + 1) % len(JOURNEY_ORDER)]
    
    def prev_stage(self, current: JourneyStage) -> Optional[JourneyStage]:
        """Get the previous stage in the loop."""
        idx = JOURNEY_ORDER.index(current)
        return JOURNEY_ORDER[(idx - 1) % len(JOURNEY_ORDER)]


def build_journey(tenant_id: int, def_counts: Dict[str, dict]) -> JourneyReport:
    """Build a journey report from entity definition counts."""
    from app.shunya.journey import JourneyStage, JourneyItem, JOURNEY_ORDER
    
    report = JourneyReport()
    stage_counts = {s: 0 for s in JourneyStage}
    stage_entities = {s: [] for s in JourneyStage}
    
    for type_key, info in def_counts.items():
        js = report.stage_by_type(type_key)
        if js:
            stage_counts[js] = stage_counts.get(js, 0) + info.get('count', 0)
            stage_entities[js].append(info)
    
    # Determine next actions per stage
    next_entity_map = {
        JourneyStage.LEAD: ('Quote', 'quote'),
        JourneyStage.QUOTE: ('Booking', 'booking'),
        JourneyStage.BOOKING: ('Invoice', 'invoice'),
        JourneyStage.PAYMENT: ('Trip', 'trip'),
        JourneyStage.TRIP: ('Feedback', 'feedback'),
        JourneyStage.FEEDBACK: ('Retention Campaign', 'campaign'),
        JourneyStage.RETENTION: ('New Lead', 'lead'),
    }
    
    for stage in JOURNEY_ORDER:
        next_name, next_type = next_entity_map.get(stage, ('', ''))
        report.stages.append(JourneyItem(
            stage=stage,
            count=stage_counts.get(stage, 0),
            entities=stage_entities.get(stage, []),
            next_action=f"Create {next_name}" if next_name else None,
            next_entity_type=next_type if next_type else None,
        ))
    
    report.total_active = sum(stage_counts.values())
    
    # Focus: stage with lowest count that should have high count
    # (e.g., if leads are high but bookings are low, focus on conversion)
    if stage_counts.get(JourneyStage.LEAD, 0) > 0 and stage_counts.get(JourneyStage.BOOKING, 0) == 0:
        report.current_focus = "conversion"
    elif stage_counts.get(JourneyStage.TRIP, 0) > 0 and stage_counts.get(JourneyStage.FEEDBACK, 0) == 0:
        report.current_focus = "feedback"
    elif stage_counts.get(JourneyStage.RETENTION, 0) == 0 and stage_counts.get(JourneyStage.FEEDBACK, 0) > 0:
        report.current_focus = "retention"
    
    return report