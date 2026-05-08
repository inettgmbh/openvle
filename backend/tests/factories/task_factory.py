"""Factories for Task and SubTask models."""

import uuid

import factory

from models import SubTask, Task

from .base import BaseFactory


class TaskFactory(BaseFactory):
    class Meta:
        model = Task

    name = factory.Sequence(lambda n: f"Task {n}")
    status = "pending"
    event_id = None


class SubTaskFactory(BaseFactory):
    class Meta:
        model = SubTask

    name = factory.Sequence(lambda n: f"SubTask {n}")
    status = "pending"
    object_type = "VirtualMachine"
    object_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    action = "vm_clone"
    attempt = "0"
    parent_task = factory.LazyFunction(uuid.uuid4)  # Must be set to actual Task.id
    response_code = None
    response_message = None
    job_id = None
