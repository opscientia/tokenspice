from enforce_typing import enforce_types
from typing import Set
import random

from assets.agents import MinterAgents
from assets.agents.opsci_pp_agents.VVersatileResearcherAgent import VVersatileResearcherAgent
from assets.agents.opsci_pp_agents.VVersatileDAOTreasuryAgent import VVersatileDAOTreasuryAgent
from assets.agents.opsci_pp_agents.PrivateMarketAgent import PrivateKnowledgeMarketAgent
from assets.agents.opsci_pp_agents.PublicMarketAgent import PublicKnowledgeMarketAgent
from assets.agents.opsci_pp_agents.ResearcherGenerator import ResearcherGeneratorAgent
from assets.agents.opsci_pp_agents.CommunityAgent import CommunityAgent
from engine import AgentBase, SimStateBase
from .KPIs import KPIs
from util import valuation
from util.constants import S_PER_YEAR, S_PER_MONTH, S_PER_DAY

@enforce_types
class SimState(SimStateBase.SimStateBase):
    '''
    SimState for the Web3 Open Science Profit Sharing Model
    '''
    def __init__(self, ss=None):
        #initialize self.tick, ss, agents, kpis
        super().__init__(ss)

        #now, fill in actual values for ss, agents, kpis
        if self.ss is None:
            from .SimStrategy import SimStrategy
            self.ss = SimStrategy()
        ss = self.ss #for convenience as we go forward
                                
        #as ecosystem improves, these parameters may change / improve
        self._marketplace_percent_toll_to_ocean = 0.002 #magic number
        self._percent_burn: float = 0.0005 #to burning, vs to OpsciMarketplace #magic number
        self._percent_dao: float = 0.05 #to dao vs to sellers

        self._speculation_valuation = 150e6 #in USD #magic number
        self._percent_increase_speculation_valuation_per_s = 0.10 / S_PER_YEAR # ""


        #Instantiate and connnect agent instances. "Wire up the circuit"
        # new_agents: Set[AgentBase.AgentBase] = set()
        researcher_agents = []
        self.researchers: dict = {}
        new_agents = []
        public_researcher_agents = []
        private_researcher_agents = []
        self.public_researchers: dict = {}
        self.private_researchers: dict = {}
        self.projects: dict = {}

        #################### Wiring of agents that send OCEAN ####################
        new_agents.append(VVersatileDAOTreasuryAgent(
            name = "dao_treasury", USD=0.0, OCEAN=1000000.0))

        # Public researcher agents
        for i in range(ss.NO_PUBLIC_RESEARCHERS):
            new_agents.append(VVersatileResearcherAgent(
                name = "researcher%x" % i, evaluator = "dao_treasury",
                USD=0.0, OCEAN=10000.0, research_type='public',
                receiving_agents = {"market": 1.0}))
            researcher_agents.append(VVersatileResearcherAgent(
                name = "researcher%x" % i, evaluator = "dao_treasury",
                USD=0.0, OCEAN=10000.0, research_type='public',
                receiving_agents = {"market": 1.0}))
            public_researcher_agents.append(VVersatileResearcherAgent(
                name = "researcher%x" % i, evaluator = "dao_treasury",
                USD=0.0, OCEAN=10000.0, research_type='public',
                receiving_agents = {"market": 1.0}))

        # don't use private researchers for now to reduce noise

        # for i in range(ss.NO_PUBLIC_RESEARCHERS, ss.NO_PUBLIC_RESEARCHERS + ss.NO_PRIVATE_RESEARCHERS):
        #     new_agents.append(VVersatileResearcherAgent(
        #             name = "researcher%x" % i, evaluator = "dao_treasury",
        #             USD=0.0, OCEAN=200000.0, research_type='private',
        #             receiving_agents = {"market": 1.0}))
        #     researcher_agents.append(VVersatileResearcherAgent(
        #             name = "researcher%x" % i, evaluator = "dao_treasury",
        #             USD=0.0, OCEAN=200000.0, research_type='private',
        #             receiving_agents = {"market": 1.0}))
        #     private_researcher_agents.append(VVersatileResearcherAgent(
        #             name = "researcher%x" % i, evaluator = "dao_treasury",
        #             USD=0.0, OCEAN=200000.0, research_type='private',
        #             receiving_agents = {"market": 1.0}))

        # new_agents.append(ResearcherGeneratorAgent(name="generator", evaluator = "dao_treasury",
        #                                             USD=0.0, OCEAN=0.0, generator_cond_type="time", generator_type="dec", time_interval=30000, start_gen=5))

        new_agents.append(PrivateKnowledgeMarketAgent(
            name = "private_market", USD=0.0, OCEAN=0.0,
            transaction_fees_percentage=0.1,
            fee_receiving_agents={"dao_treasury": 1.0}))
        
        new_agents.append(PublicKnowledgeMarketAgent(
            name = "public_market", USD=0.0, OCEAN=0.0,
            transaction_fees_percentage=0.1,
            fee_receiving_agents={"dao_treasury": 1.0}))

        new_agents.append(CommunityAgent(name="member", USD=0.0, OCEAN=10000.0))

        for agent in new_agents:
            self.agents[agent.name] = agent        

        for agent in researcher_agents:
            self.researchers[agent.name] = agent
        
        for agent in public_researcher_agents:
            self.public_researchers[agent.name] = agent
        
        for agent in private_researcher_agents:
            self.private_researchers[agent.name] = agent

        #track certain metrics over time, so that we don't have to load
        self.kpis = KPIs(self.ss.time_step)
                    
    def takeStep(self) -> None:
        """This happens once per tick"""
        #update agents
        #update kpis (global state values)
        super().takeStep()
        
        #update global state values: other
        self._speculation_valuation *= (1.0 + self._percent_increase_speculation_valuation_per_s * self.ss.time_step)

    #==============================================================      
    def marketplacePercentTollToOcean(self) -> float:
        return self._marketplace_percent_toll_to_ocean
    
    def percentToBurn(self) -> float:
        return self._percent_burn

    def percentToOpsciMrkt(self) -> float:
        return 1.0 - self._percent_burn
    
    def percentToOpsciDAO(self) -> float:
        return self._percent_dao

    def percentToSellers(self) -> float:
        return 1.0 - self._percent_dao
    
    def addResearcherAgent(self, agent):
        assert agent.name not in self.researchers, "have an agent with this name"
        assert agent.name not in self.private_researchers, "have an agent with this name"
        self.researchers[agent.name] = agent
        self.private_researchers[agent.name] = agent
    
def funcOne():
    return 1.0


