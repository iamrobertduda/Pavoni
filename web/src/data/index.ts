import raw from '../generated/data.json';
import type { AppData, Assembly, Part } from './types';
import { buildModelIndex } from '../logic/graph';

export const data = raw as unknown as AppData;
export const model = buildModelIndex(data);
export const partsById: Record<string, Part> = model.parts;
export const assembliesById: Record<string, Assembly> = model.assemblies;
