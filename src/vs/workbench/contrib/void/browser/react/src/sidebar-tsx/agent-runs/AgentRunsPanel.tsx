/*--------------------------------------------------------------------------------------
 *  Agent Observatory panel (Phase A) — run list + timeline in Pulse sidebar
 *--------------------------------------------------------------------------------------*/

import React, { useCallback, useEffect, useState } from 'react';
import {
	AgentRunListItem,
	AgentRunTrace,
	AgentTraceSpan,
	approveAgentPlan,
	getAgentTrace,
	getAusomeGatewayConfig,
	listAgentRuns,
} from '../../../../../../../workbench/contrib/void/common/ausomeGatewayHelper.js';
import { useSettingsState } from '../../util/services.js';

type Props = {
	threadId: string;
	lastGatewayRunId?: string;
	onRunUpdated?: () => void;
};

const statusColor = (status: string) => {
	if (status === 'completed') return 'text-green-500';
	if (status === 'failed' || status === 'cancelled') return 'text-red-400';
	if (status === 'awaiting_approval') return 'text-amber-400';
	return 'text-void-fg-3';
};

const RunSummaryBar = ({ trace }: { trace: AgentRunTrace }) => {
	const run = trace.run as { status?: string };
	return (
		<div className='flex flex-wrap gap-2 text-xs text-void-fg-3 py-1'>
			<span className={statusColor(run.status ?? '')}>{run.status}</span>
			{trace.duration_ms != null && <span>{trace.duration_ms}ms</span>}
			<span>{trace.usage.total_tokens} tokens</span>
			<span>${trace.usage.estimated_cost_usd.toFixed(4)}</span>
		</div>
	);
};

const SpanDetail = ({ span }: { span: AgentTraceSpan }) => {
	const [open, setOpen] = useState(false);
	return (
		<div className='border-l-2 border-zinc-600/40 pl-2 py-1'>
			<button
				type='button'
				className='text-xs text-left w-full hover:text-void-fg-1'
				onClick={() => setOpen(!open)}
			>
				<span className={statusColor(span.status)}>[{span.span_type}]</span>{' '}
				{span.name}
				{span.latency_ms != null ? ` · ${span.latency_ms}ms` : ''}
			</button>
			{open && span.payload && (
				<pre className='text-[10px] mt-1 overflow-x-auto opacity-80 max-h-32'>
					{JSON.stringify(span.payload, null, 2)}
				</pre>
			)}
		</div>
	);
};

const RunTimeline = ({ trace }: { trace: AgentRunTrace }) => (
	<div className='space-y-1 mt-2'>
		{trace.steps.map((step, i) => (
			<div key={i} className='text-xs text-void-fg-3'>
				Step {String(step.step_index)}: {String(step.step_type)}
				{step.phase ? ` (${String(step.phase)})` : ''}
			</div>
		))}
		{trace.spans.map(span => (
			<SpanDetail key={span.id} span={span} />
		))}
		{trace.eval_runs.length > 0 && (
			<div className='text-xs text-void-fg-3 mt-1'>
				Eval: {trace.eval_runs.map(e => `${e.passed ? 'pass' : 'fail'}`).join(', ')}
			</div>
		)}
	</div>
);

export const AgentRunsPanel = ({ threadId, lastGatewayRunId, onRunUpdated }: Props) => {
	const settingsState = useSettingsState();
	const [expanded, setExpanded] = useState(true);
	const [runs, setRuns] = useState<AgentRunListItem[]>([]);
	const [selectedId, setSelectedId] = useState<string | undefined>(lastGatewayRunId);
	const [trace, setTrace] = useState<AgentRunTrace | null>(null);
	const [loading, setLoading] = useState(false);
	const [error, setError] = useState<string | null>(null);

	const cfg = getAusomeGatewayConfig(settingsState.settingsOfProvider.ausome);

	const refresh = useCallback(async () => {
		if (!cfg || !settingsState.globalSettings.agentOrchestrationEnabled) return;
		setLoading(true);
		setError(null);
		try {
			const { runs: listed } = await listAgentRuns(cfg, { pulse_thread_id: threadId, limit: 20 });
			setRuns(listed);
			const id = selectedId ?? lastGatewayRunId ?? listed[0]?.id;
			if (id) {
				setSelectedId(id);
				const t = await getAgentTrace(cfg, id);
				setTrace(t);
			}
		} catch (e) {
			setError(e instanceof Error ? e.message : String(e));
		} finally {
			setLoading(false);
		}
	}, [cfg, threadId, selectedId, lastGatewayRunId, settingsState.globalSettings.agentOrchestrationEnabled]);

	useEffect(() => {
		refresh();
	}, [refresh, lastGatewayRunId]);

	const onApprove = async () => {
		if (!cfg || !selectedId) return;
		try {
			await approveAgentPlan(cfg, selectedId);
			onRunUpdated?.();
			await refresh();
		} catch (e) {
			setError(e instanceof Error ? e.message : String(e));
		}
	};

	if (!settingsState.globalSettings.agentOrchestrationEnabled || !cfg) {
		return null;
	}

	return (
		<div className='mx-4 mb-2 rounded border border-zinc-700/30 bg-zinc-800/20'>
			<button
				type='button'
				className='w-full px-3 py-2 text-left text-xs font-medium text-void-fg-2 flex justify-between'
				onClick={() => setExpanded(!expanded)}
			>
				<span>Agent runs</span>
				<span className='opacity-60'>{expanded ? '−' : '+'}</span>
			</button>
			{expanded && (
				<div className='px-3 pb-3'>
					{loading && <div className='text-xs text-void-fg-3'>Loading…</div>}
					{error && <div className='text-xs text-red-400'>{error}</div>}
					{runs.length === 0 && !loading && (
						<div className='text-xs text-void-fg-3'>No gateway runs for this thread yet.</div>
					)}
					{runs.length > 0 && (
						<select
							className='text-xs w-full mb-2 bg-transparent border border-zinc-600/40 rounded px-1 py-0.5'
							value={selectedId ?? ''}
							onChange={async e => {
								const id = e.target.value;
								setSelectedId(id);
								if (cfg && id) {
									setTrace(await getAgentTrace(cfg, id));
								}
							}}
						>
							{runs.map(r => (
								<option key={r.id} value={r.id}>
									{r.status} — {(r.goal ?? '').slice(0, 40)}
								</option>
							))}
						</select>
					)}
					{trace && (
						<>
							<RunSummaryBar trace={trace} />
							{(trace.run as { status?: string }).status === 'awaiting_approval' && (
								<button
									type='button'
									className='text-xs mt-1 px-2 py-1 rounded bg-zinc-600/40 hover:bg-zinc-600/60'
									onClick={onApprove}
								>
									Approve plan
								</button>
							)}
							<RunTimeline trace={trace} />
						</>
					)}
					<button
						type='button'
						className='text-[10px] mt-2 opacity-60 hover:opacity-100'
						onClick={() => refresh()}
					>
						Refresh
					</button>
				</div>
			)}
		</div>
	);
};
