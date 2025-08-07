# File: core/app/agents/team.py
# --- Purpose: Defines the multi-agent team using AutoGen. ---

import autogen
from . import prompts, tools
from functools import partial

# --- LLM Configuration ---
# This configuration tells the agents how to connect to your local Ollama models.
# We will define a list of configurations, one for each specialized model.
llm_config_list = [
    {
        "model": "hermes-2-pro-llama-3-8b",  # The Manager
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
    },
    {
        "model": "qwq-abliterated:32b",  # The Deep Thinker
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
    },
    {
        "model": "mythomax-l2-13b",  # The Ghostwriter
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
    },
    {
        "model": "deepseek-coder:6.7b",  # The Code Writer
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
    },
    {
        "model": "huihui_ai/baronllm-abliterated:8b",  # The Security Expert
        "api_key": "ollama",
        "base_url": "http://localhost:11434/v1",
    },
]

# --- Agent Definitions ---

# The user's proxy. It represents you in the conversation and executes tools.
user_proxy = autogen.UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=False,
    system_message="You are the user's representative. You execute functions on their behalf. Reply TERMINATE when the task is done."
)

# The Manager Agent
manager = autogen.ConversableAgent(
    name="KairosManager",
    system_message=prompts.MANAGER_PROMPT,
    llm_config={"config_list": llm_config_list, "filter_dict": {"model": ["hermes-2-pro-llama-3-8b"]}},
)

# The Research Agent (Deep Thinker)
researcher = autogen.ConversableAgent(
    name="ResearchAgent",
    system_message=prompts.DEEP_THINKER_PROMPT,
    llm_config={"config_list": llm_config_list, "filter_dict": {"model": ["qwq-abliterated:32b"]}},
)

# The Ghostwriter Agent
ghostwriter = autogen.ConversableAgent(
    name="GhostwriterAgent",
    system_message=prompts.GHOSTWRITER_PROMPT,
    llm_config={"config_list": llm_config_list, "filter_dict": {"model": ["mythomax-l2-13b"]}},
)

# The TaskMaster Agent
taskmaster = autogen.ConversableAgent(
    name="TaskMasterAgent",
    system_message=prompts.TASK_MASTER_PROMPT,
    llm_config={"config_list": llm_config_list, "filter_dict": {"model": ["hermes-2-pro-llama-3-8b"]}},
)

# --- The Group Chat ---
# We create a group chat that includes all our agents.
groupchat = autogen.GroupChat(
    agents=[user_proxy, manager, researcher, ghostwriter, taskmaster],
    messages=[],
    max_round=15,
    speaker_selection_method="auto"  # The manager will decide who speaks next
)

# The Group Chat Manager orchestrates the conversation.
group_chat_manager = autogen.GroupChatManager(
    groupchat=groupchat,
    llm_config={"config_list": llm_config_list, "filter_dict": {"model": ["hermes-2-pro-llama-3-8b"]}},
)


# --- Tool Registration ---
# We need to register our Python functions as tools that the agents can use.
# We use functools.partial to pass the db session and user_id to the tools when they are called.
def register_tools(db_session, user_id):
    # Create partial functions with the database session and user_id baked in.
    retrieve_context_with_context = partial(tools.retrieve_context, db=db_session, user_id=user_id)
    create_note_with_context = partial(tools.create_note_tool, db=db_session, user_id=user_id)
    create_project_with_context = partial(tools.create_project_tool, db=db_session, user_id=user_id)
    create_task_with_context = partial(tools.create_task_tool, db=db_session, user_id=user_id)
    log_anchor_with_context = partial(tools.log_anchor_tool, db=db_session, user_id=user_id)

    # Register tools with the agents that should have access to them.
    # The UserProxy executes the code, and the specialist agents suggest calling it.

    # Research Tool
    user_proxy.register_for_execution(name="retrieve_context")(retrieve_context_with_context)
    researcher.register_for_llm(name="retrieve_context",
                                description="Search the user's knowledge base for context on a query.")(
        retrieve_context_with_context)

    # Task Management Tools
    user_proxy.register_for_execution(name="create_note_tool")(create_note_with_context)
    taskmaster.register_for_llm(name="create_note_tool", description="Create a new note in the user's database.")(
        create_note_with_context)

    user_proxy.register_for_execution(name="create_project_tool")(create_project_with_context)
    taskmaster.register_for_llm(name="create_project_tool", description="Create a new project in the user's database.")(
        create_project_with_context)

    user_proxy.register_for_execution(name="create_task_tool")(create_task_with_context)
    taskmaster.register_for_llm(name="create_task_tool",
                                description="Create a new task under a specific project for the user.")(
        create_task_with_context)

    user_proxy.register_for_execution(name="log_anchor_tool")(log_anchor_with_context)
    taskmaster.register_for_llm(name="log_anchor_tool", description="Logs a Micro Anchor practice for the user.")(
        log_anchor_with_context)

