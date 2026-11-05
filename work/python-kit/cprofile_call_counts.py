import cProfile
import pstats

def net_total(amounts):
    return sum(amount - 3 for amount in amounts)

profile = cProfile.Profile()
for _ in range(3):
    last_total = profile.runcall(net_total, (47, 48, 49))
statistics = pstats.Stats(profile)
calls = sum(record[1] for key, record in statistics.stats.items()
            if key[2] == "net_total")
print("last_total", last_total)
print("calls", calls)
