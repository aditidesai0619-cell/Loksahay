def test_partners_list_matches_vehicle_partner_strings(seeded_client):
    partners = seeded_client.get("/partners").json()
    vehicles = seeded_client.get("/vehicles").json()

    assert len(partners) == 5
    partner_names = {p["name"] for p in partners}
    vehicle_partner_names = {v["partner"] for v in vehicles}
    assert partner_names == vehicle_partner_names, "every Vehicle.partner string must resolve to a real partner"


def test_partner_vehicle_counts_are_consistent_with_fleet(seeded_client):
    partners = seeded_client.get("/partners").json()
    vehicles = seeded_client.get("/vehicles").json()

    total_vehicles_under_partners = sum(len(p["vehicles"]) for p in partners)
    assert total_vehicles_under_partners == len(vehicles)


def test_partner_has_contact_and_phone(seeded_client):
    partners = seeded_client.get("/partners").json()
    for p in partners:
        assert p["contactPerson"]
        assert p["phone"]
        assert p["id"].startswith("PTR-")


def test_get_single_partner(seeded_client):
    partners = seeded_client.get("/partners").json()
    first = partners[0]
    resp = seeded_client.get(f"/partners/{first['id']}")
    assert resp.status_code == 200
    assert resp.json()["name"] == first["name"]


def test_get_unknown_partner_is_404(seeded_client):
    resp = seeded_client.get("/partners/PTR-DOES-NOT-EXIST")
    assert resp.status_code == 404


def test_partner_completed_and_active_deliveries_sum_consistently(seeded_client):
    partners = seeded_client.get("/partners").json()
    deliveries = seeded_client.get("/deliveries").json()
    vehicles = seeded_client.get("/vehicles").json()
    vehicle_to_partner = {v["id"]: v["partner"] for v in vehicles}

    expected_completed: dict[str, int] = {}
    expected_active: dict[str, int] = {}
    for d in deliveries:
        partner_name = vehicle_to_partner[d["vehicleId"]]
        bucket = expected_completed if d["status"] == "Delivered" else expected_active
        bucket[partner_name] = bucket.get(partner_name, 0) + 1

    for p in partners:
        assert p["completedDeliveries"] == expected_completed.get(p["name"], 0)
        assert p["activeDeliveries"] == expected_active.get(p["name"], 0)
