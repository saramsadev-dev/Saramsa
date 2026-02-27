import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap rounded-xl text-sm font-semibold tracking-[0.01em] transition-[transform,box-shadow,background-color,color] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-saramsa-brand/40 focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
  {
    variants: {
      variant: {
        default:
          "bg-primary text-primary-foreground shadow-[0_8px_20px_-12px_rgba(15,23,42,0.55)] hover:bg-primary/95 hover:shadow-[0_12px_30px_-16px_rgba(15,23,42,0.6)] hover:-translate-y-0.5",
        destructive:
          "bg-destructive text-destructive-foreground shadow-[0_8px_20px_-12px_rgba(127,29,29,0.45)] hover:bg-destructive/95 hover:shadow-[0_12px_30px_-16px_rgba(127,29,29,0.55)] hover:-translate-y-0.5",
        outline:
          "border border-border/70 bg-background/70 text-foreground shadow-[inset_0_0_0_1px_rgba(255,255,255,0.02)] hover:bg-accent/60 hover:text-accent-foreground hover:shadow-[0_10px_24px_-18px_rgba(15,23,42,0.35)]",
        secondary:
          "bg-secondary/80 text-secondary-foreground shadow-sm hover:bg-secondary/90 hover:-translate-y-0.5",
        ghost: "hover:bg-accent/60 hover:text-accent-foreground",
        link: "text-primary underline-offset-4 hover:underline",
        saramsa:
          "bg-gradient-to-r from-saramsa-gradient-from to-saramsa-gradient-to text-white shadow-[0_14px_30px_-18px_rgba(230,3,235,0.65)] hover:shadow-[0_18px_40px_-20px_rgba(230,3,235,0.75)] hover:-translate-y-0.5",
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
