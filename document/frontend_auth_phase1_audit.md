# Frontend Auth Phase 1 Architecture Audit

## Existing state mechanisms

| Mechanism | Current ownership | Provider / location | Auth decision |
| --- | --- | --- | --- |
| TanStack Query | Backend-owned server state | `src/providers/QueryProvider.tsx` | Own `/auth/me`, KS auth requirement, and auth mutation lifecycle/cache invalidation. |
| Redux Toolkit | Cross-application client UI state | `src/store/provider.tsx`, `src/store/slices/appSlice.ts` | Keep for app UI preferences such as sidebar state. Do not store users, sessions, tokens, or MFA state. |
| Zustand | Feature-scoped UI coordination | `src/modules/ingestion/store/ingestion.store.ts` | Existing usage is feature UI state. Auth does not currently need a Zustand store. |
| React local state | Component/form/transient state | Existing dialogs and feature components | Own email/password fields, password visibility, MFA code, validation messages, and temporary challenge data. |
| URL state | Current route/context | Next.js App Router and route/search params | Own the current `knowledgeSpaceId` and navigation destination. |

There is no need for a new Auth context, global Auth store, state library, or event bus.

## Providers

`src/app/layout.tsx` composes `AppProviders`. `AppProviders` installs the Redux
provider and TanStack Query provider once at the application root. Zustand stores
do not require a provider.

## API convention

- Shared Axios instance: `src/lib/api/client.ts`.
- Browser requests use the same-origin `/backend-api` rewrite.
- Server-side requests use `NEXT_PUBLIC_API_URL`.
- Feature API files own HTTP contracts and return `response.data`.
- Components do not call Axios directly.
- Auth cookie support belongs in the shared client through `withCredentials`, not
  in a second Auth-specific HTTP client.

## Query and mutation convention

- Query keys use a module-level hierarchical factory with an `all` root key.
- Queries and mutations live under each feature's `hooks` directory.
- Mutations invalidate the narrowest relevant query key after success.
- Auth will use one canonical key for `/auth/me` and one canonical parameterized
  key for each KS requirement.
- Login and MFA success will invalidate/refetch `/auth/me`; logout will remove or
  reset Auth-owned cached resources.

## Error handling

The repository has no shared API error parser or toast infrastructure. Existing
forms retain a local error string and display it inline. Auth should add only a
small feature-local error mapper if endpoint errors require consistent messages;
it should not introduce a parallel global error system.

## Existing reusable UI

- Inputs and forms: `Input`, `Label`, `Checkbox`, `Button`.
- Surfaces: `Card`, `Dialog`, `FormModal`, `AlertDialog`.
- Feedback: `ErrorState`, `Skeleton`, disabled/loading button patterns.
- Supporting controls: `Avatar`, `Badge`, `Separator`, `Tooltip`.
- Layout: existing `AdminShell`; Chat currently has a minimal route layout.

No form library is installed or used. Auth forms should follow the established
controlled-input and local-state pattern.

## Routing decisions

- App Router pages/layouts remain composition-only.
- Management login belongs under the admin route group but outside the protected
  `AdminShell` boundary.
- KS login and Chat protection derive `knowledgeSpaceId` from the URL.
- Login/protected transitions should use `router.replace`.
- The current navigation helper pattern in `src/config/navigation.ts` should be
  extended only when a route is reused in multiple places.

## Auth state ownership

| State | Owner | Reason |
| --- | --- | --- |
| Current session | TanStack Query | `/auth/me` is backend source of truth. |
| KS auth requirement | TanStack Query | Backend policy is authoritative. |
| Current KS ID | URL route parameter | Route is canonical navigation context. |
| Login email/password | React local state | Transient form input. |
| MFA challenge ID and code | React local/flow state | Short-lived flow data; never global persistence. |
| Sidebar preference | Redux Toolkit | Existing cross-layout client UI concern. |

## Constraints for later phases

- Do not store Microsoft tokens or application session tokens in browser state or
  storage; authentication remains HttpOnly-cookie based.
- Do not copy `/auth/me` data into Redux, Zustand, Context, or local storage.
- Do not create an Auth-specific Axios client.
- Do not add dependencies for state, HTTP, forms, or notifications.
- Reuse a single local login form, Microsoft login button, and MFA form across
  Management and Knowledge Space flows.
- Auth gates share pure context-check helpers while retaining separate Management
  and Knowledge Space boundary behavior.

