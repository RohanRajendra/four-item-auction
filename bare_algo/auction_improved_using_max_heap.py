"""
Four-Item Auction: exact revenue-maximizing assignment.

N bidders, four item types A, B, C, D with capacities summing to N.
Every bidder gets exactly one item; goal is to maximize total revenue.

This file keeps the same I/O conventions as the reference implementation:
  solve(bids, A, B, C, D) -> (assignment, revenue, ops)
where `assignment` is a list of type-name strings, `revenue` is the optimum,
and `ops` counts primitive operations for empirical-cost reporting.

The algorithm is incremental and exact (O(N log K), K = largest small capacity).
Conflicts are resolved AT INSERTION via an augmenting chain -- there is no
post-processing reconciliation pass.
"""

import heapq
import time
from itertools import combinations

NAMES = ["Artifact", "Balloon", "Crystal", "Diamond"]

# --- Defaults ---
DEFAULT_A, DEFAULT_B, DEFAULT_C, DEFAULT_D = 1, 1, 1, 5
DEFAULT_BIDS = [
    (10, 3,  2, 8),
    (4,  9,  1, 7),
    (6,  2, 11, 5),
    (1,  5,  3, 9),
    (7,  4,  6, 2),
    (2,  8,  4, 3),
    (3,  1,  7, 6),
    (5,  6,  8, 4),
]


# ===========================================================================
# Core solver
# ===========================================================================
class _HeapAuction:
    """
    Maintains the optimal assignment of all bidders inserted so far.

    The absorbed type (the one with the most slots) is the baseline: every
    effective bid is measured relative to it, so the absorbed type contributes 0.
    All four types are still modelled as heaps with mandatory capacities summing
    to N, so every bidder lands in exactly one heap.

      eff(i, t) = bids[i][t] - bids[i][base]      (eff(i, base) = 0)

    Data structures, all O(log K) via lazy (versioned) deletion:
      minh[t]          : min-heap on eff(i, t). Root = weakest member of type t.
      dmax[here][dest] : max-heap on eff(i, dest) - eff(i, here) over members of
                         `here`. Root = member cheapest to relocate here -> dest.
    """

    def __init__(self, bids, caps, base):
        self.bids = bids
        self.cap = list(caps)
        self.base = base
        self.const = sum(b[base] for b in bids)
        self.owner = {}
        self.ver = {}
        self.size = [0, 0, 0, 0]
        self.minh = [[] for _ in range(4)]
        self.dmax = [[[] for _ in range(4)] for _ in range(4)]
        self.ops = 0

    def eff(self, i, t):
        return 0 if t == self.base else self.bids[i][t] - self.bids[i][self.base]

    def _add(self, i, t):
        self.owner[i] = t
        self.size[t] += 1
        v = self.ver.get(i, 0) + 1
        self.ver[i] = v
        heapq.heappush(self.minh[t], (self.eff(i, t), i, v))
        self.ops += 1
        for dest in range(4):
            if dest != t:
                key = -(self.eff(i, dest) - self.eff(i, t))
                heapq.heappush(self.dmax[t][dest], (key, i, v))
                self.ops += 1

    def _remove(self, i):
        t = self.owner.pop(i)
        self.size[t] -= 1
        self.ver[i] = self.ver.get(i, 0) + 1     # bump version: stale entries die lazily

    def _live(self, entry, t):
        _, i, v = entry
        return self.owner.get(i) == t and self.ver.get(i) == v

    def _best_victim(self, here, dest):
        h = self.dmax[here][dest]
        while h and not self._live(h[0], here):
            heapq.heappop(h)
            self.ops += 1
        return h[0][1] if h else None

    def insert(self, i):
        """Seat bidder i via the maximum-gain augmenting chain (depth <= 4)."""
        best = (float("-inf"), None)

        def dfs(cur, used, gain, ops_list):
            nonlocal best
            for t in range(4):
                if t in used:
                    continue
                e = self.eff(cur, t)
                self.ops += 1
                if self.size[t] < self.cap[t]:                 # free slot ends the chain
                    g = gain + e
                    if g > best[0]:
                        best = (g, ops_list + [("seat", cur, t)])
                else:                                          # full: relocate a victim
                    for dest in range(4):
                        if dest == t or dest in used:
                            continue
                        victim = self._best_victim(t, dest)
                        if victim is None:
                            continue
                        g2 = gain + e - self.eff(victim, t)
                        dfs(victim, used | {t}, g2,
                            ops_list + [("swap", cur, t, victim)])

        dfs(i, frozenset(), 0.0, [])
        for op in best[1]:
            if op[0] == "seat":
                _, c, t = op
                self._add(c, t)
            else:
                _, c, t, victim = op
                self._remove(victim)
                self._add(c, t)

    def revenue(self):
        return self.const + sum(self.eff(i, self.owner[i]) for i in self.owner)

    def assignment(self):
        out = [None] * len(self.bids)
        for i, t in self.owner.items():
            out[i] = NAMES[t]
        return out


