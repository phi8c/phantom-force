Được. Mình tổng hợp lại thành **baseline kiến trúc chính thức của frontend PICO** để từ đây về sau mình và bạn dùng nó làm chuẩn, tránh tình trạng đang code rồi lại đổi architecture giữa chừng.

# UNICORN FRONTEND PROTOTYPE — Architecture & Stack

## 1. Mục tiêu

Frontend này không chỉ là một trang RAG Chat đơn giản mà là **platform quản lý dữ liệu + Ingestion + RAG + Chat**.

Có hai trải nghiệm chính:

```text
                    PICO Platform
                         │
             ┌───────────┴───────────┐
             │                       │
           ADMIN                    CHAT
             │                       │
       Data / Ingest /          RAG Conversation
       Configuration             / Citations
```

### Admin

Phục vụ việc vận hành platform:

```text
Knowledge Spaces
Sources
Documents
Ingestion
Workers
Jobs
Models
Settings
Monitoring
```

### Chat

Phục vụ người dùng cuối:

```text
Conversations
Messages
RAG retrieval
Citations
Sources
Streaming
```

Mục tiêu architecture:

* dễ maintain
* dễ mở rộng
* module độc lập
* hạn chế coupling
* không duplicate component
* không mirror backend một cách máy móc
* có thể thêm feature lớn mà không phải refactor architecture
* phù hợp production

---

# 2. Core Stack

## Framework

### Next.js 16.3.1

Dùng:

```text
Next.js 16.3.1
App Router
React Server Components
Turbopack
```

Next.js chịu trách nhiệm:

```text
Routing
Rendering
Layouts
Server Components
Client Components
Metadata
Build
```

---

## React

```text
React 19.2.8
```

Dùng React hiện đại:

```text
Server Components
Client Components
Hooks
Suspense
```

Không sử dụng kiến trúc React Router riêng.

Routing hoàn toàn do Next.js App Router quản lý.

---

## TypeScript

```text
TypeScript 5.x
```

Project bật:

```json
"strict": true
```

Mục tiêu là type-safe xuyên suốt:

```text
UI
↓
Feature
↓
API
↓
Backend contract
```

Không dùng `any` tùy tiện.

---

# 3. Styling

## Tailwind CSS

```text
Tailwind CSS v4
```

Đang sử dụng:

```text
@tailwindcss/postcss
```

CSS chính:

```text
src/app/globals.css
```

Tailwind chịu trách nhiệm:

```text
layout
spacing
responsive
typography
colors
states
dark mode
```

Không sử dụng CSS framework kiểu Bootstrap.

---

# 4. UI System

## shadcn/ui

Đã setup:

```text
shadcn/ui
Base UI
Nova preset
Lucide icons
```

`components.json` hiện dùng:

```text
style: base-nova
component library: Base UI
icon library: Lucide
base color: neutral
CSS variables: enabled
```

Điểm quan trọng:

> shadcn/ui không phải một component library runtime mà mình import toàn bộ từ một package.

Component được đưa vào source code:

```text
src/components/ui/
```

nên mình có toàn quyền customize.

---

# 5. UI Primitive hiện có

Foundation đã cài những component có khả năng dùng thường xuyên.

### Form

```text
Button
Input
Textarea
Label
Select
Checkbox
Switch
Radio Group
```

### Overlay

```text
Dialog
Alert Dialog
Dropdown Menu
Sheet
Popover
```

### Display

```text
Card
Badge
Avatar
Separator
Skeleton
Scroll Area
Tooltip
```

### Data / Navigation

```text
Table
Tabs
Command
```

Không cài hàng loạt component chỉ để “đủ bộ”.

Nguyên tắc:

> Component nào feature thực sự cần thì mới `shadcn add` thêm.

---

# 6. Icon

Dùng:

```text
Lucide React
```

Không dùng nhiều icon library khác nhau.

Ví dụ:

```tsx
import {
  Search,
  Settings,
  Database,
  MessageSquare,
} from "lucide-react";
```

Mục tiêu là giữ visual language nhất quán.

---

