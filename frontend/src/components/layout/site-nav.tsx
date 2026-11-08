"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "/campaigns", label: "Campaigns" },
  { href: "/campaigns/new", label: "New campaign" },
] as const;

export function SiteNav() {
  const pathname = usePathname();
  const inCampaignSection =
    pathname === "/campaigns" ||
    (pathname.startsWith("/campaigns/") && pathname !== "/campaigns/new");

  return (
    <nav aria-label="Primary" className="flex items-center gap-1">
      {LINKS.map((link) => {
        const isActive =
          link.href === "/campaigns"
            ? inCampaignSection
            : pathname === link.href;

        return (
          <Link
            key={link.href}
            href={link.href}
            aria-current={isActive ? "page" : undefined}
            className={cn(
              buttonVariants({
                variant: isActive ? "secondary" : "ghost",
                size: "sm",
              }),
            )}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
