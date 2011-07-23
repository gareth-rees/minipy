cache = {0: 0, 1: 1, 2: 1, 3: 2}
def fibonacci(n):
    """Return the nth Fibonacci number."""
    if n not in cache:
        a = n // 2
        r = n % 2
        m = r * 2 - 1
        cache[n] = fibonacci(a + 1) ** 2 + m * fibonacci(a + r - 1) ** 2
    return cache[n]

