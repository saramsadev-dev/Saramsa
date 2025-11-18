"use client";

import { useState, useEffect, useRef } from "react";
import { ThemeToggle } from "./theme-toggle";
import {
  Settings,
  LogOut,
  User,
  Bell,
  Search,
  ChevronDown,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/useAuth";
import { BrandLogo } from "./brand-logo";
import { shouldShowNavbar } from "@/lib/auth-pages";

export function Navbar() {
  const pathname = usePathname();
  const { isAuthenticated, user: currentUser, loading, logout } = useAuth();
  const [open, setOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Check if navbar should be shown based on current page and auth state
  const showNavbar = shouldShowNavbar(pathname, isAuthenticated);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setOpen(false);
      }
    };

    if (open) {
      document.addEventListener("mousedown", handleClickOutside);
      return () =>
        document.removeEventListener("mousedown", handleClickOutside);
    }
  }, [open]);

  const handleLogout = async () => {
    try {
      setOpen(false);
      await logout();
      // Force redirect to login page
      window.location.href = "/login";
    } catch (error) {
      console.error("Logout error:", error);
      // Force redirect even if logout fails
      window.location.href = "/login";
    }
  };

  // Don't render until auth state is determined
  if (loading) {
    return null;
  }

  // Hide navbar on auth pages or when not authenticated on home page
  if (!showNavbar) {
    return null;
  }

  return (
    <>
      <nav className="z-100 w-full sticky top-0 bg-background/95 backdrop-blur-sm border-b border-border shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex-shrink-0">
              <Link href="/projects">
                <BrandLogo size="md" />
              </Link>
            </div>

            {/* Right side - Theme Toggle and Profile */}
            <div className="flex items-center space-x-4">
              {isAuthenticated && currentUser && (
                <div className="relative" ref={dropdownRef}>
                  <button
                    onClick={() => setOpen((v) => !v)}
                    className="flex items-center space-x-2 px-3 py-2 text-muted-foreground hover:text-foreground hover:bg-accent rounded-lg transition-colors"
                  >
                    <div className="w-8 h-8 bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to rounded-full flex items-center justify-center">
                      <span className="text-white font-bold text-sm">
                        {currentUser.username.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <span className="hidden sm:block font-medium">
                      {currentUser.username}
                    </span>
                    <ChevronDown
                      className={`w-4 h-4 transition-transform ${
                        open ? "rotate-180" : ""
                      }`}
                    />
                  </button>
                  {open && (
                    <div className="absolute z-50 right-0 mt-2 w-56 bg-popover border border-border rounded-lg shadow-xl animate-in slide-in-from-top-2 duration-200">
                      <div className="px-4 py-3 border-b border-border bg-gradient-to-r from-saramsa-gradient-from/5 to-saramsa-gradient-to/5">
                        <div className="text-sm font-medium text-popover-foreground">
                          {currentUser.username}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {currentUser.email || "No email"}
                        </div>
                      </div>
                      <div className="py-1">
                        <button
                          onClick={() => {
                            setOpen(false);
                            window.location.href = "/settings";
                          }}
                          className="w-full flex items-center gap-2 px-4 py-2 text-sm text-popover-foreground hover:bg-accent transition-all duration-300 group"
                        >
                          <Settings className="w-4 h-4 group-hover:rotate-12 transition-transform duration-300" />
                          Settings
                        </button>
                        <button
                          onClick={handleLogout}
                          className="w-full flex items-center gap-2 px-4 py-2 text-sm text-destructive hover:bg-destructive/10 transition-all duration-300 group"
                        >
                          <LogOut className="w-4 h-4 group-hover:translate-x-1 transition-transform duration-300" />
                          Logout
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              )}
              <ThemeToggle />

          
            </div>
          </div>
        </div>
      </nav>
    </>
  );
}
