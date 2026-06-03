from enum import Enum, auto
from typing import Callable

# --- ENUMS ---
class Easings(Enum):
    Linear = auto()
    Quad = auto()
    Cubic = auto()

class Direction(Enum):
    In = auto()
    Out = auto()
    InOut = auto()
class Easings(Enum):
    Linear = 0
    Quad = 1
    Cubic = 2

class Direction(Enum):
    Out = 0,
    In = 1,
    InOut = 2,

# --- 2. EASING MATH ---
# These functions take a value 't' (between 0.0 and 1.0) and return the eased 't'
def _ease_linear(t): return t

def _ease_quad_in(t): return t * t
def _ease_quad_out(t): return t * (2 - t)
def _ease_quad_in_out(t): return 2 * t * t if t < 0.5 else -1 + (4 - 2 * t) * t

def _ease_cubic_in(t): return t * t * t
def _ease_cubic_out(t): return 1 - pow(1 - t, 3)
def _ease_cubic_in_out(t): return 4 * t * t * t if t < 0.5 else 1 - pow(-2 * t + 2, 3) / 2

# Map Enums to actual math functions
_EASING_MAP = {
    Easings.Linear: {
        Direction.In: _ease_linear,
        Direction.Out: _ease_linear,
        Direction.InOut: _ease_linear,
    },
    Easings.Quad: {
        Direction.In: _ease_quad_in,
        Direction.Out: _ease_quad_out,
        Direction.InOut: _ease_quad_in_out,
    },
    Easings.Cubic: {
        Direction.In: _ease_cubic_in,
        Direction.Out: _ease_cubic_out,
        Direction.InOut: _ease_cubic_in_out,
    }
}

# --- 3. TWEEN MANAGER ---
_active_tweens = []

class Tween:
    def __init__(self, on_update: Callable[[float], None] = None, on_complete: Callable[[], None] = None):
        """
        on_update: A function that takes the current interpolated value (e.g., to move a sprite).
        on_complete: A function that fires when the tween finishes.
        """
        self.time = 0.0
        self.duration = 1.0
        self.start_value = 0.0
        self.end_value = 0.0
        self.change = 0.0
        self.easing_func = _ease_linear
        self.is_playing = False
        
        self.on_update = on_update
        self.on_complete = on_complete
        
        _active_tweens.append(self)

    def Start(self, duration: float, startValue: float, endValue: float, easing: Easings, direction: Direction):
        self.duration = duration
        self.start_value = startValue
        self.end_value = endValue
        self.change = endValue - startValue
        self.time = 0.0
        
        # Grab the correct math function from the dictionary
        self.easing_func = _EASING_MAP.get(easing, _EASING_MAP[Easings.Linear])[direction]
        self.is_playing = True

    def Update(self, dt: float):
        if not self.is_playing:
            return
            
        self.time += dt
        
        # Check if tween is finished
        if self.time >= self.duration:
            self.time = self.duration
            self.is_playing = False
            if self.on_update:
                self.on_update(self.end_value)
            if self.on_complete:
                self.on_complete()
            return

        # Calculate progress (t goes from 0.0 to 1.0)
        t = self.time / self.duration
        eased_t = self.easing_func(t)
        current_value = self.start_value + (self.change * eased_t)
        
        if self.on_update:
            self.on_update(current_value)

