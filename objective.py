class Objective:
    """One goal, e.g. {"type": "enemy_defeated", "target": 3, "text": "Defeat the walkers"}.

    "type" is the name of the game event that counts towards it.
    """

    def __init__(self, data):
        self.kind = data["type"]
        self.id = data.get("id", self.kind)
        self.text = data.get("text", self.kind)
        self.target = data.get("target", 1)
        self.required = data.get("required", True)  # required ones unlock the exit
        self.progress = 0

    @property
    def complete(self):
        return self.progress >= self.target

    def add(self, amount=1):
        self.progress = min(self.target, self.progress + amount)


class ObjectiveTracker:
    def __init__(self, objectives_data):
        self.items = [Objective(d) for d in (objectives_data or [])]

    def on_event(self, kind, amount=1):
        for obj in self.items:
            if obj.kind == kind:
                obj.add(amount)

    @property
    def required_done(self):
        return all(o.complete for o in self.items if o.required)

    @property
    def completed_count(self):
        return sum(1 for o in self.items if o.complete)

    @property
    def total(self):
        return len(self.items)