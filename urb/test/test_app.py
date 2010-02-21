import unittest
import fudge

import sys

from urb.app import ApplicationClass

class TestApp(unittest.TestCase):

    def setUp(self): 
        fudge.clear_expectations()
        MOCK_GE = (
            fudge.Fake('GameEngine')
            .expects('__init__')
            .expects('get_signal_matrix').returns(dict(fakesig=123))
            .has_attr(fighters=dict(f1='fighter1', f2='fighter2'))
            .has_attr(players=dict(p1='player1', p2='player2'))
        )

        MOCK_DD = (
            fudge.Fake('DataDriver')
            .expects('__init__')
        )

        _mock_config = (MOCK_DD.provides('get_config').returns_fake()
                        .has_attr(irc_log_channel='#log', irc_main_channel="#main"))

        MOCK_LOAD_ALL = fudge.Fake('load_all', expect_call=True)

        self.fake_dd = fudge.patch_object('urb.db', 'DataDriver', MOCK_DD)
        self.fake_ge = fudge.patch_object('urb.engine', 'GameEngine', MOCK_GE)
        self.fake_la = fudge.patch_object('urb.imports', 'load_all', MOCK_LOAD_ALL)
        fudge.clear_calls()

    def tearDown(self): 
        self.fake_la.restore()
        self.fake_ge.restore()
        self.fake_dd.restore()

    def _not_implemented(self):
        # self.fail("not implemented")
        pass


    @fudge.with_fakes
    def testNew(self):
        app = ApplicationClass()
        # more like a test of our own mocks but it's a good sanity test
        self.assertEqual(app.game.get_signal_matrix()['fakesig'], 123)

    @fudge.with_fakes
    def testOnGameMsgDirect(self):
        app = ApplicationClass()
        
        # XXX dammit this just does not work for some reason
        # listener = fudge.Fake(expect_call=True)
        # app.signals['outgoing_msg'] += listener

        # Fine then, we'll make our own
        output = []
        listener = lambda *args: output.append(args)
        app.signals['outgoing_msg'] += listener

        expect = [('f1', 'test message'), ('f2', 'test message'), ('#log', 'test message')]
        app.on_game_msg('test message')
        self.assertEqual(output, expect)

    @fudge.with_fakes
    def testOnGameMsgEvent(self):
        # We haven't mocked AppClass itself so we can't really ensure
        # on_game_msg itself is called from the game_msg event.  We
        # can of course smoke-test the event dispatcher here and
        # ensure it propagates to the same outgoing_msg signal
        app = ApplicationClass()
        
        output = []
        listener = lambda *args: output.append(args)
        app.signals['outgoing_msg'] += listener

        expect = [('f1', 'test message'), ('f2', 'test message'), ('#log', 'test message')]
        app.signals['game_msg'].emit('test message')
        self.assertEqual(output, expect)

    @fudge.with_fakes
    def testonGlobalMsgDirect(self):
        app = ApplicationClass()

        output = []
        listener = lambda *args: output.append(args)
        app.signals['outgoing_msg'] += listener

        expect =  [('p2', 'test global'), ('p1', 'test global'), ('#log', 'test global'), ('#main', 'test global')]
        app.on_global_msg('test global')
        self.assertEqual(output, expect)

    @fudge.with_fakes
    def testonGlobalMsgEvent(self):
        app = ApplicationClass()

        output = []
        listener = lambda *args: output.append(args)
        app.signals['outgoing_msg'] += listener

        expect =  [('p2', 'test global'), ('p1', 'test global'), ('#log', 'test global'), ('#main', 'test global')]
        app.signals['global_msg'].emit('test global')
        self.assertEqual(output, expect)

    def testRegisterListeners(self):
        self._not_implemented()

    def testUnRegisterListeners(self):
        self._not_implemented()

    def testAddService(self):
        self._not_implemented()

    def testStartService(self):
        self._not_implemented()

    def testStopService(self):
        self._not_implemented()

    def testGetService(self):
        self._not_implemented()

    def testIsSvcRunning(self):
        self._not_implemented()

    def testTell(self):
        self._not_implemented()

    @fudge.with_fakes
    def testDoCommand(self):
        app = ApplicationClass()
        app.database.expects('commit')

        output = []
        listener = lambda *args: output.append(args)
        app.signals['command'] += listener

        expect = [('fakey', 'fakecommand', ['arg1', 'arg2'])]
        app.do_command('fakey', 'fakecommand', ['arg1', 'arg2'])
        self.assertEqual(output, expect)

if __name__ == '__main__':
    unittest.main()
