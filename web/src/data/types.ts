export type I18n = { de: string; en?: string; it?: string };
export type Vec3 = [number, number, number];
/** distance_mm: way in the exploded view. removal_mm: the way the part travels instead when it is
 * removed while its assembly still sits on the machine (see logic/explode.ts, travel). */
export type Explode = { axis: Vec3; distance_mm: number; removal_mm?: number; stage: number };
export type Confidence = 'measured' | 'catalog' | 'spec' | 'photo' | 'guess';
export type Status = 'planned' | 'blockout' | 'modeled' | 'verified';

export interface Part {
  id: string;
  pos: number | null;
  name: I18n;
  assembly: string;
  instances: string[];
  kind: 'seal' | 'fastener' | 'structural' | 'electrical' | 'accessory';
  material: string;
  wear_part: boolean;
  detail_tier: 'A' | 'B' | 'C';
  status: Status;
  spec?: Record<string, string | number>;
  dims?: string[];
  thread?: string;
  notes?: I18n;
  order_terms?: string[];
  tools?: string[];
  versions?: string[];
  sources?: string[];
  open_questions?: string[];
  explode: Explode;
  instance_explode?: Record<string, Explode>;
  requires_removed: string[];
  instance_requires?: Record<string, string[]>;
  carrier?: string;
}

export interface Assembly {
  id: string;
  name: I18n;
  detachable: boolean;
  explode: Explode;
  requires_removed?: string[];
  notes?: I18n;
}

export interface Tool {
  id: string;
  name: I18n;
  note?: I18n;
  source?: string;
}

export interface Step {
  id: string;
  title: I18n;
  text: I18n;
  remove?: string[];
  motion?: { type: string; turns?: number };
  highlight?: string[];
  camera?: string;
  section?: string;
  tools?: string[];
  warn?: I18n;
  reassembly?: I18n;
}

export interface Procedure {
  id: string;
  order?: number;
  title: I18n;
  summary?: I18n;
  difficulty: number;
  duration_min: number;
  tools: string[];
  parts_needed?: string[];
  preconditions: string[];
  danger?: I18n;
  sources?: string[];
  start_removed?: string[];
  steps: Step[];
}

export interface DimEntry {
  key: string;
  resolved: number;
  unit: string;
  confidence: Confidence;
  source: string;
  note?: string;
  alt?: { value: number; source: string }[];
  value?: number;
  ratio_of?: string;
  ratio?: number;
  expr?: string;
}

export interface InstanceGeo {
  part: string;
  assembly: string;
  bbox: [Vec3, Vec3];
  center: Vec3;
  volume: number;
  explode: Explode;
}

export interface AssemblyGeo {
  parent: string | null;
  detachable: boolean;
  explode: Explode;
}

export interface View {
  label: string;
  position: Vec3;
  target: Vec3;
  fov?: number;
  photo?: string;
  render?: boolean;
}

export interface Section {
  label: string;
  normal: Vec3;
  point: Vec3;
  view?: string;
}

export interface AppData {
  generated: string;
  git: string;
  machine: { version: string; version_confidence?: Confidence; note?: string };
  parts: Part[];
  assemblies: Assembly[];
  tools: Tool[];
  procedures: Procedure[];
  views: Record<string, View>;
  sections: Record<string, Section>;
  dims: Record<string, DimEntry>;
  instances: Record<string, InstanceGeo>;
  assemblyGeo: Record<string, AssemblyGeo>;
}
