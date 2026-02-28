"use client";

import * as React from "react";
import { CheckIcon } from "lucide-react";
import { cn } from "./utils";

interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
  onCheckedChange?: (checked: boolean) => void;
}

function Checkbox({
  className,
  checked,
  onChange,
  onCheckedChange
}: CheckboxProps) {
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    const newChecked = !checked;
    
    // Call onCheckedChange if provided
    if (onCheckedChange) {
      onCheckedChange(newChecked);
    }
    
    // Call onChange if provided
    if (onChange) {
      const syntheticEvent = {
        target: { checked: newChecked },
        currentTarget: { checked: newChecked }
      } as React.ChangeEvent<HTMLInputElement>;
      onChange(syntheticEvent);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      e.stopPropagation();
      
      const newChecked = !checked;
      
      if (onCheckedChange) {
        onCheckedChange(newChecked);
      }
      
      if (onChange) {
        const syntheticEvent = {
          target: { checked: newChecked },
          currentTarget: { checked: newChecked }
        } as React.ChangeEvent<HTMLInputElement>;
        onChange(syntheticEvent);
      }
    }
  };

  return (
    <div 
      className={cn(
        "relative w-4 h-4 border-2 border-border/70 rounded transition-all duration-200 cursor-pointer select-none",
        checked 
          ? "bg-saramsa-brand border-saramsa-brand"
          : "bg-background/80 hover:border-saramsa-brand/40",
        "focus:ring-2 focus:ring-saramsa-brand/30 focus:border-saramsa-brand/40",
        "disabled:cursor-not-allowed disabled:opacity-50",
        className,
      )}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      role="checkbox"
      aria-checked={checked}
      tabIndex={0}
      data-slot="checkbox"
    >
      {checked && (
        <CheckIcon 
          data-slot="checkbox-indicator"
          className="absolute inset-0 w-4 h-4 text-white transition-all duration-200" 
        />
      )}
    </div>
  );
}

export { Checkbox }; 
