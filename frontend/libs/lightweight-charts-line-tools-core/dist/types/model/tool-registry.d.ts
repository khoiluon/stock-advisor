import { LineToolType } from '../types';
import { BaseLineTool } from './base-line-tool';
/**
 * A registry for mapping line tool type names to their corresponding class constructors.
 *
 * This class ensures that when a tool is requested by its string identifier (e.g., `'Rectangle'`),
 * the plugin can reliably retrieve the correct class constructor to dynamically instantiate the tool.
 *
 * @typeParam HorzScaleItem - The type of the horizontal scale item.
 */
export declare class ToolRegistry<HorzScaleItem> {
    /**
     * Private map to store the registered tool classes.
     * Key: {@link LineToolType} string (e.g., 'Rectangle')
     * Value: Constructor of a class that extends {@link BaseLineTool}
     * @private
     */
    private readonly _toolConstructors;
    /**
     * Registers a new line tool class with the registry.
     *
     * This method is typically called via the public {@link LineToolsCorePlugin.registerLineTool} API
     * to make a custom tool available for creation.
     *
     * @param type - The string identifier for the tool (e.g., 'Rectangle').
     * @param toolClass - The constructor of the class that extends {@link BaseLineTool}.
     * @returns void
     */
    registerTool(type: LineToolType, toolClass: new (...args: any[]) => BaseLineTool<HorzScaleItem>): void;
    /**
     * Checks if a line tool of a specific type has been registered.
     *
     * @param type - The line tool type to check.
     * @returns `true` if the tool is registered, otherwise `false`.
     */
    isRegistered(type: LineToolType): boolean;
    /**
     * Retrieves the constructor for a specific line tool type.
     *
     * @param type - The line tool type to retrieve.
     * @returns The class constructor if found.
     * @throws Will throw an error if the tool type is not registered.
     */
    getToolClass(type: LineToolType): new (...args: any[]) => BaseLineTool<HorzScaleItem>;
}
