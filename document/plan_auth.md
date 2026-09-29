PHASE: COMPLETE USER + AUTHENTICATION BACKEND
LOCAL AUTH + MICROSOFT ENTRA SSO + SECURE SESSION

MỤC TIÊU

Hoàn thiện backend User/Auth hiện tại theo architecture và DB đã có.

Sau phase này BACKEND phải hoàn chỉnh:

LOCAL:
- register
- email verification
- login
- MFA flow nếu policy yêu cầu
- session creation/resolution
- /me
- logout
- logout all

MICROSOFT ENTRA:
- SSO authorization start
- backend callback
- OIDC validation
- tenant validation
- canonical user resolution/provisioning
- iam.identity_links
- session creation
- /me
- logout application session

SESSION:
- MANAGEMENT context
- KNOWLEDGE_SPACE context
- idle timeout
- absolute timeout
- revocation
- MFA assurance
- context enforcement
- KS binding

Không implement Role/Permission/KS Membership/Ingestion/Retrieval trong phase này.

============================================================
0. INSPECT SOURCE TRƯỚC KHI CODE
============================================================

Inspect kỹ:

backend/module/auth/
backend/module/user/
backend/module/knowledge_space/

và:
- composition/bootstrap hiện tại
- auth presentation/controllers/dependencies
- AuthSession domain/model/mapper/repository
- Credential
- IdentityLink
- VerificationToken
- MFA contracts/providers/store
- OIDC contracts/providers
- password hasher
- token service
- lockout policy
- audit infrastructure/contracts
- UserModuleFacade/public boundary
- Knowledge Space public/composition boundary
- settings hiện có cho Microsoft Entra

Không viết lại abstraction đã tồn tại.

Trước khi implementation, report ngắn:

1. component nào đã có và sẽ reuse;
2. component nào thiếu;
3. files dự kiến create/modify;
4. conflict nào giữa source hiện tại và DB mới.

Nếu không có blocker thật sự thì implementation tiếp.

============================================================
1. ARCHITECTURE ĐÃ CHỐT
============================================================

Authentication có hai security contexts riêng.

---------------------------
A. MANAGEMENT
---------------------------

Dành cho Admin/Manager vận hành platform.

Management user:
→ authenticate bằng policy MANAGEMENT
→ tạo MANAGEMENT session
→ mới được truy cập Management/Admin APIs/UI.

MANAGEMENT session:

context_type = MANAGEMENT
knowledge_space_id = NULL

Chat-user session tuyệt đối không được dùng cho Management API.

Không dùng frontend hide menu làm security boundary.
Backend phải enforce.

---------------------------
B. KNOWLEDGE_SPACE
---------------------------

Dành cho end-user sử dụng Chat.

User truy cập/chọn một Knowledge Space:

→ backend đọc authentication policy của KS
→ policy quyết định LOCAL hay MICROSOFT_ENTRA
→ user authenticate theo policy đó
→ tạo KNOWLEDGE_SPACE session
→ session bound với đúng KS đó
→ user mới có authentication context để vào Chat Plane.

KNOWLEDGE_SPACE session:

context_type = KNOWLEDGE_SPACE
knowledge_space_id = selected KS

KS-A session không được dùng cho KS-B.

NOTE:
Authentication thành công CHƯA đồng nghĩa user được authorize vào KS.

KS Membership + Role/Permission là phase sau.

============================================================
2. USER LÀ CANONICAL IDENTITY
============================================================

iam.users tiếp tục là canonical user.

Không tạo:
- LocalUser
- MicrosoftUser
- KnowledgeSpaceUser

thành các user độc lập.

Mô hình:

iam.users
   |
   +-- iam.credentials
   |      LOCAL authentication
   |
   +-- iam.identity_links
          external identities
          Microsoft Entra etc.

Một user có thể có nhiều authentication identities.

Không thêm is_admin vào iam.users.

Admin/Manager sau này được xác định bằng authorization/roles,
không bằng boolean field.

============================================================
3. DATABASE ĐÃ MIGRATE - PHẢI SYNC PERSISTENCE
============================================================

DB migration đã chạy.
KHÔNG tạo raw SQL/migration mới.

iam.auth_sessions đã thêm:

- context_type varchar(32) NOT NULL
- knowledge_space_id uuid NULL
- identity_link_id uuid NULL
- authenticated_at timestamptz NOT NULL
- mfa_verified_at timestamptz NULL

