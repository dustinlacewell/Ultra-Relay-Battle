import unittest
from urb.event import Signal

def _consume(*args, **kw):
    pass


class TestSignal(unittest.TestCase):
    def setUp(self): 
        self.signal = Signal()
        self.recorded = []

    def tearDown(self): 
        pass

    def testRegister(self):
        self.signal.register(_consume)
        self.signal += _consume
        self.signal.register(_consume, 123)

    def testUnregister(self):
        self.signal += _consume
        self.signal.unregister(_consume)
        # multiple unregs do nothing
        self.signal.unregister(_consume)
        self.signal -= _consume 

        # unregistering nonexistent things also is no-op
        self.signal -= None
        self.signal -= 1j
        


    def testEmit(self):
        # Our first actually interesting test
        recorders = [Recorder(name, self) for name in "A B C D".split()]
        for rec in recorders:
            self.signal.register(rec)

        # ensure dispatch was ordered
        # self.signal.emit('hello', a=123, b=456)
        self.signal('hello', a=123, b=456)

        self.assertEquals(recorders, [r[0] for r in self.recorded])

        # TODO test ordering of registering using the second arg
            


# A poor-man's mock.  We'll be using real mocks when we test users of
# Signal instead of Signal itself.
import weakref
class Recorder(object):
    def __init__(self, name, testcase):
        self.name = name
        self.testcase = weakref.ref(testcase)

    def __call__(self, *args, **kw):
        self.testcase().recorded.append((self, args, kw))

if __name__ == '__main__':
    unittest.main()
