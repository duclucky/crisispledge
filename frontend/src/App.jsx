import { useState, useEffect } from 'react';
import { readVault, makeWriteClient, PLEDGE_VAULT, TransactionStatus } from './genlayer.js';

const MYANMAR_CRITERIA =
  'Magnitude 7.7 earthquake struck Myanmar near Mandalay/Sagaing on 28 March 2025, causing thousands of deaths and major building collapses, with tremors felt in Thailand.';
const MYANMAR_URL = 'https://en.wikipedia.org/wiki/2025_Myanmar_earthquake';

export default function App() {
  const [wallet, setWallet] = useState('');
  const [pledges, setPledges] = useState([]);
  const [loadingList, setLoadingList] = useState(false);
  const [busy, setBusy] = useState('');
  const [error, setError] = useState('');

  const [org, setOrg] = useState('relief_myanmar_org');
  const [amount, setAmount] = useState('10000');
  const [criteria, setCriteria] = useState(MYANMAR_CRITERIA);
  const [urls, setUrls] = useState(MYANMAR_URL);
  const [deadline, setDeadline] = useState('9999999');

  async function connectWallet() {
    setError('');
    try {
      if (!window.ethereum) {
        setError('MetaMask not found. Please install MetaMask.');
        return;
      }
      const accounts = await window.ethereum.request({ method: 'eth_requestAccounts' });
      setWallet(accounts[0]);
    } catch (e) {
      setError(String(e?.message || e));
    }
  }

  async function refreshList() {
    setLoadingList(true);
    setError('');
    try {
      const count = Number(await readVault('get_pledge_count', []));
      const items = [];
      for (let i = 0; i < count; i++) {
        const status = String(await readVault('get_status', [i]));
        const verdict = String(await readVault('get_verdict', [i]));
        const reason = String(await readVault('get_reason', [i]));
        items.push({ id: i, status, verdict, reason });
      }
      setPledges(items);
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setLoadingList(false);
    }
  }

  useEffect(() => {
    refreshList();
  }, []);

  async function txWrite(functionName, args, busyLabel) {
    if (!wallet) {
      setError('Connect your wallet first.');
      return;
    }
    setBusy(busyLabel);
    setError('');
    try {
      const client = makeWriteClient(wallet);
      const hash = await client.writeContract({
        address: PLEDGE_VAULT,
        functionName,
        args,
        value: BigInt(0),
      });
      await client.waitForTransactionReceipt({
        hash,
        status: TransactionStatus.ACCEPTED,
      });
      await refreshList();
    } catch (e) {
      setError(String(e?.message || e));
    } finally {
      setBusy('');
    }
  }

  async function handleSetTrusted() {
    await txWrite('set_trusted_org', [org], 'Setting trusted org…');
  }

  async function handleCreate() {
    await txWrite(
      'create_pledge',
      [org, parseInt(amount, 10), criteria, urls, parseInt(deadline, 10)],
      'Creating pledge…'
    );
  }

  async function handleTrigger(id) {
    await txWrite('trigger_verification', [id], 'AI jury is investigating… (consensus may take a few minutes)');
  }

  return (
    <div style={{ maxWidth: 760, margin: '40px auto', fontFamily: 'system-ui, sans-serif', padding: 16 }}>
      <h1>CrisisPledge</h1>
      <p style={{ color: '#666' }}>
        Autonomous disaster-relief pledges, adjudicated on-chain by AI validators.
      </p>

      <div style={{ marginBottom: 16 }}>
        {wallet ? (
          <span style={{ color: '#0a7' }}>Wallet: {wallet.slice(0, 6)}…{wallet.slice(-4)}</span>
        ) : (
          <button onClick={connectWallet}>Connect MetaMask</button>
        )}
      </div>

      {error && (
        <p style={{ color: 'crimson', whiteSpace: 'pre-wrap' }}>Error: {error}</p>
      )}
      {busy && (
        <p style={{ color: '#c70', fontWeight: 600 }}>⏳ {busy}</p>
      )}

      <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 16, marginBottom: 16 }}>
        <h3>Create a pledge</h3>
        <div style={{ display: 'grid', gap: 8 }}>
          <label>Relief org (address/id):
            <input value={org} onChange={(e) => setOrg(e.target.value)} style={{ width: '100%' }} />
          </label>
          <label>Amount (cents):
            <input value={amount} onChange={(e) => setAmount(e.target.value)} style={{ width: '100%' }} />
          </label>
          <label>Disaster criteria:
            <textarea value={criteria} onChange={(e) => setCriteria(e.target.value)} rows={3} style={{ width: '100%' }} />
          </label>
          <label>Source URLs (one per line):
            <textarea value={urls} onChange={(e) => setUrls(e.target.value)} rows={3} style={{ width: '100%' }} />
          </label>
          <label>Deadline (timestamp):
            <input value={deadline} onChange={(e) => setDeadline(e.target.value)} style={{ width: '100%' }} />
          </label>
          <div style={{ display: 'flex', gap: 8 }}>
            <button onClick={handleSetTrusted} disabled={!!busy}>1. Mark org trusted</button>
            <button onClick={handleCreate} disabled={!!busy}>2. Create pledge</button>
          </div>
        </div>
      </div>

      <div style={{ border: '1px solid #ddd', borderRadius: 8, padding: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h3>Pledges</h3>
          <button onClick={refreshList} disabled={loadingList}>
            {loadingList ? 'Loading…' : 'Refresh'}
          </button>
        </div>
        {pledges.length === 0 && !loadingList && <p style={{ color: '#888' }}>No pledges yet.</p>}
        {pledges.map((p) => (
          <div key={p.id} style={{ borderTop: '1px solid #eee', padding: '12px 0' }}>
            <strong>Pledge #{p.id}</strong> — Status:{' '}
            <span style={{ color: p.status === 'RELEASED' ? '#0a7' : p.status === 'REFUNDED' ? '#c70' : '#555' }}>
              {p.status}
            </span>
            <div style={{ fontSize: 14, color: '#444', marginTop: 4 }}>
              <div>Verdict: {p.verdict}</div>
              {p.reason && p.reason !== 'NONE' && p.reason !== '' && <div>AI reason: {p.reason}</div>}
            </div>
            {p.status === 'OPEN' && (
              <button onClick={() => handleTrigger(p.id)} disabled={!!busy} style={{ marginTop: 6 }}>
                Trigger AI verification
              </button>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
