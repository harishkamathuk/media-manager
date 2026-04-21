import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { ErrorAlert } from "@/components/ErrorAlert";
import { PageShell } from "@/components/layout/PageShell";
import { MediaPreviewModal } from "@/components/media/MediaPreviewModal";
import { StatusBadge } from "@/components/StatusBadge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { getHome } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import { queryOptions } from "@/lib/api/queryOptions";
import type { CanonicalFile, HomePageData } from "@/types";
import { ArrowRight, ImageIcon, Video } from "lucide-react";

function getErrorMessage(err: unknown): string | null {
  if (!err) return null;
  if (err instanceof Error) return err.message;
  return String(err);
}

function MediaThumbCard({
  file,
  onPreview,
}: {
  file: CanonicalFile;
  onPreview: (file: CanonicalFile) => void;
}) {
  const previewSrc = file.file_type === "video" ? file.poster_url ?? null : file.media_url;
  const [imageSrc, setImageSrc] = useState(previewSrc);

  useEffect(() => {
    setImageSrc(previewSrc);
  }, [previewSrc]);

  return (
    <button
      type="button"
      onClick={() => onPreview(file)}
      className="group overflow-hidden rounded-[24px] border border-border/80 bg-card text-left shadow-sm transition-all hover:-translate-y-0.5 hover:border-primary/40 hover:shadow-lg hover:shadow-primary/10"
    >
      <div className="relative aspect-[5/4] overflow-hidden bg-gradient-to-br from-muted via-muted to-secondary/60">
        {imageSrc ? (
          <img
            src={imageSrc}
            alt={file.filename}
            className="h-full w-full object-cover transition-transform duration-300 group-hover:scale-[1.03]"
            onError={() => setImageSrc(null)}
          />
        ) : (
          <div className="flex h-full items-center justify-center">
            {file.file_type === "video" ? (
              <Video className="h-10 w-10 text-muted-foreground" />
            ) : (
              <ImageIcon className="h-10 w-10 text-muted-foreground" />
            )}
          </div>
        )}
        <div className="absolute inset-x-0 bottom-0 h-20 bg-gradient-to-t from-black/65 via-black/15 to-transparent" />
        <div className="absolute left-3 top-3">
          <StatusBadge
            label={file.file_type === "video" ? "Video" : "Image"}
            severity="neutral"
            className="border-white/20 bg-background/85 text-foreground"
          />
        </div>
      </div>
      <div className="space-y-1 p-3">
        <p className="truncate text-sm font-semibold text-foreground">{file.filename}</p>
        <p className="truncate text-xs text-muted-foreground">
          {file.sort_tag_name ?? file.matched_tags[0] ?? "Ready for review"}
        </p>
      </div>
    </button>
  );
}

function SectionHeader({
  title,
  description,
  actionLabel,
  actionHref,
}: {
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
}) {
  return (
    <div className="flex items-end justify-between gap-3">
      <div>
        <h2 className="text-lg font-semibold tracking-tight">{title}</h2>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </div>
      {actionLabel && actionHref ? (
        <Button asChild variant="ghost" size="sm">
          <Link to={actionHref}>
            {actionLabel}
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      ) : null}
    </div>
  );
}

function SummarySkeleton() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, index) => (
        <Skeleton key={index} className="h-24 rounded-2xl" />
      ))}
    </div>
  );
}

function LibrarySummaryCards({
  totalAssets,
  images,
  videos,
  duplicateGroups,
}: {
  totalAssets: number;
  images: number;
  videos: number;
  duplicateGroups: number;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
      <div className="rounded-2xl border border-border/70 bg-background/85 p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Total assets
        </p>
        <p className="mt-2 text-2xl font-semibold">{totalAssets}</p>
      </div>
      <div className="rounded-2xl border border-border/70 bg-background/85 p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Images
        </p>
        <p className="mt-2 text-2xl font-semibold">{images}</p>
      </div>
      <div className="rounded-2xl border border-border/70 bg-background/85 p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Videos
        </p>
        <p className="mt-2 text-2xl font-semibold">{videos}</p>
      </div>
      <div className="rounded-2xl border border-border/70 bg-background/85 p-4 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted-foreground">
          Duplicate groups
        </p>
        <p className="mt-2 text-2xl font-semibold">{duplicateGroups}</p>
      </div>
    </div>
  );
}