# 7. State Management

Đây là phần rất quan trọng.

Ta dùng **hai hệ thống state**, nhưng mỗi cái có trách nhiệm riêng.

---

## Redux Toolkit

Version hiện tại:

```text
@reduxjs/toolkit 2.12.0
react-redux 9.3.0
```

Redux dùng cho:

> **Global client state**

Ví dụ:

```text
UI state
Auth state
Sidebar state
Workspace selection
User preferences
```

Hiện tại đã có:

```text
store/
└── slices/
    └── appSlice.ts
```

với:

```text
sidebarCollapsed
```

---

## Không dùng Redux để cache API

Không làm:

```text
Redux
└── documents
└── ingestionJobs
└── knowledgeSpaces
└── conversations
```

chỉ để lưu response backend.

Đó là việc của TanStack Query.

---

# 8. TanStack Query

Version:

```text
@tanstack/react-query 5.101.4
```

Dùng cho:

> Server state / remote state

Ví dụ:

```text
Knowledge Spaces
Documents
Sources
Ingestion Jobs
Workers
Models
Conversations
Messages
System Configuration
```

Flow:

```text
Backend API
     ↓
TanStack Query
     ↓
Cache
     ↓
React Component
```

Thay vì:

```text
Backend
 ↓
Redux
 ↓
Component
```

---

# 9. Query Provider

Đã có:

```text
src/providers/QueryProvider.tsx
```

và:

```text
QueryClient
```

default `staleTime`:

```text
30 seconds
```

Đây chỉ là default.

Feature/query có thể override:

```text
staleTime
gcTime
retry
refetchInterval
```

theo nhu cầu thực tế.

Ví dụ ingestion status có thể cần:

```text
refetchInterval
```

trong khi static configuration có thể có:

```text
staleTime: Infinity
```

---

# 10. Axios

Version:

```text
axios 1.19.0
```

Dùng Axios làm HTTP client.

Có một client duy nhất:

```text
src/lib/api/client.ts
```

Hiện tại:

```text
baseURL =
NEXT_PUBLIC_API_URL
```

Local:

```text
http://localhost:8000
```

Environment:

```text
.env.local
```

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

`.env.local` đã nằm trong `.gitignore`.

---

# 11. API Architecture

Không để mỗi feature tự:

```ts
axios.create(...)
```

Ta có:

```text
lib/api/client.ts
        ↓
      Axios
        ↓
      Backend
```

Sau này sẽ mở rộng infrastructure ở:

```text
lib/api/
```

ví dụ:

```text
client.ts
errors.ts
interceptors.ts
```

nhưng chỉ tạo khi thực sự cần.

Authentication/interceptor hiện **chưa được nhét vào**, vì auth flow chưa implement.

---

# 12. Architecture tổng thể

Frontend sử dụng:

> **Modular Monolith / Feature-oriented Architecture**

Không phải microfrontend.

Không mirror backend.

Không chia project thành những layer kiểu:

```text
controllers
services
repositories
```

như backend.

Frontend có trách nhiệm khác backend.

---

# 13. Folder Architecture

Baseline đã chốt:

```text
src/
│
├── app/
│
├── modules/
│
├── components/
│
├── store/
│
├── providers/
│
├── lib/
│
├── config/
│
├── constants/
│
├── hooks/
│
└── types/
```

---

# 14. `app/` — Routing Layer

`app` dành cho:

```text
Next.js routing
layouts
pages
route composition
```

Không nhét business logic lớn vào đây.

Hiện tại:

```text
app/
├── (admin)/
│   └── admin/
│       ├── layout.tsx
│       └── page.tsx
│
├── (chat)/
│   └── chat/
│       ├── layout.tsx
│       └── page.tsx
│
├── layout.tsx
├── page.tsx
└── globals.css
```

---

# 15. Route Groups

Dùng Next.js Route Groups:

```text
(admin)
(chat)
```

Nhưng chúng **không xuất hiện trong URL**.

Do đó:

```text
app/(admin)/admin
```

→

```text
/admin
```

và:

