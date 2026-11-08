"use client";

import { RefreshCw } from "lucide-react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export interface RetryRefreshButtonProps {
  label?: string;
}

export function RetryRefreshButton({ label = "Try again" }: RetryRefreshButtonProps) {
  const router = useRouter();

  return (
    <Button type="button" variant="secondary" onClick={() => router.refresh()}>
      <RefreshCw aria-hidden="true" />
      {label}
    </Button>
  );
}
