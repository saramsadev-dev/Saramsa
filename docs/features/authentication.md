# Feature: Authentication & User Management

## Overview
JWT-based authentication using `rest_framework_simplejwt` with users stored in Azure Cosmos DB. Supports registration with OTP, login, password reset, and role-based access control.

## Endpoints
| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/api/auth/register/` | None | Register new user |
| POST | `/api/auth/register/request-otp/` | None | Request OTP for registration |
| POST | `/api/auth/login/` | None | Login, returns JWT access + refresh tokens |
| GET | `/api/auth/me/` | Bearer | Get current user profile |
| POST | `/api/auth/forgot-password/` | None | Request password reset email |
| POST | `/api/auth/reset-password/` | None | Reset password with token |
| POST | `/api/auth/token/` | None | Obtain token pair |
| POST | `/api/auth/refresh/` | None | Refresh access token |
| GET | `/api/auth/users/` | Admin | List all users |
| GET | `/api/auth/users/<id>/` | Admin | Get user detail |

## Token Structure
- Access token: short-lived JWT
- Refresh token: long-lived, used to obtain new access tokens
- Tokens carry `user_id` (subject for API auth), `email`, `profile_role`, `is_staff`

## Roles & Permissions
| Role | Scope | Permission Classes |
|------|-------|--------------------|
| `admin` | Global | `IsAdminOrUser` — full access |
| `user` | Own data | `IsAdminOrUser` — own data only |
| Project Viewer | Project | `IsProjectViewer` — read analysis |
| Project Editor | Project | `IsProjectEditor` — run analysis, upload |

## Key Files
| File | Purpose |
|------|---------|
| `authentication/views.py` | All auth views |
| `authentication/urls.py` | URL routing |
| `authentication/permissions.py` | Permission classes |
| `authentication/serializers.py` | Request validation |

## Frontend Integration
- Redux slice at `saramsa-ai/src/store/` manages tokens
- `apiRequest.ts` attaches `Authorization: Bearer <token>` to all requests
- Auto-refresh on 401 via interceptor

## Test User
`backend/scripts/create_test_user.py` creates a test user and writes credentials to `.env` as `LOGIN_EMAIL` and `LOGIN_PASSWORD`.