function EmptyMediaRow({
  title,
  description,
}: {
  title: string;
  description: string;
}) {
  return (
    <Card className="rounded-[28px] border-dashed">
      <CardContent className="p-6">
        <p className="text-sm font-medium">{title}</p>
        <p className="mt-1 text-sm text-muted-foreground">{description}</p>
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const [selectedFile, setSelectedFile] = useState<CanonicalFile | null>(null);

  const homeQuery = useQuery({
    queryKey: queryKeys.home,
    queryFn: async () => (await getHome()).data as HomePageData,
    staleTime: queryOptions.home.staleTime,
  });

  const home = homeQuery.data;
  const error = getErrorMessage(homeQuery.error);
  const recentImages =
    home?.recent_images ?? (home?.recent_media ?? []).filter((file) => file.file_type === "image");
  const recentVideos =
    home?.recent_videos ?? (home?.recent_media ?? []).filter((file) => file.file_type === "video");
  const secondary = home ? (
    <div className="space-y-6 xl:sticky xl:top-6 xl:self-start">
      <Card className="rounded-[28px] border-border/70 bg-background/90 shadow-sm">
        <CardHeader className="pb-3">
          <CardDescription>Overview of the current library state</CardDescription>
          <CardTitle className="text-xl">Library Snapshot</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm leading-6 text-muted-foreground">
            Canonical media currently available for browsing, review, and follow-up work.
          </p>
          <LibrarySummaryCards
            totalAssets={home.library_summary.total_assets}
            images={home.library_summary.images}
            videos={home.library_summary.videos}
            duplicateGroups={home.library_summary.duplicate_groups}
          />
        </CardContent>
      </Card>

      <Card className="rounded-[28px] border-border/70 shadow-sm">
        <CardHeader className="pb-3">
          <CardDescription>Items that need review before you continue</CardDescription>
          <CardTitle className="text-xl">Needs Attention</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-background/80 p-4">
            <div>
              <p className="text-sm font-semibold">Duplicate groups</p>
              <p className="mt-1 text-sm text-muted-foreground">Review likely duplicate clusters.</p>
            </div>
            <span className="text-2xl font-semibold">{home.attention_summary.duplicate_groups}</span>
          </div>
          <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-background/80 p-4">
            <div>
              <p className="text-sm font-semibold">Failed runs</p>
              <p className="mt-1 text-sm text-muted-foreground">Jobs that need follow-up.</p>
            </div>
            <span className="text-2xl font-semibold">{home.attention_summary.failed_runs}</span>
          </div>
          <div className="flex items-center justify-between rounded-2xl border border-border/70 bg-background/80 p-4">
            <div>
              <p className="text-sm font-semibold">Untagged assets</p>
              <p className="mt-1 text-sm text-muted-foreground">
                Canonical items that still need metadata enrichment.
              </p>
            </div>
            <span className="text-2xl font-semibold">{home.attention_summary.untagged_assets}</span>
          </div>
          <div className="rounded-2xl border border-primary/15 bg-primary/5 p-4">
            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-muted-foreground">
              Recommended workflow
            </p>
            <p className="mt-2 text-sm leading-6 text-foreground/90">
              Start in Organize for guided ingest and review, then use Duplicate Review and
              Library as follow-up tools when you want more detail. Use Admin if
              a job needs troubleshooting.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  ) : null;

  return (
    <PageShell
      variant="standard-admin"
      title="Media Manager"
      description="Browse recent media, review what needs attention, and jump into the guided workflow when you're ready."
      secondary={secondary}
    >
      {error ? <ErrorAlert message={error} /> : null}

      {homeQuery.isLoading && !home ? <SummarySkeleton /> : null}

      {home ? (
        <div className="space-y-6">
          <section className="space-y-4">
            <SectionHeader
              title="Recent Images"
              description="Newest image items ready for review."
              actionLabel="View All Media"
              actionHref="/gallery"
            />
            {recentImages.length ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {recentImages.map((file) => (
                  <MediaThumbCard key={file.id} file={file} onPreview={setSelectedFile} />
                ))}
              </div>
            ) : (
              <EmptyMediaRow
                title="No recent images yet"
                description="Image uploads will appear here once they are added to the library."
              />
            )}
          </section>

          <section className="space-y-4">
            <SectionHeader
              title="Recent Videos"
              description="Newest video items ready for review."
              actionLabel="View All Media"
              actionHref="/gallery"
            />
            {recentVideos.length ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
                {recentVideos.map((file) => (
                  <MediaThumbCard key={file.id} file={file} onPreview={setSelectedFile} />
                ))}
              </div>
            ) : (
              <EmptyMediaRow
                title="No recent videos yet"
                description="Video uploads will appear here once they are added to the library."
              />
            )}
          </section>
        </div>
      ) : null}

      <MediaPreviewModal file={selectedFile} onClose={() => setSelectedFile(null)} />
    </PageShell>
  );
}