FK:

knowledge_space_id
→ public.knowledge_spaces(id)

identity_link_id
→ iam.identity_links(id)

Invariant DB:

MANAGEMENT:
knowledge_space_id IS NULL

KNOWLEDGE_SPACE:
knowledge_space_id IS NOT NULL


Source hiện tại vẫn map AuthSession schema cũ.

PHẢI update đồng bộ:

- AuthSession domain entity
- AuthSessionModel
- AuthSessionMapper
- AuthSessionRepository implementation nếu cần
- DTO/application models liên quan

Không được chỉ sửa SQLAlchemy model.


DB mới:

iam.knowledge_space_auth_policies

fields:

id
knowledge_space_id
auth_method
tenant_id
require_mfa
idle_timeout_minutes
absolute_timeout_minutes
is_active
created_by
created_at
updated_at


DB mới:

iam.management_auth_policy

fields:

id
auth_method
tenant_id
require_mfa
idle_timeout_minutes
absolute_timeout_minutes
reauthentication_minutes
is_active
created_at
updated_at


Tạo persistence đầy đủ cho hai bảng:

domain entity
→ repository contract
→ SQLAlchemy model
→ mapper
→ repository implementation
→ composition wiring

NO RAW SQL.

Dùng SQLAlchemy ORM/select theo pattern repository hiện tại.

============================================================
4. DOMAIN MODEL
============================================================

Không magic string rải khắp source.

Có domain representation rõ cho:

AuthenticationContextType:
- MANAGEMENT
- KNOWLEDGE_SPACE

Authentication method/provider phải reuse abstraction hiện có.

Source hiện đã có naming provider như:
local
entra
google

Trong policy DB hiện dùng:
LOCAL
MICROSOFT_ENTRA

KHÔNG tạo hai hệ provider domain trùng nghĩa.

Tạo mapping tại persistence/application boundary.

Tạo domain entities:

KnowledgeSpaceAuthPolicy
ManagementAuthPolicy

Business invariant nằm domain/application,
không nằm controller.

============================================================
5. AUTH SESSION DOMAIN
============================================================

AuthSession phải biểu diễn:

user_id
session_token_hash
auth_method

context_type
knowledge_space_id
identity_link_id

authenticated_at
mfa_verified_at

issued_at
last_seen_at
idle_expires_at
absolute_expires_at

revoked_at
revoked_reason

và metadata hiện có như:
IP
user-agent
device fingerprint

AuthSession creation phải enforce:

MANAGEMENT
→ knowledge_space_id == None

KNOWLEDGE_SPACE
→ knowledge_space_id != None

identity_link_id:
- LOCAL thường None
- ENTRA phải reference external identity dùng để authenticate.

mfa_verified_at:
chỉ set SAU khi MFA thực sự verify thành công.

authenticated_at:
thời điểm authentication thành công.

============================================================
6. POLICY RESOLUTION
============================================================

Tạo application abstraction/service rõ ràng, ví dụ:

AuthenticationPolicyResolver

resolve_management_policy()

resolve_knowledge_space_policy(
    knowledge_space_id
)

Không để controller query policy.

Không để login use case biết SQLAlchemy table.

Không cho client tự quyết auth method.

Server luôn derive auth method từ persisted policy.

Ví dụ:

GET/START authentication cho KS-X
→ load KS-X policy
→ policy LOCAL
→ chỉ LOCAL flow hợp lệ.

Nếu client cố gọi Microsoft flow cho LOCAL KS:
→ reject.

Nếu policy MICROSOFT_ENTRA:
→ local login không được bypass.

Missing/inactive policy:
→ fail closed.

============================================================
7. CROSS-MODULE RULE
============================================================

Giữa module phải đi qua public contract/facade/composition.

Auth application/domain KHÔNG được import:

knowledge_space.infrastructure.*
knowledge_space.*repository_impl
knowledge_space SQLAlchemy model

Nếu Auth cần verify KS tồn tại:
→ use Knowledge Space public facade/contract.

Nếu facade hiện tại thiếu operation tối thiểu:
→ mở rộng public contract hợp lý
→ wire qua composition.

Không phá module boundary.

SQLAlchemy FK tới:

public.knowledge_spaces.id

là persistence concern,
không phải lý do để application coupling infrastructure KS.

============================================================
8. LOCAL REGISTER
============================================================

Reuse RegisterLocalUserUseCase hiện có.

