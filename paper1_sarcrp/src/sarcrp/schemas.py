from dataclasses import dataclass, field
from typing import Literal, Optional

ActionType = Literal["RELOCATE", "RETRIEVE", "NOOP"]
CommitStatus = Literal["executed", "committed", "planned", "cancelled"]
EventType = Literal[
    "ORDER_SWAP", "URGENT_INSERTION", "ETA_EARLY", "ETA_LATE",
    "PROBABILITY_UPDATE", "STALE_INFORMATION",
]
Severity = Literal["low", "medium", "high"]


@dataclass
class Layout:
    num_stacks: int
    max_tier: int


@dataclass
class Stack:
    id: str
    containers: list[str]  # index 0 = bottom, index -1 = top (spec 37.1)
    max_tier: int


@dataclass
class YardState:
    instance_id: str
    time_step: int
    layout: Layout
    stacks: list[Stack]
    container_attributes: dict[str, dict]
    retrieval_queue: list[str]
    pickup_prob: dict[str, float]
    data_timestamp: int
    state_confidence: float


@dataclass
class Action:
    action_id: str
    step_index: int
    type: ActionType
    container: str
    source_stack: Optional[str]
    dest_stack: Optional[str]
    commit_status: CommitStatus
    planned_time: int


@dataclass
class Plan:
    plan_id: str
    created_at: int
    source: str
    actions: list[Action] = field(default_factory=list)


@dataclass
class RetrievalInformation:
    info_id: str
    timestamp: int
    retrieval_queue: list[str]
    pickup_prob: dict[str, float]
    urgent_containers: list[str]
    confidence: float
    source: str


@dataclass
class Event:
    event_id: str
    time_step: int
    type: EventType
    severity: Severity
    affected_containers: list[str]
    old_queue: list[str]
    new_queue: list[str]
    confidence: float
    timestamp_generated: int
    timestamp_observed: int
    metadata: dict = field(default_factory=dict)
