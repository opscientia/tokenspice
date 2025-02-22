import logging
from enforce_typing import enforce_types
import random
from typing import List

from engine.AgentBase import AgentBase
log = logging.getLogger('agents')

@enforce_types
class BaselineResearcherAgent(AgentBase):
    '''
    ResearcherAgent publishes proposals, creates knowledge assets and publishes them to a knowledge curator.
    Also, it keeps track of the following metrics:
    - number of proposals submitted
    - number of proposals funded
    - total funds received for research
    '''   
    def __init__(self, name: str, evaluator: str, USD: float, OCEAN: float,
                 receiving_agents : dict, proposal_setup : dict = None):
        super().__init__(name, USD, OCEAN)
        self._spent_at_tick = 0.0 #USD and OCEAN (in USD) spent
        self._receiving_agents = receiving_agents
        self._evaluator = evaluator
        self.proposal_setup = proposal_setup

        self.proposal: dict = {}
        self.new_proposal = False
        self.knowledge_access: float = 1.0
        self.ticks_since_proposal: int = 0
        self.proposal_accepted = False

        # metrics to track
        self.my_OCEAN: float = 0.0
        self.no_proposals_submitted: int = 0
        self.no_proposals_funded: int = 0
        self.total_research_funds_received: float = 0.0
        self.total_assets_in_mrkt: int = 0

        self.ratio_funds_to_publish: float = 0.0

        self.last_tick_spent = 0 # used by KnowledgeMarket to determine who just sent funds
    
    def createProposal(self, state) -> dict:
        self.new_proposal = True
        if self.proposal_setup is not None:
            self.proposal = self.proposal_setup
            self.proposal['knowledge_access'] = self.knowledge_access
            return self.proposal
        else:
            return {'grant_requested': random.randint(10000, 50000), # Note: might be worth considering some distribution based on other params
                    'assets_generated': random.randint(1, 10), # Note: might be worth considering some distribution based on other params 
                    'no_researchers': 10,
                    'knowledge_access': self.knowledge_access}

    def spentAtTick(self) -> float:
        return self._spent_at_tick

    def _USDToDisbursePerTick(self, state) -> None:
        '''
        1 tick = 1 hour
        '''
        USD = self.USD()
        # in this naive model, it makes little difference whether the money from grants is spent in one tick or across many
        if self.proposal != {} and self.USD() != 0.0:
            for name, computePercent in self._receiving_agents.items():
                self._transferUSD(state.getAgent(name), computePercent * USD) # NOTE: computePercent() should be used when it is a function in SimState.py
    
    def _BuyAndPublishAssets(self, state) -> None:
        '''
        This is only for interaction with KnowledgeMarket. Whenever this is called,
        it is presumed that at least a part of the funds are for buying assets in the marketplace.
        1 tick = 1 hour
        '''
        OCEAN = self.OCEAN()
        if OCEAN != 0 and self.proposal != {}:
            OCEAN_DISBURSE: float = self.proposal['grant_requested']
            for name, computePercent in self._receiving_agents.items():
                self._transferOCEAN(state.getAgent(name), computePercent * OCEAN_DISBURSE)
            self.knowledge_access += 1 # self.proposal['assets_generated'] # subject to change, but we can say that the knowledge assets published ~ knowledge gained
    
    def takeStep(self, state):

        if self.proposal != {}:
            self.ticks_since_proposal += 1

        # Proposal functionality
        if self.proposal == {}:
            self.proposal = self.createProposal(state)
            self.no_proposals_submitted += 1
            self.ticks_since_proposal = 0

        # checking to see whether it is time to submit a new proposal
        if (self.ticks_since_proposal % state.ss.TICKS_BETWEEN_PROPOSALS) == 0:
            self.proposal = self.createProposal(state)
            self.no_proposals_submitted += 1
            self.ticks_since_proposal = 0

        # Checking if proposal accepted (should only be checked at the tick right after the tick when createProposal() was called)
        if (self.ticks_since_proposal == 1) and (state.getAgent(self._evaluator).proposal_evaluation != {}):
            self.new_proposal = False
            # if I am the winner, send the funds received to KnowledgeMarket
            if state.getAgent(self._evaluator).proposal_evaluation['winner'] == self.name:
                self.proposal_accepted = True
                self.no_proposals_funded += 1
                self.total_assets_in_mrkt += self.proposal['assets_generated']
                self.total_research_funds_received += self.proposal['grant_requested']
                if self.OCEAN() >= self.proposal['grant_requested']:
                    self.ratio_funds_to_publish = state.ss.RATIO_FUNDS_TO_PUBLISH # KnowledgeMarketAgent will check this parameter
                    self.last_tick_spent = state.tick
                    self._BuyAndPublishAssets(state)
            else:
                assert(state.getAgent(self._evaluator).proposal_evaluation['winner'] != self.name)
                self.proposal_accepted = False
            self.my_OCEAN = self.OCEAN()
        elif (self.ticks_since_proposal == 1) and not state.getAgent(self._evaluator).proposal_evaluation:
            # In case the funding is misaligned with the researchers
            self.ticks_since_proposal = 0
            self.new_proposal = True

        self._spent_at_tick = self.OCEAN()

        if self.USD() > 0:
            self._USDToDisbursePerTick(state)