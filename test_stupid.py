from errbot.backends.test import testbot


testbot


class TestMyPlugin(object):
    extra_plugin_dir = '.'

    def test_command(self, testbot):
        testbot.push_message('!mycommand')
        assert 'This is my awesome command' in testbot.pop_message()
