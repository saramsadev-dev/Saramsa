# Authentication System Documentation

## Overview

The Saramsa AI application implements a comprehensive authentication system with industry-standard security practices. The system uses JWT tokens with automatic refresh capabilities and proper route protection.

## Architecture

### Token Management
- **Access Token**: Stored in `sessionStorage` (client-side) and cookies (server-side middleware)
- **Refresh Token**: Stored in secure HTTP-only cookies
- **User Data**: Stored in `localStorage`

### Security Features
- Automatic token refresh before expiration
- Secure cookie storage with `SameSite=Strict` and `Secure` flags
- HTTP-only cookies for refresh tokens
- Session-based access tokens (cleared on browser close)
- Server-side middleware for route protection

## Components

### 1. AuthGuard (`src/components/auth/AuthGuard.tsx`)
Handles client-side route protection and authentication state management.

**Protected Routes:**
- `/dashboard`
- `/upload`
- `/config`
- `/comments`
- `/test-gradients`

**Public-Only Routes:**
- `/login`
- `/register`

**Behavior:**
- Unauthenticated users accessing protected routes → redirected to `/login`
- Authenticated users accessing public-only routes → redirected to `/`
- Unauthenticated users on `/` → shown landing page
- Authenticated users on `/` → shown dashboard

### 2. TokenManager (`src/lib/tokenManager.ts`)
Manages token storage, validation, and refresh logic.

**Key Methods:**
- `storeTokens()`: Stores tokens in sessionStorage and cookies
- `getValidAccessToken()`: Returns valid access token, refreshes if needed
- `isAuthenticated()`: Checks if user has valid tokens
- `clearTokens()`: Removes all tokens and user data

### 3. AuthService (`src/lib/auth.ts`)
Handles API communication and authentication operations.

**Key Methods:**
- `login()`: Authenticates user and stores tokens
- `register()`: Creates new user account
- `refreshToken()`: Refreshes access token using refresh token
- `logout()`: Clears all authentication data

### 4. Middleware (`src/middleware.ts`)
Provides server-side route protection and redirects.

**Features:**
- Checks authentication status via cookies
- Redirects unauthenticated users from protected routes
- Redirects authenticated users from public-only routes
- Runs before page rendering for better UX

## Authentication Flow

### 1. Initial Load
```
User visits site → Middleware checks cookies → 
If authenticated → Load dashboard
If not authenticated → Show landing page
```

### 2. Login Process
```
User submits credentials → AuthService.login() → 
Store tokens → Update Redux state → Redirect to dashboard
```

### 3. Token Refresh
```
API call fails with 401 → Interceptor catches error → 
Use refresh token → Get new access token → Retry original request
```

### 4. Logout Process
```
User clicks logout → Clear all tokens → 
Clear Redux state → Redirect to login
```

## Token Storage Strategy

### Access Token
- **Client-side**: `sessionStorage` (cleared on browser close)
- **Server-side**: Cookie for middleware access
- **Expiration**: 1 day (configurable)
- **Security**: Non-HTTP-only for client access

### Refresh Token
- **Storage**: HTTP-only cookie
- **Expiration**: 30 days (configurable)
- **Security**: HTTP-only, SameSite=Strict, Secure

### User Data
- **Storage**: `localStorage`
- **Content**: Username, email, role
- **Persistence**: Survives browser sessions

## Error Handling

### Token Expiration
- Automatic refresh before expiration
- Graceful fallback to login on refresh failure
- Clear all data on refresh token expiration

### Network Errors
- Retry mechanism for failed requests
- User-friendly error messages
- Fallback to login page on authentication failures

## Security Considerations

### XSS Protection
- HTTP-only cookies for refresh tokens
- SessionStorage for access tokens (not accessible via JavaScript)
- Input sanitization and validation

### CSRF Protection
- SameSite=Strict cookie policy
- Token-based authentication
- Secure cookie flags

### Token Security
- Short-lived access tokens (1 day)
- Long-lived refresh tokens (30 days)
- Automatic token rotation
- Secure storage mechanisms

## Usage Examples

### Checking Authentication Status
```typescript
const { isAuthenticated, user, loading } = useAuth();

if (loading) {
  return <LoadingSpinner />;
}

if (!isAuthenticated) {
  return <LoginPage />;
}
```

### Making Authenticated API Calls
```typescript
// Automatically includes auth headers
const response = await api.get('/protected-endpoint');
```

### Manual Token Refresh
```typescript
const { manualRefresh } = useAuth();
await manualRefresh();
```

## Configuration

### Environment Variables
```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

### Token Expiration Times
- Access Token: 1 day (configurable in `tokenManager.ts`)
- Refresh Token: 30 days (configurable in `tokenManager.ts`)

### Cookie Settings
- SameSite: Strict
- Secure: true (HTTPS only)
- HttpOnly: true (refresh tokens only)

## Troubleshooting

### Common Issues

1. **Tokens not persisting**
   - Check browser cookie settings
   - Verify HTTPS in production
   - Check SameSite cookie policy

2. **Infinite redirects**
   - Clear all cookies and localStorage
   - Check middleware configuration
   - Verify route protection logic

3. **Token refresh failures**
   - Check backend refresh endpoint
   - Verify refresh token validity
   - Check network connectivity

### Debug Mode
Enable debug logging by setting:
```typescript
localStorage.setItem('debug_auth', 'true');
```

## Best Practices

1. **Always use the `useAuth` hook** for authentication state
2. **Don't manually manipulate tokens** - use TokenManager methods
3. **Handle loading states** in components
4. **Use the AuthGuard** for route protection
5. **Test authentication flows** thoroughly
6. **Monitor token expiration** in production
7. **Implement proper error boundaries** for auth failures

## Future Enhancements

- [ ] Implement biometric authentication
- [ ] Add multi-factor authentication
- [ ] Support for OAuth providers
- [ ] Enhanced token security with rotation
- [ ] Audit logging for authentication events
- [ ] Rate limiting for authentication attempts 