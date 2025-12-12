import time

from server.sim.loop import Simulation, SimClock, TICK_DT


def test_sim_deterministic_rng():
    seq1 = []
    seq2 = []

    def on_tick(clock, rng):
        seq1.append(rng.random())

    def on_tick2(clock, rng):
        seq2.append(rng.random())

    s1 = Simulation(seed=42, on_tick=on_tick)
    s2 = Simulation(seed=42, on_tick=on_tick2)

    s1.run_for_ticks(20, realtime=False)
    s2.run_for_ticks(20, realtime=False)

    assert seq1 == seq2


def test_sim_clock_progression_no_realtime():
    s = Simulation(seed=1)
    s.run_for_ticks(5, realtime=False)
    assert s.clock.tick == 5
    assert abs(s.clock.time_seconds - 5 * TICK_DT) < 1e-9


def test_sim_realtime_sleeping():
    s = Simulation(seed=1)
    start = time.perf_counter()
    s.run_for_ticks(5, realtime=True)
    elapsed = time.perf_counter() - start
    assert elapsed >= 5 * TICK_DT * 0.9  # allow small scheduling variance
