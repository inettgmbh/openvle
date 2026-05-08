import BaseButtonMock from './mocks/components/BaseButtonMock'
import BaseButtonsMock from './mocks/components/BaseButtonsMock'
import BaseIconMock from './mocks/components/BaseIconMock'
import MarkdownRendererMock from './mocks/components/MarkdownRendererMock'
import PillTagMock from './mocks/components/PillTagMock'
import TableCheckboxCellMock from './mocks/components/TableCheckboxCellMock'
import TablePaginationMock from './mocks/components/TablePaginationMock'
import TableSearchBarMock from './mocks/components/TableSearchBarMock'
import UserAvatarMock from './mocks/components/UserAvatarMock'

import { vi } from 'vitest'

vi.mock('@/components/BaseButton.vue', () => ({
  default: BaseButtonMock,
}))

vi.mock('@/components/BaseButtons.vue', () => ({
  default: BaseButtonsMock,
}))

vi.mock('@/components/BaseIcon.vue', () => ({
  default: BaseIconMock,
}))

vi.mock('@/components/PillTag.vue', () => ({
  default: PillTagMock,
}))

vi.mock('@/components/UserAvatar.vue', () => ({
  default: UserAvatarMock,
}))

vi.mock('@/components/MarkdownRenderer.vue', () => ({
  default: MarkdownRendererMock,
}))

vi.mock('@/components/Tables/TableCheckboxCell.vue', () => ({
  default: TableCheckboxCellMock,
}))

vi.mock('@/components/Tables/TablePagination.vue', () => ({
  default: TablePaginationMock,
}))

vi.mock('@/components/Tables/TableSearchBar.vue', () => ({
  __esModule: true,
  __isTeleport: false,
  __isFragment: false,
  __isSuspense: false,
  default: TableSearchBarMock,
}))
