import config

cache = {}

log = config.get_logger('cache')


def remember(group, key, operation):
    if group not in cache:
        cache[group] = {}
    if key not in cache[group]:
        value = operation()
        cache[group][key] = value
    return cache[group][key]

