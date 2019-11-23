from hurricane_simulator import Simulator
from agents.base_agents import Human, Greedy, Vandal
from agents.search_agents import GreedySearch, RTAStar, AStar
from configurator import Configurator

if __name__ == '__main__':
    Configurator.get_user_config()

    # part I #
    # basic_config = 'tests/basic.config'
    # base_agents_sim = Simulator(basic_config)
    # base_agents_sim.run_simulation([Human, Greedy, Vandal])

    # part II #
    # search_config = 'tests/graph1.config'
    # for search_agent_type in [GreedySearch, RTAStar, AStar]:
    #     search_agent_sim = Simulator(search_config)
    #     search_agent_sim.run_simulation([search_agent_type])

    # Bonus #
    # for search_agent_type in [GreedySearch, RTAStar, AStar]:
    #     bonus_sim = Simulator()
    #     bonus_sim.run_simulation([search_agent_type, Vandal])

    # Additional tests
    all_agents = [Human, Greedy, Vandal, GreedySearch, RTAStar, AStar]
    active_agents = [agent_type for agent_type in all_agents if agent_type.__name__ in Configurator.agents]
    sim = Simulator()
    sim.run_simulation(active_agents)
