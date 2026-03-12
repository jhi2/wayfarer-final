from oompaloompa import OompaLoompaManager

def dothething(ipt, guide_text):
    #Use the default model

    oom = OompaLoompaManager()
    oom.setup_agent(
        "itinerary_agent",
        (
            "Combine all of these agent outputs into a full travel itinerary: "
            f"{guide_text}. The original input is {ipt}. "
            "It must be a full schedule for every day of the trip. "
            "Write the output as static HTML. No styling."
        ),
        tools=[]
    )

    oom.start_all_agents()
    oom.join_all()

    return oom.get_agent_result("itinerary_agent")