import type { ReactNode } from "react";

import { cn } from "@/lib/utils";

type PageShellVariant = "standard-admin" | "workflow" | "browse-list";

interface PageShellProps {
  variant: PageShellVariant;
  title: string;
  description?: string;
  controls?: ReactNode;
  secondary?: ReactNode;
  children: ReactNode;
}

const bodyLayoutClasses: Record<PageShellVariant, string> = {
  "standard-admin": "xl:grid xl:grid-cols-[minmax(0,1.45fr)_22rem] xl:items-start",
  workflow: "min-w-0",
  "browse-list": "min-w-0",
};

export function PageShell({
  variant,
  title,
  description,
  controls,
  secondary,
  children,
}: PageShellProps) {
  const workflow = variant === "workflow";
  const standardAdmin = variant === "standard-admin";

  return (
    <div
      data-page-shell={variant}
      className={cn(
        "mx-auto max-w-7xl px-6 pb-6",
        workflow ? "pt-4" : "pt-6",
      )}
    >
      <div className={cn("flex flex-col", workflow ? "gap-4" : "gap-6")}>
        <header className="space-y-2">
          <h1 className={cn("font-semibold tracking-tight text-foreground", workflow ? "text-3xl" : "text-3xl sm:text-4xl")}>
            {title}
          </h1>
          {description ? (
            <p className="max-w-4xl text-sm leading-6 text-muted-foreground sm:text-base">
              {description}
            </p>
          ) : null}
        </header>

        {controls ? (
          <section
            data-page-shell-controls
            className={cn(
              "min-w-0",
              workflow && "-mt-1",
            )}
          >
            {controls}
          </section>
        ) : null}

        <div className={cn("gap-6", bodyLayoutClasses[variant])}>
          <main className="min-w-0">{children}</main>
          {secondary ? (
            <aside
              data-page-shell-secondary
              className={cn(
                "min-w-0",
                standardAdmin && "mt-6 xl:mt-0",
              )}
            >
              {secondary}
            </aside>
          ) : null}
        </div>
      </div>
    </div>
  );
}