Không rewrite nếu logic hiện tại đúng.

Flow:

register
→ validate input
→ create canonical iam.users
→ create credential
→ Argon2id password hashing
→ create verification token
→ DB chỉ lưu HASH của verification token
→ dispatch verification delivery
→ user verify email
→ activate/verify account

Không:
- lưu plaintext password
- lưu plaintext verification token
- log token
- trả token production response.

============================================================
9. EMAIL VERIFICATION
============================================================

Hiện register đã tạo verification token nhưng lifecycle chưa hoàn chỉnh.

Implement complete:

verification request
→ token lookup/validation
→ expiry validation
→ one-time consumption
→ mark email verified
→ transition user status đúng domain rule

Token:
- cryptographically secure
- DB stores hash only
- one-time
- expires
- replay rejected.

Email delivery phải qua abstraction.

Ví dụ:

VerificationEmailSender

Không SMTP trực tiếp trong use case.

Nếu production mail provider chưa có:
→ tạo adapter/dev implementation phù hợp architecture.

Không hard-code provider-specific logic vào application.

============================================================
10. LOCAL MANAGEMENT LOGIN
============================================================

Flow:

Management login
→ resolve active ManagementAuthPolicy
→ policy.auth_method phải cho LOCAL
→ resolve canonical user
→ verify credential/password
→ account status
→ lockout policy
→ MFA requirement
→ authentication complete
→ create MANAGEMENT session

Session:

context_type = MANAGEMENT
knowledge_space_id = NULL

Timeout lấy từ ManagementAuthPolicy:

idle_timeout_minutes
absolute_timeout_minutes

Không hard-code timeout nếu policy đã cung cấp.

============================================================
11. LOCAL KNOWLEDGE SPACE LOGIN
============================================================

Flow:

selected knowledge_space_id
→ verify KS exists
→ resolve KnowledgeSpaceAuthPolicy
→ policy active?
→ auth_method == LOCAL?
→ local credential authentication
→ MFA nếu policy yêu cầu
→ create KNOWLEDGE_SPACE session

Session:

context_type = KNOWLEDGE_SPACE
knowledge_space_id = selected KS

Timeout lấy từ KS policy.

Không cho request truyền context_type tùy ý.

Endpoint/use case quyết định context.

============================================================
12. MFA
============================================================

Reuse MFA contracts/providers/store hiện có.

Correct flow:

primary authentication
        ↓
MFA required?
        ↓
YES
        ↓
create short-lived challenge
        ↓
client verifies challenge
        ↓
MFA success
        ↓
create/finalize authenticated session

Không tạo fully-authenticated session trước MFA.

MFA challenge phải bound với:

- user_id
- intended context_type
- intended auth method
- knowledge_space_id nếu KNOWLEDGE_SPACE
- expiration
- one-time state

Challenge phải:
- short TTL
- one-time
- replay protected.

Nếu management policy require_mfa=true
nhưng user chưa enroll MFA:

→ return explicit MFA_ENROLLMENT_REQUIRED state

KHÔNG bypass MFA.

mfa_verified_at chỉ set khi challenge thực sự pass.

============================================================
13. MICROSOFT ENTRA SSO - COMPLETE BACKEND FLOW
============================================================

ĐÂY KHÔNG PHẢI FOUNDATION/TODO.

Sau phase này Entra backend flow phải hoàn chỉnh.

Reuse OIDC abstraction hiện có.

Provider-specific Microsoft implementation nằm infrastructure.

Application/use case không gọi Microsoft SDK/API trực tiếp.

Controller không chứa OIDC business logic.

---------------------------
13A. START FLOW
---------------------------

Knowledge Space:

request SSO start for KS
→ verify KS
→ resolve KS auth policy
→ require MICROSOFT_ENTRA
→ get expected tenant_id
→ create secure authorization transaction
→ generate state
→ generate nonce
→ PKCE nếu architecture/provider flow sử dụng
→ build Microsoft authorization URL
→ redirect/return redirect URL theo presentation design.

Transaction phải bound:

- context_type = KNOWLEDGE_SPACE
- knowledge_space_id
- expected tenant
- state
- nonce
- expiry

Management:

→ resolve ManagementAuthPolicy
→ require MICROSOFT_ENTRA
→ same principle
→ context_type = MANAGEMENT.

---------------------------
13B. CALLBACK
---------------------------

Microsoft redirects tới BACKEND callback.

