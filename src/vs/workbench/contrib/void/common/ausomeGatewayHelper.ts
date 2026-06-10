/*--------------------------------------------------------------------------------------
 *  Copyright 2025 Glass Devtools, Inc. All rights reserved.
 *  Licensed under the Apache License, Version 2.0. See LICENSE.txt for more information.
 *--------------------------------------------------------------------------------------*/

import { SettingsAtProvider } from './voidSettingsTypes.js';

export type AusomeGatewayConfig = {
	baseUrl: string;
	apiKey: string;
	projectId: string;
	workspaceId: string;
	sandboxEnabled: boolean;
};

export type AgentRunResponse = {
	run_id: string;
	status: string;
	phase?: string | null;
	plan?: Record<string, unknown> | null;
	pending_tool?: {
		tool_name: string;
		arguments: Record<string, unknown>;
		tool_call_id?: string;
		phase?: string;
	} | null;
	message?: string | null;
	steps?: Record<string, unknown>[];
};

export const getAusomeGatewayConfig = (
	ausome: SettingsAtProvider<'ausome'> | undefined,
): AusomeGatewayConfig | null => {
	if (!ausome?._didFillInProviderSettings) return null;
	const headers = parseAusomeHeaders(ausome.headersJSON);
	return {
		baseUrl: (ausome.endpoint || 'http://127.0.0.1:8000').replace(/\/+$/, ''),
		apiKey: ausome.apiKey || 'ausome-dev',
		projectId: headers['X-Ausome-Project-Id'] || '00000000-0000-0000-0000-000000000001',
		workspaceId: headers['X-Ausome-Workspace-Id'] || 'default',
		sandboxEnabled: headers['X-Ausome-Sandbox'] === 'true',
	};
};

export const parseAusomeHeaders = (s: string | undefined): Record<string, string> => {
	if (!s) return {};
	try {
		const parsed = JSON.parse(s);
		if (typeof parsed !== 'object' || parsed === null) return {};
		const out: Record<string, string> = {};
		for (const [k, v] of Object.entries(parsed)) {
			if (typeof v === 'string') out[k] = v;
		}
		return out;
	} catch {
		return {};
	}
};

export const ausomeAuthHeaders = (apiKey: string): Record<string, string> => ({
	'Content-Type': 'application/json',
	'Authorization': `Bearer ${apiKey}`,
});

const gatewayFetch = async <T>(
	cfg: AusomeGatewayConfig,
	path: string,
	init?: RequestInit,
): Promise<T> => {
	const resp = await fetch(`${cfg.baseUrl}${path}`, {
		...init,
		headers: {
			...ausomeAuthHeaders(cfg.apiKey),
			...(init?.headers as Record<string, string> | undefined),
		},
	});
	if (!resp.ok) {
		const detail = await resp.text();
		throw new Error(`Gateway ${path} failed (${resp.status}): ${detail}`);
	}
	return resp.json() as Promise<T>;
};

export const startAgentRun = (
	cfg: AusomeGatewayConfig,
	body: {
		goal: string;
		session_id?: string;
		project_id?: string;
		pulse_thread_id?: string;
		require_plan_approval?: boolean;
	},
): Promise<AgentRunResponse> =>
	gatewayFetch(cfg, '/v1/agent/run', { method: 'POST', body: JSON.stringify(body) });

export const pollAgentRun = (cfg: AusomeGatewayConfig, runId: string): Promise<AgentRunResponse> =>
	gatewayFetch(cfg, `/v1/agent/runs/${runId}`, { method: 'GET' });

export const submitAgentToolResult = (
	cfg: AusomeGatewayConfig,
	runId: string,
	body: { tool_name: string; result: string; success?: boolean; tool_call_id?: string },
): Promise<AgentRunResponse> =>
	gatewayFetch(cfg, `/v1/agent/runs/${runId}/tool-result`, {
		method: 'POST',
		body: JSON.stringify(body),
	});

export const cancelAgentRun = (cfg: AusomeGatewayConfig, runId: string): Promise<AgentRunResponse> =>
	gatewayFetch(cfg, `/v1/agent/runs/${runId}/cancel`, { method: 'POST' });

export const approveAgentPlan = (cfg: AusomeGatewayConfig, runId: string): Promise<AgentRunResponse> =>
	gatewayFetch(cfg, `/v1/agent/runs/${runId}/approve-plan`, { method: 'POST' });

export type AgentRunListItem = {
	id: string;
	status: string;
	goal?: string | null;
	project_id?: string | null;
	phase?: string | null;
	pulse_thread_id?: string | null;
	started_at?: string;
	ended_at?: string | null;
};

export type AgentTraceSpan = {
	id: string;
	span_type: string;
	phase?: string | null;
	name: string;
	started_at?: string;
	ended_at?: string | null;
	latency_ms?: number | null;
	status: string;
	payload?: Record<string, unknown>;
};

export type AgentRunTrace = {
	run: Record<string, unknown>;
	steps: Record<string, unknown>[];
	spans: AgentTraceSpan[];
	usage: {
		prompt_tokens: number;
		completion_tokens: number;
		total_tokens: number;
		estimated_cost_usd: number;
		by_model: { model: string; tokens: number; cost: number }[];
	};
	eval_runs: Record<string, unknown>[];
	snapshot?: Record<string, unknown> | null;
	memories_written: Record<string, unknown>[];
	duration_ms?: number | null;
};

export const listAgentRuns = (
	cfg: AusomeGatewayConfig,
	params: { pulse_thread_id?: string; project_id?: string; status?: string; limit?: number },
): Promise<{ runs: AgentRunListItem[] }> => {
	const q = new URLSearchParams();
	if (params.pulse_thread_id) q.set('pulse_thread_id', params.pulse_thread_id);
	if (params.project_id) q.set('project_id', params.project_id);
	if (params.status) q.set('status', params.status);
	if (params.limit) q.set('limit', String(params.limit));
	const qs = q.toString();
	return gatewayFetch(cfg, `/v1/agent/runs${qs ? `?${qs}` : ''}`, { method: 'GET' });
};

export const getAgentTrace = (cfg: AusomeGatewayConfig, runId: string): Promise<AgentRunTrace> =>
	gatewayFetch(cfg, `/v1/agent/runs/${runId}/trace`, { method: 'GET' });
