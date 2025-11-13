"use client";

import * as React from "react";
import { cn } from "./utils";

interface TabsProps {
  value: string;
  onValueChange: (value: string) => void;
  className?: string;
  children: React.ReactNode;
}

interface TabsListProps {
  className?: string;
  children: React.ReactNode;
}

interface TabsTriggerProps {
  value: string;
  className?: string;
  children: React.ReactNode;
  isActive?: boolean;
  onClick?: () => void;
}

interface TabsContentProps {
  value: string;
  className?: string;
  children: React.ReactNode;
  isActive?: boolean;
}

function Tabs({ value, onValueChange, className, children }: TabsProps) {
  return (
    <div className={cn("flex flex-col gap-2", className)}>
      {React.Children.map(children, (child) => {
        if (React.isValidElement(child)) {
          return React.cloneElement(child, { 
            value, 
            onValueChange,
            isActive: (child.props as any).value === value 
          } as any);
        }
        return child;
      })}
    </div>
  );
}

function TabsList({ className, children }: TabsListProps) {
  return (
    <div
      className={cn(
        "bg-gray-100 dark:bg-gray-700 flex h-9 w-fit items-center justify-center rounded-xl p-[3px]",
        className,
      )}
    >
      {children}
    </div>
  );
}

function TabsTrigger({ value, className, children, isActive, onClick }: TabsTriggerProps) {
  return (
    <button
      data-state={isActive ? "active" : "inactive"}
      className={cn(
        "flex h-[calc(100%-1px)] flex-1 items-center justify-center gap-1.5 rounded-xl border border-transparent px-2 py-1 text-sm font-medium whitespace-nowrap transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 disabled:pointer-events-none disabled:opacity-50",
        isActive 
          ? "bg-gradient-to-r from-[#E603EB] to-[#8B5FBF] text-white shadow-sm" 
          : "text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-50 dark:hover:bg-gray-600",
        className,
      )}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function TabsContent({ value, className, children, isActive }: TabsContentProps) {
  if (!isActive) return null;
  
  return (
    <div
      className={cn("flex-1 outline-none", className)}
    >
      {children}
    </div>
  );
}

export { Tabs, TabsList, TabsTrigger, TabsContent };
