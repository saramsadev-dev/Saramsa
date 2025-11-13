'use client';

import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, User, Mail, LogOut, Settings, Shield } from 'lucide-react';
import { useAuth } from '@/lib/useAuth';
import * as authApi from '@/lib/auth';

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
          className="bg-white dark:bg-gray-800 rounded-xl shadow-2xl w-full max-w-md overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200 dark:border-gray-700">
            <h2 className="text-xl font-semibold text-gray-900 dark:text-white">
              Profile
            </h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-2 border-gray-300 border-t-[#E603EB] rounded-full animate-spin" />
              </div>
            ) : (
              <div className="space-y-6">
                {/* User Avatar */}
                <div className="flex items-center space-x-4">
                  <div className="w-16 h-16 bg-gradient-to-br from-[#E603EB] to-[#8B5FBF] rounded-full flex items-center justify-center">
                    <span className="text-white font-bold text-xl">
                      {user?.username?.charAt(0).toUpperCase() || 'U'}
                    </span>
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                      {user?.username || 'User'}
                    </h3>
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                      {user?.role || 'User'}
                    </p>
                  </div>
                </div>

                {/* User Details */}
                <div className="space-y-4">
                  <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                    <Mail className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        Email
                      </p>
                      <p className="text-sm text-gray-600 dark:text-gray-400">
                        {user?.email || 'No email provided'}
                      </p>
                    </div>
                  </div>

                  {userData && (
                    <>
                      <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <User className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            Full Name
                          </p>
                          <p className="text-sm text-gray-600 dark:text-gray-400">
                            {userData.first_name && userData.last_name
                              ? `${userData.first_name} ${userData.last_name}`
                              : 'Not provided'}
                          </p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3 p-3 bg-gray-50 dark:bg-gray-700 rounded-lg">
                        <Shield className="w-4 h-4 text-gray-500 dark:text-gray-400" />
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white">
                            Role
                          </p>
                    <p className="text-sm text-gray-600 dark:text-gray-400 capitalize">
                      {userData.role || user?.role || 'User'}
                          </p>
                        </div>
                      </div>
                    </>
                  )}
                </div>

                {/* Actions */}
                <div className="space-y-2 pt-4 border-t border-gray-200 dark:border-gray-700">
                  <button className="w-full flex items-center space-x-3 p-3 text-left text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors">
                    <Settings className="w-4 h-4" />
                    <span>Settings</span>
                  </button>
                  
                  <button
                    onClick={handleLogout}
                    className="w-full flex items-center space-x-3 p-3 text-left text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                    <span>Logout</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
} 