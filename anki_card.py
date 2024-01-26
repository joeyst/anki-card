
from dataclasses import dataclass, field
from datetime import datetime, timedelta 
import pickle 
from pprint import pprint 
import math 

def default_learning_steps():
  return [1, 10]

def default_relearning_steps():
  return [10]

@dataclass
class AnkiCard:
  # LEARNING CONFIG 
  learning_steps: list[int]     = field(default_factory=default_learning_steps) # Used when learning a new card. (In minutes.)
  graduating_interval: int      = 1 # Used when graduating a card from learning mode. (In days.)
  easy_graduating_interval: int = 4 # Used when easy pressed in learning mode. (In days.) 
  
  # RELEARNING CONFIG 
  relearning_steps: list[int]   = field(default_factory=default_relearning_steps) # Used when relearning a card (lapsed). (In minutes.) 
  lapse_minimum_interval: int   = 1 # Used when lapsed. 

  # REVIEW CONFIG 
  starting_ease: float          = 2.50 # Start for ease multiplier. 
  easy_bonus: float             = 1.30 # Bonus for easy. 
  hard_interval_modifier: float = 1.20 # Multiplier for hard. Replaces other interval multipliers. 
  new_interval_modifier: float  = 0.00 # Multiplier for new cards. Replaces other interval multipliers. 
  max_interval: float           = 36500.00 # Max interval. 

  # VARIABLES 
  ease: float                   = starting_ease # Ease multiplier.
  stage: str                    = "Learning" # Stage of card. "Learning" | "Review" | "Relearning". 
  step: int                     = 0 # Step in learning or relearning.
  interval: int                 = None # Interval in days.
  _next_review_date: datetime   = field(default_factory=datetime.now) # Next review date. 

  # HISTORY 
  keep_history: bool            = True 
  history: list[dict]           = field(default_factory=list) # Stores list of settings/operations dicts. 

  @property
  def next_review_date(self) -> datetime: 
    return self._next_review_date 
  
  def pickle(self) -> bytes: 
    return pickle.dumps(self.dict())

  @staticmethod
  def unpickle(bytes) -> "AnkiCard":
    bytes = pickle.loads(bytes)
    
    return AnkiCard(
      learning_steps=bytes["learning_steps"],
      graduating_interval=bytes["graduating_interval"],
      easy_graduating_interval=bytes["easy_graduating_interval"],
      relearning_steps=bytes["relearning_steps"],
      lapse_minimum_interval=bytes["lapse_minimum_interval"],
      
      starting_ease=bytes["starting_ease"],
      easy_bonus=bytes["easy_bonus"],
      hard_interval_modifier=bytes["hard_interval_modifier"],
      new_interval_modifier=bytes["new_interval_modifier"],
      
      ease=bytes["ease"],
      stage=bytes["stage"],
      step=bytes["step"],
      interval=bytes["interval"],
      _next_review_date=bytes["next_review_date"],
      
      keep_history=bytes["keep_history"],
      history=bytes["history"],
    )

  def config(self, **kwargs):
    if self.keep_history:
      self.history.append({"action": "config"} | kwargs)
    
  def easy(self):
    match self.stage:
      case "Learning":
        self.learn_easy()
      case "Review":
        self.review_easy()
      case "Relearning":
        self.relearn_easy()
      case _:
        raise NotImplementedError()

  def good(self):
    match self.stage:
      case "Learning":
        self.learn_good()
      case "Review":
        self.review_good()
      case "Relearning":
        self.relearn_good()
      case _:
        raise NotImplementedError()
      
  def hard(self):
    match self.stage:
      case "Learning":
        self.learn_hard()
      case "Review":
        self.review_hard()
      case "Relearning":
        self.relearn_hard()
      case _:
        raise NotImplementedError()

  def again(self):
    match self.stage:
      case "Learning":
        self.learn_again()
      case "Review":
        self.review_again()
      case "Relearning":
        self.relearn_again()
      case _:
        raise NotImplementedError()
      
  def learn_easy(self):
    self._cond_add_guess_to_history("easy")
    self.set_to_review()
    self.set_to_easy_graduating_interval()
    self.set_next_review_date_to_interval()
    
  def review_easy(self):
    self._cond_add_guess_to_history("easy")
    interval = self.interval * (self.ease * self.easy_bonus) 
    next_int = math.ceil(interval)
    if next_int == self.interval:
      next_int += 1
    self.interval = next_int
    self.clip_interval()
    self.set_next_review_date_to_interval()
    self.ease += 0.15
    
  def relearn_easy(self):
    self._cond_add_guess_to_history("easy")
    self.stage = "Review"
    self.interval = self.easy_graduating_interval
    self.clip_interval() # Ambitious easy graduating interval :) 
    self.set_next_review_date_to_interval()

  def learn_good(self):
    self._cond_add_guess_to_history("good")
    if self.is_ready_to_graduate_learn():
      self.set_to_review()
      self.set_to_graduating_interval()
      self.set_next_review_date_to_interval()
      
    else:
      self.step += 1
      self.set_next_review_date_to_learning_step()
      
  def review_good(self):
    self._cond_add_guess_to_history("good")
    interval = self.interval * self.ease 
    next_int = math.ceil(interval)
    if next_int == self.interval:
      next_int += 1
    self.interval = next_int
    self.clip_interval()
    self.set_next_review_date_to_interval()
    
  def relearn_good(self):
    self._cond_add_guess_to_history("good")
    if self.is_ready_to_graduate_relearn():
      self.set_to_review()
      self.set_next_review_date_to_interval()
      
    else:
      self.step += 1
      self.set_next_review_date_to_relearning_step()
      
  def learn_hard(self):
    self._cond_add_guess_to_history("hard")
    if self.has_only_one_learning_step():
      self.set_review_date_to_one_card_hard_delay_learning()
    elif self.is_first_step():
      self.set_review_date_to_average_of_first_two_steps_learn()
    else:
      self.set_next_review_date_to_learning_step()
      
  def review_hard(self):
    self._cond_add_guess_to_history("hard")
    self.interval *= math.ceil(self.hard_interval_modifier)
    self.clip_interval()
    self.ease = max(self.ease - 0.15, 1.3)
    self.set_next_review_date_to_interval()
    
  def relearn_hard(self):
    self._cond_add_guess_to_history("hard")
    if self.has_only_one_relearning_step():
      self.set_review_date_to_one_card_hard_delay_relearning()
    elif self.is_first_step():
      self.set_review_date_to_average_of_first_two_steps_relearn()
    else:
      self.set_next_review_date_to_relearning_step()

  def learn_again(self):
    self._cond_add_guess_to_history("again")
    self.step = 0
    self.set_next_review_date_to_learning_step()
    
  def review_again(self):
    self._cond_add_guess_to_history("again")
    self.ease = max(self.ease - 0.20, 1.3)
    self.interval *= math.ceil(max(self.new_interval_modifier, self.lapse_minimum_interval))
    self.clip_interval()
    self.step = 0
    self.set_to_relearning()
    self.set_next_review_date_to_relearning_step()
    
  def relearn_again(self):
    self._cond_add_guess_to_history("again")
    self.step = 0
    self.set_next_review_date_to_relearning_step()
    
  def is_ready_for_review(self) -> bool:
    return self.time_til_review() <= timedelta(0)

  def time_til_review(self) -> timedelta:
    return self.next_review_date - datetime.now()
    
  def dict(self) -> dict:
    return {
      "learning_steps": self.learning_steps,
      "graduating_interval": self.graduating_interval,
      "easy_graduating_interval": self.easy_graduating_interval,
      "relearning_steps": self.relearning_steps,
      "lapse_minimum_interval": self.lapse_minimum_interval,
      
      "starting_ease": self.starting_ease,
      "easy_bonus": self.easy_bonus,
      "hard_interval_modifier": self.hard_interval_modifier,
      "new_interval_modifier": self.new_interval_modifier,
      "max_interval": self.max_interval,
      
      "ease": self.ease,
      "stage": self.stage,
      "step": self.step,
      "interval": self.interval,
      "next_review_date": self.next_review_date,
      
      "keep_history": self.keep_history,
      "history": self.history,
    }
    
  def print(self, incl_history=True): 
    dct = self.dict()
    dct["next_review_date"] = round(((dct["next_review_date"] - datetime.now()).total_seconds() / 60), 2)
    if not incl_history: del dct["history"]
    pprint(dct, indent=2)
  
  def set_to_review(self):
    self.stage = "Review"
  def set_to_learning(self):
    self.stage = "Learning"
  def set_to_relearning(self):
    self.stage = "Relearning"
  def set_next_review_date_to_interval(self):
    self._next_review_date = datetime.now() + timedelta(days=self.interval)
  def set_next_review_date_to_learning_step(self):
    self._next_review_date = datetime.now() + timedelta(minutes=self.learning_steps[self.step])
  def set_next_review_date_to_relearning_step(self):
    self._next_review_date = datetime.now() + timedelta(minutes=self.relearning_steps[self.step])
    
  def set_to_easy_graduating_interval(self):
    self.interval = self.easy_graduating_interval
    self.clip_interval()
  def set_to_graduating_interval(self):
    self.interval = self.graduating_interval
    self.clip_interval()
  
  def is_ready_to_graduate_learn(self) -> bool:
    return self.step == len(self.learning_steps) - 1
  def is_ready_to_graduate_relearn(self) -> bool:
    return self.step == len(self.relearning_steps) - 1
  def has_only_one_learning_step(self) -> bool:
    return len(self.learning_steps) == 1
  def has_only_one_relearning_step(self) -> bool:
    return len(self.relearning_steps) == 1
  def is_first_step(self) -> bool:
    return self.step == 0
  
  def set_review_date_to_one_card_hard_delay_learning(self):
    """ Sets delay for when there is only one card and recall is rated as hard. """
    # For more info: https://docs.ankiweb.net/studying.html 
    one_and_a_half_delay = self.learning_steps[0] * 1.5
    delay = min(1440 + self.learning_steps[0], one_and_a_half_delay) # At max a day more than regular delay. 
    self._next_review_date = datetime.now() + timedelta(minutes=delay)
  def set_review_date_to_average_of_first_two_steps_learn(self): 
    delay = (self.learning_steps[0] + self.learning_steps[1]) / 2
    self._next_review_date = datetime.now() + timedelta(minutes=delay)
  def set_review_date_to_average_of_first_two_steps_relearn(self): 
    delay = (self.relearning_steps[0] + self.relearning_steps[1]) / 2
    self._next_review_date = datetime.now() + timedelta(minutes=delay)
  def set_review_date_to_one_card_hard_delay_relearning(self):
    """ Sets delay for when there is only one card and recall is rated as hard. """
    # For more info: https://docs.ankiweb.net/studying.html 
    one_and_a_half_delay = self.relearning_steps[0] * 1.5
    delay = min(1440 + self.relearning_steps[0], one_and_a_half_delay) # At max a day more than regular delay. 
    self._next_review_date = datetime.now() + timedelta(minutes=delay)

  def clip_interval(self):
    self.interval = min(self.interval, self.max_interval)
  
  def _cond_add_guess_to_history(self, rating):
    if self.keep_history:
      self._add_guess_to_history(rating)
  
  def _add_guess_to_history(self, rating):
    dct = self.dict()
    self.history.append({
      "action": "guess",
      "rating": rating,
      "ease": dct["ease"],
      "stage": dct["stage"],
      "step": dct["interval"],
      "next_review_date": dct["next_review_date"],
      "time": datetime.now(),
    })
  
if __name__ == "__main__":
  ac = AnkiCard()
  methods = [
    "learn_easy", "learn_good", "learn_hard", "learn_again",
    "review_easy", "review_good", "review_hard", "review_again",
    "relearn_easy", "relearn_good", "relearn_hard", "relearn_again"
  ]
  for method in methods:
    print(f"Calling {method}")
    getattr(ac, method)()
    ac.print()
    print()
    ac_pickled = ac.pickle()
    print(AnkiCard.unpickle(ac_pickled))