```text
app/(chat)/chat
```

→

```text
/chat
```

---

# 16. Admin

Admin có layout riêng:

```text
app/(admin)/admin/layout.tsx
```

Mục tiêu:

```text
AdminShell
├── Sidebar
├── Topbar
├── Workspace selector
├── User menu
└── Main content
```

Các route tương lai:

```text
/admin
/admin/knowledge-spaces
/admin/sources
/admin/documents
/admin/ingestion
/admin/workers
/admin/models
/admin/settings
```

---

# 17. Chat

Chat có layout riêng:

```text
app/(chat)/chat/layout.tsx
```

Mục tiêu:

```text
ChatShell
├── Conversation sidebar
├── Chat header
├── Chat workspace
└── Composer
```

Route tương lai:

```text
/chat
/chat/[conversationId]
```

---

# 18. Root route

Đã chốt:

```text
/
```

redirect sang:

```text
/chat
```

Hiện tại:

```tsx
redirect("/chat");
```

Lý do:

Chat là trải nghiệm chính của platform.

Admin là operational interface:

```text
/admin
```

---

# 19. `modules/` — Domain Feature Layer

Đây là phần quan trọng nhất của architecture.

Mỗi business domain là một module độc lập.

Ví dụ:

```text
modules/
├── auth/
├── knowledge-space/
├── source/
├── document/
├── ingestion/
├── chat/
├── model/
└── settings/
```

Nhưng:

> **Không tạo tất cả ngay bây giờ.**

Làm tới đâu tạo tới đó.

---

# 20. Module structure

Một module có thể phát triển thành:

```text
modules/
└── ingestion/
    ├── api/
    ├── components/
    ├── hooks/
    ├── schemas/
    ├── types/
    ├── constants/
    └── index.ts
```

Nhưng nếu module nhỏ:

```text
modules/
└── source/
    ├── api/
    ├── components/
    ├── hooks/
    ├── types/
    └── index.ts
```

Không bắt mọi module phải có 10 folder.

---

# 21. Module độc lập

Ví dụ Ingestion:

```text
modules/ingestion/
├── api/
├── components/
├── hooks/
├── schemas/
├── types/
└── constants/
```

Không đưa:

```text
IngestionTable
IngestionJobCard
IngestionStatus
```

vào shared chỉ vì chúng là React component.

Chúng thuộc:

```text
modules/ingestion/components/
```

---

# 22. `components/`

Đây là shared UI layer.

Chia:

```text
components/
├── ui/
├── layout/
└── shared/
```

---

## `components/ui`

shadcn primitives:

```text
Button
Dialog
Table
Input
...
```

Không business logic.

---

## `components/layout`

Application-level layout components:

```text
AdminShell
ChatShell
Sidebar
Topbar
```

---

## `components/shared`

Component dùng chung thực sự:

```text
DataTable
PageHeader
EmptyState
LoadingState
ErrorState
ConfirmDialog
```

Ví dụ:

```text
Documents
Ingestion
Workers
Users
```

đều có thể dùng:

```text
DataTable
```

mà không duplicate implementation.

---

# 23. Quy tắc Shared Component

Một component chỉ được đưa vào:

```text
components/shared
```

khi nó thực sự được dùng bởi nhiều domain.

Không làm:

```text
"có thể dùng lại"
```

rồi đưa vào shared.

Ví dụ:

```text
KnowledgeSpaceCard
```

ban đầu:

```text
modules/knowledge-space/components/
```

Nếu sau này nhiều module thực sự cần nó thì mới cân nhắc extract.

Điều này tránh:

> `shared/` trở thành bãi rác business logic.

---

# 24. `store/`

Redux infrastructure:

```text
store/
├── slices/
├── index.ts
└── provider.tsx
```

Hiện tại:

```text
appSlice
```

Sau này nếu cần:

```text
authSlice
workspaceSlice
uiSlice
```

nhưng không tạo trước.

---

# 25. `providers/`

Application providers:

```text
providers/
├── AppProviders.tsx
└── QueryProvider.tsx
```

Flow:

