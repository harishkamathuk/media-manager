import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import AdminPage from "@/pages/AdminPage";

const mocks = vi.hoisted(() => ({
  adminDbReset: vi.fn(),
  cancelBenchmarkRun: vi.fn(),
  getAdminAppSettings: vi.fn(),
  getAdminObservabilityFailures: vi.fn(),
  getAdminObservabilityMetricsSeries: vi.fn(),
  getAdminObservabilityOperationRuns: vi.fn(),
  getAdminObservabilitySummary: vi.fn(),
  getAnalytics: vi.fn(),
  getBenchmarkRun: vi.fn(),
  getBenchmarkRuns: vi.fn(),
  getHashAudit: vi.fn(),
  getMediaByHash: vi.fn(),
  getMediaByStatus: vi.fn(),
  getMediaHistory: vi.fn(),
  getPolicy: vi.fn(),
  getReappearances: vi.fn(),
  getRuns: vi.fn(),
  invalidateAllReadsAfterDbReset: vi.fn(),
  invalidateReadsAfterPolicyUpdate: vi.fn(),
  queueDiscoveryBenchmark: vi.fn(),
  queueMetadataBenchmark: vi.fn(),
  reconcileStaleOperationRuns: vi.fn(),
  updatePolicy: vi.fn(),
}));

vi.mock("@/lib/api/endpoints", () => ({
  adminDbReset: mocks.adminDbReset,
  cancelBenchmarkRun: mocks.cancelBenchmarkRun,
  getAdminAppSettings: mocks.getAdminAppSettings,
  getAdminObservabilityFailures: mocks.getAdminObservabilityFailures,
  getAdminObservabilityMetricsSeries: mocks.getAdminObservabilityMetricsSeries,
  getAdminObservabilityOperationRuns: mocks.getAdminObservabilityOperationRuns,
  getAdminObservabilitySummary: mocks.getAdminObservabilitySummary,
  getAnalytics: mocks.getAnalytics,
  getBenchmarkRun: mocks.getBenchmarkRun,
  getBenchmarkRuns: mocks.getBenchmarkRuns,
  getHashAudit: mocks.getHashAudit,
  getMediaByHash: mocks.getMediaByHash,
  getMediaByStatus: mocks.getMediaByStatus,
  getMediaHistory: mocks.getMediaHistory,
  getPolicy: mocks.getPolicy,
  getReappearances: mocks.getReappearances,
  getRuns: mocks.getRuns,
  invalidateAllReadsAfterDbReset: mocks.invalidateAllReadsAfterDbReset,
  invalidateReadsAfterPolicyUpdate: mocks.invalidateReadsAfterPolicyUpdate,
  queueDiscoveryBenchmark: mocks.queueDiscoveryBenchmark,
  queueMetadataBenchmark: mocks.queueMetadataBenchmark,
  reconcileStaleOperationRuns: mocks.reconcileStaleOperationRuns,
  updatePolicy: mocks.updatePolicy,
}));

function renderPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <MemoryRouter initialEntries={["/admin?tab=activity"]}>
      <QueryClientProvider client={queryClient}>
        <AdminPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

function renderLibraryRulesPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <MemoryRouter initialEntries={["/admin?tab=library-rules"]}>
      <QueryClientProvider client={queryClient}>
        <AdminPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

function renderSystemHealthPage() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });

  return render(
    <MemoryRouter initialEntries={["/admin?tab=system-health"]}>
      <QueryClientProvider client={queryClient}>
        <AdminPage />
      </QueryClientProvider>
    </MemoryRouter>,
  );
}

