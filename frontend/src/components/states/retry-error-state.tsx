"use client";

import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ErrorState, type ErrorStateProps } from "./error-state";

export interface RetryErrorStateProps extends Omit<ErrorStateProps, "action"> {
  onRetry: () => void;
  retryLabel?: string;
  isRetrying?: boolean;
}

export function RetryErrorState({
  onRetry,
  retryLabel = "Try again",
  isRetrying = false,
  ...props
}: RetryErrorStateProps) {
  return (
    <ErrorState
      {...props}
      action={
        <Button
          type="button"
          variant="secondary"
          onClick={onRetry}
          disabled={isRetrying}
        >
          <RefreshCw aria-hidden="true" />
          {isRetrying ? "Retrying…" : retryLabel}
        </Button>
      }
    />
  );
}
