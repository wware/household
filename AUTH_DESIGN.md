# Authentication & Authorization Design

## Overview

This document outlines the authentication and authorization strategy for integrating the household AI assistant with the markdown document management website. Both services will eventually be deployed as a single FastAPI application on AWS under one domain, but will maintain separate auth tiers reflecting their different sensitivity levels.

## System Architecture

### Deployment Target
- **Local Development**: Two separate services running on localhost (household on port 3000, website on separate port or via ngrok)
- **AWS Production**: Single containerized FastAPI application
  - Single domain (e.g., `household.example.com`)
  - Unified auth system
  - ALB routing: `/api/household/*` → household endpoints, `/api/docs/*` → document endpoints, `/docs/*` or `/editor` → UI
  - Shared session/token management

### Services
1. **Household Service** (`/api/household/*`)
   - Appointment management
   - Grocery lists
   - Tasks/to-dos
   - Weather data
   - User management

2. **Document Service** (`/api/docs/*` or similar)
   - Markdown CRUD
   - Document metadata (created, modified, tags, etc.)
   - Document storage (S3 or filesystem in local dev)

## Authentication Tiers

### Tier 1: Public (No Auth Required)
- **Household**: None (all household data is private)
- **Documents**: Public markdown documents (portfolio pieces, shared knowledge, etc.)

### Tier 2: Authenticated Users (Login Required)
- **Household**: All read/write access requires authentication
  - Medical appointments, grocery lists, tasks, etc. are all protected
  - Users must be logged in to view any household data
- **Documents**: Accessing owned/shared private documents requires authentication
  - Public documents remain viewable without auth

### Tier 3: Authorization/Permissions
- **Household**:
  - Role-based or attribute-based (TBD based on user feedback)
  - Example: Both household members can see grocery lists, but medical appointments might be owner-only
  - Possible roles: `household_member`, `admin`, or finer-grained permissions

- **Documents**:
  - **Public**: Viewable by anyone (no login)
  - **Private**: Viewable/editable by owner only
  - **Shared**: Owner can grant specific users read or read-write access
  - Possible future: Viewer role (read-only) vs Editor role (read-write) vs Owner (read-write-delete-share)

## Permission Models

### Household Resources
All household resources require authentication. Specific permission model TBD:

**Option A: All-or-Nothing (Simpler)**
- Any authenticated household member can view and edit all household data
- Suitable for 2-person household where privacy boundaries are looser
- Future refinement: Flag sensitive items (medical appointments) with viewer restrictions

**Option B: Granular Permissions (More Complex)**
- Define permissions per resource type:
  - `household:appointments:read` / `write` / `delete`
  - `household:grocery:read` / `write`
  - `household:tasks:read` / `write`
- Assign roles with bundles of permissions
- Allows flexibility if household grows or specific items need protection

**Option C: Hybrid (Recommended for now)**
- By default, authenticated users can see everything
- Medical appointments: Add owner-only flag that restricts visibility
- Grocery list: Everyone can read/write (shared responsibility)
- Tasks: Each user's personal tasks are owner-read-write, shared tasks are open

### Document Permissions
Document permission model (detailed):

```
Document {
  id: string
  title: string
  content: markdown
  owner_id: user_id
  created_at: timestamp
  modified_at: timestamp

  # Permission model
  visibility: "public" | "private" | "shared"

  # If visibility == "shared", maintain access list
  shared_access: [
    {
      user_id: user_id,
      access_level: "viewer" | "editor"  # viewer = read-only, editor = read-write
    }
  ]
}
```

**Visibility Rules:**
- `public`: Accessible to anyone (unauthenticated users included)
- `private`: Only owner can view/edit
- `shared`: Only owner and explicitly shared users can access based on their access level

## Authentication Method

### Recommended: JWT Tokens + Refresh Tokens
- Standard web approach, plays well with AWS
- Browser stores JWT in httpOnly cookie (CSRF protection)
- Refresh token in secure cookie for long-lived sessions
- Works for both API and browser clients

