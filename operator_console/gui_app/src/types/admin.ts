import type { LatestMetrics } from "@/types/dashboard";
import type { Run } from "@/types/runs";

export interface AdminAppSettingPatchPayload {
  value: boolean | number;
  version: number;
}

export interface AppSettingInspectionItem {
  key: string;
  category: string;
  value_type: string;
  is_sensitive: boolean;
  editable_in_slice: boolean;
  runtime_dual_read_enabled: boolean;
  db_present: boolean;
  effective_source: "db" | "env_fallback" | null;
  updated_at: string | null;
  updated_by: string | null;
  version: number | null;
  source: string | null;
  value_redacted?: boolean;
  value_json?: Record<string, unknown>;
}

export interface AppSettingsInspection {
  items: AppSettingInspectionItem[];
}

export interface DbResetPreview {
  affected_tables: string[];
  record_counts?: Record<string, number>;
  warnings?: string[];
  message?: string;
  dry_run?: boolean;
}

export interface DbResetResult {
  success: boolean;
  affected_tables: string[];
  message: string;
  dry_run: boolean;
}

export interface ObservabilitySummary {
  metrics_enabled: boolean;
  prometheus_url?: string | null;
  grafana_url?: string | null;
  generated_at: string;
  window_hours: number;
  recent_failure_count: number;
  recent_runs_by_status: Record<string, number>;
  recent_runs_by_type: Record<string, number>;
  last_success_by_type: Record<string, string | null>;
  latest_metrics: LatestMetrics;
}

export interface FailureEventItem {
  id: string;
  run_id: string;
  phase: string;
  error_code: string;
  error_message: string;
  created_at: string;
}

export interface ObservabilityFailures {
  failure_events: FailureEventItem[];
  failed_operation_runs: Run[];
}

export interface SeriesPoint {
  timestamp: string;
  value: number;
}

export interface ObservabilityMetricsSeries {
  hours: number;
  series: {
    operation_volume: SeriesPoint[];
    failure_volume: SeriesPoint[];
    latency_ms_avg: SeriesPoint[];
  };
}

export interface OperationRunReconcileResult {
  cutoff: string;
  scanned_count: number;
  updated_count: number;
  include_current_day: boolean;
}

export interface BenchmarkRun {
  benchmark_run_id: string;
  operation_run_id: string;
  benchmark_type: "METADATA" | "DISCOVERY" | string;
  status: "QUEUED" | "RUNNING" | "COMPLETED" | "FAILED" | "CANCEL_REQUESTED" | "CANCELLED" | string;
  parameters: Record<string, unknown>;
  report_payload?: Record<string, unknown> | null;
  summary_payload?: Record<string, unknown> | null;
  cleanup_status?: string | null;
  cleanup_error?: string | null;
  error_message?: string | null;
  queued_at: string;
  started_at?: string | null;
  completed_at?: string | null;
  cancel_requested_at?: string | null;
}

export interface BenchmarkQueueResult {
  queued: boolean;
  operation_run_id: string;
  benchmark: BenchmarkRun;
}
