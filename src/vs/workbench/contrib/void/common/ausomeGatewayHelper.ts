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
