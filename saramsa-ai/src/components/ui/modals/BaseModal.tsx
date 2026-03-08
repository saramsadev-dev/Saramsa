"use client";

import type { ReactNode, MouseEvent } from "react";
import { useId } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { X } from 'lucide-react';
import { Button } from "../button";

type ModalSize = "sm" | "md" | "lg";

const panelSizes: Record<ModalSize, string> = {
  sm: "max-w-md",
  md: "max-w-2xl",
  lg: "max-w-4xl",
};

export interface BaseModalProps {
  isOpen: boolean;
  onClose: () => void;
  /**
   * Optional title rendered in the modal header.
   */
  title?: ReactNode;
  /**
   * Optional supporting text rendered under the title.
   */
  description?: ReactNode;
  /**
   * Optional icon or element displayed next to the title.
   */
  icon?: ReactNode;
  /**
   * Primary modal content.
   */
  children: ReactNode;
  /**
   * Footer node (usually action buttons).
   */
  footer?: ReactNode;
  /**
   * Override the default header with custom content.
   */
  headerContent?: ReactNode;
  /**
   * Size preset that controls the panel max width.
   */
  size?: ModalSize;
  /**
    * Additional classes for the motion panel.
    */
  className?: string;
  /**
   * Additional classes for the overlay.
   */
  overlayClassName?: string;
  /**
   * Hide the default close button.
   */
  hideCloseButton?: boolean;
  /**
   * Accessible label for the close button.
   */
  closeButtonLabel?: string;
}

export function BaseModal({
  isOpen,
  onClose,
  title,
  description,
  icon,
  children,
  footer,
  headerContent,
  size = "md",
  className = "",
  overlayClassName = "",
  hideCloseButton = false,
  closeButtonLabel = "Close modal",
}: BaseModalProps) {
  const titleId = useId();
  const descriptionId = useId();

  const handleOverlayClick = () => {
    onClose();
  };

  const handlePanelClick = (event: MouseEvent<HTMLDivElement>) => {
    event.stopPropagation();
  };

  const sizeClass = panelSizes[size] ?? panelSizes.md;

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className={`fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-[9999] p-4 ${overlayClassName}`}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={handleOverlayClick}
        >
          <motion.div
            role="dialog"
            aria-modal="true"
            aria-labelledby={title ? titleId : undefined}
            aria-describedby={description ? descriptionId : undefined}
            className={`w-full ${sizeClass} rounded-3xl bg-card/95 shadow-[0_30px_90px_-40px_rgba(15,23,42,0.7)] border border-border/60 backdrop-blur-sm ${className}`}
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            onClick={handlePanelClick}
          >
            {(title || description || icon || headerContent || !hideCloseButton) && (
              <div className="flex items-start justify-between gap-4 p-6 border-b border-border/60">
                {headerContent ?? (
                  <div className="flex items-start gap-4">
                    {icon && <div className="flex-shrink-0">{icon}</div>}
                    <div className="space-y-1">
                      {title && (
                        <h3 id={titleId} className="text-lg font-semibold text-foreground">
                          {title}
                        </h3>
                      )}
                      {description && (
                        <p id={descriptionId} className="text-sm text-muted-foreground">
                          {description}
                        </p>
                      )}
                    </div>
                  </div>
                )}
                {!hideCloseButton && (
                  <Button
                    type="button"
                    onClick={onClose}
                    variant="ghost"
                    size="icon"
                    className="h-9 w-9 rounded-xl text-muted-foreground hover:text-foreground hover:bg-accent/70"
                    aria-label={closeButtonLabel}
                  >
                    <X className="w-5 h-5" />
                  </Button>
                )}
              </div>
            )}

            <div className="p-6">{children}</div>

            {footer && (
              <div className="p-6 border-t border-border/60">
                {footer}
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