```text
RootLayout
    ↓
AppProviders
    ├── StoreProvider
    │       ↓
    │     Redux
    │
    └── QueryProvider
            ↓
        TanStack Query
```

Sau này có thể thêm:

```text
ThemeProvider
AuthProvider
```

nhưng chỉ khi cần.

---

# 26. `lib/`

Infrastructure/helper không thuộc business domain.

Hiện tại:

```text
lib/
├── api/
│   └── client.ts
└── utils.ts
```

Ví dụ tương lai:

```text
lib/
├── api/
├── auth/
├── storage/
└── utils/
```

---

# 27. `config/`

Configuration của frontend:

```text
config/
├── app.ts
├── navigation.ts
└── ...
```

Ví dụ:

```text
application name
navigation configuration
feature flags
UI configuration
```

Không hardcode những thứ cần configuration trong component.

---

# 28. `constants/`

Các constant dùng xuyên application:

```text
constants/
├── routes.ts
└── ...
```

Ví dụ:

```ts
ROUTES.ADMIN
ROUTES.CHAT
```

Mục tiêu là tránh rải string:

```ts
"/admin/knowledge-spaces"
```

khắp codebase.

---

# 29. `hooks/`

Chỉ dành cho hooks **thực sự global/shared**.

Ví dụ:

```text
useDebounce
useMediaQuery
```

Còn:

```text
useIngestionJobs
useKnowledgeSpaces
useConversations
```

phải nằm trong module tương ứng:

```text
modules/ingestion/hooks/
modules/knowledge-space/hooks/
modules/chat/hooks/
```

---

# 30. `types/`

Chỉ dành cho types dùng xuyên nhiều module.

Ví dụ:

```text
types/
├── api.ts
└── common.ts
```

Domain type:

```text
KnowledgeSpace
IngestionJob
Conversation
```

nên nằm trong module của nó:

```text
modules/knowledge-space/types/
modules/ingestion/types/
modules/chat/types/
```

Không biến `types/` thành một thư mục chứa tất cả type của hệ thống.

---

# 31. Data Flow

Một feature điển hình sẽ chạy như sau:

```text
Page
 ↓
Module Component
 ↓
Module Hook
 ↓
Module API
 ↓
lib/api/client
 ↓
Axios
 ↓
FastAPI
```

Response:

```text
FastAPI
 ↓
Axios
 ↓
TanStack Query
 ↓
Module Hook
 ↓
Component
```

---

# 32. Client State Flow

Ví dụ sidebar:

```text
AdminSidebar
      ↓
Redux
      ↓
appSlice
      ↓
sidebarCollapsed
```

Không cần API.

---

# 33. Server State Flow

Ví dụ ingestion jobs:

```text
IngestionPage
      ↓
useIngestionJobs()
      ↓
TanStack Query
      ↓
ingestion/api
      ↓
Axios
      ↓
FastAPI
```

Không đưa jobs vào Redux.

---

# 34. Form / Validation

Khi bắt đầu làm form thực tế, mình đề xuất:

```text
React Hook Form
+
Zod
```

Architecture:

```text
Form
 ↓
React Hook Form
 ↓
Zod schema
 ↓
API mutation
 ↓
TanStack Query
```

Mình **chưa cài hai package này**, vì chưa tới feature form đầu tiên.

Khi làm Knowledge Space hoặc Auth sẽ cài lúc đó.

---

# 35. Data Table

Admin sẽ có rất nhiều table:

```text
Documents
Sources
Jobs
Workers
Models
Users
```

Ta sẽ dùng:

```text
TanStack Table
```

khi bắt đầu xây table phức tạp.

shadcn `Table` đã có, nhưng:

```text
shadcn Table
```

chỉ là UI primitive.

Logic sorting/filtering/pagination sẽ do TanStack Table xử lý.

**Chưa cài TanStack Table**, vì chưa cần ở foundation.

---

# 36. Authentication

Chưa implement.

Nhưng architecture đã dành chỗ cho:

```text
modules/auth/
lib/auth/
store/slices/authSlice.ts
```

