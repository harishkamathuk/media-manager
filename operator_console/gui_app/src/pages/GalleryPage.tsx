import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { useSearchParams } from "react-router-dom";
import { ErrorAlert } from "@/components/ErrorAlert";
import { PageShell } from "@/components/layout/PageShell";
import { MediaGrid } from "@/components/media/MediaGrid";
import { MediaPreviewModal } from "@/components/media/MediaPreviewModal";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Pagination, PaginationContent, PaginationEllipsis, PaginationItem, PaginationLink, PaginationNext, PaginationPrevious } from "@/components/ui/pagination";
import { Slider } from "@/components/ui/slider";
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { getCanonical, getCanonicalTags } from "@/lib/api/endpoints";
import { queryKeys } from "@/lib/api/queryKeys";
import type { MediaType } from "@/lib/api/queryKeys";
import { queryOptions } from "@/lib/api/queryOptions";
import type { CanonicalFile, PaginatedResponse, Tag } from "@/types";
import { ArrowUpDown, Grid2X2, LayoutGrid, Loader2, Search, X } from "lucide-react";

function getErrorMessage(err: unknown): string | null {
  if (!err) return null;
  if (err instanceof Error) return err.message;
  return String(err);
}

const DENSITY_PRESETS = [
  {
    key: "large",
    label: "Large",
    limit: 12,
    gridClassName: "grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-4",
  },
  {
    key: "medium",
    label: "Medium",
    limit: 20,
    gridClassName: "grid grid-cols-2 gap-4 md:grid-cols-3 xl:grid-cols-5",
  },
  {
    key: "small",
    label: "Small",
    limit: 30,
    gridClassName: "grid grid-cols-2 gap-4 md:grid-cols-4 xl:grid-cols-6",
  },
  {
    key: "compact",
    label: "Compact",
    limit: 42,
    gridClassName: "grid grid-cols-3 gap-4 md:grid-cols-5 xl:grid-cols-7",
  },
] as const;

type DensityKey = (typeof DENSITY_PRESETS)[number]["key"];
type MediaTypeFilter = "all" | MediaType;

function getDensityPreset(densityParam: string | null) {
  return DENSITY_PRESETS.find((preset) => preset.key === densityParam) ?? DENSITY_PRESETS[1];
}

function getMediaTypeFilter(mediaTypeParam: string | null): MediaTypeFilter {
  return mediaTypeParam === "image" || mediaTypeParam === "video" ? mediaTypeParam : "all";
}

function getVisiblePages(currentPage: number, totalPages: number): Array<number | "ellipsis"> {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, index) => index + 1);
  }

  const pages: Array<number | "ellipsis"> = [1];
  if (currentPage > 3) pages.push("ellipsis");

  const start = Math.max(2, currentPage - 1);
  const end = Math.min(totalPages - 1, currentPage + 1);
  for (let page = start; page <= end; page += 1) pages.push(page);

  if (currentPage < totalPages - 2) pages.push("ellipsis");
  pages.push(totalPages);
  return pages;
}

