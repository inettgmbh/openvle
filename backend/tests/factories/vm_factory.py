"""Factories for VirtualMachine, Template, and Vendor models."""

import factory

from models import Template, Vendor, VirtualMachine

from .base import BaseFactory


class VendorFactory(BaseFactory):
    class Meta:
        model = Vendor

    name = factory.Sequence(lambda n: f"Vendor {n}")
    description = factory.Faker("sentence")


class TemplateFactory(BaseFactory):
    class Meta:
        model = Template

    name = factory.Sequence(lambda n: f"Template {n}")
    description = factory.Faker("sentence")
    status = "Ready"
    proxmoxId = factory.Sequence(lambda n: 1000 + n)
    proxmoxNode = "pve-node-01"
    cpu = 2
    ram = 4096
    disk = 32
    os = None
    prevent_delete = False


class VirtualMachineFactory(BaseFactory):
    class Meta:
        model = VirtualMachine

    name = factory.Sequence(lambda n: f"VM {n}")
    description = factory.Faker("sentence")
    status = "running"
    proxmoxId = factory.Sequence(lambda n: 2000 + n)
    proxmoxNode = "pve-node-01"
    cpu = 2
    ram = 4096
    disk = 32
    os = None
    template = None
    event = None
    prevent_delete = False
    ipv4 = factory.Sequence(lambda n: f"10.0.0.{n + 10}")
