import math
import pytest
from hypothesis import given, strategies as st
from app import curves


def test_linear():
    # ...existing setup...
    assert curves.linear(0.5) == 0.5  # default slope=1.0
    assert curves.linear(0.5, slope=2.0) == 1.0


def test_linear_deferred():
    # Trigger deferred lambda by not providing required argument "t"
    partial = curves.linear()
    assert callable(partial)
    result = partial(0.5)
    assert result == 0.5


def test_sinusoidal():
    # ...existing setup...
    # With t=0.0, frequency=1.0, phase=0.0 => (sin(0)+1)/2 = 0.5
    assert pytest.approx(curves.sinusoidal(0.0)) == 0.5
    # Test a non-zero t
    t = 0.25
    expected = (math.sin(2 * math.pi * 1.0 * t) + 1) / 2
    assert pytest.approx(curves.sinusoidal(t)) == expected


def test_sinusoidal_deferred():
    # Trigger deferred lambda by not providing "t" even though others have defaults
    partial = curves.sinusoidal()
    assert callable(partial)
    result = partial(0.0)
    # With default frequency and phase, expected value is 0.5
    assert pytest.approx(result) == 0.5


def test_exponential():
    # ...existing setup...
    assert curves.exponential(2.0, power=3.0) == 8.0  # 2^3=8
    assert curves.exponential(3.0) == 9.0  # default power=2.0


def test_parabolic():
    # ...existing setup...
    # When t=0.5, output should be 0 regardless of constant a
    assert curves.parabolic(0.5) == 0.0
    # Example: for t=0, (0-0.5)^2 = 0.25
    assert curves.parabolic(0.0) == 0.25


# --- Property-based tests using Hypothesis ---


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    slope=st.floats(min_value=0.1, max_value=10.0),
)
def test_linear_hypothesis(t, slope):
    result = curves.linear(t, slope=slope)
    assert pytest.approx(result) == t * slope


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    frequency=st.floats(min_value=0.1, max_value=10.0),
    phase=st.floats(min_value=-math.pi, max_value=math.pi),
)
def test_sinusoidal_hypothesis(t, frequency, phase):
    result = curves.sinusoidal(t, frequency=frequency, phase=phase)
    assert 0.0 <= result <= 1.0


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    power=st.floats(min_value=1.0, max_value=5.0),
)
def test_exponential_hypothesis(t, power):
    result = curves.exponential(t, power=power)
    assert pytest.approx(result) == t**power


@given(
    t=st.floats(min_value=0.0, max_value=1.0), a=st.floats(min_value=0.1, max_value=5.0)
)
def test_parabolic_hypothesis(t, a):
    result = curves.parabolic(t, a=a)
    assert pytest.approx(result) == a * (t - 0.5) ** 2


@given(x=st.floats(min_value=-1.0, max_value=2.0))
def test_linear_identity_hypothesis(x):
    result = curves.linear_identity(x)
    assert result == x


@given(
    value=st.floats(min_value=-5.0, max_value=15.0),
    minimum=st.floats(min_value=-10.0, max_value=0.0),
    maximum=st.floats(min_value=10.0, max_value=20.0),
)
def test_clamp_hypothesis(value, minimum, maximum):
    result = curves.clamp(value, minimum, maximum)
    assert minimum <= result <= maximum


@given(t=st.floats(min_value=-1.0, max_value=2.0))
def test_linear_clamped_hypothesis(t):
    result = curves.linear_clamped(t)
    assert 0.0 <= result <= 1.0


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    frequency=st.floats(min_value=0.1, max_value=10.0),
    phase=st.floats(min_value=-math.pi, max_value=math.pi),
)
def test_sine_hypothesis(t, frequency, phase):
    result = curves.sine(t, frequency=frequency, phase=phase)
    assert -1.0 <= result <= 1.0


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    frequency=st.floats(min_value=0.1, max_value=10.0),
    phase=st.floats(min_value=-math.pi, max_value=math.pi),
)
def test_cosine_hypothesis(t, frequency, phase):
    result = curves.cosine(t, frequency=frequency, phase=phase)
    assert -1.0 <= result <= 1.0


@given(
    t=st.floats(min_value=-1.0, max_value=2.0),
    frequency=st.integers(min_value=2, max_value=10),
)
def test_step_hypothesis(t, frequency):
    result = curves.step(t, frequency)
    assert 0.0 <= result <= 1.0


@given(
    t=st.floats(min_value=-1.0, max_value=2.0),
    edge0=st.floats(min_value=-1.0, max_value=0.0),
    edge1=st.floats(min_value=1.0, max_value=2.0),
)
def test_smoothstep_hypothesis(t, edge0, edge1):
    if edge0 >= edge1:
        pass  # avoid zero division
    else:
        result = curves.smoothstep(t, edge0, edge1)
        assert 0.0 <= result <= 1.0


