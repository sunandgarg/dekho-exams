class IncidentSlabCache:
    def __init__(self, slots_per_page=3):
        if slots_per_page < 1:
            raise ValueError("page must hold at least one slot")
        self.slots_per_page = slots_per_page
        self.pages = []
        self.generations = []
        self.free_slots = []
        self.live = set()

    def _add_page(self):
        page_id = len(self.pages)
        self.pages.append([None] * self.slots_per_page)
        self.generations.append([0] * self.slots_per_page)
        self.free_slots.extend((page_id, slot) for slot in reversed(range(self.slots_per_page)))

    def allocate(self, incident):
        if not self.free_slots:
            self._add_page()
        page, slot = self.free_slots.pop()
        self.pages[page][slot] = incident
        self.live.add((page, slot))
        return page, slot, self.generations[page][slot]

    def _validate(self, handle):
        page, slot, generation = handle
        if ((page, slot) not in self.live or
                self.generations[page][slot] != generation):
            raise KeyError("stale or released incident handle")
        return page, slot

    def get(self, handle):
        page, slot = self._validate(handle)
        return self.pages[page][slot]

    def release(self, handle):
        page, slot = self._validate(handle)
        self.live.remove((page, slot))
        self.pages[page][slot] = None
        self.generations[page][slot] += 1
        self.free_slots.append((page, slot))


cache = IncidentSlabCache(slots_per_page=3)
handles = [cache.allocate(f"incident-{number}") for number in (47, 19, 61, 83)]
cache.release(handles[1])
replacement = cache.allocate("incident-29")
try:
    cache.get(handles[1])
except KeyError:
    stale = True
print("pages=", len(cache.pages), " reused-slot=", replacement[:2] == handles[1][:2],
      " stale=", stale, sep="")
