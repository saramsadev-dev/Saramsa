# Redux Store Implementation for Saramsa AI

This directory contains the Redux store implementation for Saramsa AI, providing centralized state management with proper JWT token expiration handling.s

### Authentication (authSlice.ts)
- User login/logout/registration
- JWT token management
- Automatic token refresh
- Token expiration handling
- User profile management

### Analysis (analysisSlice.ts)
- Content analysis operations
- Analysis history management
- Real-time analysis status
- Error handling for analysis operations

### Upload (uploadSlice.ts)
- File upload management
- Upload progress tracking
- File status management
- Upload history

## JWT Token Expiration Handling

The implementation includes comprehensive JWT token expiration handling:

1. **Automatic Token Refresh**: Tokens are automatically refreshed 1 minute before expiry
2. **Token Expiry Monitoring**: Continuous monitoring of token expiration
3. **Graceful Logout**: Automatic logout when refresh tokens expire
4. **Manual Refresh**: Support for manual token refresh
5. **Error Handling**: Proper error handling for failed token operations

## Usage

### Basic Store Usage
```typescript
import { useAppDispatch, useAppSelector } from '@/store/hooks';

// In a component
const dispatch = useAppDispatch();
const { user, isAuthenticated } = useAppSelector(state => state.auth);
```

### Authentication
```typescript
import { useAuth } from '@/lib/useAuth';

const { login, logout, user, isAuthenticated } = useAuth();
```

### Analysis Operations
```typescript
import { useAnalysis } from '@/lib/useAnalysis';

const { analyze, analysisData, loading } = useAnalysis();
```

### File Upload
```typescript
import { useUpload } from '@/lib/useUpload';

const { upload, uploadProgress, isUploading } = useUpload();
```

## Token Management

The token management system includes:

- **Token Storage**: Secure localStorage management
- **Token Validation**: JWT payload validation
- **Automatic Refresh**: Proactive token refresh
- **Expiry Tracking**: Real-time expiry monitoring
- **Cleanup**: Proper cleanup on logout

## Error Handling

All async operations include comprehensive error handling:

- Network errors
- Authentication errors
- Server errors
- Validation errors
- Token refresh failures

## Integration with Components

The store is integrated with the app through:

1. **StoreProvider**: Wraps the entire app
2. **TokenRefreshProvider**: Handles automatic token refresh
3. **AuthGuard**: Protects routes based on authentication
4. **Custom Hooks**: Provide easy access to store functionality

## Best Practices

- Type-safe Redux usage with TypeScript
- Proper error handling and user feedback
- Automatic cleanup of timeouts and intervals
- Secure token management
- Responsive UI during loading states 