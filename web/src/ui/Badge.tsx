import type { Confidence, Status } from '../data/types';

const CONF: Record<Confidence, { label: string; title: string }> = {
  measured: { label: 'gemessen', title: 'Am Gerät gemessen' },
  catalog: { label: 'Katalog', title: 'Händler-/Katalogangabe' },
  spec: { label: 'Datenblatt', title: 'Herstellerangabe' },
  photo: { label: 'Foto', title: 'Aus Fotos abgeleitet (± 10 %)' },
  guess: { label: 'geschätzt', title: 'Geschätzt - nicht als Maß verwenden' },
};

export function ConfBadge({ c }: { c: Confidence }) {
  return (
    <span className={`badge conf-${c}`} title={CONF[c].title}>
      {CONF[c].label}
    </span>
  );
}

const STATUS: Record<Status, string> = { planned: 'geplant', blockout: 'Grobform', modeled: 'modelliert', verified: 'geprüft' };

export function StatusBadge({ s }: { s: Status }) {
  return <span className={`badge status-${s}`}>{STATUS[s]}</span>;
}