export default function GalleryPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [selectedFile, setSelectedFile] = useState<CanonicalFile | null>(null);
  const [tagInput, setTagInput] = useState("");
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const tagsParam = searchParams.get("tags") || "";
  const selectedTags = useMemo(() => tagsParam.split(",").filter(Boolean), [tagsParam]);
  const sortBy = searchParams.get("sort_by") || "created_at";
  const sortOrder = searchParams.get("sort_order") || "desc";
  const page = Math.max(1, Number(searchParams.get("page") || 1));
  const densityPreset = getDensityPreset(searchParams.get("density"));
  const mediaTypeFilter = getMediaTypeFilter(searchParams.get("media_type"));
  const densityIndex = DENSITY_PRESETS.findIndex((preset) => preset.key === densityPreset.key);

  const updateParams = (updates: Record<string, string | undefined>) => {
    const next = new URLSearchParams(searchParams);
    Object.entries(updates).forEach(([key, value]) => {
      if (value) next.set(key, value);
      else next.delete(key);
    });
    setSearchParams(next);
  };

  const addTag = (tag: string) => {
    if (!tag.trim() || selectedTags.includes(tag)) return;
    updateParams({ tags: [...selectedTags, tag].join(","), page: "1" });
    setTagInput("");
    setSuggestions([]);
  };

  const removeTag = (tag: string) => {
    const nextTags = selectedTags.filter((item) => item !== tag);
    updateParams({ tags: nextTags.length ? nextTags.join(",") : undefined, page: "1" });
  };

  const canonicalParams = useMemo(
    () => ({
      page,
      limit: densityPreset.limit,
      tags: tagsParam || undefined,
      sort_by: sortBy,
      sort_order: sortOrder,
      media_type: mediaTypeFilter === "all" ? undefined : mediaTypeFilter,
    }),
    [densityPreset.limit, mediaTypeFilter, page, sortBy, sortOrder, tagsParam],
  );

  const tagsQuery = useQuery({
    queryKey: queryKeys.canonicalTags(""),
    queryFn: async () => (await getCanonicalTags()).data,
    staleTime: queryOptions.canonicalTags.staleTime,
  });

  const galleryQuery = useQuery({
    queryKey: queryKeys.canonical(canonicalParams),
    queryFn: async () => (await getCanonical(canonicalParams)).data,
    staleTime: queryOptions.canonical.staleTime,
  });

  const data = (galleryQuery.data as PaginatedResponse<CanonicalFile> | undefined) ?? null;
  const items = data?.items ?? [];
  const allTags = useMemo(() => (tagsQuery.data as Tag[] | undefined) ?? [], [tagsQuery.data]);
  const totalCount = data?.total ?? 0;
  const totalPages = Math.max(data?.total_pages ?? 1, 1);
  const visiblePages = useMemo(() => getVisiblePages(page, totalPages), [page, totalPages]);
  const hasActiveFilters = selectedTags.length > 0 || mediaTypeFilter !== "all";
  const activeFilterSummary = [
    selectedTags.length ? `${selectedTags.length} tag filter${selectedTags.length === 1 ? "" : "s"}` : null,
    mediaTypeFilter === "image" ? "Images only" : mediaTypeFilter === "video" ? "Videos only" : null,
  ]
    .filter(Boolean)
    .join(" · ");

  useEffect(() => {
    if (!tagInput) {
      setSuggestions([]);
      return;
    }

    const nextSuggestions = allTags
      .map((tag) => tag.name)
      .filter(
        (name) =>
          name.toLowerCase().includes(tagInput.toLowerCase()) &&
          !selectedTags.includes(name),
      )
      .slice(0, 8);
    setSuggestions(nextSuggestions);
  }, [allTags, selectedTags, tagInput]);

  const controls = (
    <div className="rounded-[28px] border border-border/70 bg-card/70 p-4 shadow-sm backdrop-blur">
      <div className="flex flex-col gap-3">
        <div className="flex flex-wrap gap-3">
          <div className="rounded-2xl border border-border/70 bg-background/85 px-4 py-3 text-sm text-muted-foreground shadow-sm">
            {hasActiveFilters ? `${activeFilterSummary} applied` : "No filters applied yet"}
          </div>
          <div className="rounded-2xl border border-border/70 bg-background/85 px-4 py-3 text-sm text-muted-foreground shadow-sm">
            Sorted by {sortBy.replace("_", " ")} in {sortOrder === "asc" ? "ascending" : "descending"} order
          </div>
          <div className="rounded-2xl border border-border/70 bg-background/85 px-4 py-3 text-sm text-muted-foreground shadow-sm">
            {galleryQuery.isLoading && !data
              ? "Loading gallery..."
              : `${totalCount} item${totalCount === 1 ? "" : "s"} · Page ${page} of ${totalPages}`}
          </div>
        </div>

        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex flex-1 flex-col gap-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-sm font-medium text-foreground">Media type</span>
              <ToggleGroup
                type="single"
                value={mediaTypeFilter}
                onValueChange={(value) => {
                  if (value !== "all" && value !== "image" && value !== "video") return;
                  updateParams({
                    media_type: value === "all" ? undefined : value,
                    page: "1",
                  });
                }}
                variant="outline"
                size="sm"
                aria-label="Filter library by media type"
              >
                <ToggleGroupItem value="all" aria-label="All" data-testid="gallery-media-type-all">
                  All
                </ToggleGroupItem>
                <ToggleGroupItem value="image" aria-label="Images" data-testid="gallery-media-type-images">
                  Images
                </ToggleGroupItem>
                <ToggleGroupItem value="video" aria-label="Videos" data-testid="gallery-media-type-videos">
                  Videos
                </ToggleGroupItem>
              </ToggleGroup>
            </div>

            <div className="relative max-w-md">
              <Input
                value={tagInput}
                onChange={(event) => setTagInput(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" && tagInput) {
                    event.preventDefault();
                    addTag(tagInput);
                  }
                }}
                aria-label="Filter gallery by tag"
                placeholder="Filter gallery by tag"
                className="pl-9"
              />
              <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              {suggestions.length ? (
                <div className="absolute left-0 right-0 top-full z-10 mt-2 overflow-hidden rounded-2xl border border-border bg-popover shadow-lg">
                  {suggestions.map((suggestion) => (
                    <button
                      key={suggestion}
                      type="button"
                      onClick={() => addTag(suggestion)}
                      className="block w-full px-4 py-2 text-left text-sm hover:bg-muted"
                    >
                      {suggestion}
                    </button>
                  ))}
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap gap-2">
              {selectedTags.length ? (
                selectedTags.map((tag) => (
                  <button
                    key={tag}
                    type="button"
                    onClick={() => removeTag(tag)}
                    aria-label={`Remove tag filter ${tag}`}
                    className="inline-flex items-center gap-1 rounded-full border border-primary/20 bg-primary/10 px-3 py-1 text-xs font-medium text-primary"
                  >
                    {tag}
                    <X className="h-3 w-3" />
                  </button>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">
                  No tags selected. Use the search box to narrow the gallery.
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3 self-start lg:self-auto">
            {galleryQuery.isFetching ? <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" /> : null}
            <div className="flex items-center gap-2">
              <Grid2X2 className="h-4 w-4 text-muted-foreground" />
              <Slider
                value={[densityIndex]}
                onValueChange={([value]) => {
                  const nextPreset = DENSITY_PRESETS[value as number];
                  if (!nextPreset) return;
                  updateParams({
                    density: nextPreset.key === "medium" ? undefined : nextPreset.key,
                    page: undefined,
                  });
                }}
                min={0}
                max={DENSITY_PRESETS.length - 1}
                step={1}
                aria-label="Gallery density"
                className="w-24"
              />
              <LayoutGrid className="h-4 w-4 text-muted-foreground" />
              <span className="min-w-14 text-right text-sm text-muted-foreground">
                {densityPreset.label}
              </span>
            </div>
            <select
              value={sortBy}
              onChange={(event) => updateParams({ sort_by: event.target.value, page: "1" })}
              aria-label="Sort gallery by"
              className="h-10 rounded-md border border-input bg-background px-3 text-sm"
            >
              <option value="created_at">Created</option>
              <option value="tag_name">Tag</option>
              <option value="confidence_score">Confidence</option>
            </select>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() =>
                updateParams({
                  sort_order: sortOrder === "asc" ? "desc" : "asc",
                  page: "1",
                })
              }
            >
              <ArrowUpDown className="mr-2 h-4 w-4" />
              {sortOrder === "asc" ? "Ascending" : "Descending"}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <PageShell
      variant="browse-list"
      title="Library"
      description="Library shows usable media by default. Broken, unplayable, and integrity-failed items are excluded from default browsing. Use filters, sorting, preview, and the detail view to quickly find the photo or video you need."
      controls={controls}
    >
      {galleryQuery.error ? (
        <ErrorAlert
          message={getErrorMessage(galleryQuery.error) || "Failed to load gallery"}
        />
      ) : null}

      <div data-page-primary-surface className="-mt-1 space-y-5">
        <MediaGrid
          files={items}
          loading={galleryQuery.isLoading && !data}
          gridClassName={densityPreset.gridClassName}
          skeletonCount={densityPreset.limit}
          density={densityPreset.key}
          emptyTitle="No media files"
          emptyDescription={
            selectedTags.length || mediaTypeFilter !== "all"
              ? "Try adjusting your tag filters, media type, or sort order."
              : "Run an ingest to populate the gallery."
          }
          onPreview={setSelectedFile}
          getDetailHref={(file) => `/gallery/${file.id}`}
          getIntegrityHref={(file) =>
            file.integrity_status === "BROKEN" || file.integrity_status === "SUSPECT" ? "/integrity" : undefined
          }
        />

        {data && totalPages > 1 && (
          <Pagination className="justify-center">
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  href="#"
                  onClick={(event) => {
                    event.preventDefault();
                    if (page === 1) return;
                    updateParams({ page: page - 1 <= 1 ? undefined : String(page - 1) });
                  }}
                  className={page === 1 ? "pointer-events-none opacity-50" : "cursor-pointer"}
                />
              </PaginationItem>
              {visiblePages.map((pageNumber, index) =>
                pageNumber === "ellipsis" ? (
                  <PaginationItem key={`ellipsis-${index}`}>
                    <PaginationEllipsis />
                  </PaginationItem>
                ) : (
                  <PaginationItem key={pageNumber}>
                    <PaginationLink
                      href="#"
                      isActive={pageNumber === page}
                      onClick={(event) => {
                        event.preventDefault();
                        updateParams({ page: pageNumber === 1 ? undefined : String(pageNumber) });
                      }}
                      className="cursor-pointer"
                    >
                      {pageNumber}
                    </PaginationLink>
                  </PaginationItem>
                ),
              )}
              <PaginationItem>
                <PaginationNext
                  href="#"
                  onClick={(event) => {
                    event.preventDefault();
                    if (page >= totalPages) return;
                    updateParams({ page: String(page + 1) });
                  }}
                  className={page >= totalPages ? "pointer-events-none opacity-50" : "cursor-pointer"}
                />
              </PaginationItem>
            </PaginationContent>
          </Pagination>
        )}
      </div>

      <MediaPreviewModal file={selectedFile} onClose={() => setSelectedFile(null)} />
    </PageShell>
  );
}
