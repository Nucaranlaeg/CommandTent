from server.sim.loop import Simulation
from server.radio.bus import RadioBus
from server.orders.executor import OrderExecutor
from map.map import Map
from unit.unit import UnitModel
from schemas.types import ROE, Posture


def test_radio_latency_and_suppression():
    radio = RadioBus(latency_ticks=2, suppress_window_ticks=3)
    sim = Simulation(seed=1)

    delivered = []
    def handler(evt):
        delivered.append((evt.tick_emit, evt.channel, evt.message))

    radio.send(sim.clock, channel="Red", message="Ack")
    radio.send(sim.clock, channel="Red", message="Ack")

    for _ in range(2):
        sim.step()
        radio.deliver(sim.clock, handler)

    assert len(delivered) == 1
    assert delivered[0][1] == "Red"


def test_order_executor_move_sets_station_and_acks():
    m = Map(1000, 1000, seed=5)
    radio = RadioBus(latency_ticks=1)
    units = {
        "Red": UnitModel(unit_id="Red", speed_cells_per_second=5.0, position=(10.5, 10.5), fireteam_name="Red")
    }
    exec = OrderExecutor(m, units, radio)
    sim = Simulation(seed=2)

    order = {
        "units": ["Red"],
        "intent": "move",
        "waypoints": ["C2", "D3"],
        "constraints": {"preferTerrain": ["forest"], "stayConcealed": True},
        "roe": "hold",
        "posture": "prone"
    }

    assert exec.apply_order(sim.clock, order)
    # ROE and posture applied
    assert units["Red"].roe == ROE.HOLD
    assert units["Red"].posture == Posture.PRONE

    radio.deliver(sim.clock, lambda e: None)
    sim.step()
    delivered = []
    radio.deliver(sim.clock, lambda e: delivered.append(e))

    assert delivered and delivered[0].channel == "Red"
    assert units["Red"].path
