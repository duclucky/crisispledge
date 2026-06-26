# TrustlessAgent

**The trust layer for the AI agent economy, built on GenLayer Intelligent Contracts.**

> Why this dies without GenLayer: judging whether a delivered work product truly meets agreed terms is a subjective, evidence based decision that reads the open web and that no single party should control. Solidity cannot read a URL or reason over unstructured deliverables. GenLayer's AI validators can, and they agree on the meaning of the verdict through consensus.

Live app: https://trustlessagent.vercel.app
Repository: https://github.com/duclucky/trustlessagent

## 1. The problem

As autonomous AI agents start trading goods, data, and services with each other, they hit a wall of distrust. When two agents transact, neither side can be sure of the other. Did the seller deliver real quality, or a convincing shell with poor substance inside? Did the buyer pay after receiving the work, or copy it and falsely report a failure? Ordinary smart contracts only see token movements, never whether a deliverable actually satisfies the terms of the deal. That judgment has never been possible on-chain.

## 2. The solution

TrustlessAgent is an Intelligent Contract that acts as a neutral AI jury for agent to agent commerce. A buyer locks funds together with the deal terms in plain language, the URLs where the deliverable lives (a repository, a hosted output, an API response, a file), and a deadline. On trigger, the contract reads those sources live on-chain with `gl.nondet.web.render`, and a jury of AI validators reaches consensus with `gl.nondet.exec_prompt` on a subjective question: was the deliverable actually provided, at the agreed quality, consistent with the terms? A CONFIRMED verdict releases the funds to the seller. If it is not confirmed by the deadline, the buyer is refunded.

The first public demo applied the exact same engine to disaster relief verification, which is why the deployed contracts use pledge style naming internally.

## 3. Architecture

Three cooperating contracts on GenLayer testnet (Bradbury):

- **PledgeVault** (`0xD108Cb3c2bF0b619d73a911ac89211DEd5259aEd`) holds the deal state and owns the lifecycle: open escrow, trigger the AI verdict, release or refund. It contains the core non deterministic verification logic.
- **DisasterOracle** (`0x36D6928a8359005Dd916C8347b6c42FB9cbCA3FF`) the standalone verdict engine: multi source `web.render` plus `exec_prompt` with an independent validator consensus.
- **ReliefRegistry** (`0x29CCD0E0e2E28e42b1778635beD55757d34eF58a`) a lighter second non deterministic use that checks whether a counterparty looks legitimate.

Flow: open escrow, trigger verification, read sources on-chain, AI jury reaches a verdict, release to seller or keep locked, refund after the deadline if never confirmed.

## 4. Why the consensus is on meaning, not format

This is the most important design point. The verdict is reached with `gl.vm.run_nondet_unsafe(leader_fn, validator_fn)`. The leader reads the sources and asks the LLM for a structured verdict. Each validator then independently re runs the same work and compares only the decision fields: the verdict label (CONFIRMED, REJECTED, INSUFFICIENT) and the cross source consistency flag. The free text reason may differ between validators, but the decision must match. Two validators returning valid JSON yet disagreeing on the verdict fail consensus. The agreement is on the meaning of the ruling, never on the JSON schema.

## 5. Edge cases handled

Dead or empty URL, broken or partial LLM output, zero sources, amount of zero rejected at creation, double release blocked once resolved, refund blocked before the deadline or after resolution, untrusted counterparty blocks release, and a confidence threshold below which funds are never released.

## 6. Testnet lessons baked into the code

Discovered the hard way on Bradbury and applied across all contracts:

1. No `import json` in a contract. It breaks schema loading. JSON is parsed manually.
2. `int` and `bool` cannot be storage fields. Numbers use `u256`, booleans are stored as the strings "true" and "false".
3. No free functions at module level. All helpers are methods inside the `Contract` class.
4. Consensus uses a hand written validator with `run_nondet_unsafe`, not `prompt_comparative`, which caused non deterministic disagreement on free text.
5. Values read from storage must be coerced to plain Python strings and any list must be materialized outside the leader closure, otherwise the non deterministic block fails to use them.

## 7. Tech stack

GenLayer Intelligent Contracts in Python (GenVM v0.2.16). Frontend in React with Vite and genlayer-js, connecting to testnet Bradbury through MetaMask. Frontend hosted on Vercel.

## 8. Repository layout

```
contracts/      PledgeVault.py, DisasterOracle.py, ReliefRegistry.py, storage_test.py
frontend/       Vite + React app using genlayer-js
tests/          contract test notes
scripts/        helper scripts
README.md
```

## 9. Deploy the contracts to testnet (GenLayer Studio)

1. Open https://studio.genlayer.com/run-debug
2. Deploy `contracts/storage_test.py` first as a sanity check. Click the transaction and confirm Result: SUCCESS.
3. Deploy `contracts/DisasterOracle.py`, then `contracts/ReliefRegistry.py`, then `contracts/PledgeVault.py`. Record each address.
4. For every deploy, click the transaction in the sidebar and confirm Result: SUCCESS, not just FINALIZED.

## 10. Run the frontend locally

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173, connect MetaMask on the GenLayer testnet, and use the app. The deployed contract addresses are set in `frontend/src/genlayer.js`.

## 11. Full user flow

Connect MetaMask, register the seller agent as trusted, open an escrow deal with the terms and the deliverable URLs, trigger the AI jury and wait through consensus (a few minutes), then watch the deal resolve to RELEASED with the on-chain verdict and the jury's reason, or refund after the deadline.

## 12. Scope and roadmap

Proof of concept. The RELEASED state represents the on-chain release decision reached by the AI jury. Native token custody and transfer is the next integration step. The same engine generalizes to bug bounties, creator and KOL payouts, grant milestones, and parametric style settlements, any market where a payout depends on a subjective judgment over real world evidence.