def solve(bids, A, B, C, D):
    """
    Exact optimum. Returns (assignment, revenue, ops).

    Absorb the largest-capacity type (deterministic tie-break: highest index),
    which minimizes the log factor in the runtime.
    """
    caps = [A, B, C, D]
    max_count = max(caps)
    base = max(i for i in range(4) if caps[i] == max_count)
    au = _HeapAuction(bids, caps, base)
    for i in range(len(bids)):
        au.insert(i)
    return au.assignment(), au.revenue(), au.ops


# ===========================================================================
# Reference solver (brute force) -- for testing only
# ===========================================================================
def brute_force(bids, A, B, C, D):
    ids = range(len(bids))
    best = None
    for SA in combinations(ids, A):
        r1 = [i for i in ids if i not in SA]
        for SB in combinations(r1, B):
            r2 = [i for i in r1 if i not in SB]
            for SC in combinations(r2, C):
                SD = [i for i in r2 if i not in SC]
                rev = (sum(bids[i][0] for i in SA) + sum(bids[i][1] for i in SB)
                       + sum(bids[i][2] for i in SC) + sum(bids[i][3] for i in SD))
                if best is None or rev > best:
                    best = rev
    return best


# ===========================================================================
# Interactive front-end (same prompts/format as the reference)
# ===========================================================================
def prompt_int(msg, default):
    val = input(f"{msg} [default={default}]: ").strip()
    return int(val) if val else default


def get_params():
    print("\n=== Auction Parameters ===")
    A = prompt_int("A (Artifact slots)", DEFAULT_A)
    B = prompt_int("B (Balloon slots)",  DEFAULT_B)
    C = prompt_int("C (Crystal slots)",  DEFAULT_C)
    D = prompt_int("D (Diamond slots)",  DEFAULT_D)
    N = prompt_int("N (total bidders)",  A + B + C + D)
    if N != A + B + C + D:
        print(f"Error: A+B+C+D={A+B+C+D} must equal N. Using N={A+B+C+D}.")
        N = A + B + C + D
    return A, B, C, D, N


def get_bids(N):
    print("\n=== Bid Entry (press Enter to use defaults) ===")
    print("Format per bidder: a b c d  (space separated)")
    bids = []
    for i in range(N):
        default = DEFAULT_BIDS[i] if i < len(DEFAULT_BIDS) else (1, 1, 1, 1)
        val = input(f"Bidder {i+1} {default}: ").strip()
        if val:
            parts = list(map(int, val.split()))
            bids.append(tuple(parts) if len(parts) == 4 else default)
        else:
            bids.append(default)
    return bids


def main():
    A, B, C, D, N = get_params()
    bids = get_bids(N)

    print("\nRunning...")
    t0 = time.perf_counter()
    assignment, revenue, ops = solve(bids, A, B, C, D)
    elapsed = time.perf_counter() - t0

    print("\n=== Results ===")
    print(f"{'Bidder':<10} {'Bids (A,B,C,D)':<25} {'Assigned':<12} {'Price'}")
    print("-" * 60)
    type_map = {name: i for i, name in enumerate(NAMES)}
    for i, (bid, item) in enumerate(zip(bids, assignment)):
        price = bid[type_map[item]]
        print(f"{i+1:<10} {str(bid):<25} {item:<12} {price}")
    print("-" * 60)
    print(f"Total revenue  : {revenue}")
    print(f"Time taken     : {elapsed*1000:.4f} ms")
    print(f"Operations     : {ops}")


if __name__ == "__main__":
    main()