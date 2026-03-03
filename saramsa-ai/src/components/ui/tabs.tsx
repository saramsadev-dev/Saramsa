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
        "flex h-10 w-fit items-center justify-center rounded-2xl border border-border/60 bg-secondary/60 p-1",
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
        "flex h-full flex-1 items-center justify-center gap-1.5 rounded-xl border border-transparent px-4 py-2 text-sm font-semibold whitespace-nowrap transition-[background-color,color] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-saramsa-brand/30 disabled:pointer-events-none disabled:opacity-50",
        isActive 
          ? "bg-secondary/80 text-foreground border-border/70" 
          : "text-muted-foreground hover:text-foreground hover:bg-background/80",
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
