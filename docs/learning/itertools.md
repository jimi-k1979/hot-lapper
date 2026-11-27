# `itertools`

The standard library's `itertools` module builds lazy iterators out of other iterators. Nothing is computed until something loops over the result, and nothing is copied into a list on the way.

## Wrapping round the loop: `cycle`, `islice` and `count`

```python
def visible_segments(circuit, distance):
    first = int(distance // SEGMENT_LENGTH)
    behind = distance - first * SEGMENT_LENGTH
    start = first % len(circuit.segments)
    ahead = count(-behind, SEGMENT_LENGTH)
    segments = islice(cycle(circuit.segments), start, start + DRAW_DISTANCE)
    yield from zip(ahead, segments, strict=False)
```

- `cycle(circuit.segments)` repeats the segments for ever: the last one is followed by the first again, which is exactly what a closed circuit does.
- `islice(iterator, start, stop)` is slicing for iterators. It skips to the segment under the car and stops after `DRAW_DISTANCE` of them. Because the cycle never ends, the slice still gives a full draw distance on a circuit shorter than it.
- `count(start, step)` counts for ever: here the distance to each segment's near edge, one segment length apart.
- `zip` stops at its shortest input, the slice. `strict=False` says so on purpose, since `count` never runs out.

## Runs of the same value: `groupby`

```python
for height, run in groupby(enumerate(heights), key=itemgetter(1)):
    columns = [x for x, _ in run]
```

`groupby` splits an iterator into runs of neighbours with the same key. The skyline is one height per screen column, so each run of equal heights becomes one box instead of a box per column. Unlike SQL's `GROUP BY`, it only groups *neighbouring* items.

`itemgetter(1)` from the `operator` module is a ready-made `lambda pair: pair[1]`: here it picks the height out of each `(column, height)` pair as the key.

## A neighbour from `collections`: `defaultdict`

`defaultdict(list)` is a dictionary that makes an empty list the first time a missing key is read, so `pieces[start].append(paint)` needs no "is the key there yet?" check. The road uses it to group painted markings by the segment they fall in.

## Successive pairs: `pairwise`

`pairwise([a, b, c])` gives `(a, b), (b, c)`. A test uses it to check each road strip against the one in front of it.

## Why here

The road is drawn from the segments just ahead of the car, round and round the circuit. `cycle` and `islice` say that directly, with no index arithmetic and no list rebuilt each frame.

## In the code

- [`domain/road.py`](../../src/hotlapper/domain/road.py): `visible_segments`, and `_paintwork_by_segment` for `defaultdict`
- [`domain/race_view.py`](../../src/hotlapper/domain/race_view.py): `_skyline_boxes`
- [`tests/test_race_view.py`](../../tests/test_race_view.py): `test_road_strips_run_near_to_far_each_wholly_above_the_last`
