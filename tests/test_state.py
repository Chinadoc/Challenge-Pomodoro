"""Tests for the Pomodoro Timer FSM."""
import pytest
from pomodoro_enhanced.core.state import TimerFSM, Phase, Durations, TransitionError


def test_initial_state():
    """Test that the FSM initializes with the correct default state."""
    fsm = TimerFSM(durations=Durations(work=25, short_break=5, long_break=15))
    assert fsm.state == Phase.WORK
    assert fsm.cycles == 0
    assert fsm.seconds_left == 25 * 60  # 25 minutes in seconds


def test_work_to_short_break():
    """Test transitioning from work to a short break."""
    fsm = TimerFSM(durations=Durations(work=25, short_break=5, long_break=15))
    
    # Work -> Short break
    fsm.next()
    assert fsm.state == Phase.SHORT_BREAK
    assert fsm.seconds_left == 5 * 60
    assert fsm.cycles == 1


def test_work_to_long_break():
    """Test transitioning from work to a long break after the interval."""
    fsm = TimerFSM(durations=Durations(work=25, short_break=5, long_break=15, long_break_interval=2))
    
    # First work -> short break
    fsm.next()  # work -> short break
    fsm.next()  # short break -> work
    
    # Second work -> long break (because interval=2)
    fsm.next()
    assert fsm.state == Phase.LONG_BREAK
    assert fsm.seconds_left == 15 * 60
    assert fsm.cycles == 2


def test_pause_resume():
    """Test pausing and resuming the timer."""
    fsm = TimerFSM(durations=Durations(work=25, short_break=5, long_break=15))
    
    # Pause during work
    fsm.pause()
    assert fsm.state == Phase.PAUSED
    assert fsm.is_paused
    
    # Resume work
    fsm.resume()
    assert fsm.state == Phase.WORK
    assert not fsm.is_paused


def test_invalid_transition():
    """Test that invalid transitions raise an error."""
    fsm = TimerFSM(durations=Durations(work=25, short_break=5, long_break=15))
    
    # Can't go directly from work to long break (must go through short break first)
    with pytest.raises(TransitionError):
        fsm._set_phase(Phase.LONG_BREAK)


def test_tick():
    """Test the tick method advances time and handles phase completion."""
    fsm = TimerFSM(durations=Durations(work=1, short_break=1, long_break=1))
    
    # First tick shouldn't complete the phase
    assert not fsm.tick(30)  # 30 seconds into 1-minute work period
    assert fsm.seconds_left == 30
    
    # Next tick completes the work phase
    assert fsm.tick(30)
    assert fsm.state == Phase.SHORT_BREAK
    assert fsm.seconds_left == 60  # 1-minute break


def test_state_change_callback():
    """Test that the state change callback is called."""
    callback_states = []
    
    def on_state_change(state):
        callback_states.append(state)
    
    fsm = TimerFSM(
        durations=Durations(work=1, short_break=1, long_break=1),
        on_state_change=on_state_change
    )
    
    fsm.next()  # work -> short break
    fsm.pause()  # short break -> paused
    fsm.resume()  # paused -> short break
    
    assert callback_states == [
        Phase.SHORT_BREAK,
        Phase.PAUSED,
        Phase.SHORT_BREAK,
    ]
