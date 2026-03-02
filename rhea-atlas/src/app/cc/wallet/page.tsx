"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

const API = typeof window !== "undefined" ? window.location.origin : "";

interface WalletAddress {
  symbol: string;
  name: string;
  address: string;
  network: string;
  color: string;
  icon: string;
}

// On-chain balance cache (60s TTL)
const balanceCache: Record<string, { value: string; ts: number }> = {};
const CACHE_TTL = 60000;

async function fetchBalance(symbol: string, address: string): Promise<string> {
  const key = `${symbol}:${address}`;
  const cached = balanceCache[key];
  if (cached && Date.now() - cached.ts < CACHE_TTL) return cached.value;

  try {
    let balance = "—";
    if (symbol === "BTC") {
      const r = await fetch(`https://blockchain.info/q/addressbalance/${address}?confirmations=1`);
      if (r.ok) {
        const sats = parseInt(await r.text());
        balance = (sats / 1e8).toFixed(8) + " BTC";
      }
    } else if (symbol === "ETH") {
      // Public Ethereum RPC — eth_getBalance
      const r = await fetch("https://eth.llamarpc.com", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ jsonrpc: "2.0", method: "eth_getBalance", params: [address, "latest"], id: 1 }),
      });
      if (r.ok) {
        const data = await r.json();
        const wei = parseInt(data.result, 16);
        balance = (wei / 1e18).toFixed(6) + " ETH";
      }
    }
    balanceCache[key] = { value: balance, ts: Date.now() };
    return balance;
  } catch {
    return "—";
  }
}

