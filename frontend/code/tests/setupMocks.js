import ActivityServiceMock from './mocks/ActivityServiceMock'
import ApplicationServiceMock from './mocks/ApplicationServiceMock'
import AuthServiceMock from './mocks/AuthServiceMock'
import ChangelogServiceMock from './mocks/ChangelogServiceMock'
import ConnectionServiceMock from './mocks/ConnectionServiceMock'
import CourseServiceMock from './mocks/CourseServiceMock'
import EventServiceMock from './mocks/EventServiceMock'
import GuacamoleServiceMock from './mocks/GuacamoleServiceMock'
import LanguageServiceMock from './mocks/LanguageServiceMock'
import MailActionServiceMock from './mocks/MailActionServiceMock'
import MailServiceMock from './mocks/MailServiceMock'
import MailTemplateServiceMock from './mocks/MailTemplateServiceMock'
import MeServiceMock from './mocks/MeServiceMock'
import MoodleServiceMock from './mocks/MoodleServiceMock'
import ObjectPermissionServiceMock from './mocks/ObjectPermissionServiceMock'
import OSServiceMock from './mocks/OSServiceMock'
import PolicyServiceMock from './mocks/PolicyServiceMock'
import ProxmoxServiceMock from './mocks/ProxmoxServiceMock'
import RoleServiceMock from './mocks/RoleServiceMock'
import ScimClientServiceMock from './mocks/ScimClientServiceMock'
import ScimProviderServiceMock from './mocks/ScimProviderServiceMock'
import StatisticServiceMock from './mocks/StatisticServiceMock'
import TagServiceMock from './mocks/TagServiceMock'
import TaskServiceMock from './mocks/TaskServiceMock'
import TemplateServiceMock from './mocks/TemplateServiceMock'
import UserServiceMock from './mocks/UserServiceMock'
import VendorServiceMock from './mocks/VendorServiceMock'
import VMServiceMock from './mocks/VMServiceMock'

import { vi } from 'vitest'

// Mock the singleton backend export from @/services
vi.mock('@/services', () => ({
  default: {
    activities: ActivityServiceMock,
    applications: ApplicationServiceMock,
    auth: AuthServiceMock,
    changelog: ChangelogServiceMock,
    connections: ConnectionServiceMock,
    courses: CourseServiceMock,
    events: EventServiceMock,
    guacamole: GuacamoleServiceMock,
    languages: LanguageServiceMock,
    mailActions: MailActionServiceMock,
    mail: MailServiceMock,
    mailTemplates: MailTemplateServiceMock,
    me: MeServiceMock,
    moodle: MoodleServiceMock,
    objectPermissions: ObjectPermissionServiceMock,
    os: OSServiceMock,
    policies: PolicyServiceMock,
    proxmox: ProxmoxServiceMock,
    roles: RoleServiceMock,
    scimClients: ScimClientServiceMock,
    scimProviders: ScimProviderServiceMock,
    statistics: StatisticServiceMock,
    tags: TagServiceMock,
    tasks: TaskServiceMock,
    templates: TemplateServiceMock,
    users: UserServiceMock,
    vendors: VendorServiceMock,
    vms: VMServiceMock,
    // Interceptor-silencing helpers from BackendClient
    beginSilent: vi.fn(),
    endSilent: vi.fn(),
  },
}))

// Mock individual service class exports (for direct imports)
vi.mock('@/services/ActivityService.js', () => ({
  default: ActivityServiceMock,
}))

vi.mock('@/services/ApplicationService.js', () => ({
  default: ApplicationServiceMock,
}))

vi.mock('@/services/AuthService.js', () => ({
  default: AuthServiceMock,
}))

vi.mock('@/services/ChangelogService.js', () => ({
  default: ChangelogServiceMock,
}))

vi.mock('@/services/ConnectionService.js', () => ({
  default: ConnectionServiceMock,
}))

vi.mock('@/services/CourseService.js', () => ({
  default: CourseServiceMock,
}))

vi.mock('@/services/EventService.js', () => ({
  default: EventServiceMock,
}))

vi.mock('@/services/GuacamoleService.js', () => ({
  default: GuacamoleServiceMock,
}))

vi.mock('@/services/LanguageService.js', () => ({
  default: LanguageServiceMock,
}))

vi.mock('@/services/MailActionService.js', () => ({
  default: MailActionServiceMock,
}))

vi.mock('@/services/MailService.js', () => ({
  default: MailServiceMock,
}))

vi.mock('@/services/MailTemplateService.js', () => ({
  default: MailTemplateServiceMock,
}))

vi.mock('@/services/MeService.js', () => ({
  default: MeServiceMock,
}))

vi.mock('@/services/MoodleService.js', () => ({
  default: MoodleServiceMock,
}))

vi.mock('@/services/ObjectPermissionService.js', () => ({
  default: ObjectPermissionServiceMock,
}))

vi.mock('@/services/OSService.js', () => ({
  default: OSServiceMock,
}))

vi.mock('@/services/PolicyService.js', () => ({
  default: PolicyServiceMock,
}))

vi.mock('@/services/ProxmoxService.js', () => ({
  default: ProxmoxServiceMock,
}))

vi.mock('@/services/RoleService.js', () => ({
  default: RoleServiceMock,
}))

vi.mock('@/services/ScimClientService.js', () => ({
  default: ScimClientServiceMock,
}))

vi.mock('@/services/ScimProviderService.js', () => ({
  default: ScimProviderServiceMock,
}))

vi.mock('@/services/StatisticService.js', () => ({
  default: StatisticServiceMock,
}))

vi.mock('@/services/TagService.js', () => ({
  default: TagServiceMock,
}))

vi.mock('@/services/TaskService.js', () => ({
  default: TaskServiceMock,
}))

vi.mock('@/services/TemplateService.js', () => ({
  default: TemplateServiceMock,
}))

vi.mock('@/services/UserService.js', () => ({
  default: UserServiceMock,
}))

vi.mock('@/services/VendorService.js', () => ({
  default: VendorServiceMock,
}))

vi.mock('@/services/VMService.js', () => ({
  default: VMServiceMock,
}))
