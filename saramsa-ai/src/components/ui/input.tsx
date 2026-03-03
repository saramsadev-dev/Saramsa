import * as React from "react"
import { cn } from "./utils"

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {
  // Extends all standard input attributes
}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex h-10 w-full rounded-xl border border-border/60 bg-background/80 px-3 py-2 text-sm ring-offset-background transition-[border-color] file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:border-saramsa-brand/30 focus-visible:ring-2 focus-visible:ring-saramsa-brand/20 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
          className
        )}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"

export { Input } 
