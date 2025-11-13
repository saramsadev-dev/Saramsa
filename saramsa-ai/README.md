# Saramsa AI

AI-powered content analysis platform built with Next.js, TypeScript, and Tailwind CSS.

## Features

- 🔐 **Secure Authentication** - JWT-based authentication with automatic token refresh
- 📊 **AI-Powered Analysis** - Upload and analyze CSV, JSON, and MP3 files
- 🎨 **Modern UI** - Beautiful, responsive design with dark mode support
- ⚡ **Fast Performance** - Built with Next.js 14 and optimized for speed
- 🔒 **Route Protection** - Server-side and client-side authentication guards

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn
- Backend API server running on `http://127.0.0.1:8000/api`

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd saramsa-ai
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
# Create .env.local file
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3000](http://localhost:3000) in your browser.

## Authentication System

The application implements a comprehensive authentication system with industry-standard security practices:

- **JWT Tokens** with automatic refresh
- **Secure cookie storage** for refresh tokens
- **Session-based access tokens** for enhanced security
- **Server-side middleware** for route protection
- **Client-side guards** for seamless UX

### Quick Start with Authentication

1. **First-time users**: Visit the landing page and click "Get Started" or "Create Account"
2. **Existing users**: Click "Get Started" to access the login page
3. **Protected routes**: Automatically redirect to login if not authenticated
4. **Token management**: Automatic refresh and secure storage

For detailed authentication documentation, see [AUTHENTICATION.md](./AUTHENTICATION.md).

## Project Structure

```
src/
├── app/                    # Next.js app router pages
│   ├── login/             # Login page
│   ├── register/          # Registration page
│   ├── upload/            # File upload and analysis
│   ├── config/            # Configuration settings
│   └── layout.tsx         # Root layout with providers
├── components/            # React components
│   ├── auth/              # Authentication components
│   ├── ui/                # UI components
│   └── providers/         # Context providers
├── lib/                   # Utility libraries
│   ├── auth.ts            # Authentication service
│   ├── tokenManager.ts    # Token management
│   └── useAuth.ts         # Authentication hook
├── store/                 # Redux store
│   └── features/          # Redux slices
└── middleware.ts          # Server-side route protection
```

## Key Components

### Authentication
- **AuthGuard**: Client-side route protection
- **TokenManager**: Secure token storage and refresh
- **AuthService**: API communication for auth operations
- **Middleware**: Server-side route protection

### UI Components
- **LandingPage**: Welcome page for unauthenticated users
- **Navbar**: Navigation with user profile
- **ThemeToggle**: Dark/light mode switcher

## Development

### Available Scripts

```bash
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server
npm run lint         # Run ESLint
```

### Environment Variables

```env
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000/api
```

## Security Features

- ✅ **XSS Protection** - HTTP-only cookies, secure storage
- ✅ **CSRF Protection** - SameSite cookies, token-based auth
- ✅ **Token Security** - Short-lived access tokens, automatic refresh
- ✅ **Route Protection** - Server and client-side guards
- ✅ **Secure Storage** - SessionStorage + cookies strategy

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For authentication-related issues, see [AUTHENTICATION.md](./AUTHENTICATION.md).

For general support, please open an issue in the repository.
