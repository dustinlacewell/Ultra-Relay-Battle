from urb import contexts
from urb.colors import colorize
from urb.util import dlog, metadata

class NumbersGameContext(contexts.Context):
    """
Guess the Number! A Minigame show casing session contexts.
The number is between 1 and 1000 and you get 8 guesses. 

                   Good luck!
"""
        
    def enter(_self, self):
        import random
        _self.answer = random.randint(1, 1000)
        _self.guesses = 8
          
            
    def com_exit(_self, self, args):
        """Exit back to the minigames menu."""
        self.switch('minigames')         
    
    @metadata(schema=(('int*','number'),))
    def com_guess(_self, self, args):
        """guess <number> Guess the number!"""
        
        if 'number' not in args:
            self.app.tell(self.nickname, "You have %d guesses left." % _self.guesses)
        else:
            number = args['number']
            if number > _self.answer:
                self.app.tell(self.nickname,
                "Lower.")
            elif number < _self.answer:
                self.app.tell(self.nickname,
                "Higher.")
            elif number == _self.answer:
                self.app.tell(self.nickname,
                "That it! %d was the right answer!" % number)
                self.switch('minigames')
                return
            _self.guesses -= 1
            if _self.guesses == 0:
                self.app.tell(self.nickname,
                    "Out of guesses! Guess you'll never know.")
                self.switch('minigames')

exported_class = NumbersGameContext
