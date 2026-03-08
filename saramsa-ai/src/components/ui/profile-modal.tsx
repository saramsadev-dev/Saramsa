'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, User, Mail, LogOut, Settings, Shield } from 'lucide-react';
import { useAuth } from '@/lib/useAuth';
import * as authApi from '@/lib/auth';
import { Button } from '@/components/ui/button';

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function ProfileModal({ isOpen, onClose }: ProfileModalProps) {
  const { user, logout } = useAuth();
  const [userData, setUserData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const fetchUserData = async () => {
      if (isOpen && user) {
        setLoading(true);
        try {
          const data = await authApi.getCurrentUser();
          setUserData(data);
        } catch (error) {
          console.error('Failed to fetch user data:', error);
        } finally {
          setLoading(false);
        }
      }
    };

    fetchUserData();
  }, [isOpen, user]);

  const handleLogout = () => {
    logout();
    onClose();
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 20 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 20 }}
          className="bg-card/95 dark:bg-card/95 rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-border/60 dark:border-border/60">
            <h2 className="text-xl font-semibold text-foreground dark:text-foreground">
              Profile
            </h2>
            <Button
              onClick={onClose}
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-foreground"
            >
              <X className="w-5 h-5" />
            </Button>
          </div>

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-2 border-border/60 border-t-saramsa-brand rounded-full animate-spin" />
              </div>
            ) : (
              <div className="space-y-6">
                {/* User Avatar */}
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-saramsa-gradient-from to-saramsa-gradient-to rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-xl">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-foreground dark:text-foreground">
                      {user?.username || 'User'}
                    </h3>
                    <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                      {user?.role || 'User'}
                    </p>
                  </div>
                </div>

                {/* User Details */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 p-3 bg-secondary/40 dark:bg-secondary/40 rounded-xl">
                    <Mail className="w-4 h-4 text-muted-foreground dark:text-muted-foreground" />
                    <div>
                      <p className="text-sm font-medium text-foreground dark:text-foreground">
                        Email
                      </p>
                      <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                        {user?.email || 'No email provided'}
                      </p>
                    </div>
                  </div>

                  {userData && (
                    <>
                      <div className="flex items-center space-x-3 p-3 bg-secondary/40 dark:bg-secondary/40 rounded-xl">
                        <User className="w-4 h-4 text-muted-foreground dark:text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium text-foreground dark:text-foreground">
                            Full Name
                          </p>
                          <p className="text-sm text-muted-foreground dark:text-muted-foreground">
                            {userData.first_name && userData.last_name
                              ? `${userData.first_name} ${userData.last_name}`
                              : 'Not provided'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-secondary/40 dark:bg-secondary/40 rounded-xl">
                        <Shield className="w-4 h-4 text-muted-foreground dark:text-muted-foreground" />
                        <div>
                          <p className="text-sm font-medium text-foreground dark:text-foreground">
                            Role
                          </p>
                    <p className="text-sm text-muted-foreground dark:text-muted-foreground capitalize">
                      {userData.role || user?.role || 'User'}
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="space-y-2 pt-4 border-t border-border/60 dark:border-border/60">
                  <Button
                    variant="ghost"
                    className="w-full flex items-center space-x-3 p-3 text-left text-muted-foreground dark:text-muted-foreground hover:bg-accent/60 dark:hover:bg-accent/60 rounded-xl transition-colors"
                  >
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </Button>
                  
                  <Button
                    onClick={handleLogout}
                    variant="ghost"
                    className="w-full flex items-center space-x-3 p-3 text-left text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-xl transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </Button>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
} 