Không callback security logic ở frontend.

Backend callback phải:

1. validate state
2. reject expired/replayed auth transaction
3. exchange authorization code server-side
4. validate ID token:
   - signature
   - issuer
   - audience/client ID
   - expiry/not-before
   - nonce
   - expected tenant
5. extract verified external identity
6. resolve iam.identity_links
7. resolve/provision canonical iam.users
8. enforce account status
9. MFA nếu policy yêu cầu thêm
10. create correct AuthSession
11. set secure application session cookie
12. redirect frontend tới safe configured destination.

Không redirect tùy arbitrary URL client cung cấp.
Chống open redirect.

============================================================
14. ENTRA IDENTITY LINKING / PROVISIONING
============================================================

Không dùng email làm immutable external identity.

Use verified:
- provider
- tenant
- subject/object identity phù hợp OIDC contract.

iam.identity_links là source mapping:

external identity
→ canonical iam.users

Existing identity link:
→ resolve same user.

Unlinked Entra identity:
→ provision/link theo explicit application service/rule.

KHÔNG tự merge với existing local user chỉ vì email giống nhau.

Email-only auto-link có account takeover risk.

Nếu chưa có safe explicit linking proof:
→ không merge.

Không tạo duplicate identity link khi callback retry/concurrent login.

Handle race/idempotency đúng repository/DB constraint.

============================================================
15. MANAGEMENT ENTRA LOGIN
============================================================

ManagementAuthPolicy:

auth_method = MICROSOFT_ENTRA
tenant_id = configured tenant

Flow:

Management SSO start
→ Entra
→ backend callback
→ validate expected tenant
→ canonical user
→ management security/MFA policy
→ MANAGEMENT session

Session:

context_type = MANAGEMENT
knowledge_space_id = NULL
identity_link_id = resolved Entra identity

Không dùng KS policy cho Management.

============================================================
16. KNOWLEDGE SPACE ENTRA LOGIN
============================================================

KnowledgeSpaceAuthPolicy:

auth_method = MICROSOFT_ENTRA
tenant_id = expected tenant

Flow:

KS SSO start
→ policy
→ Entra
→ backend callback
→ tenant validation
→ canonical user
→ MFA policy nếu cần
→ KNOWLEDGE_SPACE session

Session:

context_type = KNOWLEDGE_SPACE
knowledge_space_id = selected KS
identity_link_id = resolved Entra identity

Session của KS-A không authenticate KS-B.

============================================================
17. SERVER-SIDE SESSION ARCHITECTURE
============================================================

GIỮ architecture hiện tại:

opaque server-side session token.

KHÔNG redesign thành JWT access/refresh.

iam.refresh_tokens tồn tại nhưng không được lấy làm lý do
để thay architecture trong phase này.

Session token:

- high entropy CSPRNG
- raw token chỉ ở client cookie
- DB chỉ lưu hash
- HttpOnly
- Secure
- appropriate SameSite
- appropriate Path/Domain
- no token logging.

Resolve session server-side mỗi authenticated request theo architecture hiện tại.

Validate:

- session exists
- hash matches
- revoked_at
- idle_expires_at
- absolute_expires_at
- user status
- context
- KS binding khi cần.

Sliding idle expiry giữ optimization/throttle hiện tại nếu đã có.

============================================================
18. AUTHENTICATION CONTEXT ENFORCEMENT
============================================================

Tạo reusable dependencies/guards/application boundary.

Management APIs require:

session.context_type == MANAGEMENT

Chat/Knowledge API require:

session.context_type == KNOWLEDGE_SPACE

AND:

session.knowledge_space_id == requested knowledge_space_id

Fail closed.

Không duplicate logic này trong từng controller.

Không tin context gửi từ frontend.

============================================================
19. /ME
============================================================

/me phải trả minimum safe authentication context cần cho frontend:

user:
- id
- safe profile fields

authentication:
- context_type
- auth_method
- knowledge_space_id nếu applicable
- authenticated_at
- MFA assurance state nếu cần.

Không expose:

session_token_hash
credential/password data
MFA secret
verification token hash
OIDC tokens
internal secrets.

Frontend sau này dùng /me để quyết định UX.

Backend vẫn là source of truth.

============================================================
20. LOGOUT
============================================================

Application logout:

→ identify current session
→ revoke session server-side
→ set revoked_at/reason
→ clear HttpOnly cookie

Không delete session record.