### Alternative Considerations:
- **Cognito**: Mentioned in website template, more managed AWS approach, might add complexity
- **Sessions + Cookies**: Simpler for browser-only, less flexible for future mobile apps
- **OAuth2**: Overkill unless planning social login

**Decision Point for Later**: Choose between JWT or Cognito based on deployment AWS strategy and preference for managed vs. custom implementation.

## Data Models & Database Schema

### User Model
```python
class User(Base):
    __tablename__ = "users"

    id: UUID = primary key
    username: str = unique
    email: str = unique
    password_hash: str = argon2/bcrypt hash
    full_name: str = optional
    created_at: datetime

    # Relationships
    appointments: list[Appointment]
    documents: list[Document]
    shared_document_access: list[DocumentAccess]
```

### Document Model
```python
class Document(Base):
    __tablename__ = "documents"

    id: UUID = primary key
    owner_id: UUID = foreign key to User
    title: str
    content: str = markdown content
    created_at: datetime
    modified_at: datetime
    visibility: str = Enum("public", "private", "shared")

    # Relationships
    owner: User
    access_list: list[DocumentAccess]
```

### DocumentAccess Model (for shared documents)
```python
class DocumentAccess(Base):
    __tablename__ = "document_access"

    id: UUID = primary key
    document_id: UUID = foreign key to Document
    user_id: UUID = foreign key to User
    access_level: str = Enum("viewer", "editor")
    granted_at: datetime

    # Relationships
    document: Document
    user: User

    # Compound unique constraint on (document_id, user_id)
```

### Household Resources (Appointments, etc.)
```python
class Appointment(Base):
    __tablename__ = "appointments"

    id: UUID = primary key
    user_id: UUID = foreign key to User (owner/primary subject)
    title: str
    date: datetime
    type: str = "medical" | "pet" | "maintenance" | etc.

    # Permission flag
    visibility: str = Enum("private", "shared_household")  # or similar

    # Other existing fields...
```

## API Endpoint Protection

### Current Household Routes (All require auth after implementation)
```
POST   /api/household/users              (signup) - maybe public?
POST   /api/household/auth/login         (login) - public
POST   /api/household/auth/logout        (logout) - requires auth
POST   /api/household/appointments       (create) - requires auth
GET    /api/household/appointments       (list) - requires auth
GET    /api/household/appointments/{id}  (read) - requires auth + permission check
PUT    /api/household/appointments/{id}  (update) - requires auth + ownership
DELETE /api/household/appointments/{id}  (delete) - requires auth + ownership
# Similar for /grocery, /tasks, /weather
```

### Document Routes
```
# Public read
GET    /api/docs                         (list public docs) - no auth
GET    /api/docs/{id}                    (read if public) - no auth
GET    /api/docs/editor                  (editor UI) - no auth (but document must be public)

# Authenticated operations
POST   /api/docs                         (create) - requires auth
PUT    /api/docs/{id}                    (update) - requires auth + ownership/permission
DELETE /api/docs/{id}                    (delete) - requires auth + ownership
GET    /api/docs/shared                  (list shared with me) - requires auth

# Permission management
POST   /api/docs/{id}/share              (share document) - requires auth + ownership
PUT    /api/docs/{id}/access/{user_id}   (update access level) - requires auth + ownership
DELETE /api/docs/{id}/access/{user_id}   (revoke access) - requires auth + ownership
```

## Implementation Phases

### Phase 1: Basic Auth (Foundation)
- [ ] User registration & login endpoints
- [ ] Password hashing (argon2)
- [ ] JWT token generation & validation
- [ ] Auth middleware for protecting household endpoints
- [ ] Session/token refresh mechanism
- [ ] Basic tests for auth flow

### Phase 2: Household Protection
- [ ] Add auth checks to all household routes
- [ ] Implement permission checks (at least ownership)
- [ ] Add visibility flags to appointments/tasks
- [ ] Fine-grained permission model (Option A, B, or C from above)

