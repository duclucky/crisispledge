import { useState, useEffect } from 'react';
import { readVault, makeWriteClient, PLEDGE_VAULT, TransactionStatus } from './genlayer.js';

const MYANMAR_CRITERIA =
  'Magnitude 7.7 earthquake struck Myanmar near Mandalay/Sagaing on 28 March 2025, causing thousands of deaths and major building collapses, with tremors felt in Thailand.';
const MYANMAR_URL = 'https://en.wikipedia.org/wiki/2025_Myanmar_earthquake';

const C = {
  bg: '#FBF6EF',
  card: '#FFFFFF',
  ink: '#3A2E25',
  sub: '#8A7B6D',
  line: '#EADFD2',
  warm: '#E07A3F',
  warmDark: '#C4612C',
  green: '#2E8B6F',
  amber: '#C98A1A',
  slate: '#6B7A86',
};

const badgeStyle = (status) => {
  let bg = '#EFE7DB', fg = C.sub;
  if (status === 'RELEASED') { bg = '#DDF1EA'; fg = C.green; }
  else if (status === 'REFUNDED') { bg = '#FBEED2'; fg = C.amber; }
  else if (status === 'OPEN') { bg = '#E7EEF2'; fg = C.slate; }
  return {
    display: 'inline-block', padding: '2px 12px', borderRadius: 999,
    fontSize: 13, fontWeight: 700, background: bg, color: fg, letterSpacing: 0.3,
  };
};

