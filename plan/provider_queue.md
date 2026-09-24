CREATE TABLE public.queue_providers (
    id uuid NOT NULL DEFAULT gen_random_uuid(),

    code varchar(100) NOT NULL,
    name varchar(255) NOT NULL,
    description text NULL,

    enabled boolean NOT NULL DEFAULT true,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT queue_providers_pkey PRIMARY KEY (id),
    CONSTRAINT uq_queue_providers_code UNIQUE (code)
);

CREATE INDEX IF NOT EXISTS idx_queue_providers_enabled
    ON public.queue_providers (enabled);



//
CREATE TABLE public.knowledge_space_queues (
    id uuid NOT NULL DEFAULT gen_random_uuid(),

    knowledge_space_id uuid NOT NULL,
    queue_provider_id uuid NOT NULL,

    configuration jsonb NOT NULL DEFAULT '{}'::jsonb,

    is_default boolean NOT NULL DEFAULT false,
    enabled boolean NOT NULL DEFAULT true,

    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT knowledge_space_queues_pkey
        PRIMARY KEY (id),

    CONSTRAINT knowledge_space_queues_knowledge_space_id_fkey
        FOREIGN KEY (knowledge_space_id)
        REFERENCES public.knowledge_spaces (id)
        ON DELETE CASCADE,

    CONSTRAINT knowledge_space_queues_provider_id_fkey
        FOREIGN KEY (queue_provider_id)
        REFERENCES public.queue_providers (id),

    CONSTRAINT uq_knowledge_space_queue_provider
        UNIQUE (knowledge_space_id, queue_provider_id)
);





CREATE INDEX IF NOT EXISTS idx_knowledge_space_queues_knowledge_space
    ON public.knowledge_space_queues (knowledge_space_id);

CREATE INDEX IF NOT EXISTS idx_knowledge_space_queues_provider
    ON public.knowledge_space_queues (queue_provider_id);



CREATE UNIQUE INDEX IF NOT EXISTS uq_knowledge_space_default_queue
    ON public.knowledge_space_queues (knowledge_space_id)
    WHERE is_default = true;