/**
 * Represents a pair of colors designed to ensure text readability.
 *
 * Used primarily by axis views to determine the best text color (foreground)
 * to display on top of a specific label background color.
 */
export interface ContrastColors {
    foreground: string;
    background: string;
}
/**
 * Generates a high-contrast color pair based on a given background color string.
 *
 * This utility parses CSS color strings (RGBA, RGB, Hex, or named colors) to calculate
 * the background's luminance. It then returns 'black' or 'white' as the foreground color
 * to ensure maximum readability.
 *
 * @param backgroundColor - A CSS color string (e.g., `'#FF0000'`, `'rgba(0, 0, 0, 0.5)'`).
 * @returns A {@link ContrastColors} object containing the background and the optimal foreground color.
 */
export declare function generateContrastColors(backgroundColor: string): ContrastColors;
/**
 * Type guard to check if a value is a finite number.
 *
 * @param value - The value to check.
 * @returns `true` if the value is of type 'number' and is not `Infinity` or `NaN`.
 */
export declare function isNumber(value: unknown): value is number;
/**
 * Checks if a value is an integer number.
 *
 * @param value - The value to check.
 * @returns `true` if the value is a number with no fractional part.
 */
export declare function isInteger(value: unknown): boolean;
/**
 * Type guard to check if a value is a string.
 *
 * @param value - The value to check.
 * @returns `true` if the value is of type 'string'.
 */
export declare function isString(value: unknown): value is string;
/**
 * Type guard to check if a value is a boolean.
 *
 * @param value - The value to check.
 * @returns `true` if the value is of type 'boolean'.
 */
export declare function isBoolean(value: unknown): value is boolean;
/**
 * asserts that a condition is true.
 *
 * If the condition is false, this function throws an Error. This is useful for
 * invariant checking and narrowing types in TypeScript flow analysis.
 *
 * @param condition - The boolean condition to verify.
 * @param message - Optional text to include in the Error message if the assertion fails.
 * @throws Error if `condition` is `false`.
 */
export declare function assert(condition: boolean, message?: string): asserts condition;
/**
 * Ensures a value is not `null`.
 *
 * This is a utility for runtime checks where TypeScript might allow `null` but the
 * logic strictly requires a value.
 *
 * @typeParam T - The type of the value.
 * @param value - The value to check.
 * @returns The value `T` (guaranteed not to be null).
 * @throws Error if `value` is `null`.
 */
export declare function ensureNotNull<T>(value: T | null): T;
/**
 * Ensures a value is not `undefined`.
 *
 * Similar to {@link ensureNotNull}, this guarantees existence at runtime.
 *
 * @typeParam T - The type of the value.
 * @param value - The value to check.
 * @returns The value `T` (guaranteed not to be undefined).
 * @throws Error if `value` is `undefined`.
 */
export declare function ensureDefined<T>(value: T | undefined): T;
/**
 * Creates a deep copy of an object, array, or Date.
 *
 * This recursive function ensures that nested structures are duplicated rather than
 * referenced, preventing side effects when modifying configuration objects or state.
 *
 * @typeParam T - The type of the object being copied.
 * @param object - The source object to copy.
 * @returns A strictly typed deep copy of the input.
 */
export declare function deepCopy<T>(object: T): T;
/**
 * Deeply merges multiple source objects into a destination object.
 *
 * **Special Behavior for Arrays:**
 * Unlike standard merges, if a source array is shorter than the destination array,
 * the destination array is truncated to match the length of the source. This prevents
 * stale data (e.g., old points) from lingering when a tool is updated with fewer points.
 *
 * @param dst - The target object to modify.
 * @param sources - One or more source objects to merge properties from.
 * @returns The modified `dst` object.
 */
export declare function merge(dst: Record<string, any>, ...sources: Record<string, any>[]): Record<string, any>;
/**
 * Generates a random alphanumeric hash string.
 *
 * Used primarily for generating unique identifiers (`id`) for new line tools
 * if one is not provided by the user.
 *
 * @param count - The length of the hash to generate (default is 12).
 * @returns A random string.
 */
export declare function randomHash(count?: number): string;
/**
 * The default font stack used by the plugin for text rendering.
 * Value: `'Trebuchet MS', Roboto, Ubuntu, sans-serif`
 */
export declare const defaultFontFamily = "'Trebuchet MS', Roboto, Ubuntu, sans-serif";
/**
 * Constructs a valid CSS font string for the HTML5 Canvas context.
 *
 * @param size - The font size in pixels.
 * @param family - The font family (defaults to {@link defaultFontFamily}).
 * @param style - Optional style (e.g., `'bold'`, `'italic'`).
 * @returns A string like `"bold 14px 'Trebuchet MS'"`.
 */
export declare function makeFont(size: number, family?: string, style?: string): string;
/**
 * A generic function signature for event callbacks.
 *
 * Supports up to three typed parameters.
 * @typeParam T1 - Type of the first parameter.
 * @typeParam T2 - Type of the second parameter.
 * @typeParam T3 - Type of the third parameter.
 */
