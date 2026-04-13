import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import GalleryPage from "@/pages/GalleryPage";

const mocks = vi.hoisted(() => ({
  getCanonical: vi.fn(),
  getCanonicalTags: vi.fn(),
}));

vi.mock("@/lib/api/endpoints", () => ({
  getCanonical: mocks.getCanonical,
  getCanonicalTags: mocks.getCanonicalTags,
}));

vi.mock("@/components/ui/slider", () => ({
  Slider: ({ value }: { value?: number[] }) => (
    <div data-testid="density-slider">{value?.[0] ?? 0}</div>
  ),
}));

function renderPage(initialEntries?: string[]) {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return render(
    <MemoryRouter initialEntries={initialEntries}>
      <QueryClientProvider client={queryClient}>
        <GalleryPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe("Gallery page", () => {
  beforeEach(() => {
    mocks.getCanonicalTags.mockResolvedValue({
      data: [{ name: "travel" }, { name: "family" }, { name: "pets" }],
    });
    mocks.getCanonical.mockResolvedValue({
      data: {
        items: [
          {
            id: "image-1",
            filename: "first.jpg",
            file_type: "image",
            media_url: "/media/image-1",
            poster_url: null,
            matched_tags: ["travel"],
            top_confidence_score: 0.94,
            sort_tag_name: "travel",
          },
          {
            id: "video-1",
            filename: "clip.mp4",
            file_type: "video",
            media_url: "/media/video-1",
            poster_url: "/poster/video-1",
            matched_tags: ["family"],
            top_confidence_score: 0.88,
            sort_tag_name: "family",
          },
        ],
        total_count: 2,
        page: 1,
        limit: 20,
        total_pages: 1,
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("renders the browse-list shell with library controls above the grid", async () => {
    renderPage();

    expect(await screen.findByText("Library")).toBeInTheDocument();
    expect(
      screen.getByText("Use filters, sorting, preview, and the detail view to quickly find the photo or video you need."),
    ).toBeInTheDocument();
    expect(document.querySelector('[data-page-shell="browse-list"]')).toBeTruthy();
    expect(document.querySelector("[data-page-shell-controls]")).toBeTruthy();
    expect(document.querySelector("[data-page-primary-surface]")).toBeTruthy();
    expect(screen.getByRole("radio", { name: "All" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Images" })).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "Videos" })).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Filter gallery by tag")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Descending" })).toBeInTheDocument();
    expect(await screen.findByText("2 items · Page 1 of 1")).toBeInTheDocument();
    expect(screen.getByText("first.jpg")).toBeInTheDocument();
    expect(screen.getByText("clip.mp4")).toBeInTheDocument();
    expect(screen.getByRole("radio", { name: "All" })).toHaveAttribute("aria-checked", "true");
  });

  it("keeps filter controls interactive inside the shell controls row", async () => {
    renderPage();

    const input = await screen.findByPlaceholderText("Filter gallery by tag");
    fireEvent.change(input, { target: { value: "travel" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(await screen.findByRole("button", { name: "Remove tag filter travel" })).toBeInTheDocument();
    expect(mocks.getCanonical).toHaveBeenLastCalledWith(
      expect.objectContaining({
        page: 1,
        limit: 20,
        tags: "travel",
        sort_by: "created_at",
        sort_order: "desc",
      }),
    );
  });

  it("filters visible library items by media type", async () => {
    renderPage();

    await screen.findByText("first.jpg");
    expect(screen.getByText("clip.mp4")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.queryByText("clip.mp4")).not.toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("radio", { name: "Videos" }));

    await waitFor(() => {
      expect(screen.queryByText("first.jpg")).not.toBeInTheDocument();
      expect(screen.getByText("clip.mp4")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("radio", { name: "All" }));

    await waitFor(() => {
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.getByText("clip.mp4")).toBeInTheDocument();
    });
  });

  it("resets to page 1 when media type filter changes", async () => {
    mocks.getCanonical.mockResolvedValue({
      data: {
        items: Array.from({ length: 20 }, (_, i) => ({
          id: `img-${i}`,
          filename: `img-${i}.jpg`,
          file_type: i % 2 === 0 ? "image" : "video",
          media_url: `/img-${i}`,
          poster_url: i % 2 === 1 ? `/poster-${i}` : null,
          matched_tags: [],
          top_confidence_score: 0.9,
          sort_tag_name: null,
        })),
        total_count: 20,
        page: 2,
        limit: 10,
        total_pages: 2,
      },
    });

    renderPage(["/gallery?page=2&media_type=image"]);

    await screen.findByText("img-10.jpg");
    expect(mocks.getCanonical).toHaveBeenLastCalledWith(
      expect.objectContaining({
        page: 2,
      }),
    );

    fireEvent.click(screen.getByRole("radio", { name: "Videos" }));

    await waitFor(() => {
      expect(mocks.getCanonical).toHaveBeenLastCalledWith(
        expect.objectContaining({
          page: 1,
        }),
      );
    });
  });

  it("updates status count to show filtered count when media type changes", async () => {
    mocks.getCanonical.mockResolvedValue({
      data: {
        items: [
          { id: "v1", filename: "v1.jpg", file_type: "image", media_url: "/v1", poster_url: null, matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null },
          { id: "v2", filename: "v2.mp4", file_type: "video", media_url: "/v2", poster_url: "/v2", matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null },
        ],
        total_count: 2,
        page: 1,
        limit: 20,
        total_pages: 1,
      },
    });

    renderPage();

    await screen.findByText("2 items · Page 1 of 1");

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("1 item · Page 1 of 1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("radio", { name: "Videos" }));

    await waitFor(() => {
      expect(screen.getByText("1 item · Page 1 of 1")).toBeInTheDocument();
    });

    fireEvent.click(screen.getByRole("radio", { name: "All" }));

    await waitFor(() => {
      expect(screen.getByText("2 items · Page 1 of 1")).toBeInTheDocument();
    });
  });
});
