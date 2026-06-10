/*--------------------------------------------------------------------------------------
 *  Copyright 2025 Glass Devtools, Inc. All rights reserved.
 *  Licensed under the Apache License, Version 2.0. See LICENSE.txt for more information.
 *--------------------------------------------------------------------------------------*/

import OpenAI, { ClientOptions } from 'openai';
import { SettingsOfProvider } from '../../common/voidSettingsTypes.js';

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

export const createAusomeGatewayClient = (
	settingsOfProvider: SettingsOfProvider,
	commonPayloadOpts: ClientOptions,
): OpenAI => {
	const config = settingsOfProvider.ausome;
	const headers = parseAusomeHeaders(config.headersJSON);
	const base = (config.endpoint || 'http://127.0.0.1:8000').replace(/\/+$/, '');
	return new OpenAI({
		baseURL: `${base}/v1`,
		apiKey: config.apiKey || 'ausome-dev',
		defaultHeaders: headers,
		...commonPayloadOpts,
	});
};
