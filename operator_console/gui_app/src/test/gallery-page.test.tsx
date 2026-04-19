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
        total: 2,
        page: 1,
        page_size: 20,
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
    expect(screen.getByText(/Library shows usable media by default\./)).toBeInTheDocument();
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

  it("states the default library visibility rule without introducing integrity actions", async () => {
    renderPage();

    expect(await screen.findByText(/Library shows usable media by default\./)).toBeInTheDocument();
    expect(screen.getByText(/Items marked BROKEN or SUSPECT are excluded from default browsing\./)).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: /integrity/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /integrity/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("tab", { name: /integrity/i })).not.toBeInTheDocument();
  });

  it("shows a per-row Review in Integrity action only for items already marked with an integrity problem", async () => {
    mocks.getCanonical.mockResolvedValueOnce({
      data: {
        items: [
          {
            id: "broken-1",
            filename: "broken.mp4",
            file_type: "video",
            media_url: "/media/broken-1",
            poster_url: "/poster/broken-1",
            matched_tags: ["travel"],
            top_confidence_score: 0.94,
            sort_tag_name: "travel",
            integrity_status: "BROKEN",
          },
          {
            id: "healthy-1",
            filename: "healthy.jpg",
            file_type: "image",
            media_url: "/media/healthy-1",
            poster_url: null,
            matched_tags: ["family"],
            top_confidence_score: 0.88,
            sort_tag_name: "family",
            integrity_status: "OK",
          },
          {
            id: "suspect-1",
            filename: "suspect.mov",
            file_type: "video",
            media_url: "/media/suspect-1",
            poster_url: "/poster/suspect-1",
            matched_tags: ["pets"],
            top_confidence_score: 0.72,
            sort_tag_name: "pets",
            integrity_status: "SUSPECT",
          },
        ],
        total: 3,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    renderPage();

    const integrityLinks = await screen.findAllByRole("link", { name: "Review in Integrity" });
    expect(integrityLinks).toHaveLength(2);
    expect(integrityLinks[0]).toHaveAttribute("href", "/integrity");
    expect(integrityLinks[1]).toHaveAttribute("href", "/integrity");
    expect(screen.getByText("broken.mp4")).toBeInTheDocument();
    expect(screen.getByText("healthy.jpg")).toBeInTheDocument();
    expect(screen.getByText("suspect.mov")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Review healthy.jpg in Integrity" })).not.toBeInTheDocument();
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

  it("requests filtered library items by media type", async () => {
    renderPage();

    await screen.findByText("first.jpg");
    expect(screen.getByText("clip.mp4")).toBeInTheDocument();

    mocks.getCanonical.mockResolvedValueOnce({
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
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.queryByText("clip.mp4")).not.toBeInTheDocument();
      expect(screen.getByText("1 item · Page 1 of 1")).toBeInTheDocument();
      expect(mocks.getCanonical).toHaveBeenLastCalledWith(
        expect.objectContaining({
          media_type: "image",
        }),
      );
    });

    expect(screen.queryByRole("button", { name: "Remove tag filter travel" })).not.toBeInTheDocument();

    mocks.getCanonical.mockResolvedValueOnce({
      data: {
        items: [
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
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "Videos" }));

    await waitFor(() => {
      expect(screen.queryByText("first.jpg")).not.toBeInTheDocument();
      expect(screen.getByText("clip.mp4")).toBeInTheDocument();
      expect(screen.getByText("1 item · Page 1 of 1")).toBeInTheDocument();
      expect(mocks.getCanonical).toHaveBeenLastCalledWith(
        expect.objectContaining({
          media_type: "video",
        }),
      );
    });

    mocks.getCanonical.mockResolvedValueOnce({
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
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "All" }));

    await waitFor(() => {
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.getByText("clip.mp4")).toBeInTheDocument();
      expect(screen.getByText("2 items · Page 1 of 1")).toBeInTheDocument();
      expect(mocks.getCanonical).toHaveBeenLastCalledWith(
        expect.not.objectContaining({
          media_type: expect.anything(),
        }),
      );
    });
  });

  it("clears previous page data when media type filter changes", async () => {
    renderPage();

    await screen.findByText("first.jpg");
    let resolveFiltered: ((value: unknown) => void) | null = null;
    mocks.getCanonical.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolveFiltered = resolve;
        }),
    );

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("Loading gallery...")).toBeInTheDocument();
      expect(screen.queryByText("clip.mp4")).not.toBeInTheDocument();
    });

    resolveFiltered?.({
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
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    await waitFor(() => {
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.queryByText("clip.mp4")).not.toBeInTheDocument();
      expect(screen.getByText("1 item · Page 1 of 1")).toBeInTheDocument();
    });
  });

  it("composes media type and tag filters", async () => {
    renderPage();

    await screen.findByText("first.jpg");

    mocks.getCanonical.mockResolvedValueOnce({
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
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.queryByText("clip.mp4")).not.toBeInTheDocument();
      expect(screen.getByText("Images only applied")).toBeInTheDocument();
    });

    const input = screen.getByPlaceholderText("Filter gallery by tag");
    mocks.getCanonical.mockResolvedValueOnce({
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
        ],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });
    fireEvent.change(input, { target: { value: "travel" } });
    fireEvent.keyDown(input, { key: "Enter" });

    expect(await screen.findByRole("button", { name: "Remove tag filter travel" })).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText("1 tag filter · Images only applied")).toBeInTheDocument();
      expect(screen.getByText("first.jpg")).toBeInTheDocument();
      expect(screen.queryByText("clip.mp4")).not.toBeInTheDocument();
      expect(mocks.getCanonical).toHaveBeenLastCalledWith(
        expect.objectContaining({
          media_type: "image",
          tags: "travel",
        }),
      );
    });
  });

  it("treats media type selection as an active filter in the summary", async () => {
    renderPage();

    await screen.findByText("No filters applied yet");

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("Images only applied")).toBeInTheDocument();
      expect(screen.queryByText("No filters applied yet")).not.toBeInTheDocument();
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
        total: 20,
        page: 2,
        page_size: 10,
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

  it("keeps status count aligned with server-filtered pagination", async () => {
    mocks.getCanonical.mockResolvedValue({
      data: {
        items: [
          { id: "v1", filename: "v1.jpg", file_type: "image", media_url: "/v1", poster_url: null, matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null },
          { id: "v2", filename: "v2.mp4", file_type: "video", media_url: "/v2", poster_url: "/v2", matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null },
        ],
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    renderPage();

    await screen.findByText("2 items · Page 1 of 1");

    mocks.getCanonical.mockResolvedValueOnce({
      data: {
        items: [{ id: "v1", filename: "v1.jpg", file_type: "image", media_url: "/v1", poster_url: null, matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null }],
        total: 3,
        page: 1,
        page_size: 20,
        total_pages: 2,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "Images" }));

    await waitFor(() => {
      expect(screen.getByText("3 items · Page 1 of 2")).toBeInTheDocument();
    });

    mocks.getCanonical.mockResolvedValueOnce({
      data: {
        items: [{ id: "v2", filename: "v2.mp4", file_type: "video", media_url: "/v2", poster_url: "/v2", matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null }],
        total: 1,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "Videos" }));

    await waitFor(() => {
      expect(screen.getByText("1 item · Page 1 of 1")).toBeInTheDocument();
    });

    mocks.getCanonical.mockResolvedValueOnce({
      data: {
        items: [
          { id: "v1", filename: "v1.jpg", file_type: "image", media_url: "/v1", poster_url: null, matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null },
          { id: "v2", filename: "v2.mp4", file_type: "video", media_url: "/v2", poster_url: "/v2", matched_tags: [], top_confidence_score: 0.9, sort_tag_name: null },
        ],
        total: 2,
        page: 1,
        page_size: 20,
        total_pages: 1,
      },
    });

    fireEvent.click(screen.getByRole("radio", { name: "All" }));

    await waitFor(() => {
      expect(screen.getByText("2 items · Page 1 of 1")).toBeInTheDocument();
    });
  });

  it("does not show previous page items while the next page is loading", async () => {
    mocks.getCanonical
      .mockResolvedValueOnce({
        data: {
          items: [
            {
              id: "page-1-image",
              filename: "page-1-image.jpg",
              file_type: "image",
              media_url: "/media/page-1-image",
              poster_url: null,
              matched_tags: [],
              top_confidence_score: 0.91,
              sort_tag_name: null,
            },
            {
              id: "page-1-video",
              filename: "page-1-video.mp4",
              file_type: "video",
              media_url: "/media/page-1-video",
              poster_url: "/poster/page-1-video",
              matched_tags: [],
              top_confidence_score: 0.88,
              sort_tag_name: null,
            },
          ],
          total: 40,
          page: 1,
          page_size: 20,
          total_pages: 2,
        },
      });

    let resolvePageTwo: ((value: unknown) => void) | null = null;
    mocks.getCanonical.mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          resolvePageTwo = resolve;
        }),
    );

    renderPage();

    expect(await screen.findByText("page-1-image.jpg")).toBeInTheDocument();
    expect(screen.getByText("page-1-video.mp4")).toBeInTheDocument();
    expect(screen.getByText("40 items · Page 1 of 2")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("link", { name: "Go to next page" }));

    await waitFor(() => {
      expect(mocks.getCanonical).toHaveBeenLastCalledWith(
        expect.objectContaining({
          page: 2,
        }),
      );
      expect(screen.getByText("Loading gallery...")).toBeInTheDocument();
      expect(screen.queryByText("page-1-image.jpg")).not.toBeInTheDocument();
      expect(screen.queryByText("page-1-video.mp4")).not.toBeInTheDocument();
    });

    resolvePageTwo?.({
      data: {
        items: [
          {
            id: "page-2-image",
            filename: "page-2-image.jpg",
            file_type: "image",
            media_url: "/media/page-2-image",
            poster_url: null,
            matched_tags: [],
            top_confidence_score: 0.82,
            sort_tag_name: null,
          },
        ],
        total: 40,
        page: 2,
        page_size: 20,
        total_pages: 2,
      },
    });

    await waitFor(() => {
      expect(screen.getByText("40 items · Page 2 of 2")).toBeInTheDocument();
      expect(screen.getByText("page-2-image.jpg")).toBeInTheDocument();
      expect(screen.queryByText("page-1-image.jpg")).not.toBeInTheDocument();
    });
  });
});
