from google.adk.agents import Agent

root_agent = Agent(
    name = "gweb_agent",
    model = "gemini-2.0-flash",
    description = "Welcoming Agent",
    instruction = "you are a helpful agent ! ask for the user name and greet them",
)