describe("Admin page", () => {
  beforeEach(() => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue({
      ok: true,
      json: async () => [],
    } as Response);
    mocks.getRuns.mockResolvedValue({
      data: {
        items: [
          {
            operation_run_id: "run-1",
            operation_type: "PLAN",
            status: "STARTED",
            started_at: "2026-03-15T10:00:00Z",
            completed_at: null,
            duration_ms: null,
            linked_run_id: "durable-1",
            context: {},
            details: {},
          },
        ],
      },
    });
    mocks.getPolicy.mockResolvedValue({
      data: {
        canonical_priority: {
          selected_policy: "FIRST_SEEN",
          preferred_roots: [],
        },
        integrity: {
          default_scan_mode: "FAST",
          issue_min_confidence: 0.9,
          notify_on_high_confidence: true,
        },
        duplicate_reclaim: {
          archive_root: "/tmp/media-manager/reclaim",
          default_retention_days: 14,
          notify_on_reviewed_safe: true,
        },
        retention: {
          quarantine_root: "/tmp/media-manager/quarantine",
          recycle_bin_root: "/tmp/media-manager/recycle-bin",
          quarantine_retention_days: 14,
          recycle_purge_days: 30,
        },
        automation: {
          mode: "NOTIFY_ONLY",
        },
        naming: {
          strategy: "SHARED_CANONICAL_NAME",
        },
        recanonicalization: {
          enabled: false,
        },
        metadata: {
          version: 3,
          updated_at: "2026-03-20T10:00:00Z",
        },
        tie_breaker_rules: {
          policy_name: "default",
          policy_version: 1,
          effective_order: ["first_seen_at ASC", "file_instance_id ASC"],
        },
      },
    });
    mocks.getAdminObservabilitySummary.mockResolvedValue({
      data: {
        metrics_enabled: true,
        prometheus_url: null,
        grafana_url: null,
        generated_at: "2026-03-20T10:00:00Z",
        window_hours: 24,
        recent_failure_count: 2,
        recent_runs_by_status: { COMPLETED: 8, FAILED: 2, STARTED: 1 },
        recent_runs_by_type: { PLAN: 4 },
        last_success_by_type: { PLAN: "2026-03-20T09:00:00Z" },
        latest_metrics: {
          apply_time_ms: 88.5,
          cache_hit_rate: 91.2,
          ingest_time_ms: 12,
          canonicalize_time_ms: 10,
          tag_time_ms: 9,
        },
      },
    });
    mocks.getAdminObservabilityOperationRuns.mockResolvedValue({
      data: [
        {
          operation_run_id: "run-1",
          operation_type: "PLAN",
          status: "STARTED",
          started_at: "2026-03-15T10:00:00Z",
          completed_at: null,
          duration_ms: null,
          linked_run_id: null,
          context: {},
          error_message: null,
        },
      ],
    });
    mocks.getAdminObservabilityFailures.mockResolvedValue({
      data: {
        failure_events: [],
        failed_operation_runs: [],
      },
    });
    mocks.getAdminObservabilityMetricsSeries.mockResolvedValue({
      data: {
        hours: 24,
        series: {
          operation_volume: [{ timestamp: "2026-03-20T09:00:00Z", value: 4 }],
          failure_volume: [{ timestamp: "2026-03-20T09:00:00Z", value: 1 }],
          latency_ms_avg: [{ timestamp: "2026-03-20T09:00:00Z", value: 88.5 }],
        },
      },
    });
    mocks.reconcileStaleOperationRuns.mockResolvedValue({
      data: {
        cutoff: "2026-03-20T00:00:00+00:00",
        scanned_count: 3,
        updated_count: 2,
        include_current_day: false,
      },
    });
    mocks.getAdminAppSettings.mockResolvedValue({
      data: {
        items: [
          {
            key: "video_thumbnails_enabled",
            category: "ui",
            value_type: "bool",
            is_sensitive: false,
            runtime_dual_read_enabled: true,
            db_present: true,
            effective_source: "db",
            updated_at: "2026-03-20T10:00:00Z",
            updated_by: "tester",
            version: 1,
            source: "bootstrap",
            value_json: { value: true },
          },
          {
            key: "directory_picker_enabled",
            category: "ui",
            value_type: "bool",
            is_sensitive: false,
            runtime_dual_read_enabled: false,
            db_present: false,
            effective_source: null,
            updated_at: null,
            updated_by: null,
            version: null,
            source: null,
          },
          {
            key: "admin_api_token",
            category: "admin_safety",
            value_type: "string",
            is_sensitive: true,
            runtime_dual_read_enabled: true,
            db_present: true,
            effective_source: "env_fallback",
            updated_at: "2026-03-20T11:00:00Z",
            updated_by: "tester",
            version: 2,
            source: "bootstrap",
            value_redacted: true,
          },
        ],
      },
    });
  });

  afterEach(() => {
    vi.clearAllMocks();
    vi.unstubAllGlobals();
  });

  it("renders the live progress panel in the activity detail rail", async () => {
    renderPage();

    const pageHeader = screen.getByTestId("admin-page-header");
    const sectionNav = screen.getByTestId("admin-page-section-nav");
    expect(pageHeader.querySelector("button")).toBeNull();
    expect(pageHeader.querySelector("a")).toBeNull();
    expect(sectionNav).toBeInTheDocument();
    expect(await screen.findByRole("tab", { name: "Activity" })).toBeInTheDocument();
    expect(screen.getByText("What happened in this job")).toBeInTheDocument();
    expect(await screen.findByText("[ WAITING FOR LOGS ]")).toBeInTheDocument();
  });

  it("renders the library rules tab without crashing", async () => {
    renderLibraryRulesPage();

    expect(await screen.findByRole("tab", { name: "Library Rules" })).toBeInTheDocument();
    expect(await screen.findByText("How should the app choose the main version?")).toBeInTheDocument();
    expect(screen.getByText("How should filenames be built after the main version is chosen?")).toBeInTheDocument();
    expect(screen.getByText("Default naming")).toBeInTheDocument();
    expect(screen.getByText("Preferred folders")).toBeInTheDocument();
    expect(screen.getByText("Change state")).toBeInTheDocument();
  });

  it("saves naming strategy changes as default library rules", async () => {
    mocks.updatePolicy.mockResolvedValue({
      data: {
        canonical_priority: {
          selected_policy: "FIRST_SEEN",
          preferred_roots: [],
        },
        integrity: {
          default_scan_mode: "FAST",
          issue_min_confidence: 0.9,
          notify_on_high_confidence: true,
        },
        duplicate_reclaim: {
          archive_root: "/tmp/media-manager/reclaim",
          default_retention_days: 14,
          notify_on_reviewed_safe: true,
        },
        retention: {
          quarantine_root: "/tmp/media-manager/quarantine",
          recycle_bin_root: "/tmp/media-manager/recycle-bin",
          quarantine_retention_days: 14,
          recycle_purge_days: 30,
        },
        automation: {
          mode: "NOTIFY_ONLY",
        },
        naming: {
          strategy: "DUPLICATE_OWNS_DATE_STANDARDIZED",
        },
        recanonicalization: {
          enabled: false,
        },
        metadata: {
          version: 4,
          updated_at: "2026-03-22T10:00:00Z",
        },
        tie_breaker_rules: {
          policy_name: "default",
          policy_version: 1,
          effective_order: ["first_seen_at ASC", "file_instance_id ASC"],
        },
      },
    });

    renderLibraryRulesPage();

    fireEvent.click(await screen.findByRole("button", { name: /Duplicate owns date \(standardized\)/ }));
    fireEvent.click(screen.getByRole("button", { name: /Save library rules/i }));

    await waitFor(() =>
      expect(mocks.updatePolicy).toHaveBeenCalledWith({
        selected_policy: "FIRST_SEEN",
        naming_strategy: "DUPLICATE_OWNS_DATE_STANDARDIZED",
        preferred_roots: [],
        integrity_scan_default_mode: "FAST",
        integrity_issue_min_confidence: 0.9,
        integrity_notify_on_high_confidence: true,
        duplicate_reclaim_archive_root: "/tmp/media-manager/reclaim",
        duplicate_reclaim_default_retention_days: 14,
        duplicate_reclaim_notify_on_reviewed_safe: true,
        integrity_quarantine_root: "/tmp/media-manager/quarantine",
        integrity_quarantine_retention_days: 14,
        recycle_bin_root: "/tmp/media-manager/recycle-bin",
        recycle_purge_days: 30,
        automation_mode: "NOTIFY_ONLY",
        recanonicalization_enabled: false,
        version: 3,
      }),
    );
  });

  it("renders stale operation run reconciliation controls on system health", async () => {
    renderSystemHealthPage();

    expect(await screen.findByText("Reconcile stale operation runs")).toBeInTheDocument();
    expect(screen.getByLabelText("Include today's STARTED runs")).not.toBeChecked();
    expect(screen.getByRole("button", { name: "Reconcile Stale Runs" })).toBeInTheDocument();
  });

  it("runs stale operation reconciliation without current-day override by default", async () => {
    renderSystemHealthPage();

    fireEvent.click(await screen.findByRole("button", { name: "Reconcile Stale Runs" }));

    await waitFor(() =>
      expect(mocks.reconcileStaleOperationRuns).toHaveBeenCalledWith({ include_current_day: false }),
    );
    expect(await screen.findByText(/Scanned: 3/)).toBeInTheDocument();
    expect(screen.getByText(/Updated: 2/)).toBeInTheDocument();
    expect(screen.getByText(/Included today: No/)).toBeInTheDocument();
  });

  it("passes the current-day override when selected", async () => {
    mocks.reconcileStaleOperationRuns.mockResolvedValueOnce({
      data: {
        cutoff: "2026-03-20T10:30:00+00:00",
        scanned_count: 5,
        updated_count: 4,
        include_current_day: true,
      },
    });

    renderSystemHealthPage();

    fireEvent.click(await screen.findByLabelText("Include today's STARTED runs"));
    fireEvent.click(screen.getByRole("button", { name: "Reconcile Stale Runs" }));

    await waitFor(() =>
      expect(mocks.reconcileStaleOperationRuns).toHaveBeenCalledWith({ include_current_day: true }),
    );
    expect(await screen.findByText(/Included today: Yes/)).toBeInTheDocument();
  });

  it("renders the app settings inspection section with read-only values", async () => {
    renderSystemHealthPage();

    expect(await screen.findByText("App settings inspection")).toBeInTheDocument();
    expect(screen.getByText("video_thumbnails_enabled")).toBeInTheDocument();
    expect(screen.getAllByText("Dual-read enabled").length).toBeGreaterThan(0);
    expect(screen.getByText("Runtime source: DB")).toBeInTheDocument();
    expect(screen.getByText('{"value":true}')).toBeInTheDocument();
  });

  it("redacts sensitive app setting values", async () => {
    renderSystemHealthPage();

    expect((await screen.findAllByText("Sensitive value redacted")).length).toBeGreaterThan(0);
    expect(screen.queryByText("super-secret-token")).not.toBeInTheDocument();
  });

  it("labels non-dual-read app settings as inspection only", async () => {
    renderSystemHealthPage();

    expect(await screen.findByText("directory_picker_enabled")).toBeInTheDocument();
    expect(screen.getAllByText("Inspection only").length).toBeGreaterThan(0);
    expect(screen.getByText("DB presence does not make this an active runtime authority.")).toBeInTheDocument();
    expect(screen.getByText("No DB value")).toBeInTheDocument();
  });

  it("shows env fallback as the runtime source for dual-read app settings when returned", async () => {
    renderSystemHealthPage();

    expect(await screen.findByText("Runtime source: env fallback")).toBeInTheDocument();
  });

  it("shows an empty state when no app settings are returned", async () => {
    mocks.getAdminAppSettings.mockResolvedValueOnce({
      data: {
        items: [],
      },
    });

    renderSystemHealthPage();

    expect(await screen.findByText("No app settings were returned by the inspection endpoint.")).toBeInTheDocument();
  });

  it("shows an error state when app settings inspection fails", async () => {
    mocks.getAdminAppSettings.mockRejectedValueOnce(new Error("network down"));

    renderSystemHealthPage();

    expect(await screen.findByText("Unable to load app settings inspection. network down")).toBeInTheDocument();
  });
});