Giữ auditability.

Logout phải idempotent.

============================================================
21. LOGOUT ALL
============================================================

Reuse/complete existing LogoutAllSessions use case.

→ revoke all active application sessions của canonical user.

Phải xác định semantics rõ:
logout-all là toàn bộ contexts của user,
trừ khi existing product contract đã có scoped semantics.

Không silently chỉ revoke current KS.

============================================================
22. MICROSOFT LOGOUT
============================================================

Phân biệt:

APPLICATION LOGOUT
và
MICROSOFT FEDERATED LOGOUT.

Default application logout:

→ revoke our AuthSession
→ clear our cookie

Không bắt buộc logout Microsoft browser session.

Không tự redirect Entra logout mỗi lần user rời KS.

Federated logout nếu support:
→ explicit separate flow/use case.

============================================================
23. MANAGEMENT REAUTHENTICATION
============================================================

ManagementAuthPolicy có:

reauthentication_minutes

Phase này phải ít nhất model + expose capability/domain service để xác định:

is_recently_authenticated(session, policy)

để phase Role/Permission sau có thể yêu cầu recent authentication
cho sensitive actions như:

- change authentication policy
- manage admin roles
- change permissions
- security configuration.

Không cần áp vào Role APIs chưa tồn tại.

Nhưng đừng bỏ field này khỏi domain/persistence.

============================================================
24. AUDIT SECURITY EVENTS
============================================================

Inspect iam.audit_logs và abstraction hiện có.

Security events nên audit qua contract/service:

- registration
- verification success/failure
- login success
- login failure
- lockout
- MFA challenge/verify
- Entra SSO success/failure
- identity provision/link
- session creation
- logout
- logout-all
- revoke
- suspicious/replayed auth transaction nếu phù hợp.

NO raw INSERT audit_logs.

Không log secrets:

password
raw session token
verification token
MFA secret/code
authorization code
access token
refresh token
ID token.

============================================================
25. PRESENTATION/API DESIGN
============================================================

Controller thin.

Controller:
- DTO validation
- call use case
- cookie handling
- redirect handling
- translate known errors.

Controller không:
- query DB
- SQLAlchemy
- password verification
- OIDC token validation
- Microsoft API calls
- policy logic.

Tách intent rõ.

Conceptual API surface có thể gồm:

Management:
- local login
- Entra SSO start
- Entra callback/context callback handling

Knowledge Space:
- get auth requirement
- local login for KS
- Entra SSO start for KS

Common:
- register
- verify email
- MFA verify
- /me
- logout
- logout-all

Không bắt buộc đúng URL naming trên.
Follow route conventions hiện có.

KHÔNG tạo generic insecure endpoint kiểu:

POST /auth/login
{
  "provider": "...",
  "context": "...",
  "knowledge_space_id": "..."
}

rồi tin input.

============================================================
26. FRONTEND BOUNDARY
============================================================

KHÔNG implement frontend trong phase backend này.

Nhưng backend API phải support FE flow sau:

Knowledge Space selector/access:
→ FE asks backend auth requirement.

LOCAL:
→ FE render login form
→ POST backend.

MICROSOFT_ENTRA:
→ FE redirects browser tới backend SSO start endpoint
→ backend redirects Microsoft
→ Microsoft redirects BACKEND callback
→ backend validates everything
→ backend sets HttpOnly application cookie
→ backend redirects FE chat URL.

Frontend KHÔNG:
- exchange authorization code
- validate Microsoft token
- store Microsoft access/id token
- create session itself.

============================================================
27. COMPOSITION / DEPENDENCY INJECTION
============================================================

Composition root phải wire:

repositories
policy resolver
password hasher
token service
MFA provider/store
OIDC provider
user facade
KS facade/contract
audit service
email delivery
use cases.

Không instantiate infrastructure dependency bên trong use case.

Không service locator.

Không global mutable repository/provider.

Không circular import.

Cross-module dependency phải qua composition/public contract.

============================================================
28. ERROR MODEL
============================================================

Dùng typed domain/application errors.

Ví dụ concept:

InvalidCredentials
AccountLocked
AccountInactive
EmailNotVerified
AuthenticationPolicyMissing
AuthenticationMethodNotAllowed
MfaRequired
MfaEnrollmentRequired
InvalidMfaChallenge
SessionExpired
SessionRevoked
InvalidAuthenticationContext
KnowledgeSpaceContextMismatch
OidcStateInvalid
OidcTransactionExpired
OidcTenantMismatch
ExternalIdentityConflict

