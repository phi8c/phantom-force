create table iam.audit_logs (
  id uuid not null default gen_random_uuid (),
  actor_user_id uuid null,
  action character varying(150) not null,
  target_type character varying(100) null,
  target_id uuid null,
  ip_address inet null,
  user_agent text null,
  device_fingerprint character varying(255) null,
  metadata jsonb null,
  occurred_at timestamp with time zone not null default now(),
  constraint audit_logs_pkey primary key (id),
  constraint audit_logs_actor_user_id_fkey foreign KEY (actor_user_id) references iam.users (id)
) TABLESPACE pg_default;

create index IF not exists idx_audit_logs_occurred on iam.audit_logs using btree (occurred_at desc) TABLESPACE pg_default;

create index IF not exists idx_audit_logs_actor on iam.audit_logs using btree (actor_user_id) TABLESPACE pg_default;

#######################################################

create table iam.auth_sessions (
  id uuid not null default gen_random_uuid (),
  user_id uuid not null,
  session_token_hash text not null,
  auth_method iam.auth_provider not null,
  ip_address inet null,
  user_agent text null,
  device_fingerprint character varying(255) null,
  issued_at timestamp with time zone not null default now(),
  last_seen_at timestamp with time zone not null default now(),
  idle_expires_at timestamp with time zone not null,
  absolute_expires_at timestamp with time zone not null,
  revoked_at timestamp with time zone null,
  revoked_reason character varying(64) null,
  constraint auth_sessions_pkey primary key (id),
  constraint auth_sessions_session_token_hash_key unique (session_token_hash),
  constraint auth_sessions_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_auth_sessions_user on iam.auth_sessions using btree (user_id) TABLESPACE pg_default
where
  (revoked_at is null);

create index IF not exists idx_auth_sessions_expiry on iam.auth_sessions using btree (idle_expires_at) TABLESPACE pg_default
where
  (revoked_at is null);

#######################################################

create table iam.auth_sessions (
  id uuid not null default gen_random_uuid (),
  user_id uuid not null,
  session_token_hash text not null,
  auth_method iam.auth_provider not null,
  ip_address inet null,
  user_agent text null,
  device_fingerprint character varying(255) null,
  issued_at timestamp with time zone not null default now(),
  last_seen_at timestamp with time zone not null default now(),
  idle_expires_at timestamp with time zone not null,
  absolute_expires_at timestamp with time zone not null,
  revoked_at timestamp with time zone null,
  revoked_reason character varying(64) null,
  constraint auth_sessions_pkey primary key (id),
  constraint auth_sessions_session_token_hash_key unique (session_token_hash),
  constraint auth_sessions_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_auth_sessions_user on iam.auth_sessions using btree (user_id) TABLESPACE pg_default
where
  (revoked_at is null);

create index IF not exists idx_auth_sessions_expiry on iam.auth_sessions using btree (idle_expires_at) TABLESPACE pg_default
where
  (revoked_at is null);

#######################################################

create table iam.credentials (
  user_id uuid not null,
  password_hash text not null,
  password_algo character varying(32) not null default 'argon2id'::character varying,
  password_changed_at timestamp with time zone not null default now(),
  failed_attempts smallint not null default 0,
  locked_until timestamp with time zone null,
  mfa_enabled boolean not null default false,
  mfa_secret_encrypted text null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint credentials_pkey primary key (user_id),
  constraint credentials_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create trigger trg_credentials_updated_at BEFORE
update on iam.credentials for EACH row
execute FUNCTION iam.set_updated_at ();

create table iam.identity_links (
  id uuid not null default gen_random_uuid (),
  user_id uuid not null,
  provider iam.auth_provider not null,
  external_sub character varying(255) not null,
  tenant_id character varying(255) null,
  email_at_link public.citext not null,
  linked_at timestamp with time zone not null default now(),
  constraint identity_links_pkey primary key (id),
  constraint identity_links_provider_external_sub_key unique (provider, external_sub),
  constraint identity_links_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_identity_links_user on iam.identity_links using btree (user_id) TABLESPACE pg_default;

create table iam.mfa_recovery_codes (
  id uuid not null default gen_random_uuid (),
  user_id uuid not null,
  code_hash text not null,
  used_at timestamp with time zone null,
  created_at timestamp with time zone not null default now(),
  constraint mfa_recovery_codes_pkey primary key (id),
  constraint mfa_recovery_codes_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_mfa_recovery_codes_user on iam.mfa_recovery_codes using btree (user_id) TABLESPACE pg_default
where
  (used_at is null);

create table iam.password_history (
  id uuid not null default gen_random_uuid (),
  user_id uuid not null,
  password_hash text not null,
  created_at timestamp with time zone not null default now(),
  constraint password_history_pkey primary key (id),
  constraint password_history_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_password_history_user on iam.password_history using btree (user_id, created_at desc) TABLESPACE pg_default;

create table iam.permissions (
  id uuid not null default gen_random_uuid (),
  code character varying(100) not null,
  resource_type character varying(100) not null,
  action character varying(100) not null,
  description text null,
  created_at timestamp with time zone not null default now(),
  constraint permissions_pkey primary key (id),
  constraint permissions_code_key unique (code)
) TABLESPACE pg_default;

create index IF not exists idx_permissions_resource_action on iam.permissions using btree (resource_type, action) TABLESPACE pg_default;

create table iam.policies (
  id uuid not null default gen_random_uuid (),
  name character varying(150) not null,
  effect iam.policy_effect not null,
  resource_type character varying(100) not null,
  action character varying(100) not null,
  priority smallint not null default 0,
  is_active boolean not null default true,
  created_by uuid null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint policies_pkey primary key (id),
  constraint policies_name_key unique (name),
  constraint policies_created_by_fkey foreign KEY (created_by) references iam.users (id)
) TABLESPACE pg_default;

create index IF not exists idx_policies_lookup on iam.policies using btree (resource_type, action) TABLESPACE pg_default
where
  (is_active = true);

create trigger trg_policies_updated_at BEFORE
update on iam.policies for EACH row
execute FUNCTION iam.set_updated_at ();

create table iam.policy_conditions (
  id uuid not null default gen_random_uuid (),
  policy_id uuid not null,
  attribute_path character varying(150) not null,
  operator iam.policy_operator not null,
  value jsonb not null,
  constraint policy_conditions_pkey primary key (id),
  constraint policy_conditions_policy_id_fkey foreign KEY (policy_id) references iam.policies (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_policy_conditions_policy on iam.policy_conditions using btree (policy_id) TABLESPACE pg_default;

create table iam.refresh_tokens (
  id uuid not null default gen_random_uuid (),
  session_id uuid not null,
  token_hash text not null,
  issued_at timestamp with time zone not null default now(),
  expires_at timestamp with time zone not null,
  used_at timestamp with time zone null,
  revoked_at timestamp with time zone null,
  replaced_by uuid null,
  constraint refresh_tokens_pkey primary key (id),
  constraint refresh_tokens_token_hash_key unique (token_hash),
  constraint refresh_tokens_replaced_by_fkey foreign KEY (replaced_by) references iam.refresh_tokens (id),
  constraint refresh_tokens_session_id_fkey foreign KEY (session_id) references iam.auth_sessions (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_refresh_tokens_session on iam.refresh_tokens using btree (session_id) TABLESPACE pg_default;

create table iam.role_permissions (
  role_id uuid not null,
  permission_id uuid not null,
  constraint role_permissions_pkey primary key (role_id, permission_id),
  constraint role_permissions_permission_id_fkey foreign KEY (permission_id) references iam.permissions (id) on delete CASCADE,
  constraint role_permissions_role_id_fkey foreign KEY (role_id) references iam.roles (id) on delete CASCADE
) TABLESPACE pg_default;

create table iam.roles (
  id uuid not null default gen_random_uuid (),
  name character varying(100) not null,
  description text null,
  source iam.role_source not null default 'system'::iam.role_source,
  external_role_value character varying(255) null,
  is_protected boolean not null default false,
  created_by uuid null,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  constraint roles_pkey primary key (id),
  constraint roles_name_key unique (name),
  constraint roles_created_by_fkey foreign KEY (created_by) references iam.users (id)
) TABLESPACE pg_default;

create trigger trg_roles_updated_at BEFORE
update on iam.roles for EACH row
execute FUNCTION iam.set_updated_at ();

create table iam.user_roles (
  user_id uuid not null,
  role_id uuid not null,
  source iam.role_assignment_source not null default 'manual'::iam.role_assignment_source,
  assigned_by uuid null,
  assigned_at timestamp with time zone not null default now(),
  constraint user_roles_pkey primary key (user_id, role_id),
  constraint user_roles_assigned_by_fkey foreign KEY (assigned_by) references iam.users (id),
  constraint user_roles_role_id_fkey foreign KEY (role_id) references iam.roles (id) on delete CASCADE,
  constraint user_roles_user_id_fkey foreign KEY (user_id) references iam.users (id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_user_roles_user on iam.user_roles using btree (user_id) TABLESPACE pg_default;

create table iam.users (
  id uuid not null default gen_random_uuid (),
  email public.citext not null,
  email_verified_at timestamp with time zone null,
  full_name character varying(255) null,
  status iam.user_status not null default 'pending_verification'::iam.user_status,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone not null default now(),
  deleted_at timestamp with time zone null,
  constraint users_pkey primary key (id),
  constraint users_email_key unique (email)
) TABLESPACE pg_default;

create index IF not exists idx_users_status on iam.users using btree (status) TABLESPACE pg_default
where
  (deleted_at is null);

create trigger trg_users_updated_at BEFORE
update on iam.users for EACH row
execute FUNCTION iam.set_updated_at ();



BEGIN;

-- ============================================================
-- 1. AUTH SESSION CONTEXT
--
-- Một session thuộc đúng một security context:
--
-- MANAGEMENT:
--   Admin / Manager sử dụng Management Plane.
--
-- KNOWLEDGE_SPACE:
--   End-user sử dụng Chat Plane và session chỉ có giá trị
--   đối với Knowledge Space đã authenticate.
-- ============================================================

ALTER TABLE iam.auth_sessions
    ADD COLUMN IF NOT EXISTS context_type varchar(32)
        NOT NULL DEFAULT 'MANAGEMENT',

    ADD COLUMN IF NOT EXISTS knowledge_space_id uuid NULL,

    ADD COLUMN IF NOT EXISTS identity_link_id uuid NULL,

    ADD COLUMN IF NOT EXISTS authenticated_at timestamptz
        NOT NULL DEFAULT now(),

    ADD COLUMN IF NOT EXISTS mfa_verified_at timestamptz NULL;


-- ------------------------------------------------------------
-- Context type
-- ------------------------------------------------------------

ALTER TABLE iam.auth_sessions
    DROP CONSTRAINT IF EXISTS ck_auth_sessions_context_type;

ALTER TABLE iam.auth_sessions
    ADD CONSTRAINT ck_auth_sessions_context_type
    CHECK (
        context_type IN (
            'MANAGEMENT',
            'KNOWLEDGE_SPACE'
        )
    );


-- ------------------------------------------------------------
-- MANAGEMENT:
--     knowledge_space_id MUST be NULL
--
-- KNOWLEDGE_SPACE:
--     knowledge_space_id MUST NOT be NULL
-- ------------------------------------------------------------

ALTER TABLE iam.auth_sessions
    DROP CONSTRAINT IF EXISTS ck_auth_sessions_context_scope;

ALTER TABLE iam.auth_sessions
    ADD CONSTRAINT ck_auth_sessions_context_scope
    CHECK (
        (
            context_type = 'MANAGEMENT'
            AND knowledge_space_id IS NULL
        )
        OR
        (
            context_type = 'KNOWLEDGE_SPACE'
            AND knowledge_space_id IS NOT NULL
        )
    );


-- ------------------------------------------------------------
-- Knowledge Space FK
-- ------------------------------------------------------------

ALTER TABLE iam.auth_sessions
    DROP CONSTRAINT IF EXISTS fk_auth_sessions_knowledge_space;

ALTER TABLE iam.auth_sessions
    ADD CONSTRAINT fk_auth_sessions_knowledge_space
    FOREIGN KEY (knowledge_space_id)
    REFERENCES public.knowledge_spaces(id)
    ON DELETE CASCADE;


-- ------------------------------------------------------------
-- External identity used to establish this session.
--
-- NULL is valid for LOCAL authentication.
-- Entra session can reference iam.identity_links.
-- ------------------------------------------------------------

ALTER TABLE iam.auth_sessions
    DROP CONSTRAINT IF EXISTS fk_auth_sessions_identity_link;

ALTER TABLE iam.auth_sessions
    ADD CONSTRAINT fk_auth_sessions_identity_link
    FOREIGN KEY (identity_link_id)
    REFERENCES iam.identity_links(id)
    ON DELETE SET NULL;


-- ------------------------------------------------------------
-- Session indexes
-- ------------------------------------------------------------

CREATE INDEX IF NOT EXISTS idx_auth_sessions_context
    ON iam.auth_sessions (
        context_type,
        knowledge_space_id
    )
    WHERE revoked_at IS NULL;


CREATE INDEX IF NOT EXISTS idx_auth_sessions_knowledge_space_user
    ON iam.auth_sessions (
        knowledge_space_id,
        user_id
    )
    WHERE context_type = 'KNOWLEDGE_SPACE'
      AND revoked_at IS NULL;


CREATE INDEX IF NOT EXISTS idx_auth_sessions_identity_link
    ON iam.auth_sessions(identity_link_id)
    WHERE identity_link_id IS NOT NULL
      AND revoked_at IS NULL;


-- ============================================================
-- 2. KNOWLEDGE SPACE AUTHENTICATION POLICY
--
-- Authentication ONLY.
--
-- Không chứa:
--   role
--   permission
--   sensitivity
--   SharePoint ACL
--
-- Những thứ trên thuộc Authorization phase sau.
-- ============================================================

CREATE TABLE IF NOT EXISTS iam.knowledge_space_auth_policies (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    knowledge_space_id uuid NOT NULL,

    -- LOCAL
    -- MICROSOFT_ENTRA
    auth_method varchar(32) NOT NULL,

    -- Required đối với MICROSOFT_ENTRA.
    -- NULL đối với LOCAL.
    tenant_id varchar(255) NULL,

    require_mfa boolean NOT NULL DEFAULT false,

    -- Security/session policy riêng của KS.
    idle_timeout_minutes integer NOT NULL DEFAULT 30,

    absolute_timeout_minutes integer NOT NULL DEFAULT 480,

    -- Có thể disable policy mà không xóa lịch sử/config.
    is_active boolean NOT NULL DEFAULT true,

    created_by uuid NULL,

    created_at timestamptz NOT NULL DEFAULT now(),

    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT uq_knowledge_space_auth_policy
        UNIQUE (knowledge_space_id),

    CONSTRAINT fk_ks_auth_policy_knowledge_space
        FOREIGN KEY (knowledge_space_id)
        REFERENCES public.knowledge_spaces(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_ks_auth_policy_created_by
        FOREIGN KEY (created_by)
        REFERENCES iam.users(id)
        ON DELETE SET NULL,

    CONSTRAINT ck_ks_auth_method
        CHECK (
            auth_method IN (
                'LOCAL',
                'MICROSOFT_ENTRA'
            )
        ),

    CONSTRAINT ck_ks_auth_timeout
        CHECK (
            idle_timeout_minutes > 0
            AND absolute_timeout_minutes > 0
            AND idle_timeout_minutes <= absolute_timeout_minutes
        ),

    CONSTRAINT ck_ks_auth_tenant
        CHECK (
            (
                auth_method = 'LOCAL'
                AND tenant_id IS NULL
            )
            OR
            (
                auth_method = 'MICROSOFT_ENTRA'
                AND tenant_id IS NOT NULL
            )
        )
);


CREATE INDEX IF NOT EXISTS idx_ks_auth_policy_active
    ON iam.knowledge_space_auth_policies(knowledge_space_id)
    WHERE is_active = true;


CREATE INDEX IF NOT EXISTS idx_ks_auth_policy_method
    ON iam.knowledge_space_auth_policies(auth_method)
    WHERE is_active = true;


-- ============================================================
-- 3. MANAGEMENT AUTHENTICATION POLICY
--
-- Management Plane hoàn toàn độc lập với Knowledge Space.
--
-- Admin / Manager bắt buộc đi qua policy này.
--
-- Không được dùng KS session để truy cập Management Plane.
-- ============================================================

CREATE TABLE IF NOT EXISTS iam.management_auth_policy (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),

    auth_method varchar(32)
        NOT NULL DEFAULT 'LOCAL',

    tenant_id varchar(255) NULL,

    -- Management mặc định yêu cầu MFA.
    require_mfa boolean NOT NULL DEFAULT true,

    -- Management security chặt hơn Chat Plane.
    idle_timeout_minutes integer NOT NULL DEFAULT 15,

    absolute_timeout_minutes integer NOT NULL DEFAULT 480,

    -- Sensitive operation:
    -- role changes
    -- security settings
    -- authentication settings
    -- user management
    -- etc.
    --
    -- Có thể yêu cầu recent authentication.
    reauthentication_minutes integer NOT NULL DEFAULT 15,

    is_active boolean NOT NULL DEFAULT true,

    created_at timestamptz NOT NULL DEFAULT now(),

    updated_at timestamptz NOT NULL DEFAULT now(),

    CONSTRAINT ck_management_auth_method
        CHECK (
            auth_method IN (
                'LOCAL',
                'MICROSOFT_ENTRA'
            )
        ),

    CONSTRAINT ck_management_auth_timeout
        CHECK (
            idle_timeout_minutes > 0
            AND absolute_timeout_minutes > 0
            AND idle_timeout_minutes <= absolute_timeout_minutes
            AND reauthentication_minutes > 0
            AND reauthentication_minutes <= absolute_timeout_minutes
        ),

    CONSTRAINT ck_management_auth_tenant
        CHECK (
            (
                auth_method = 'LOCAL'
                AND tenant_id IS NULL
            )
            OR
            (
                auth_method = 'MICROSOFT_ENTRA'
                AND tenant_id IS NOT NULL
            )
        )
);


-- Hiện tại một deployment/enterprise chỉ có một
-- active Management Authentication Policy.
CREATE UNIQUE INDEX IF NOT EXISTS uq_management_auth_policy_active
    ON iam.management_auth_policy ((1))
    WHERE is_active = true;


-- ============================================================
-- 4. UPDATED_AT TRIGGERS
--
-- Project đã có iam.set_updated_at().
-- ============================================================

DROP TRIGGER IF EXISTS trg_ks_auth_policy_updated_at
    ON iam.knowledge_space_auth_policies;

CREATE TRIGGER trg_ks_auth_policy_updated_at
BEFORE UPDATE
ON iam.knowledge_space_auth_policies
FOR EACH ROW
EXECUTE FUNCTION iam.set_updated_at();


DROP TRIGGER IF EXISTS trg_management_auth_policy_updated_at
    ON iam.management_auth_policy;

CREATE TRIGGER trg_management_auth_policy_updated_at
BEFORE UPDATE
ON iam.management_auth_policy
FOR EACH ROW
EXECUTE FUNCTION iam.set_updated_at();


COMMIT;