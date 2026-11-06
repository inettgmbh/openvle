"""Tests for schemas/events.py - Event schema validation."""

import uuid
from datetime import date, datetime, timezone

import pytest
from core.exceptions import InvalidFieldValue
from pydantic import ValidationError
from schemas.events import (
    EventCreate,
    EventStatusReport,
    EventStatusReportConnectionStats,
    EventStatusReportSubTask,
    EventStatusReportTask,
    EventStatusReportTaskStats,
    EventStatusReportVmStats,
    EventUpdateTemplate,
    EventUpdateVirtualMachine,
    EventVirtualMachinesHaAdd,
    EventVirtualMachinesMigrate,
)


class TestEventCreateSlugValidation:
    """Test slug validator on EventCreate schema."""

    def _make_event(self, slug, **kwargs):
        defaults = {
            "name": "Test Event",
            "dateStart": date.today().isoformat(),
            "dateEnd": date.today().isoformat(),
            "timeStart": "08:00:00",
            "timeEnd": "17:00:00",
            "guacamole": False,
            "status": str(uuid.uuid4()),
            "course": str(uuid.uuid4()),
        }
        defaults.update(kwargs)
        return EventCreate(slug=slug, **defaults)

    def test_valid_slug(self):
        event = self._make_event("abcd")
        assert event.slug == "abcd"

    @pytest.mark.parametrize(
        "slug",
        [
            "abcd",
            "ab-cd",
            "ab_cd",
            "a1b2",
            "1234",
            "abcdefgh",  # 8 chars max
        ],
    )
    def test_valid_slug_patterns(self, slug):
        event = self._make_event(slug)
        assert event.slug == slug

    def test_slug_too_short_raises(self):
        with pytest.raises(InvalidFieldValue):
            self._make_event("abc")  # 3 chars < 4

    def test_slug_too_long_raises(self):
        with pytest.raises(InvalidFieldValue):
            self._make_event("abcdefghi")  # 9 chars > 8

    def test_slug_uppercase_rejected(self):
        with pytest.raises(InvalidFieldValue):
            self._make_event("ABCD")

    def test_slug_special_chars_rejected(self):
        with pytest.raises(InvalidFieldValue):
            self._make_event("ab!d")

    def test_slug_space_rejected(self):
        with pytest.raises(InvalidFieldValue):
            self._make_event("ab cd")


class TestEventCreateDateValidation:
    def _make_event(self, **kwargs):
        defaults = {
            "name": "Test Event",
            "slug": "test",
            "dateStart": date.today().isoformat(),
            "dateEnd": date.today().isoformat(),
            "timeStart": "08:00:00",
            "timeEnd": "17:00:00",
            "guacamole": False,
            "status": str(uuid.uuid4()),
            "course": str(uuid.uuid4()),
        }
        defaults.update(kwargs)
        return EventCreate(**defaults)

    def test_valid_date_string_parsed(self):
        event = self._make_event(dateStart="2026-03-15")
        assert event.dateStart == date(2026, 3, 15)

    def test_date_object_accepted(self):
        d = date(2026, 6, 1)
        event = self._make_event(dateStart=d)
        assert event.dateStart == d


class TestEventVirtualMachinesMigrate:
    def test_valid_migrate(self):
        m = EventVirtualMachinesMigrate(targetNode="pve-node-01")
        assert m.targetNode == "pve-node-01"

    def test_missing_target_node_raises(self):
        with pytest.raises(ValidationError):
            EventVirtualMachinesMigrate()


class TestEventVirtualMachinesHaAdd:
    def test_defaults(self):
        ha = EventVirtualMachinesHaAdd()
        assert ha.ha_state == "started"
        assert ha.ha_max_restart == 5
        assert ha.ha_max_relocate == 5

    def test_custom_values(self):
        ha = EventVirtualMachinesHaAdd(
            ha_state="stopped", ha_max_restart=3, ha_max_relocate=2
        )
        assert ha.ha_state == "stopped"
        assert ha.ha_max_restart == 3
        assert ha.ha_max_relocate == 2


class TestEventUpdateTemplate:
    def test_valid_update(self):
        tid = uuid.uuid4()
        u = EventUpdateTemplate(templates=[{"id": tid}])
        assert len(u.templates) == 1
        assert u.templates[0].id == tid

    def test_missing_templates_raises(self):
        with pytest.raises(ValidationError):
            EventUpdateTemplate()

    def test_empty_list(self):
        u = EventUpdateTemplate(templates=[])
        assert u.templates == []


class TestEventUpdateVirtualMachine:
    def test_valid_update(self):
        vid = uuid.uuid4()
        u = EventUpdateVirtualMachine(vms=[{"id": vid}])
        assert len(u.vms) == 1
        assert u.vms[0].id == vid

    def test_missing_vms_raises(self):
        with pytest.raises(ValidationError):
            EventUpdateVirtualMachine()


# ---------------------------------------------------------------------------
# EventStatusReport schemas
# ---------------------------------------------------------------------------


