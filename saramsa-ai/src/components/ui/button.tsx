import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "./utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold tracking-[0.01em] cursor-pointer transition-[background-color,color] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-saramsa-brand/30 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground hover:bg-primary/95",
        destructive:
          "bg-destructive text-destructive-foreground hover:bg-destructive/95",
        outline:
          "border border-border bg-background text-foreground hover:bg-secondary hover:text-accent-foreground dark:border-border/70 dark:bg-background/70 dark:hover:bg-accent/60",
        secondary:
          "bg-secondary text-secondary-foreground hover:bg-secondary/90 dark:bg-secondary/80",
        ghost: "hover:bg-secondary hover:text-accent-foreground dark:hover:bg-accent/60",
        link: "text-primary underline-offset-4 hover:underline",
        saramsa:
          "bg-saramsa-brand text-white hover:bg-saramsa-brand-hover",
      },
      size: {
        default: "h-10 px-5",
        sm: "h-9 rounded-lg px-3 text-xs",
        lg: "h-11 rounded-xl px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
