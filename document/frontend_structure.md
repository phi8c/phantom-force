frontend/
│
├── public/
│   ├── images/
│   ├── icons/
│   └── ...
│
├── src/
│   │
│   ├── app/
│   │   │
│   │   ├── (auth)/
│   │   │   └── login/
│   │   │       └── page.tsx
│   │   │
│   │   ├── (admin)/
│   │   │   └── admin/
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       │
│   │   │       ├── knowledge-spaces/
│   │   │       │   └── page.tsx
│   │   │       │
│   │   │       ├── sources/
│   │   │       │   └── page.tsx
│   │   │       │
│   │   │       ├── documents/
│   │   │       │   └── page.tsx
│   │   │       │
│   │   │       ├── ingestion/
│   │   │       │   └── page.tsx
│   │   │       │
│   │   │       ├── workers/
│   │   │       │   └── page.tsx
│   │   │       │
│   │   │       ├── models/
│   │   │       │   └── page.tsx
│   │   │       │
│   │   │       └── settings/
│   │   │           └── page.tsx
│   │   │
│   │   ├── (chat)/
│   │   │   └── chat/
│   │   │       ├── layout.tsx
│   │   │       ├── page.tsx
│   │   │       └── [conversationId]/
│   │   │           └── page.tsx
│   │   │
│   │   ├── api/
│   │   │   └── ...
│   │   │
│   │   ├── favicon.ico
│   │   ├── globals.css
│   │   ├── layout.tsx
│   │   └── page.tsx
│   │
│   ├── modules/
│   │   │
│   │   ├── auth/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── knowledge-space/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── source/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── document/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   ├── ingestion/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   ├── constants/
│   │   │   └── index.ts
│   │   │
│   │   ├── chat/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   ├── utils/
│   │   │   └── index.ts
│   │   │
│   │   ├── model/
│   │   │   ├── api/
│   │   │   ├── components/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── types/
│   │   │   └── index.ts
│   │   │
│   │   └── settings/
│   │       ├── api/
│   │       ├── components/
│   │       ├── hooks/
│   │       ├── schemas/
│   │       ├── types/
│   │       └── index.ts
│   │
│   ├── components/
│   │   │
│   │   ├── ui/
│   │   │   ├── button.tsx
│   │   │   ├── input.tsx
│   │   │   ├── dialog.tsx
│   │   │   ├── table.tsx
│   │   │   └── ...
│   │   │
│   │   ├── layout/
│   │   │   ├── app-shell/
│   │   │   ├── admin-shell/
│   │   │   └── chat-shell/
│   │   │
│   │   └── shared/
│   │       ├── data-table/
│   │       ├── empty-state/
│   │       ├── error-state/
│   │       ├── loading-state/
│   │       ├── page-header/
│   │       └── ...
│   │
│   ├── store/
│   │   ├── slices/
│   │   │   ├── appSlice.ts
│   │   │   ├── authSlice.ts
│   │   │   └── ...
│   │   ├── index.ts
│   │   └── provider.tsx
│   │
│   ├── providers/
│   │   ├── AppProviders.tsx
│   │   └── QueryProvider.tsx
│   │
│   ├── lib/
│   │   ├── api/
│   │   │   ├── client.ts
│   │   │   ├── errors.ts
│   │   │   └── ...
│   │   ├── auth/
│   │   ├── storage/
│   │   ├── utils/
│   │   └── ...
│   │
│   ├── config/
│   │   ├── app.ts
│   │   ├── navigation.ts
│   │   └── ...
│   │
│   ├── constants/
│   │   ├── routes.ts
│   │   └── ...
│   │
│   ├── hooks/
│   │   ├── use-debounce.ts
│   │   ├── use-media-query.ts
│   │   └── ...
│   │
│   └── types/
│       ├── api.ts
│       └── common.ts
│
├── .env.local
├── components.json
├── eslint.config.mjs
├── next.config.ts
├── package.json
├── postcss.config.mjs
├── tsconfig.json
└── ...