/*--------------------------------------------------------------------------------------
 *  Copyright 2025 Glass Devtools, Inc. All rights reserved.
 *  Licensed under the Apache License, Version 2.0. See LICENSE.txt for more information.
 *--------------------------------------------------------------------------------------*/

import React, { useEffect, useState } from 'react';

export const IconLoading = ({ className = '' }: { className?: string }) => {
	const [loadingText, setLoadingText] = useState('.');

	useEffect(() => {
		const intervalId = setInterval(() => {
			setLoadingText(prev => (prev === '...' ? '.' : prev + '.'));
		}, 300);
		return () => clearInterval(intervalId);
	}, []);

	return <div className={`${className}`}>{loadingText}</div>;
};
