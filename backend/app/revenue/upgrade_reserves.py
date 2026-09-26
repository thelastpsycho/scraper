"""Rebuild upgrade commitments from one inventory snapshot, never from history.

PMS room assignment restores the booked category and consumes the destination.
Only negative balances in the current snapshot need virtual accommodation.
"""
import json
import math
import os
from collections import deque
from datetime import date

from ..infrastructure.paths import get_data_path


DEFAULT_ROUTES = {
    'Deluxe Room': ['Premiere Room'],
    'Deluxe Suite Room': ['Premiere Suite Room'],
}


def room_count(value, name, signed=False):
    if isinstance(value, bool):
        raise ValueError(f'{name} must be a whole room count')
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f'{name} must be a whole room count') from None
    if not math.isfinite(number) or not number.is_integer() or (number < 0 and not signed):
        raise ValueError(f'{name} must be a finite {"signed " if signed else "nonnegative "}whole room count')
    return int(number)


def load_policy(room_types, policy=None):
    """Runtime JSON is shared by default, custom and pipeline yield calculations.

    Unspecified routes retain the two relationships already used in the engine.
    No new higher-category route is assumed without an operator configuration.
    """
    if policy is None:
        path = os.environ.get('ALLOCATION_POLICY_PATH', get_data_path('allocation_policy.json'))
        if os.path.exists(path):
            with open(path, encoding='utf-8') as stream:
                policy = json.load(stream)
        else:
            policy = {}
    if not isinstance(policy, dict) or set(policy) - {'routes', 'buffers', 'holds'}:
        raise ValueError('Allocation policy accepts routes, buffers and holds only')
    rooms = set(room_types)
    routes = {room: list(DEFAULT_ROUTES.get(room, [])) for room in room_types}
    supplied_routes = policy.get('routes', {})
    if not isinstance(supplied_routes, dict):
        raise ValueError('routes must be an object')
    for source, destinations in supplied_routes.items():
        if source not in rooms or not isinstance(destinations, list):
            raise ValueError(f'Invalid upgrade route: {source}')
        if any(not isinstance(dest, str) or dest not in rooms for dest in destinations):
            raise ValueError(f'Unknown destination for {source}')
        if len(destinations) != len(set(destinations)):
            raise ValueError(f'Duplicate upgrade destination for {source}')
        routes[source] = list(destinations)

    def visit(room, path):
        if room in path:
            raise ValueError('Upgrade routes must not contain cycles or downgrades back to a source')
        for dest in routes[room]:
            visit(dest, path | {room})
    for room in room_types:
        visit(room, set())

    buffers = policy.get('buffers', {})
    if not isinstance(buffers, dict) or set(buffers) - rooms:
        raise ValueError('buffers must contain known room types only')
    buffers = {room: room_count(value, f'Buffer for {room}') for room, value in buffers.items()}
    holds = policy.get('holds', [])
    if not isinstance(holds, list):
        raise ValueError('holds must be a list')
    validated_holds = []
    for hold in holds:
        if not isinstance(hold, dict) or set(hold) - {'room_type', 'start_date', 'end_date', 'rooms', 'max_online'}:
            raise ValueError('Invalid manual hold')
        if hold.get('room_type') not in rooms:
            raise ValueError('Manual hold requires a known room_type')
        try:
            start = date.fromisoformat(hold['start_date'])
            end = date.fromisoformat(hold['end_date'])
        except (KeyError, TypeError, ValueError):
            raise ValueError('Manual hold requires ISO start_date and end_date') from None
        if start > end:
            raise ValueError('Manual hold end_date precedes start_date')
        item = dict(hold, rooms=room_count(hold.get('rooms', 0), 'Held rooms'))
        if 'max_online' in item:
            item['max_online'] = room_count(item['max_online'], 'Manual online cap')
        validated_holds.append(item)
    return {'routes': routes, 'buffers': buffers, 'holds': validated_holds}


def destinations_for(source, routes):
    """Ordered reachable upgrades; a Deluxe guest can move via Premiere upward."""
    result = []
    def walk(room):
        for dest in routes.get(room, []):
            if dest not in result:
                result.append(dest)
                walk(dest)
    walk(source)
    return result


def reserve_shortages(shortages, capacity, routes):
    """Integral max flow with ordered edges and rerouting for shared destinations.

    Unlike independent/greedy deductions, this can reassign a flexible guest's
    virtual reserve to accommodate another category with only one destination.
    Counts are augmented in batches, including arbitrarily large negative input.
    """
    graph = {}
    def edge(a, b, count):
        graph.setdefault(a, {})[b] = count
        graph.setdefault(b, {})[a] = 0
    total = sum(shortages.values())
    for room, count in shortages.items():
        edge('source', ('demand', room), count)
        for dest in destinations_for(room, routes):
            edge(('demand', room), ('supply', dest), total)
    for room, count in capacity.items():
        edge(('supply', room), 'sink', count)

    covered = 0
    while True:
        parents = {'source': None}
        queue = deque(['source'])
        while queue and 'sink' not in parents:
            node = queue.popleft()
            for neighbor, residual in graph.get(node, {}).items():
                if residual > 0 and neighbor not in parents:
                    parents[neighbor] = node
                    queue.append(neighbor)
        if 'sink' not in parents:
            break
        amount, node = total, 'sink'
        while parents[node] is not None:
            previous = parents[node]
            amount = min(amount, graph[previous][node])
            node = previous
        node = 'sink'
        while parents[node] is not None:
            previous = parents[node]
            graph[previous][node] -= amount
            graph[node][previous] += amount
            node = previous
        covered += amount
    reserved = {room: count - graph[('supply', room)]['sink'] for room, count in capacity.items()}
    return reserved, total - covered


def prepare_capacity(remaining, policy, day):
    remaining = {room: room_count(value, room, signed=True) for room, value in remaining.items()}
    protected = {room: policy['buffers'].get(room, 0) for room in remaining}
    online_caps = {}
    for hold in policy['holds']:
        if hold['start_date'] <= day <= hold['end_date']:
            room = hold['room_type']
            protected[room] += hold['rooms']
            if 'max_online' in hold:
                online_caps[room] = min(online_caps.get(room, hold['max_online']), hold['max_online'])
    capacity = {room: max(0, value - protected[room]) for room, value in remaining.items()}
    shortages = {room: -value for room, value in remaining.items() if value < 0}
    reserved, unresolved = reserve_shortages(shortages, capacity, policy['routes'])
    safe = {room: capacity[room] - reserved[room] for room in remaining}
    return safe, reserved, protected, online_caps, unresolved


def reserve_offer(source, amount, safe, routes, override_reserves):
    """Consume destination capacity before allocating it for direct online sale."""
    allocated = 0
    for dest in destinations_for(source, routes):
        take = min(amount - allocated, safe[dest])
        safe[dest] -= take
        override_reserves[dest] += take
        allocated += take
        if allocated == amount:
            break
    return allocated