class TestEventStatusReportVmStats:
    def test_all_zero(self):
        s = EventStatusReportVmStats(
            total=0, running=0, stopped=0, pending=0, protected=0
        )
        assert s.total == 0
        assert s.protected == 0

    def test_typical_values(self):
        s = EventStatusReportVmStats(
            total=10, running=6, stopped=3, pending=1, protected=2
        )
        assert s.total == 10
        assert s.running == 6
        assert s.stopped == 3
        assert s.pending == 1
        assert s.protected == 2

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            EventStatusReportVmStats(total=5, running=5, stopped=0, pending=0)


class TestEventStatusReportConnectionStats:
    def test_all_zero(self):
        s = EventStatusReportConnectionStats(total=0, deployed=0, pending=0)
        assert s.total == 0
        assert s.deployed == 0
        assert s.pending == 0

    def test_typical_values(self):
        s = EventStatusReportConnectionStats(total=5, deployed=3, pending=2)
        assert s.total == 5
        assert s.deployed == 3
        assert s.pending == 2

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            EventStatusReportConnectionStats(total=5, deployed=3)


class TestEventStatusReportTaskStats:
    def test_all_zero(self):
        s = EventStatusReportTaskStats(
            total=0, queued=0, processing=0, success=0, failed=0
        )
        assert s.total == 0
        assert s.queued == 0
        assert s.failed == 0

    def test_typical_values(self):
        s = EventStatusReportTaskStats(
            total=18, queued=5, processing=2, success=10, failed=1
        )
        assert s.total == 18
        assert s.queued == 5
        assert s.processing == 2
        assert s.success == 10
        assert s.failed == 1

    def test_missing_field_raises(self):
        with pytest.raises(ValidationError):
            EventStatusReportTaskStats(
                total=1, queued=1, processing=0, success=0
            )


class TestEventStatusReport:
    def _make_vm_stats(self, **kwargs):
        defaults = {
            "total": 0,
            "running": 0,
            "stopped": 0,
            "pending": 0,
            "protected": 0,
        }
        defaults.update(kwargs)
        return EventStatusReportVmStats(**defaults)

    def _make_connection_stats(self, **kwargs):
        defaults = {"total": 0, "deployed": 0, "pending": 0}
        defaults.update(kwargs)
        return EventStatusReportConnectionStats(**defaults)

    def _make_task_stats(self, **kwargs):
        defaults = {
            "total": 0,
            "queued": 0,
            "processing": 0,
            "success": 0,
            "failed": 0,
        }
        defaults.update(kwargs)
        return EventStatusReportTaskStats(**defaults)

    def test_minimal_construction(self):
        report = EventStatusReport(
            id=uuid.uuid4(),
            currentStatus="Geplant",
            vmStats=self._make_vm_stats(),
            connectionStats=self._make_connection_stats(),
            taskStats=self._make_task_stats(),
            tasks=[],
        )
        assert report.currentStatus == "Geplant"
        assert report.statusInitiator is None
        assert report.tasks == []

    def test_status_initiator_optional(self):
        uid = uuid.uuid4()
        report = EventStatusReport(
            id=uuid.uuid4(),
            currentStatus="Deploying",
            statusInitiator=uid,
            vmStats=self._make_vm_stats(total=5, running=3, pending=2),
            connectionStats=self._make_connection_stats(
                total=5, deployed=3, pending=2
            ),
            taskStats=self._make_task_stats(total=5, queued=3, processing=2),
            tasks=[],
        )
        assert report.statusInitiator == uid
        assert report.vmStats.total == 5
        assert report.vmStats.pending == 2
        assert report.connectionStats.total == 5
        assert report.connectionStats.deployed == 3
        assert report.taskStats.total == 5
        assert report.taskStats.queued == 3

    def test_with_nested_tasks(self):
        task_id = uuid.uuid4()
        subtask_id = uuid.uuid4()
        initiator_id = uuid.uuid4()
        report = EventStatusReport(
            id=uuid.uuid4(),
            currentStatus="Aktiv",
            statusInitiator=initiator_id,
            vmStats=self._make_vm_stats(total=4, running=4, protected=1),
            connectionStats=self._make_connection_stats(total=4, deployed=4),
            taskStats=self._make_task_stats(total=3, success=3),
            tasks=[
                EventStatusReportTask(
                    id=task_id,
                    initiatedAt=datetime.now(timezone.utc),
                    initiatedBy=initiator_id,
                    subTasks=[
                        EventStatusReportSubTask(
                            id=subtask_id,
                            name="Deploy VM",
                            status="success",
                            responseMsg="OK",
                            attempt="1",
                        )
                    ],
                )
            ],
        )
        assert len(report.tasks) == 1
        assert len(report.tasks[0].subTasks) == 1
        assert report.tasks[0].subTasks[0].status == "success"
        assert report.vmStats.protected == 1
        assert report.connectionStats.deployed == 4