@given(
    t=st.floats(min_value=-1.0, max_value=2.0),
    width=st.floats(min_value=0.01, max_value=1.0),
    center=st.floats(min_value=0.0, max_value=1.0),
    amplitude=st.floats(min_value=0.1, max_value=2.0),
)
def test_gaussian_hypothesis(t, width, center, amplitude):
    result = curves.gaussian(t, width, center, amplitude)
    # Gaussian can be any value, but let's check it's not infinite
    assert not math.isinf(result)


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    frequency=st.floats(min_value=1.0, max_value=10.0),
    width=st.floats(min_value=0.01, max_value=0.5),
    center=st.floats(min_value=0.0, max_value=1.0),
)
def test_wave_packet_hypothesis(t, frequency, width, center):
    result = curves.wave_packet(t, frequency, width, center)
    assert isinstance(result, float)


@given(
    t=st.floats(min_value=0.0, max_value=2.0),
    amplitude=st.floats(min_value=0.1, max_value=2.0),
    decay=st.floats(min_value=0.1, max_value=0.9),
)
def test_bounce_hypothesis(t, amplitude, decay):
    result = curves.bounce(t, amplitude, decay)
    assert result >= 0.0


# Remove the old tests


def test_linear_identity():
    for x in [0.0, 0.25, 0.5, 1.0]:
        assert curves.linear_identity(x) == x


def test_clamp():
    assert curves.clamp(5, 0, 10) == 5
    assert curves.clamp(-1, 0, 10) == 0
    assert curves.clamp(11, 0, 10) == 10


def test_linear_clamped():
    assert curves.linear_clamped(0.5) == 0.5
    assert curves.linear_clamped(-0.5) == 0
    assert curves.linear_clamped(1.5) == 1


def test_sine_and_cosine():
    # sine: with t=0, sine returns 0
    assert pytest.approx(curves.sine(0, frequency=1.0, phase=0.0)) == 0.0
    # cosine: with t=0, cosine returns 1.0
    assert pytest.approx(curves.cosine(0, frequency=1.0, phase=0.0)) == 1.0


def test_step():
    t = 0.5
    frequency = 4
    expected = math.floor((((t % 1) + 1) % 1) * frequency) * (1 / (frequency - 1))
    assert pytest.approx(curves.step(t, frequency)) == expected


def test_smoothstep():
    # For t=0.5 between 0 and 1, smoothstep should yield ~0.5
    assert pytest.approx(curves.smoothstep(0.5, 0.0, 1.0)) == 0.5


def test_gaussian():
    center = 0.5
    amplitude = 2.0
    result = curves.gaussian(center, width=0.2, center=center, amplitude=amplitude)
    assert pytest.approx(result) == amplitude
    # Test symmetry about the center
    left = curves.gaussian(0.4, width=0.2, center=center, amplitude=amplitude)
    right = curves.gaussian(0.6, width=0.2, center=center, amplitude=amplitude)
    assert pytest.approx(left) == right


def test_wave_packet():
    result = curves.wave_packet(0.25, frequency=8.0, width=0.2, center=0.5)
    assert isinstance(result, float)


def test_bounce():
    result = curves.bounce(0.3, amplitude=1.0, decay=0.5)
    assert isinstance(result, float)
    assert result >= 0


def test_curve_function_to_array():
    def identity(x):
        return x

    samples = curves.curve_function_to_array(identity, length=100)
    assert isinstance(samples, list)
    assert len(samples) == 100
    assert pytest.approx(samples[0]) == 0.0
    assert pytest.approx(samples[-1]) == 1.0


@given(t=st.floats(min_value=-1.0, max_value=2.0))
def test_smoothstep_range(t):
    result = curves.smoothstep(t)
    assert 0.0 <= result <= 1.0


@given(
    t=st.floats(min_value=-1.0, max_value=2.0),
    old_min=st.floats(min_value=-1.0, max_value=0.0),
    old_max=st.floats(min_value=1.0, max_value=2.0),
    new_min=st.floats(min_value=-1.0, max_value=0.0),
    new_max=st.floats(min_value=1.0, max_value=2.0),
)
def test_remap_hypothesis(t, old_min, old_max, new_min, new_max):
    if old_min >= old_max:
        with pytest.raises(ZeroDivisionError):
            curves.remap(t, old_min, old_max, new_min, new_max)
    else:
        result = curves.remap(t, old_min, old_max, new_min, new_max)
        assert -4 / 3 <= result <= 11


@given(
    t=st.floats(min_value=0.0, max_value=1.0),
    steps=st.integers(min_value=1, max_value=10),
)
def test_quantize_hypothesis(t, steps):
    result = curves.quantize(t, steps)
    assert 0.0 <= result <= 1.0


@given(t=st.floats(min_value=0.0, max_value=1.0))
def test_mirror_hypothesis(t):
    t = curves.clamp(t, 0.0, 1.0)
    result = curves.mirror(t)
    assert 0.0 <= result <= 1.0


@given(t=st.floats(min_value=0.0, max_value=1.0))
def test_reverse_hypothesis(t):
    result = curves.reverse(t)
    assert 0.0 <= result <= 1.0
