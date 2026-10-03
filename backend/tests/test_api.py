def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_seeded_requests_endpoint(seeded_client):
    resp = seeded_client.get("/requests")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 10
    assert all("areaName" in r and "location" in r for r in data)


def test_reset_demo_restores_deterministic_seed_state(seeded_client):
    # Mutate the live state first.
    seeded_client.post("/scenario/apply", json={"actions": [{"type": "Remove Vehicle", "targetId": "V-05", "targetLabel": "V-05"}]})
    allocations = seeded_client.get("/allocations").json()
    first = allocations[0]
    if first["status"] != "Rejected":
        seeded_client.post(f"/allocations/{first['id']}/reject")

    reset_resp = seeded_client.post("/system/reset-demo")
    assert reset_resp.status_code == 200

    vehicles = seeded_client.get("/vehicles").json()
    v5 = next(v for v in vehicles if v["id"] == "V-05")
    assert v5["status"] != "Unavailable"

    requests_after = seeded_client.get("/requests").json()
    assert len(requests_after) == 10

    replans = seeded_client.get("/replan").json()
    assert len(replans) >= 1
    assert replans[0]["status"] == "Pending"  # back to the fresh, undecided seed replan


def test_reset_demo_is_deterministic_across_runs(seeded_client):
    seeded_client.post("/system/reset-demo")
    requests_1 = {r["id"]: r["status"] for r in seeded_client.get("/requests").json()}

    seeded_client.post("/system/reset-demo")
    requests_2 = {r["id"]: r["status"] for r in seeded_client.get("/requests").json()}

    assert requests_1 == requests_2


def test_allocation_exposes_priority_score_and_breakdown(seeded_client):
    allocations = seeded_client.get("/allocations").json()
    assert len(allocations) > 0
    for alloc in allocations:
        assert isinstance(alloc["priorityScore"], float)
        if alloc["priorityBreakdown"] is not None:
            breakdown = alloc["priorityBreakdown"]
            assert set(breakdown.keys()) == {
                "urgencyScore",
                "populationNeedScore",
                "supplyDeficitScore",
                "accessibilityScore",
            }


def test_seeded_sources_and_vehicles(seeded_client):
    sources = seeded_client.get("/sources").json()
    vehicles = seeded_client.get("/vehicles").json()
    assert len(sources) == 7
    assert len(vehicles) == 8
    assert any(v["status"] == "Unavailable" for v in vehicles)


def test_roads_endpoint_has_blocked_segment(seeded_client):
    data = seeded_client.get("/roads").json()
    assert any(e["condition"] == "Blocked" for e in data["edges"])


def test_allocations_were_generated_by_seed(seeded_client):
    allocations = seeded_client.get("/allocations").json()
    assert len(allocations) > 0
    assert any(a["status"] == "Proposed" for a in allocations)
    assert any(a["status"] == "Accepted" for a in allocations)


def test_accept_reject_modify_allocation_flow(seeded_client):
    allocations = seeded_client.get("/allocations").json()
    proposed = next(a for a in allocations if a["status"] == "Proposed")

    modify_resp = seeded_client.post(f"/allocations/{proposed['id']}/modify", json={"quantity": 1})
    assert modify_resp.status_code == 200
    assert modify_resp.json()["status"] == "Modified"
    assert modify_resp.json()["quantity"] == 1

    accept_resp = seeded_client.post(f"/allocations/{proposed['id']}/accept")
    assert accept_resp.status_code == 200
    assert accept_resp.json()["status"] == "Accepted"

    deliveries = seeded_client.get("/deliveries").json()
    assert any(d["allocationId"] == proposed["id"] for d in deliveries)

    reject_resp = seeded_client.post(f"/allocations/{proposed['id']}/reject")
    assert reject_resp.status_code == 200
    assert reject_resp.json()["status"] == "Rejected"


def test_modify_rejects_quantity_exceeding_inventory(seeded_client):
    allocations = seeded_client.get("/allocations").json()
    target = allocations[0]
    resp = seeded_client.post(f"/allocations/{target['id']}/modify", json={"quantity": 10_000_000})
    assert resp.status_code == 422


def test_accept_unknown_allocation_is_404(client):
    resp = client.post("/allocations/ALC-DOES-NOT-EXIST/accept")
    assert resp.status_code == 404