Sau này auth sẽ xử lý:

```text
Login
Logout
Current user
Access token
Refresh token
Permission
Role
```

Axios interceptor cũng sẽ được thiết kế ở `lib/api` khi auth flow được chốt.

Không hardcode token.

---

# 37. Dark Mode

shadcn foundation hiện đã có:

```text
:root
.dark
```

và CSS variables.

Nhưng **chưa cần dựng ThemeProvider ngay**.

Khi bắt đầu design shell, mình sẽ quyết định:

```text
system
light
dark
```

và cách persist preference.

---

# 38. Responsive

Admin và Chat đều phải responsive.

Admin:

```text
Desktop
Tablet
Mobile
```

Chat đặc biệt phải xử lý:

```text
Desktop
Conversation sidebar
Chat area

Mobile
Conversation sidebar → Sheet
Chat → full screen
```

`Sheet` đã được chuẩn bị cho việc này.

---

# 39. Không dùng microfrontend

Mặc dù platform có nhiều domain:

```text
Ingestion
RAG
Chat
Knowledge
Monitoring
```

mình **không tách thành nhiều frontend application**.

Hiện tại:

```text
Một Next.js application
        ↓
Modular architecture
```

Lợi ích:

* đơn giản deployment
* shared component dễ
* shared state dễ
* shared auth dễ
* UX nhất quán
* ít infrastructure overhead

Nếu một ngày quy mô thực sự yêu cầu microfrontend thì lúc đó mới cân nhắc.

---

# 40. Nguyên tắc quan trọng nhất

Từ giờ khi code feature, mình sẽ tuân thủ:

### 1. Không duplicate component

```text
Một component dùng chung
→ một implementation
```

### 2. Không đưa business logic vào `app/`

```text
app/
→ routing/composition
```

### 3. Domain nằm trong `modules/`

```text
modules/
→ business/UI domain
```

### 4. Shared phải thực sự shared

Không biến:

```text
components/shared
```

thành dumping ground.

### 5. Redux không phải API cache

```text
Redux
→ client state

TanStack Query
→ server state
```

### 6. Không mirror backend

Frontend domain architecture độc lập.

### 7. Không tạo folder trước khi cần

> **Làm tới đâu tạo tới đó.**

### 8. Không hardcode configuration

API URL, environment-specific config... dùng environment/config layer.

### 9. Không over-engineer

Chỉ thêm abstraction khi có lý do thực tế.

### 10. Mỗi feature phải có boundary rõ

Ví dụ:

```text
modules/ingestion/
```

có thể phát triển rất lớn mà không làm rối:

```text
modules/chat/
modules/document/
```

---

# 41. Kiến trúc tổng kết

Toàn bộ frontend có thể hình dung:

```text
                         PICO FRONTEND
                              │
                       Next.js 16 / React 19
                              │
                     ┌────────┴────────┐
                     │                 │
                  ADMIN              CHAT
                     │                 │
                     └────────┬────────┘
                              │
                         APP ROUTER
                              │
                         MODULES
                              │
       ┌────────┬─────────┬───┴────┬─────────┬────────┐
       │        │         │        │         │        │
      Auth   Knowledge   Source  Document  Ingestion Chat
               Space
                              │
                    ┌─────────┴─────────┐
                    │                   │
              Shared Components      Features
                    │                   │
                 shadcn             Module UI
                    │
              Tailwind CSS
                    │
           ┌────────┴────────┐
           │                 │
        Redux          TanStack Query
           │                 │
           └────────┬────────┘
                    │
                 Axios
                    │
              FastAPI :8000
```

**Đây là baseline mình đề xuất giữ lâu dài cho PICO FE.**

Và quan trọng: **chúng ta đã hoàn tất phần foundation/tooling.** Từ đây không nên tiếp tục “setup cho đẹp” nữa; bắt đầu code product thật. Bước hợp lý nhất là dựng **Admin Shell** trước, vì Sidebar/Topbar/Layout/Navigation sẽ trở thành nền cho toàn bộ Admin và giúp mình chốt luôn design language của platform.
