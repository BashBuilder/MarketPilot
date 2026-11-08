"use client";

import type { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export interface ApprovalDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  confirmLabel: string;
  onConfirm: () => void | Promise<void>;
  isPending: boolean;
  confirmDisabled?: boolean;
  children?: ReactNode;
}

export function ApprovalDialog({
  open,
  onOpenChange,
  title,
  description,
  confirmLabel,
  onConfirm,
  isPending,
  confirmDisabled = false,
  children,
}: ApprovalDialogProps) {
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (isPending && !next) return;
        onOpenChange(next);
      }}
    >
      <DialogContent showCloseButton={!isPending}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>

        {children}

        <DialogFooter>
          <DialogClose
            render={<Button type="button" variant="outline" disabled={isPending} />}
          >
            Cancel
          </DialogClose>
          <Button
            type="button"
            onClick={() => void onConfirm()}
            disabled={isPending || confirmDisabled}
            aria-busy={isPending}
          >
            {isPending ? "Working…" : confirmLabel}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