def test_delivery_status_cannot_skip_stages(seeded_client):
    deliveries = seeded_client.get("/deliveries").json()
    target = next(d for d in deliveries if d["status"] == "Assigned")
    resp = seeded_client.post(f"/deliveries/{target['id']}/status", json={"status": "Delivered"})
    assert resp.status_code == 422
    resp_ok = seeded_client.post(f"/deliveries/{target['id']}/status", json={"status": "Accepted"})
    assert resp_ok.status_code == 200
    assert resp_ok.json()["status"] == "Accepted"


def test_replan_was_generated_by_seed(seeded_client):
    replans = seeded_client.get("/replan").json()
    assert len(replans) >= 1
    event = replans[0]
    assert event["oldPlan"]["sourceId"]
    assert event["newPlan"]["sourceId"]
    assert event["status"] == "Pending"


def test_apply_replan_updates_status(seeded_client):
    replans = seeded_client.get("/replan").json()
    event_id = replans[0]["id"]
    resp = seeded_client.post(f"/replan/{event_id}/apply")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Applied"


def test_dismiss_replan_updates_status(seeded_client):
    replans = seeded_client.get("/replan").json()
    event_id = replans[0]["id"]
    resp = seeded_client.post(f"/replan/{event_id}/dismiss")
    assert resp.status_code == 200
    assert resp.json()["status"] == "Dismissed"


def test_scenario_simulate_does_not_mutate_live_state(seeded_client):
    before_sources = seeded_client.get("/sources").json()
    resp = seeded_client.post(
        "/scenario/simulate",
        json={"actions": [{"type": "Block Road", "targetId": "R9", "targetLabel": "test"}]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert "before" in body and "after" in body

    after_sources = seeded_client.get("/sources").json()
    assert before_sources == after_sources

    roads = seeded_client.get("/roads").json()
    r9 = next(e for e in roads["edges"] if e["id"] == "R9")
    assert r9["condition"] != "Blocked", "simulate must not persist the road block"


def test_scenario_apply_does_mutate_live_state(seeded_client):
    resp = seeded_client.post(
        "/scenario/apply",
        json={"actions": [{"type": "Remove Vehicle", "targetId": "V-07", "targetLabel": "test"}]},
    )
    assert resp.status_code == 200
    vehicles = seeded_client.get("/vehicles").json()
    v7 = next(v for v in vehicles if v["id"] == "V-07")
    assert v7["status"] == "Unavailable"


def test_bottlenecks_reflect_unmet_demand(seeded_client):
    resp = seeded_client.get("/bottlenecks")
    assert resp.status_code == 200
    bottlenecks = resp.json()
    assert isinstance(bottlenecks, list)
    for b in bottlenecks:
        assert b["type"] in {"Vehicle Capacity", "Medicine Shortage", "Road Access", "Source Availability", "Deadline Constraint"}


def test_analytics_compares_loksahay_and_baseline(seeded_client):
    resp = seeded_client.get("/analytics")
    assert resp.status_code == 200
    data = resp.json()
    assert data["loksahay"]["label"] == "LokSahay Allocation"
    assert "baseline" in data["baseline"]["label"].lower() or "Baseline" in data["baseline"]["label"]
    assert data["loksahay"]["metrics"]["demandFulfilledPct"] >= data["baseline"]["metrics"]["demandFulfilledPct"]
    assert len(data["history"]) >= 1


def test_algorithm_config_get_and_put(seeded_client):
    resp = seeded_client.get("/algorithm/config")
    assert resp.status_code == 200
    original = resp.json()

    put_resp = seeded_client.put("/algorithm/config", json={"urgencyWeight": 0.6})
    assert put_resp.status_code == 200
    assert put_resp.json()["priorityWeights"]["urgency"] == 0.6
    assert put_resp.json()["priorityWeights"]["populationNeed"] == original["priorityWeights"]["populationNeed"]


def test_algorithm_config_minimum_coverage_round_trips_as_percent(seeded_client):
    # GET returns minimumCoveragePct as 0-100 (e.g. 60); PUT must accept
    # that same 0-100 scale back, not the internal 0-1 fraction.
    get_resp = seeded_client.get("/algorithm/config").json()
    assert get_resp["minimumCoveragePct"] == 60.0

    put_resp = seeded_client.put("/algorithm/config", json={"minimumCoveragePct": 75}).json()
    assert put_resp["minimumCoveragePct"] == 75.0

    reget_resp = seeded_client.get("/algorithm/config").json()
    assert reget_resp["minimumCoveragePct"] == 75.0


def test_map_endpoint_returns_full_snapshot(seeded_client):
    resp = seeded_client.get("/map")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["nodes"]) > 0
    assert len(data["requests"]) == 10


def test_run_allocation_endpoint(seeded_client):
    resp = seeded_client.post("/allocation/run")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
