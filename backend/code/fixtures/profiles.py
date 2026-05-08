from dataclasses import dataclass

from .constants import Profile


@dataclass(frozen=True)
class ProfileConfig:
    name: Profile
    users_teacher: int
    users_student: int
    courses: int
    templates_per_course: int
    events_per_course: int
    vms_per_event_template: int
    roles: int
    policies: int
    documents: int
    tags_per_entity: int
    description: str = ""


PROFILES: dict[Profile, ProfileConfig] = {
    Profile.TESTING: ProfileConfig(
        name=Profile.TESTING,
        users_teacher=2,
        users_student=5,
        courses=2,
        templates_per_course=1,
        events_per_course=1,
        vms_per_event_template=2,
        roles=2,
        policies=1,
        documents=2,
        tags_per_entity=1,
        description="Minimal data for CI/integration tests",
    ),
    Profile.STAGING: ProfileConfig(
        name=Profile.STAGING,
        users_teacher=5,
        users_student=20,
        courses=4,
        templates_per_course=2,
        events_per_course=2,
        vms_per_event_template=4,
        roles=3,
        policies=2,
        documents=5,
        tags_per_entity=2,
        description="Moderate data for staging/QA",
    ),
    Profile.DEMO: ProfileConfig(
        name=Profile.DEMO,
        users_teacher=15,
        users_student=735,
        courses=6,
        templates_per_course=3,
        events_per_course=4,
        vms_per_event_template=6,
        roles=5,
        policies=3,
        documents=10,
        tags_per_entity=3,
        description="Realistic data for demos and presentations",
    ),
}
