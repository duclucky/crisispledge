import { createClient, createAccount } from 'genlayer-js';
import { testnetBradbury } from 'genlayer-js/chains';
import { TransactionStatus } from 'genlayer-js/types';

export const PLEDGE_VAULT = '0xD108Cb3c2bF0b619d73a911ac89211DEd5259aEd';

// Read-only client (reads need no signing).
const readAccount = createAccount();
export const readClient = createClient({
  chain: testnetBradbury,
  account: readAccount,
});

export async function readVault(functionName, args = []) {
  return await readClient.readContract({
    address: PLEDGE_VAULT,
    functionName,
    args,
  });
}

// Build a write client bound to the connected MetaMask address.
export function makeWriteClient(walletAddress) {
  return createClient({
    chain: testnetBradbury,
    account: walletAddress,
  });
}

export { TransactionStatus };
