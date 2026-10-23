"""Records how the player did on each level.

This is the raw data the skill score and the adaptive difficulty will be built on.
Nothing in here changes how the game plays.
"""
import json
import os
import time

HISTORY_PATH = os.path.join("saves", "performance_history.json")
MAX_HISTORY = 30  # how many finished levels to remember


class LevelPerformance:
    """Everything measured during one attempt at one level."""

    def __init__(self, level_name, par_time=None):
        self.level_name = level_name
        self.par_time = par_time        # seconds a decent run should take (from the level JSON)
        self.time = 0.0
        self.deaths = 0
        self.death_causes = {}          # e.g. {"lava": 2, "abyss": 1}
        self.damage_taken = 0
        self.defeats = {}               # method -> count, e.g. {"stomp": 3}
        self.objectives_done = 0
        self.objectives_total = 0
        self.coins = 0
        self.coins_total = 0            # coins that existed (set when the level starts)
        self.lucky_blocks = 0
        self.buffs_used = {}            # e.g. {"speed": 2, "jump": 1}
        self.completed = False

    def tick(self, dt):
        self.time += dt

    def record_death(self, cause=None):
        self.deaths += 1
        cause = cause or "unknown"
        self.death_causes[cause] = self.death_causes.get(cause, 0) + 1

    def record_damage(self, amount):
        self.damage_taken += amount

    def record_defeat(self, method="stomp"):
        self.defeats[method] = self.defeats.get(method, 0) + 1

    def record_coin(self):
        self.coins += 1

    def record_lucky_block(self):
        self.lucky_blocks += 1

    def record_buff(self, name):
        self.buffs_used[name] = self.buffs_used.get(name, 0) + 1

    def finish(self, objectives_done, objectives_total):
        self.objectives_done = objectives_done
        self.objectives_total = objectives_total
        self.completed = True

    @property
    def total_defeats(self):
        return sum(self.defeats.values())

    @property
    def time_ratio(self):
        """1.0 means exactly par; under 1.0 is faster than par. None if the level has no par."""
        if not self.par_time:
            return None
        return self.time / self.par_time

    def to_dict(self):
        return {
            "level": self.level_name,
            "time": round(self.time, 2),
            "par_time": self.par_time,
            "time_ratio": None if self.time_ratio is None else round(self.time_ratio, 3),
            "deaths": self.deaths,
            "death_causes": dict(self.death_causes),
            "damage_taken": self.damage_taken,
            "defeats": dict(self.defeats),
            "total_defeats": self.total_defeats,
            "objectives_done": self.objectives_done,
            "objectives_total": self.objectives_total,
            "coins": self.coins,
            "coins_total": self.coins_total,
            "lucky_blocks": self.lucky_blocks,
            "buffs_used": dict(self.buffs_used),
            "completed": self.completed,
        }


class PerformanceHistory:
    """The last few finished levels, saved to disk so trends survive between sessions."""

    def __init__(self, path=HISTORY_PATH):
        self.path = path
        self.entries = []
        self.load()

    def load(self):
        try:
            with open(self.path, "r") as file:
                data = json.load(file)
            self.entries = data[-MAX_HISTORY:] if isinstance(data, list) else []
        except FileNotFoundError:
            self.entries = []
        except (OSError, ValueError) as error:
            print(f"Couldn't read {self.path}: {error}")
            self.entries = []

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w") as file:
                json.dump(self.entries, file, indent=2)
        except OSError as error:
            print(f"Couldn't save {self.path}: {error}")

    def add(self, performance):
        entry = performance.to_dict()
        entry["when"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.entries.append(entry)
        self.entries = self.entries[-MAX_HISTORY:]
        self.save()

    def recent(self, count=5):
        """The newest `count` entries, oldest first."""
        return self.entries[-count:]