// Loading overlay (PLAN 9, Phase 7): progress of the GLB download until the model is in the scene,
// and a readable message if it cannot be loaded.
import { useProgress } from '@react-three/drei';
import { Component, type ReactNode } from 'react';
import { useStore } from '../state/store';

export function Loader() {
  const ready = useStore((s) => s.modelReady);
  const { progress, active } = useProgress();
  if (ready) return null;
  return (
    <div className="loader" data-testid="loader" role="status" aria-live="polite">
      <div className="loader-box">
        <div>Modell lädt … {active ? `${Math.round(progress)} %` : ''}</div>
        <div className="loader-bar">
          <div style={{ width: `${Math.max(4, progress)}%` }} />
        </div>
        <div className="muted small">ca. 3 MB, danach offline im Browser-Cache</div>
      </div>
    </div>
  );
}

export class ModelErrorBoundary extends Component<{ children: ReactNode }, { error: string | null }> {
  state = { error: null as string | null };
  static getDerivedStateFromError(e: unknown) {
    return { error: String(e) };
  }
  render() {
    if (this.state.error)
      return (
        <div className="loader" role="alert">
          <div className="loader-box">
            <div>Das 3D-Modell konnte nicht geladen werden.</div>
            <div className="muted small">{this.state.error}</div>
            <div className="muted small">Lokal: erst „make cad“, dann „make web“.</div>
          </div>
        </div>
      );
    return this.props.children;
  }
}
