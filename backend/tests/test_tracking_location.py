def test_delivery_events_have_coordinates(seeded_client):
    deliveries = seeded_client.get("/deliveries").json()
    assert len(deliveries) > 0
    for d in deliveries:
        assert len(d["events"]) > 0
        for event in d["events"]:
            assert event["location"] is not None
            assert isinstance(event["location"]["lat"], float)
            assert isinstance(event["location"]["lng"], float)


def test_delivery_current_location_matches_last_event(seeded_client):
    deliveries = seeded_client.get("/deliveries").json()
    for d in deliveries:
        last_event = d["events"][-1]
        assert d["currentLocation"] == last_event["location"]


def test_current_location_moves_as_delivery_advances(seeded_client):
    deliveries = seeded_client.get("/deliveries").json()
    target = next(d for d in deliveries if d["status"] == "Assigned")
    origin_location = target["currentLocation"]

    advanced = seeded_client.post(f"/deliveries/{target['id']}/status", json={"status": "Accepted"}).json()
    assert advanced["currentLocation"] == origin_location  # still at origin

    picked_up = seeded_client.post(f"/deliveries/{target['id']}/status", json={"status": "Picked Up"}).json()
    assert picked_up["currentLocation"] == origin_location  # still at origin

    in_transit = seeded_client.post(f"/deliveries/{target['id']}/status", json={"status": "In Transit"}).json()
    # Should have moved away from the origin to a midpoint waypoint
    # (unless the route is only 2 nodes, in which case midpoint == origin).
    route = seeded_client.get(f"/routes/{target['routeId']}").json()
    if len(route["nodeIds"]) > 2:
        assert in_transit["currentLocation"] != origin_location
