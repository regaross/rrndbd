# How `deposits_by_lineage` works

This note explains the logic inside `Simulation.deposits_by_lineage` in [August12/rrpartiplot/rootwrap.py](August12/rrpartiplot/rootwrap.py).

## Goal

The function reorganizes deposit records from a per-event view into a per-lineage view. In a biased simulation, one primary particle can split into multiple cloned histories or paths through the detector. The raw `deposits` tree is stored event-by-event, but the important physics information is tied to each lineage path in `adjacencyList.history`.

The function tries to answer:

- which nodes belong to which lineage?
- which deposit entries belong to which history?
- how do we keep event-level and hit-level data aligned without breaking the array structure?

## First check

```python
self._boost_error()
```

This rejects the operation unless the simulation is flagged as boosted. That makes sense because the function assumes the file has `adjacencyList` information and importance-boosted histories.

---

## 1) Read the deposit branches

```python
dep_keys = self.deposits.keys()
deps = self.deposits.arrays(dep_keys)
```

This loads all branches of the `deposits` tree as an Awkward array. The result is a jagged structure with one row per deposit entry, or one group of entries per event/primary depending on the branch layout.

---

## 2) Pull the history paths

```python
node_paths = self.adjacencyList['history'].array()
```

`adjacencyList.history` is the key structure here. Each row corresponds to a primary particle, and each row contains a list of node IDs that represent a lineage path through the geometry and importance boundaries.

A typical pattern is:

```python
[0, 5, 9, 0, 3, 8, 0, ...]
```

The leading `0` marks the start of a new history. The elements after that are node IDs visited in that lineage.

---

## 3) Count how many histories each event has

```python
n_histories = np.sum(node_paths == 0, axis=1)
```

This counts how many times a history starts in each primary event. Since each history begins with a zero, this is a quick way to tell how many independent lineage paths exist for each event.

Then:

```python
event_idx = np.repeat(np.arange(len(deps)), ak.to_numpy(n_histories))
deps = deps[event_idx]
```

This repeats each event’s deposit data once for each lineage in that event. In other words, if one primary has 3 histories, the deposit rows for that primary are replicated 3 times so they can be matched to each lineage separately.

This is the step that expands the event-wise deposit structure into a lineage-wise one.

---

## 4) Flatten and recover the per-history node lists

```python
flat = ak.flatten(node_paths)
starts = ak.to_numpy(ak.local_index(flat)[flat == 0])
lengths = np.diff(np.append(starts, len(flat)))
node_histories = ak.unflatten(flat, lengths)
```

This is the trickiest part.

- `flat` turns the nested histories into one long 1D array.
- `flat == 0` identifies the start of each lineage.
- `local_index(flat)` assigns positions in the flattened array.
- `starts` is the index where each lineage begins.
- `lengths` is the length of each lineage segment.
- `ak.unflatten(flat, lengths)` rebuilds the flattened data into separate per-history arrays.

So after this step, `node_histories` is a jagged array where each row is a list of node IDs for one lineage.

Then:

```python
deps = ak.with_field(deps, node_histories, "node_history")
```

Each repeated deposit row now carries the node sequence for its lineage.

---

## 5) Match deposits to their lineage nodes

```python
mask = ak.any(deps['node'][:, :, None] == deps['node_history'][:, None, :], axis=-1)
```

This is a broadcasted membership test.

Interpretation:

- `deps['node']` is likely a list of node IDs for each deposit entry.
- `deps['node_history']` is the list of node IDs in a lineage.
- The comparison creates a boolean matrix:
  - one dimension for deposit node entries,
  - one dimension for lineage node entries.
- `ak.any(..., axis=-1)` asks: “Does this deposit’s node appear anywhere in this lineage?”

The result is a mask that says which deposits are part of the lineage being considered.

This is the heart of the function: it connects raw deposit hits to the history path they came from.

---

## 6) Keep only hit-level fields that match the node multiplicity

```python
node_counts = ak.to_numpy(ak.num(deps["node"], axis=1))
out = {}

for field in deps.fields:
    arr = deps[field]

    if field == "node_history":
        out[field] = arr
        continue

    is_hit_level = False
    try:
        counts = ak.to_numpy(ak.num(arr, axis=1))
        is_hit_level = np.array_equal(counts, node_counts)
    except Exception:
        is_hit_level = False

    out[field] = arr[mask] if is_hit_level else arr
```

This part is important because not every field in the deposits tree has the same shape.

Examples:

- a hit-level field like `node`, `energy`, or per-hit energy deposit has one value per hit and should be filtered by the lineage mask.
- an event-level field like event metadata, run information, or track metadata should not be cut down to the same shape.

The logic checks whether the field has the same nested multiplicity as `node`:

```python
np.array_equal(ak.num(arr, axis=1), node_counts)
```

If it matches, it is treated as hit-level and filtered with `arr[mask]`.

If not, it is left unchanged.

The function is intentionally careful here: it avoids accidentally dropping scalar fields that should stay attached to the event or lineage object.

---

## 7) Rebuilt Awkward record structure

```python
deps = ak.zip(out, depth_limit=1)
return deps
```

After filtering, the function packs everything back into a clean Awkward record with the same grouping structure. This makes the result easier to work with downstream, especially when you want to iterate lineage-by-lineage rather than event-by-event.

---

## Why this is useful

This conversion is essential when a boosted simulation creates multiple histories for the same primary event. Without it, deposit records remain in a single event-wise order that hides the causal structure of the lineage.

After this function, you can reason about:

- which deposits belong to which ancestry path,
- how the boosted simulation split one event into several histories,
- how to aggregate energy or detector response per lineage, rather than per primary entry.

---

## Intuition in one sentence

`deposits_by_lineage` turns a flat event-by-event deposit list into a lineage-aware structure by repeating deposit rows for each history, reconstructing each history from `adjacencyList.history`, and then keeping only the deposit entries whose nodes belong to that lineage.

---

## Minimal pseudocode

```python
if not self.boosted:
    raise RuntimeError

deps = self.deposits.arrays(...)
node_paths = self.adjacencyList['history'].array()

n_histories = count_starts_of_each_history(node_paths)
repeated_deps = repeat_each_event_once_per_history(deps, n_histories)

flat_histories = flatten(node_paths)
node_histories = rebuild_history_segments(flat_histories)

repeated_deps["node_history"] = node_histories
mask = deposits_node_is_in_lineage(repeated_deps["node"], repeated_deps["node_history"])

for each field in repeated_deps:
    if field is hit-like:
        apply mask
    else:
        keep as-is

return awkward_record_of_filtered_data
```

This is the basic logic the function implements.
