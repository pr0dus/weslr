# ROLE_PERMISSION_CONTRACT_v1

## Purpose
Provide a governed multi-user role model so WESLR can safely serve owners, admins/operators, standard users, and limited sub-users (e.g., family, staff, school/clinic participants) without leaking continuity, approvals, or private memory. The model must support permission-aware visibility, future presence signals (check-in/out), and shared workspaces.

## Role Types (baseline)
- **Owner/Master**: Full control, can add/remove admins and users, set global policies, view/audit continuity, and override approvals (within governance limits).
- **Admin/Operator**: Manage users within a workspace, manage shared resources, view shared continuity (not private user memory), can trigger approvals per policy, cannot exceed owner/global governance.
- **Standard User**: Default role; has their own private continuity/memory; may access shared workspace resources per permissions; cannot manage other users.
- **Limited Sub-User**: Narrow scope (e.g., family member, staff with limited duties, student). Access only to explicitly granted resources; no admin capabilities; private continuity isolated; may have time-bound or task-bound permissions.
- **Institutional Roles (future-ready)**: Organization-scoped roles (e.g., clinic staff, school admin/teacher/student) mapped onto the same permission scopes below with org/workspace partitioning.

## Permission Scopes
- **User/Admin Management**: add/remove users, assign roles, rotate credentials/auth links.
- **Continuity Visibility**: view own continuity; view shared workspace continuity if permitted; owners/admins may audit within policy; private user continuity stays isolated unless explicitly shared.
- **Approvals**: submit/approve/deny requests within role limits; owners can override; admins per workspace policy; standard users limited to their own requests; sub-users only if explicitly allowed.
- **Shared Workspace Access**: read/write shared resources; create shared tasks/reminders; constrained by workspace/org policies.
- **Private Memory Visibility**: own only by default; sharing requires explicit grant; owners/admins do not automatically see private memory.
- **Event Visibility**: see/log events relevant to permitted scopes; presence/check-in events constrained to the same visibility rules.
- **Capability Invocation**: what actions/capabilities can be requested or executed (e.g., approvals to run certain capabilities) per role and governance policy.

## Event / Presence (future-ready)
- Presence/check-in events (badge scans, device proximity, schedule check-in/out) are tagged with (workspace_id, user_id) and role; visibility follows permission scopes above.
- Event routing must not leak presence across users/workspaces; shared events only when explicitly in a shared workspace/org context.
- Approvals or actions triggered from presence events must respect role permissions and governance holds.

## Status
- Contract defined for future implementation; no runtime code changes here.
