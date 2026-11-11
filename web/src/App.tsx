import { useEffect, useMemo } from 'react';
import { data } from './data';
import { Viewer } from './scene/Viewer';
import { useStore } from './state/store';
import { InfoPanel } from './ui/InfoPanel';
import { PartTree } from './ui/PartTree';
import { SealList } from './ui/SealList';
import { DisassemblyPlayer, ProcedureList, ProcedurePlayer } from './ui/ProcedurePlayer';
import { Toolbar } from './ui/Toolbar';
import { readUrl, syncUrl } from './url';

export default function App() {
  const init = useMemo(() => readUrl(), []);
  const ui = useStore((s) => s.ui);
  const mode = useStore((s) => s.mode);
  const treeOpen = useStore((s) => s.treeOpen);
  const sealMap = useStore((s) => s.sealMap);
  const setView = useStore((s) => s.setView);
  useEffect(() => {
    syncUrl();
    // a procedure step chooses its own camera (ProcedurePlayer)
    if (useStore.getState().mode !== 'procedure') setView(init.view);
  }, [init, setView]);
  return (
    <div className={`app ${ui ? '' : 'no-ui'} ${init.transparent ? 'transparent' : ''}`}>
      <Viewer transparent={init.transparent} />
      {ui && (
        <>
          <Toolbar />
          {treeOpen && (
            <aside className="left">
              <PartTree />
            </aside>
          )}
          <aside className="right">
            {mode === 'procedure' && <ProcedurePlayer />}
            {mode === 'disassembly' && <DisassemblyPlayer />}
            <InfoPanel />
            {sealMap && mode === 'explore' && <SealList />}
            {mode === 'explore' && !sealMap && <ProcedureList />}
          </aside>
          <footer className="foot muted small">
            La Pavoni Professional · Modell {data.machine.version} (Version {data.machine.version_confidence === 'measured' ? 'bestätigt' : 'angenommen'}) · Stand {data.generated.slice(0, 10)} · {data.git}
            {' · '}Sehhilfe, kein Ersatz für Fachkenntnis. Geschätzte Maße sind als solche markiert.
          </footer>
        </>
      )}
    </div>
  );
}
