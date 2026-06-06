import heapq
import time

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

# --- Input helpers ---
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
        print(f"Error: A+B+C+D={A+B+C+D} must equal N={N}. Using N={A+B+C+D}.")
        N = A + B + C + D
    return A, B, C, D, N

def get_bids(N):
    print(f"\n=== Bid Entry (press Enter to use defaults) ===")
    print("Format per bidder: a b c d  (space separated)")
    bids = []
    for i in range(N):
        default = DEFAULT_BIDS[i] if i < len(DEFAULT_BIDS) else (1, 1, 1, 1)
        val = input(f"Bidder {i+1} {default}: ").strip()
        if val:
            parts = list(map(int, val.split()))
            if len(parts) != 4:
                print(f"  Need exactly 4 values. Using default {default}.")
                bids.append(default)
            else:
                bids.append(tuple(parts))
        else:
            bids.append(default)
    return bids

# --- Algorithm ---
def solve(bids, A, B, C, D):
    ops = 0
    counts = [A, B, C, D]
    names  = ["Artifact", "Balloon", "Crystal", "Diamond"]

    # pick baseline: type with most slots
    base = max(range(4), key=lambda i: counts[i])
    types = [i for i in range(4) if i != base]

    # baseline sum
    baseline = sum(b[base] for b in bids)
    ops += len(bids)

    # one min-heap per non-baseline type: stores (delta, bidder_index)
    heaps = {t: [] for t in types}
    caps  = {t: counts[t] for t in types}

    for i, bid in enumerate(bids):
        for t in types:
            delta = bid[t] - bid[base]
            ops += 1  # delta computation
            cap = caps[t]
            h = heaps[t]
            if len(h) < cap:
                heapq.heappush(h, (delta, i))
                ops += 1
            elif delta > h[0][0]:
                heapq.heapreplace(h, (delta, i))
                ops += 1

    # read out assignments
    assignment = [names[base]] * len(bids)
    total_delta = 0
    for t in types:
        for delta, i in heaps[t]:
            assignment[i] = names[t]
            total_delta += delta
            ops += 1

    revenue = baseline + total_delta
    return assignment, revenue, ops

# --- Main ---
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
    type_map = {"Artifact": 0, "Balloon": 1, "Crystal": 2, "Diamond": 3}
    for i, (bid, item) in enumerate(zip(bids, assignment)):
        price = bid[type_map[item]]
        print(f"{i+1:<10} {str(bid):<25} {item:<12} {price}")

    print("-" * 60)
    print(f"Total revenue  : {revenue}")
    print(f"Time taken     : {elapsed*1000:.4f} ms")
    print(f"Operations     : {ops}")

if __name__ == "__main__":
    main()