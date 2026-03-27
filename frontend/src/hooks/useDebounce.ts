import debounce from "lodash/debounce";
import { useEffect, useMemo, useState } from "react";

/**
 * Hook useDebounce
 * @param value - state hoặc giá trị cần debounce
 * @param delay - thời gian debounce (ms)
 * @returns giá trị đã được debounce
 */
export function useDebounce<T>(value: T, delay: number): T {
	const [debouncedValue, setDebouncedValue] = useState<T>(value);

	// Tạo hàm debounce bằng lodash
	const debouncer = useMemo(
		() =>
			debounce((val: T) => {
				setDebouncedValue(val);
			}, delay),
		[delay],
	);

	useEffect(() => {
		debouncer(value);

		// Cleanup để tránh memory leak
		return () => {
			debouncer.cancel();
		};
	}, [value, debouncer]);

	return debouncedValue;
}