### Phase 3: Document Auth
- [ ] Create Document and DocumentAccess models
- [ ] Implement public/private/shared visibility model
- [ ] Add document CRUD with auth checks
- [ ] Implement share/access management endpoints
- [ ] Access level differentiation (viewer vs editor)

### Phase 4: UI Integration
- [ ] Login form on website
- [ ] Session persistence (JWT in httpOnly cookie)
- [ ] Conditional rendering based on auth status
- [ ] Permission-based UI elements (show edit button only if editor role)
- [ ] Document sharing UI

### Phase 5: AWS Deployment
- [ ] Merge website backend into household FastAPI app
- [ ] Database migration to RDS (from SQLite)
- [ ] Update deployment configuration
- [ ] Single domain setup with ALB routing
- [ ] TLS/HTTPS enforcement
- [ ] Consider Cognito vs keeping JWT

## Security Considerations

### Passwords
- Hash with argon2 or bcrypt (configurable via pydantic settings)
- Never store plaintext
- Enforce minimum requirements (length, complexity optional for solo/household use)

### Tokens
- JWT with short expiration (15 minutes recommended)
- Refresh token with longer expiration (7-30 days) stored in httpOnly cookie
- Revocation mechanism (token blacklist or short expiration) for logout
- Sign with HS256 or RS256 (local: HS256 is fine, AWS: consider RS256 with KMS)

### CSRF
- Use httpOnly cookies to prevent XSS token theft
- Consider SameSite=Strict for cookies
- Consider CSRF tokens for state-changing operations

### HTTPS/TLS
- Not needed for local development
- Required for AWS production (enforce redirect http→https on ALB)

### Database
- Principle of least privilege for DB user
- No default SQL injection vectors if using SQLAlchemy ORM
- Audit log for sensitive operations (optional, Phase 2+)

### Input Validation
- Pydantic handles most validation
- Add rate limiting on auth endpoints (future consideration)
- Sanitize document content if rendering as HTML (currently markdown only, safe)

## Testing Strategy

### Auth Tests (Unit/Integration)
- User registration with valid/invalid inputs
- Password hashing and verification
- Token generation and validation
- Token expiration and refresh
- Middleware auth checks
- Permission checks on sensitive endpoints

### Permission Tests
- Public document accessibility
- Private document access control
- Shared document access levels
- Household data access (authenticated users only)
- Cross-user isolation (user A can't access user B's private docs)

### End-to-End Tests
- Login → access household data → logout flow
- Create and share document → access with shared user
- Attempt unauthorized access (should fail)

## Open Questions / TBD

1. **Signup flow**: Should new users be able to self-register, or admin-invite only?
   - For 2-person household: likely invite-only or manually created

2. **Household permission granularity**: Option A (all-or-nothing), B (granular), or C (hybrid)?
   - Recommend Option C initially, can refine later

3. **Auth on signup**: Should signup endpoint be public or require an invite code?
   - Recommend: Invite-code based for security

4. **Session timeout**: How long before re-login required?
   - Recommend: 24-48 hours for household members (trusted environment)

5. **Password requirements**: Strict policies or relaxed for home use?
   - Recommend: Basic (8+ chars) for now, can enforce more later

6. **Audit logging**: Track who accessed what when?
   - Recommend: Not Phase 1, add if needed later

7. **Multi-device support**: Same user logged in on phone + browser simultaneously?
   - Recommend: Support multiple tokens per user (straightforward with JWT)

8. **Document versioning**: Keep history of markdown changes?
   - Recommend: Out of scope for Phase 1, nice-to-have later

## Migration Path: Local → AWS

When deploying to AWS:
1. Refactor website Lambda backend → FastAPI (merge into household app)
2. Create unified Docker image for FastAPI + static assets
3. Push to ECR
4. Deploy ECS Fargate task running single container
5. Setup RDS for production database (migrate from SQLite)
6. Configure ALB with routing rules
7. Setup Cognito (optional, depends on preference) or keep JWT
8. Use Secrets Manager for JWT secret, DB password, etc.
9. CloudFront in front for caching static assets

This design document can be refined based on actual requirements and preferences. Key decision points are flagged as TBD.