export default function App() {
  const [wallet, setWallet] = useState('');
  const [pledges, setPledges] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');
  const [notice, setNotice] = useState('');

  const [org, setOrg] = useState('relief_myanmar_org');
  const [amount, setAmount] = useState('10000');
  const [criteria, setCriteria] = useState(MYANMAR_CRITERIA);
  const [urls, setUrls] = useState(MYANMAR_URL);
  const [deadline, setDeadline] = useState('9999999');

  async function connectWallet() {
    setError('');
    try {
      if (!window.ethereum) { setError('MetaMask not found. Please install MetaMask.'); return; }
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      setWallet(accounts[0]);
    } catch (e) { setError(String(e?.message || e)); }
  }

  async function refreshList() {
    setLoadingList(true); setError('');
    try {
      const count = Number(await readVault('get_pledge_count', []));
      const items = [];
      for (let i = 0; i < count; i++) {
        const status = String(await readVault('get_status', [i]));
        const verdict = String(await readVault('get_verdict', [i]));
        const reason = String(await readVault('get_reason', [i]));
        items.push({ id: i, status, verdict, reason });
      }
      setPledges(items.reverse());
    } catch (e) { setError(String(e?.message || e)); }
    finally { setLoadingList(false); }
  }

  useEffect(() => { refreshList(); }, []);

  async function txWrite(functionName, args, busyLabel) {
    if (!wallet) { setError('Connect your wallet first.'); return; }
    setBusy(busyLabel); setError(''); setNotice('');
    try {
      const client = makeWriteClient(wallet);
      const hash = await client.writeContract({ address: PLEDGE_VAULT, functionName, args, value: BigInt(0) });
      await client.waitForTransactionReceipt({ hash, status: TransactionStatus.ACCEPTED });
      await refreshList();
    } catch (e) {
      // A timeout here usually means consensus is still running, not a failure.
      setNotice('Transaction submitted. The AI jury may still be reaching consensus — this can take a few minutes. Use Refresh to check the latest status.');
    } finally { setBusy(''); }
  }

  const handleSetTrusted = () => txWrite('set_trusted_org', [org], 'Registering trusted relief org…');
  const handleCreate = () => txWrite('create_pledge', [org, parseInt(amount, 10), criteria, urls, parseInt(deadline, 10)], 'Locking the pledge on-chain…');
  const handleTrigger = (id) => txWrite('trigger_verification', [id], 'The AI jury is investigating the disaster… (consensus may take a few minutes)');

  const input = {
    width: '100%', padding: '10px 12px', borderRadius: 10, border: `1px solid ${C.line}`,
    background: '#FFFDFA', color: C.ink, fontSize: 14, fontFamily: 'inherit', boxSizing: 'border-box',
  };
  const label = { fontSize: 13, fontWeight: 600, color: C.sub, marginBottom: 6, display: 'block' };
  const btn = (primary) => ({
    padding: '11px 18px', borderRadius: 10, border: 'none', cursor: 'pointer',
    fontWeight: 700, fontSize: 14, color: primary ? '#fff' : C.warmDark,
    background: primary ? C.warm : '#F3E7D9', transition: 'all .15s',
  });

  return (
    <div style={{ minHeight: '100vh', background: C.bg, color: C.ink, fontFamily: "'Segoe UI', system-ui, sans-serif" }}>
      <div style={{ maxWidth: 860, margin: '0 auto', padding: '0 20px 64px' }}>

        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '28px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <div style={{ width: 42, height: 42, borderRadius: 12, background: `linear-gradient(135deg, ${C.warm}, ${C.amber})`, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 22 }}>🤍</div>
            <div>
              <div style={{ fontSize: 22, fontWeight: 800, letterSpacing: -0.5 }}>CrisisPledge</div>
              <div style={{ fontSize: 12, color: C.sub }}>AI-adjudicated disaster relief, on-chain</div>
            </div>
          </div>
          {wallet ? (
            <span style={{ ...badgeStyle('RELEASED'), fontWeight: 600 }}>● {wallet.slice(0, 6)}…{wallet.slice(-4)}</span>
          ) : (
            <button style={btn(true)} onClick={connectWallet}>Connect MetaMask</button>
          )}
        </header>

        <section style={{ textAlign: 'center', padding: '20px 0 36px' }}>
          <h1 style={{ fontSize: 34, fontWeight: 800, lineHeight: 1.2, margin: '0 0 14px', letterSpacing: -0.8 }}>
            Pledge now. Release only when<br />the disaster is <span style={{ color: C.warm }}>truly verified</span>.
          </h1>
          <p style={{ fontSize: 16, color: C.sub, maxWidth: 560, margin: '0 auto', lineHeight: 1.6 }}>
            Lock relief funds against a disaster condition. A jury of AI validators reads live news on-chain and decides — no middleman, no fake claims.
          </p>
        </section>

        {error && <div style={{ background: '#FBE3DC', color: C.warmDark, padding: '12px 16px', borderRadius: 10, marginBottom: 16, fontSize: 14, whiteSpace: 'pre-wrap' }}>⚠ {error}</div>}
        {notice && <div style={{ background: '#E7EEF2', color: C.slate, padding: '12px 16px', borderRadius: 10, marginBottom: 16, fontSize: 14 }}>ℹ {notice}</div>}
        {busy && <div style={{ background: '#FBEED2', color: C.amber, padding: '12px 16px', borderRadius: 10, marginBottom: 16, fontSize: 14, fontWeight: 600 }}>⏳ {busy}</div>}

        <div style={{ background: C.card, borderRadius: 18, padding: 28, border: `1px solid ${C.line}`, boxShadow: '0 6px 24px rgba(120,90,60,0.06)', marginBottom: 24 }}>
          <h3 style={{ margin: '0 0 4px', fontSize: 18 }}>Create a relief pledge</h3>
          <p style={{ margin: '0 0 20px', fontSize: 13, color: C.sub }}>Pre-filled with a real example (2025 Myanmar earthquake).</p>

          <div style={{ display: 'grid', gap: 16 }}>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div><span style={label}>Relief organization</span><input style={input} value={org} onChange={(e) => setOrg(e.target.value)} /></div>
              <div><span style={label}>Amount (cents)</span><input style={input} value={amount} onChange={(e) => setAmount(e.target.value)} /></div>
            </div>
            <div><span style={label}>Disaster condition to verify</span><textarea style={{ ...input, resize: 'vertical' }} rows={3} value={criteria} onChange={(e) => setCriteria(e.target.value)} /></div>
            <div><span style={label}>Source URLs (one per line)</span><textarea style={{ ...input, resize: 'vertical' }} rows={2} value={urls} onChange={(e) => setUrls(e.target.value)} /></div>
            <div style={{ maxWidth: 220 }}><span style={label}>Deadline (timestamp)</span><input style={input} value={deadline} onChange={(e) => setDeadline(e.target.value)} /></div>

            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', paddingTop: 4 }}>
              <button style={{ ...btn(false), opacity: busy ? 0.5 : 1 }} onClick={handleSetTrusted} disabled={!!busy}>1 · Register trusted org</button>
              <button style={{ ...btn(true), opacity: busy ? 0.5 : 1 }} onClick={handleCreate} disabled={!!busy}>2 · Lock pledge</button>
            </div>
          </div>
        </div>

        <div style={{ background: C.card, borderRadius: 18, padding: 28, border: `1px solid ${C.line}`, boxShadow: '0 6px 24px rgba(120,90,60,0.06)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
            <h3 style={{ margin: 0, fontSize: 18 }}>Pledges</h3>
            <button style={{ ...btn(false), padding: '8px 14px', opacity: loadingList ? 0.5 : 1 }} onClick={refreshList} disabled={loadingList}>{loadingList ? 'Loading…' : '↻ Refresh'}</button>
          </div>

          {pledges.length === 0 && !loadingList && <p style={{ color: C.sub, textAlign: 'center', padding: '24px 0' }}>No pledges yet. Create the first one above.</p>}

          {pledges.map((p) => (
            <div key={p.id} style={{ borderTop: `1px solid ${C.line}`, padding: '18px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <strong style={{ fontSize: 15 }}>Pledge #{p.id}</strong>
                <span style={badgeStyle(p.status)}>{p.status || '—'}</span>
              </div>
              <div style={{ fontSize: 14, color: C.ink, marginBottom: 4 }}>
                Verdict: <strong style={{ color: p.verdict === 'CONFIRMED' ? C.green : p.verdict === 'REJECTED' ? C.warmDark : C.sub }}>{p.verdict}</strong>
              </div>
              {p.reason && p.reason !== 'NONE' && p.reason !== '' && (
                <div style={{ fontSize: 13, color: C.sub, lineHeight: 1.6, background: '#FBF6EF', padding: '10px 14px', borderRadius: 10, marginTop: 6 }}>
                  <span style={{ fontWeight: 700, color: C.warmDark }}>AI jury: </span>{p.reason}
                </div>
              )}
              {p.status === 'OPEN' && (
                <button style={{ ...btn(true), marginTop: 12, opacity: busy ? 0.5 : 1 }} onClick={() => handleTrigger(p.id)} disabled={!!busy}>⚖ Trigger AI verification</button>
              )}
            </div>
          ))}
        </div>

        <footer style={{ textAlign: 'center', marginTop: 32, fontSize: 12, color: C.sub }}>
          Built on GenLayer · Intelligent Contracts that read the web and reason on-chain
        </footer>
      </div>
    </div>
  );
}
