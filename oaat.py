def run_agents_sequential(manager, agents):
    results = {}
    for agent_id, prompt in agents.items():
        manager.setup_agent(id=agent_id, prompt=prompt)
        manager.start_all_agents()   # only 1 agent running
        manager.join_all()
        results[agent_id] = manager.get_agent_result(agent_id)
        manager.threads.clear()  # clear so next agent can run
    return results