export default function WalletPage() {
  const [addresses, setAddresses] = useState<WalletAddress[]>([]);
  const [balances, setBalances] = useState<Record<string, string>>({});
  const [credits, setCredits] = useState<{balance: number; plan: string} | null>(null);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    // Fetch wallet addresses from the API health/config
    // These are public addresses — safe to display
    const knownAddresses: WalletAddress[] = [
      {
        symbol: "BTC",
        name: "Bitcoin",
        address: "1FuwzXXgUjxNRUs3TTkedJk3WVJmEVWXyy",
        network: "Bitcoin Mainnet",
        color: "#FF9F0A",
        icon: "\u20BF",
      },
      {
        symbol: "ETH",
        name: "Ethereum",
        address: "0xdF1EC0eB67b3cbd8E2dC518cba806742aF51DDcC",
        network: "Ethereum Mainnet",
        color: "#627EEA",
        icon: "\u039E",
      },
      {
        symbol: "USDT",
        name: "Tether (ERC-20)",
        address: "0xdF1EC0eB67b3cbd8E2dC518cba806742aF51DDcC",
        network: "Ethereum (same address)",
        color: "#26A17B",
        icon: "\u20AE",
      },
    ];
    setAddresses(knownAddresses);

    // Fetch on-chain balances (BTC + ETH only, USDT shares ETH address)
    Promise.all([
      fetchBalance("BTC", knownAddresses[0].address),
      fetchBalance("ETH", knownAddresses[1].address),
    ]).then(([btc, eth]) => {
      setBalances({
        [knownAddresses[0].address + ":BTC"]: btc,
        [knownAddresses[1].address + ":ETH"]: eth,
      });
    });

    // Fetch user credits if authenticated
    const token = typeof window !== "undefined" ? localStorage.getItem("rhea_token") : null;
    if (token) {
      fetch(`${API}/billing/credits`, {
        headers: { Authorization: `Bearer ${token}` },
      })
        .then((r) => r.ok ? r.json() : null)
        .then((d) => d && setCredits(d))
        .catch(() => {});
    }
  }, []);

  const copyAddr = (addr: string) => {
    navigator.clipboard.writeText(addr);
    setCopied(addr);
    setTimeout(() => setCopied(null), 2000);
  };

  return (
    <div className="min-h-screen bg-[#0a0a0f] text-white/90 p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-bold tracking-tight">Wallet</h1>
            <p className="text-white/40 text-sm mt-1">
              Receive crypto payments. 5% funds development, 95% credits your account.
            </p>
          </div>
          <Link
            href="/cc"
            className="text-xs text-white/30 hover:text-white/60 transition-colors"
          >
            &larr; Command Centre
          </Link>
        </div>

        {/* Credits balance */}
        {credits && (
          <div className="bg-white/[0.03] border border-white/[0.08] rounded-2xl p-5 mb-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-xs text-white/40 uppercase tracking-widest mb-1">
                  Account Balance
                </div>
                <div className="text-3xl font-bold">
                  {credits.balance.toLocaleString()}
                  <span className="text-sm text-white/30 ml-2">credits</span>
                </div>
              </div>
              <div className="text-xs text-white/30 bg-white/[0.04] px-3 py-1 rounded-full border border-white/[0.06]">
                {credits.plan} plan
              </div>
            </div>
          </div>
        )}

        {/* Crypto addresses */}
        <div className="space-y-3">
          <div className="text-xs text-white/30 uppercase tracking-widest mb-2">
            Receive Addresses
          </div>
          {addresses.map((w) => (
            <div
              key={w.symbol}
              className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-4 hover:border-white/[0.15] transition-all cursor-pointer group"
              onClick={() => copyAddr(w.address)}
            >
              <div className="flex items-center gap-4">
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold shrink-0"
                  style={{ background: `${w.color}18`, color: w.color }}
                >
                  {w.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-sm">{w.name}</span>
                    <span className="text-[10px] text-white/25">{w.symbol}</span>
                  </div>
                  <div className="font-mono text-xs text-white/40 truncate group-hover:text-white/60 transition-colors">
                    {w.address}
                  </div>
                  <div className="text-[10px] text-white/20 mt-0.5">{w.network}</div>
                </div>
                <div className="text-right shrink-0">
                  <div className="text-xs font-mono text-white/30">
                    {balances[`${w.address}:${w.symbol}`] || ""}
                  </div>
                  <div className="text-[10px] text-white/20 group-hover:text-white/50 transition-colors">
                    {copied === w.address ? (
                      <span className="text-green-400">Copied!</span>
                    ) : (
                      "Click to copy"
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* How it works */}
        <div className="mt-8 bg-white/[0.02] border border-white/[0.06] rounded-xl p-5">
          <h3 className="text-sm font-semibold mb-3">How it works</h3>
          <div className="space-y-2 text-xs text-white/40 leading-relaxed">
            <p>
              1. Send any amount to the address above. First payment auto-creates your account.
            </p>
            <p>
              2. BTCPay webhook detects the transaction. A <strong className="text-white/60">patron key</strong> is
              derived from your tx hash &mdash; redeemable anytime at <code className="text-white/50">/auth/redeem</code>.
            </p>
            <p>
              3. <strong className="text-white/60">95%</strong> converts to Rhea credits instantly.
            </p>
            <p>
              4. <strong className="text-white/60">5%</strong> funds real-world impact:
            </p>
          </div>
          <div className="flex flex-wrap gap-2 mt-3 mb-3">
            <span className="bg-green-500/10 border border-green-500/20 text-green-400 text-[10px] px-2.5 py-1 rounded-full">
              2% carbon-neutral GPU compute
            </span>
            <span className="bg-blue-500/10 border border-blue-500/20 text-blue-400 text-[10px] px-2.5 py-1 rounded-full">
              2% open-science grants
            </span>
            <span className="bg-orange-500/10 border border-orange-500/20 text-orange-400 text-[10px] px-2.5 py-1 rounded-full">
              1% animal shelter fund
            </span>
          </div>
          <div className="text-xs text-white/40 leading-relaxed">
            <p>
              5. Credits unlock tribunal queries, ICE verification, Aletheia proof storage, and sceptic mode.
            </p>
          </div>
        </div>

        {/* Security note */}
        <div className="mt-4 text-[11px] text-white/20 text-center">
          Private keys are stored in Fly.io encrypted secrets. Never exposed in code or logs.
          <br />
          Addresses are deterministically generated via ECDSA secp256k1.
        </div>
      </div>
    </div>
  );
}