Không throw ValueError/Exception generic xuyên presentation
nếu project đã có error conventions.

Không leak security detail cho client.

Ví dụ login failure không cho attacker biết:
"email tồn tại nhưng password sai".

============================================================
29. CONCURRENCY / TRANSACTION SAFETY
============================================================

Các flow security-sensitive phải transaction-safe:

register user + credential
verification consume
failed-attempt/lockout update
identity provisioning/linking
session creation
MFA challenge consumption.

Reuse UnitOfWork/transaction pattern hiện có.

Không commit lẻ tẻ từ nhiều repository nếu operation cần atomic.

Không để callback Entra concurrent tạo duplicate user/identity.

============================================================
30. KHÔNG LÀM TRONG PHASE NÀY
============================================================

KHÔNG implement:

- KS membership
- HR_MANAGER / HR_STAFF
- department
- position hierarchy
- role permission redesign
- sensitivity 0/1/2/3 authorization
- knowledge authorization_strategy
- SharePoint ACL
- permission ingestion
- permission retrieval
- Data Hub changes
- ingestion changes
- retrieval changes
- frontend implementation
- Google SSO
- JWT redesign
- refresh-token redesign.

============================================================
31. TESTS BẮT BUỘC
============================================================

LOCAL:

1. register success
2. duplicate enumeration-safe behavior
3. verification success
4. expired verification reject
5. verification replay reject
6. password login success
7. wrong password
8. lockout
9. inactive/unverified user
10. MFA required
11. MFA replay/expiry
12. successful session creation

MANAGEMENT:

13. management local session:
    context=MANAGEMENT
    knowledge_space_id=NULL

14. management MFA policy enforced

15. KS session rejected from management guard

16. management session accepted by management guard

KNOWLEDGE SPACE:

17. LOCAL KS login success

18. correct knowledge_space_id persisted

19. KS-A session rejected for KS-B

20. missing policy fails closed

21. inactive policy fails closed

22. wrong auth method rejected

ENTRA:

23. SSO start creates secure state/nonce transaction

24. invalid state rejected

25. expired transaction rejected

26. replayed transaction rejected

27. nonce mismatch rejected

28. wrong issuer/audience rejected

29. wrong tenant rejected

30. existing identity link resolves same canonical user

31. new identity provisions/links safely

32. email-only automatic account merge DOES NOT occur

33. Entra MANAGEMENT session has:
    context=MANAGEMENT
    knowledge_space_id=NULL
    identity_link_id set

34. Entra KS session has:
    context=KNOWLEDGE_SPACE
    correct knowledge_space_id
    identity_link_id set

SESSION:

35. idle expiry
36. absolute expiry
37. revoked session
38. inactive user
39. logout
40. logout idempotency
41. logout-all
42. /me safe response
43. mapper roundtrip all new AuthSession fields

PERSISTENCE:

44. KnowledgeSpaceAuthPolicy mapper/repository
45. ManagementAuthPolicy mapper/repository
46. AuthSession new fields
47. DB constraint-compatible behavior

REGRESSION:

Existing auth/user tests must remain green or be intentionally updated
because of the new context architecture.

Mock Microsoft/OIDC in unit tests.

If live Entra integration cannot run locally,
report separately:
- unit/mock verified
- live integration not verified.

============================================================
32. QUALITY GATES
============================================================

SOLID.

No raw SQL.

No business logic in controllers.

No SQLAlchemy models in application/domain.

No provider-specific Microsoft code in application use cases.

No cross-module infrastructure imports.

No God AuthService.

No duplicate abstractions when equivalent abstraction already exists.

No JWT redesign.

No unrelated refactor.

No ingestion/retrieval changes.

No frontend changes.

Run relevant tests.

Run import/static checks used by project.

Report failures honestly.

============================================================
33. FINAL REPORT
============================================================

After implementation report:

1. files created
2. files modified
3. DB models/mappers synchronized
4. local auth flows completed
5. Entra SSO flows completed
6. session/context enforcement completed
7. MFA/email verification completed
8. API endpoints added/changed
9. composition wiring changed
10. tests executed + exact results
11. anything not live-tested
12. remaining TODO specifically for next phase

Do not say "complete" if Entra backend flow is only stubbed.
Do not say "tests pass" if tests were not executed.