export type Callback<T1 = void, T2 = void, T3 = void> = (param1: T1, param2: T2, param3: T3) => void;
/**
 * Interface representing a subscription management object.
 *
 * Mirrors the internal `ISubscription` from Lightweight Charts, allowing consumers to
 * add or remove event listeners.
 */
export interface ISubscription<T1 = void, T2 = void, T3 = void> {
    subscribe(callback: Callback<T1, T2, T3>, linkedObject?: unknown, singleshot?: boolean): void;
    unsubscribe(callback: Callback<T1, T2, T3>): void;
    unsubscribeAll(linkedObject: unknown): void;
}
/**
 * A robust event dispatcher implementation.
 *
 * This class mimics the internal `Delegate` used by Lightweight Charts. It maintains a list
 * of subscribers and broadcasts events to them. It supports linking subscriptions to specific
 * objects for bulk-unsubscribe and "singleshot" (one-time) listeners.
 */
export declare class Delegate<T1 = void, T2 = void, T3 = void> implements ISubscription<T1, T2, T3> {
    /**
     * Internal list of active subscribers.
     * @private
     */
    private _listeners;
    /**
     * Subscribes a callback function to the delegate.
     *
     * When the event is fired, this callback will be executed with the provided arguments.
     *
     * @param callback - The function to call when the event fires.
     * @param linkedObject - An optional object to link the subscription to. This allows removing multiple unrelated subscriptions at once via {@link unsubscribeAll}.
     * @param singleshot - If `true`, the subscription is automatically removed after the first time it is called.
     */
    subscribe(callback: Callback<T1, T2, T3>, linkedObject?: unknown, singleshot?: boolean): void;
    /**
     * Unsubscribes a specific callback function from the delegate.
     *
     * If the callback was added multiple times, this typically removes the first occurrence
     * depending on implementation, though delegates usually enforce unique callback references per subscription context.
     *
     * @param callback - The specific function reference to remove.
     */
    unsubscribe(callback: Callback<T1, T2, T3>): void;
    /**
     * Unsubscribes all callbacks that were registered with a specific `linkedObject`.
     *
     * This is useful for cleaning up all event listeners associated with a specific UI component
     * or tool instance when it is destroyed.
     *
     * @param linkedObject - The object key used during subscription.
     */
    unsubscribeAll(linkedObject: unknown): void;
    /**
     * Fires the event, calling all subscribed callbacks with the provided arguments.
     *
     * This method takes a snapshot of the listeners array before iterating to ensure that
     * if a listener unsubscribes itself during execution, the iteration remains stable.
     *
     * @param param1 - The first event argument.
     * @param param2 - The second event argument.
     * @param param3 - The third event argument.
     */
    fire(param1: T1, param2: T2, param3: T3): void;
    /**
     * Checks if the delegate has any active listeners.
     *
     * This is useful for avoiding expensive calculations if no one is listening to the event.
     *
     * @returns `true` if there is at least one active subscriber, `false` otherwise.
     */
    hasListeners(): boolean;
    /**
     * Clears all listeners and frees up resources.
     *
     * This should be called when the owner of the Delegate (e.g., the Plugin or a Tool)
     * is being destroyed to prevent memory leaks.
     */
    destroy(): void;
}
/**
 * Internal utility type used to flatten complex intersection types into a single object type.
 *
 * This helps improve the readability of type hints in IDEs (like VS Code) when inspecting
 * types generated by `OmitRecursively` or `DeepPartial`. without this, tooltips often show
 * raw intersection logic (e.g., `A & B`) instead of the resulting properties.
 *
 * @typeParam T - The type to flatten.
 */
export type Id<T> = {} & {
    [P in keyof T]: T[P];
};
/**
 * Internal utility to apply `Omit` distributively across union types.
 *
 * Standard `Omit` can behave unexpectedly with unions. This helper ensures that the
 * omission logic is applied to each member of a union individually before recombining them.
 *
 * @typeParam T - The union type.
 * @typeParam K - The keys to omit.
 */
export type OmitDistributive<T, K extends PropertyKey> = T extends any ? (T extends object ? Id<OmitRecursively<T, K>> : T) : never;
/**
 * A utility type that recursively marks all properties of type `T` as optional.
 *
 * This is essential for configuration objects where the user might only provide
 * a few specific overrides (e.g., changing just the line color inside a complex style object).
 */
export type DeepPartial<T> = {
    [P in keyof T]?: T[P] extends (infer U)[] ? DeepPartial<U>[] : T[P] extends readonly (infer X)[] ? readonly DeepPartial<X>[] : DeepPartial<T[P]>;
};
/**
 * A utility type that recursively removes a specific key `K` from type `T` and all its nested objects.
 *
 * Useful for sanitizing configuration objects or removing internal flags from public interfaces.
 */
export type OmitRecursively<T extends any, K extends PropertyKey> = Omit<{
    [P in keyof T]: OmitDistributive<T[P], K>;
}, K>;
