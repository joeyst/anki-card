
from dataclasses import dataclass, field
from datetime import datetime, timedelta 

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
  relearning_steps: list[int]   = field(default_factory=default_relearning_steps) # Used when relearning a card (lapsed). (In minutes.) 
  lapse_minimum_interval: int   = 1 # Used when lapsed. 

  # REVIEW CONFIG 
  starting_ease: float          = 2.50 # Start for ease multiplier. 
  easy_bonus: float             = 1.30 # Bonus for easy. 
  hard_interval_modifier: float = 1.20 # Multiplier for hard. Replaces other interval multipliers. 
  new_interval_modifier: float  = 0.00 # Multiplier for new cards. Replaces other interval multipliers. 

  # VARIABLES 
  ease: float                   = starting_ease # Ease multiplier.
  stage: str                    = "Learning" # Stage of card. "Learning" | "Review" | "Relearning". 
  step: int                     = 0 # Step in learning or relearning.
  interval: int                 = None # Interval in days.
  _next_review_date: datetime   = datetime.now() # Next review date. 
  history: list[dict]           = field(default_factory=list) # Stores list of settings/operations dicts. 

  @property
  def next_review_date(self) -> datetime: ...
  def pickle(self) -> bytes: ...
  def easy(self): ...
  def good(self): ...
  def hard(self): ...
  def again(self): ...
  def print(self): ...
  