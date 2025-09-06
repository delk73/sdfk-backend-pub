import math
import inspect
from functools import wraps
from typing import Callable


def curry(func: Callable) -> Callable:
    """Creates a curried version of the given function that supports keyword arguments."""

    @wraps(func)
    def curried(*args, **kwargs):
        sig = inspect.signature(func)
        try:
            sig.bind(*args, **kwargs)
            return func(*args, **kwargs)
        except TypeError:
            return lambda *next_args, **next_kwargs: curried(
                *(args + next_args), **{**kwargs, **next_kwargs}
            )

    return curried


@curry
def linear(t: float, slope: float = 1.0) -> float:
    """Linear interpolation from 0 to 1."""
    return t * slope


@curry
def sinusoidal(t: float, frequency: float = 1.0, phase: float = 0.0) -> float:
    """Sinusoidal wave with configurable frequency and phase."""
    return (math.sin(2 * math.pi * frequency * t + phase) + 1) / 2


@curry
def exponential(t: float, power: float = 2.0) -> float:
    """Exponential curve with configurable power."""
    return t**power


@curry
def parabolic(t: float, a: float = 1.0) -> float:
    """A simple U-shaped curve."""
    return a * (t - 0.5) ** 2


def linear_identity(t: float) -> float:
    """Basic linear function that returns its input."""
    return t


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp value between minimum and maximum."""
    return max(minimum, min(value, maximum))


def linear_clamped(t: float) -> float:
    """Clamped linear function: clamping t to [0, 1]."""
    return clamp(t, 0, 1)


def sine(t: float, frequency: float = 1.0, phase: float = 0.0) -> float:
    """Sinusoidal wave value between -1 and 1."""
    return math.sin(2 * math.pi * frequency * t + phase)


def cosine(t: float, frequency: float = 1.0, phase: float = 0.0) -> float:
    """Cosine wave value between -1 and 1."""
    return math.cos(2 * math.pi * frequency * t + phase)


def step(t: float, frequency: int = 4) -> float:
    """Step function that creates discrete steps between 0 and 1."""
    wrapped_t = ((t % 1) + 1) % 1
    step_size = 1 / (frequency - 1)
    return math.floor(wrapped_t * frequency) * step_size


def smoothstep(t: float, edge0: float = 0.0, edge1: float = 1.0) -> float:
    """Smoothstep function using cubic Hermite interpolation."""
    x = clamp((t - edge0) / (edge1 - edge0), 0, 1)
    return x * x * (3 - 2 * x)


def gaussian(
    t: float, width: float = 0.2, center: float = 0.5, amplitude: float = 1.0
) -> float:
    """Gaussian (bell curve) function."""
    x = (t - center) / width
    return amplitude * math.exp(-(x**2) / 2)


def wave_packet(
    t: float, frequency: float = 8.0, width: float = 0.2, center: float = 0.5
) -> float:
    """Wave packet function combining a carrier wave with a gaussian envelope."""
    carrier = math.sin(2 * math.pi * frequency * t)
    envelope = gaussian(t, width, center)
    return carrier * envelope


def bounce(t: float, amplitude: float = 1.0, decay: float = 0.5) -> float:
    """Bounce function simulating a dampened bouncing effect."""
    wrapped_t = t - math.floor(t)
    result: float = 0.0
    for i in range(3):
        freq = (i + 1) * math.pi
        amp = amplitude * (decay**i)
        result += amp * abs(math.sin(freq * wrapped_t))
    return result * (1 - wrapped_t)


def remap(
    t: float, old_min: float, old_max: float, new_min: float, new_max: float
) -> float:
    """Remaps a value from one range to another."""
    normalized_t = (t - old_min) / (old_max - old_min)
    value = new_min + normalized_t * (new_max - new_min)
    # Clamp the output to lie between new_min and new_max
    return clamp(value, min(new_min, new_max), max(new_min, new_max))


def quantize(t: float, steps: int) -> float:
    """Quantizes a value into discrete steps."""
    step_size = 1.0 / steps
    return math.floor(t / step_size) * step_size


def mirror(t: float) -> float:
    """Mirrors a value around the center (0.5)."""
    return abs(t - 0.5) * 2


def reverse(t: float) -> float:
    """Reverses a value (1 - t)."""
    return 1 - t


def curve_function_to_array(
    curve_fn: Callable[[float], float], length: int = 256
) -> list:
    """Convert a curve function into a list of samples."""
    samples = []
    for i in range(length):
        x = i / (length - 1)
        samples.append(curve_fn(x))
    return samples
