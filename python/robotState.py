from transitions import Machine

class RobotICState(object):
    states = ['unknown', 'pick', 'place']
    def __init__(self):
        self.machine = Machine(model=self, states=RobotICState.states, initial='unknown')
        self.machine.add_transition('pick', '*', 'pick')
        self.machine.add_transition('place', '*', 'place')
        self.machine.add_transition('unknown', '*', 'unknown')


class RobotAreaState(object):
    states = ['unknown', 'socket', 'tray']
    def __init__(self):
        self.machine = Machine(model=self, states=RobotAreaState.states, initial='tray')
        self.machine.add_transition('socket', '*', 'socket')
        self.machine.add_transition('tray', '*', 'tray')

if __name__ == '__main__':
    state = RobotAreaState()
    print(state.state)
    state.socket()
    print(state.state)
    if state.state == 'socket':
        print('is socket')
    state.unknown()